# Financial Document Q&A Bot

[![CI](https://github.com/aniketnandi/financial-qa-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/aniketnandi/financial-qa-bot/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

This project answers natural-language questions about SEC filings (10-Ks) and shows where each answer came from. It has two answering modes:

- **`/ask`**: single-shot RAG. Retrieve 4 chunks, then answer with page citations.
- **`/ask_agent`**: a Gemini function-calling agent. It plans its own retrieval and calculation steps (growth %, margin %) and returns a full tool-call trace.

Both modes are served as a **FastAPI** service and as an **MCP server**, so they can be used from Claude Desktop, Claude Code or Cursor. A golden-set **eval harness** measures retrieval and answer quality.

**Stack:** Python · LangChain · FAISS · HuggingFace `all-MiniLM-L6-v2` · BM25 · Gemini API (`google-genai`) · FastAPI · MCP

## Results at a glance

These results come from a hand-built 20-question golden set over Tesla's FY2023 10-K. It has lookups, calculations, multi-hop questions and questions the filing can't answer. See [`evals/`](evals/README.md).

| What was measured | Result |
|---|---|
| Retrieval recall@4 with 1000-char chunks (baseline) | 65% |
| Retrieval recall@4 with **2000-char chunks** (current) | **94%** (100% @ k=8) |
| Hybrid dense + BM25 (RRF) recall@4 | 76%: tested and rejected for this corpus |
| `/ask` RAG answer accuracy | **16/20 (80%)**, 3/3 unanswerable questions correctly refused |
| `/ask_agent` on calculation + multi-hop questions | **6/6 answered correctly**, 3 still pending because of free-tier API quota |

**What the evals showed:**

- **Chunk size beat clever retrieval.** At 1000 characters, income-statement rows were split away from their labels and ranked 129th to 315th of 564 chunks. At 2000 characters, each table stayed in one chunk.
- **BM25 hurt.** 10-K tables repeat the same figures across many pages, so keyword matching ranked the wrong pages highly. The hybrid retriever is still in `retrieval.py` for comparison, but the API uses dense retrieval.
- **The agent addresses RAG's main failure mode.** Most of RAG's misses were refusals on margin questions where the evidence *was* retrieved but needed arithmetic. The agent's calculator tools answer every one of those questions it has been scored on.

## Architecture

```
                 ingest.py
PDFs ──► PyPDF ──► 2000/300 chunker ──► MiniLM embeddings ──► FAISS index
                                                                 │
                                                       retrieval.py (dense | bm25 | hybrid)
                                                                 │
              ┌──────────────────────────────────────────────────┼───────────────────────┐
              ▼                                                  ▼                       ▼
  rag.py  /ask                                       agent.py  /ask_agent         mcp_server.py
  top-4 chunks → Gemini → answer + pages     Gemini ⇄ tools (retrieve_context,    search / ask / analyze
                                             calculate_growth, calculate_margin)  tools for MCP clients
                                             ≤ 8 steps → answer + trace
```

| File | Purpose |
|---|---|
| `ingest.py` | Builds the FAISS index from `data/*.pdf` (chunk size, overlap and output directory are configurable) |
| `retrieval.py` | Dense, BM25 and reciprocal-rank-fusion retrievers. The API, agent, MCP server and eval all share this code |
| `rag.py` | Single-shot grounded answer with source pages |
| `agent.py` / `tools.py` | Multi-step function-calling loop and its tools |
| `main.py` | FastAPI app. Maps Gemini errors to 429/503/502 |
| `mcp_server.py` | MCP server exposing the same capabilities |
| `evals/` | Golden set, retrieval eval (no LLM calls) and answer eval |
| `tests/` | Unit tests for tools, retrieval fusion and API validation |

## Quickstart

Requires Python 3.11+ and a free [Gemini API key](https://aistudio.google.com).

```bash
git clone https://github.com/aniketnandi/financial-qa-bot.git
cd financial-qa-bot
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # then add your GEMINI_API_KEY
python ingest.py                   # indexes the Tesla 10-K in data/ (≈1 min on CPU)
uvicorn main:app --reload
```

Open http://localhost:8000/docs for the interactive Swagger UI, or use curl:

```bash
curl -X POST http://localhost:8000/ask_agent \
  -H "Content-Type: application/json" \
  -d '{"question": "What was Tesla'\''s year-over-year revenue growth from 2022 to 2023?"}'
```

Example response (abridged):

```json
{
  "question": "What was Tesla's year-over-year revenue growth from 2022 to 2023?",
  "answer": "Tesla's total revenue grew 18.80%, from $81,462M in 2022 to $96,773M in 2023.",
  "trace": [
    {"tool": "retrieve_context", "args": {"query": "total revenues 2023 2022"}, "result": "[page 50] ..."},
    {"tool": "calculate_growth", "args": {"current": 96773, "previous": 81462}, "result": "18.80%"}
  ]
}
```

`/ask` returns `{"question", "answer", "sources": [page numbers]}`.

To use your own filings, drop any 10-K or annual-report PDFs into `data/` (free from [SEC EDGAR](https://www.sec.gov/edgar/search/)) and re-run `python ingest.py`.

## MCP server

`mcp_server.py` lets MCP clients (Claude Desktop, Claude Code, Cursor) query the filings directly:

| Tool | What it does | Gemini calls |
|---|---|---|
| `search_filings(query, k)` | Top-k passages with page numbers | none |
| `ask_filings(question)` | Single-shot RAG answer + source pages | 1 |
| `analyze_filings(question)` | Multi-step agent answer + tool-call trace | several |

Register it with your client using the command `python mcp_server.py` (stdio transport), or try it in the MCP Inspector with `npx @modelcontextprotocol/inspector`.

## Evaluation

```bash
# Retrieval only: no server or API key needed
python evals/retrieval_eval.py --retriever dense bm25 hybrid --k 4 8 --diagnose

# End-to-end answers (start the API first)
python evals/eval_qa.py --endpoint rag=/ask --endpoint agent=/ask_agent \
  --golden evals/golden_set.jsonl --out evals/results --retries 2 --resume
```

Answers are scored with deterministic checks (numbers within ±1%, required keywords, refusal detection), not an LLM judge. API errors are reported separately from wrong answers. See [`evals/README.md`](evals/README.md) for the methodology and the full per-question results.

## Tests

```bash
pip install pytest
pytest
```

## Safeguards

- **Grounded answers:** both modes are told to use only retrieved filing content and never invent figures.
- **Refusal over guessing:** unanswerable questions get an explicit "could not find" answer (3/3 in the eval).
- **Traceability:** `/ask` cites pages, and `/ask_agent` returns every tool call with its arguments and result.
- **Bounded agent:** the agent stops after 8 steps, and tool exceptions are fed back to the model instead of crashing the request.
- **Clean errors:** upstream rate limits and outages come back as 429/503 instead of an opaque 500.

## Limitations and next steps

- The eval covers one filing and 20 questions. The next step is to extend it to several companies and years.
- The agent eval is incomplete because of Gemini free-tier quota. A 429 means the daily quota is used up.
- Possible next steps: a cross-encoder reranker, and table-aware chunking so the system doesn't depend on chunk size alone.

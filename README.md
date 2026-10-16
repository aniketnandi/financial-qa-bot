# Financial Document Q&A Bot

[![CI](https://github.com/aniketnandi/financial-qa-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/aniketnandi/financial-qa-bot/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

This project answers natural-language questions about SEC filings (10-Ks) and shows where each answer came from. It has two answering modes:

- **`/ask`**: single-shot RAG. Retrieve 4 chunks, then answer with page citations.
- **`/ask_agent`**: a function-calling agent. It plans its own retrieval and calculation steps (growth %, margin %) and returns a full tool-call trace.

Both modes are served as a **FastAPI** service and as an **MCP server**, so they can be used from Claude Desktop, Claude Code or Cursor. The LLM backend is pluggable: **Gemini** (default) or **Azure OpenAI**, chosen with one environment variable. A Docker image and a guide for deploying to **Azure Container Apps** are included. A golden-set **eval harness** measures retrieval and answer quality.

**Stack:** Python · LangChain · FAISS · HuggingFace `all-MiniLM-L6-v2` · BM25 · Gemini API · Azure OpenAI · FastAPI · MCP · Docker · Azure Container Apps · GitHub Actions

## Results at a glance

These results come from a hand-built 20-question golden set over Tesla's FY2023 10-K. It has lookups, calculations, multi-hop questions and questions the filing can't answer. The answer results below were measured with the Gemini backend. See [`evals/`](evals/README.md).

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

## See it in action

These are real outputs from the bot over Tesla's FY2023 10-K, copied from the saved eval runs in [`evals/results_rag/`](evals/results_rag/results.jsonl) and [`evals/results_agent/`](evals/results_agent/results.jsonl). The wording is unchanged. Only the formatting was flattened to fit the README: the model's LaTeX math was written out as plain text, and nested lists were collapsed onto one line.

### Same question, two modes

**Q: What was Tesla's net profit margin in 2023?**

**`/ask` (single-shot RAG)** retrieved the right income-statement rows, but the margin isn't printed in the filing, so it declined instead of guessing:

> I could not find this information in the provided documents.

**`/ask_agent` (tool-calling agent)** retrieved the same figures, then called `calculate_margin`:

> According to Tesla's Consolidated Statements of Operations in its 2023 Form 10-K, the financial results for the year ended December 31, 2023 were:
>
> * **Total Revenues:** $96,773 million
> * **Net Income:** $14,974 million
> * **Net Income Attributable to Common Stockholders:** $14,997 million
>
> **Net Profit Margin Calculations:**
> * **Based on Total Net Income:** $14,974 million / $96,773 million × 100 = **15.47%**
> * **Based on Net Income Attributable to Common Stockholders:** $14,997 million / $96,773 million × 100 = **15.50%**

This gap is the reason the agent exists: two of RAG's four eval misses were cases where the numbers were in the retrieved context but the answer needed arithmetic.

### Multi-step reasoning across years

**Q: Did Tesla's total operating expenses grow faster or slower than its total revenue from 2022 to 2023?** (`/ask_agent`)

> From 2022 to 2023, Tesla's **total operating expenses grew faster than its total revenue**.
>
> 1. **Total Revenue:** 2022: $81,462 million · 2023: $96,773 million · Growth Rate: **18.80%**
> 2. **Total Operating Expenses:** 2022: $7,197 million · 2023: $8,769 million · Growth Rate: **21.84%**
>
> With total operating expenses growing at **21.84%** compared to total revenue growth of **18.80%**, Tesla's operating expenses grew **faster** than its total revenue over this period.

### Refusing questions the filing can't answer

| Question (`/ask`) | Answer |
|---|---|
| What is Tesla's stock price today? | I could not find this information in the provided documents. |
| What total revenue will Tesla report for 2025? | I could not find this information in the provided documents. |
| What was Ford Motor Company's total revenue in 2023? | I could not find this information in the provided documents. |

All of these figures match the 10-K: revenue $96,773M (2022: $81,462M), net income $14,974M, operating expenses $8,769M (2022: $7,197M).

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
  top-4 chunks → LLM → answer + pages        LLM ⇄ tools (retrieve_context,       search / ask / analyze
                                             calculate_growth, calculate_margin)  tools for MCP clients
                                             ≤ 8 steps → answer + trace
                     LLM = llm.py: Gemini (default) | Azure OpenAI
```

| File | Purpose |
|---|---|
| `ingest.py` | Builds the FAISS index from `data/*.pdf` (chunk size, overlap and output directory are configurable) |
| `retrieval.py` | Dense, BM25 and reciprocal-rank-fusion retrievers. The API, agent, MCP server and eval all share this code |
| `llm.py` | Pluggable LLM backend (Gemini or Azure OpenAI), with provider errors normalized for the API |
| `rag.py` | Single-shot grounded answer with source pages |
| `agent.py` / `tools.py` | Multi-step function-calling loop for each provider, and its tools (declared once) |
| `main.py` | FastAPI app. Maps provider errors to 429/503/502, with an optional API-key check |
| `mcp_server.py` | MCP server exposing the same capabilities |
| `evals/` | Golden set, retrieval eval (no LLM calls) and answer eval |
| `tests/` | Unit tests for tools, retrieval fusion, API validation, and both provider loops (with mocked LLM clients) |
| `Dockerfile` / `docs/DEPLOY_AZURE.md` | Container image (index and embedding model built in) and the Azure Container Apps deployment guide |

## Quickstart

Requires Python 3.11+ and either a free [Gemini API key](https://aistudio.google.com) or an Azure OpenAI deployment.

```bash
git clone https://github.com/aniketnandi/financial-qa-bot.git
cd financial-qa-bot
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env               # then add your GEMINI_API_KEY (or the Azure OpenAI settings)
python ingest.py                   # indexes the Tesla 10-K in data/ (≈1 min on CPU)
uvicorn main:app --reload
```

Open http://localhost:8000/docs for the interactive Swagger UI, or use curl:

```bash
curl -X POST http://localhost:8000/ask_agent \
  -H "Content-Type: application/json" \
  -d '{"question": "What was Tesla'\''s year-over-year revenue growth from 2022 to 2023?"}'
```

Response format (illustrative values; the `/ask_agent` response includes the full tool-call trace):

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

## Deploy to Azure

The API can run on **Azure Container Apps** with **Azure OpenAI** as the LLM:

- CI builds the Docker image, smoke-tests it and publishes it to GitHub Container Registry.
- Container Apps pulls the image and scales from 0 to 1 replicas.
- The Azure OpenAI key and the API key are stored as Container Apps secrets.

Set `LLM_PROVIDER=azure_openai` to use the same backend locally. For step-by-step Cloud Shell commands, cost controls and troubleshooting, see [`docs/DEPLOY_AZURE.md`](docs/DEPLOY_AZURE.md).

## MCP server

`mcp_server.py` lets MCP clients (Claude Desktop, Claude Code, Cursor) query the filings directly:

| Tool | What it does | LLM calls |
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
- **Clean errors:** upstream rate limits and outages come back as 429/503 instead of an opaque 500, for either provider.
- **Protected deployment:** with `API_KEY` set, the POST endpoints require an `X-API-Key` header, and the keys live in Container Apps secrets.

## Limitations and next steps

- The eval covers one filing and 20 questions. The next step is to extend it to several companies and years.
- The agent eval is incomplete because of Gemini free-tier quota. A 429 means the daily quota is used up.
- Possible next steps: a cross-encoder reranker, and table-aware chunking so the system doesn't depend on chunk size alone.

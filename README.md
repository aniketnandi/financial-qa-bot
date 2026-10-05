# Financial Document Q&A Bot

A RAG pipeline and tool-calling agent that answer natural-language questions over financial PDF filings (e.g. SEC 10-Ks). Built with LangChain, HuggingFace embeddings, FAISS, Gemini API, and FastAPI.

## Architecture

```
PDF files → PyPDF loader → text chunker → HuggingFace embeddings → FAISS index
                                                                         ↓
/ask:       question → embeddings → FAISS top-4 chunks → Gemini → answer + source pages
/ask_agent: question → Gemini agent ⇄ tools (retrieve_context, calculate_growth, calculate_margin) → answer + tool-call trace
```

## Project Structure

```
financial-qa-bot/
├── requirements.txt   # dependencies
├── .env               # API key (never commit this)
├── ingest.py          # builds the FAISS index from PDFs
├── rag.py             # single-shot RAG logic
├── agent.py           # multi-step tool-calling agent
├── tools.py           # retrieval + growth/margin calculation tools
├── main.py            # FastAPI app
├── mcp_server.py      # MCP server exposing the bot as tools
├── evals/             # golden-set retrieval and answer evals
└── data/              # drop your PDF(s) here
```

## Setup

### 1. Clone and create a virtual environment
```bash
     python -m venv .venv
     .venv\Scripts\activate      # Windows
     source .venv/bin/activate   # macOS/Linux
```

### 2. Install dependencies
```bash
     pip install -r requirements.txt
```

### 3. Add your Gemini API key
Edit `.env` and replace the placeholder:
```
GEMINI_API_KEY=your_actual_key_here
```
Get a free key at: https://aistudio.google.com

### 4. Add PDF files
Create a `data/` folder in the project root and drop one or more financial PDFs into it.
Any annual report, 10-K filing, earnings document, or financial statement works.
You can download free sample PDFs from SEC EDGAR: https://www.sec.gov/cgi-bin/browse-edgar

### 5. Run ingestion
```bash
python ingest.py
```
This loads the PDFs, splits them into chunks, generates embeddings, and saves the FAISS index to `faiss_index/`. Run this once, or re-run whenever you add new PDFs.

### 6. Start the API
```bash
uvicorn main:app --reload
```
The API will be available at http://localhost:8000

### 7. Test it
Open http://localhost:8000/docs in your browser — FastAPI auto-generates an interactive Swagger UI.

Or use curl:
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What was the total revenue for the year?"}'
```
```bash
curl -X POST http://localhost:8000/ask_agent \
  -H "Content-Type: application/json" \
  -d '{"question": "What was revenue growth year over year?"}'
```
Expected `/ask` response:
```json
{
  "question": "What was the total revenue for the year?",
  "answer": "The total revenue for the year was $X billion, as reported in...",
  "sources": [4, 5, 12]
}
```
Expected `/ask_agent` response:
```json
{
  "question": "What was revenue growth year over year?",
  "answer": "Revenue grew X% year over year...",
  "trace": [
    {"tool": "retrieve_context", "args": {"query": "..."}, "result": "..."},
    {"tool": "calculate_growth", "args": {"current": 0, "previous": 0}, "result": "X%"}
  ]
}
```

## How it works

1. **Ingestion** — PDFs are loaded page by page, split into 2000-character chunks with 300-character overlap, and embedded using the HuggingFace all-MiniLM-L6-v2 model. The vectors are stored in a local FAISS index and the chunk size was chosen from the eval.

2. **Retrieval** — At query time, the question is embedded using the same model. FAISS finds the 4 most similar chunks by nearest-neighbor search (L2 distance).

3. **Generation** — The retrieved chunks are passed as context to gemini-3.6-flash along with the question. The LLM is instructed to answer only from the provided context. If the answer isn't in the context, it replies "I could not find this information in the provided documents."

4. **API** — FastAPI exposes two POST endpoints: /ask returns the answer with source page numbers, and /ask_agent returns the answer with a full tool-call trace, capped at 8 reasoning steps.

## MCP server

`mcp_server.py` exposes the bot over the Model Context Protocol, so MCP clients (Claude Desktop, Claude Code, Cursor) can use the filings as tools:

| Tool | What it does | Gemini calls |
|---|---|---|
| `search_filings(query, k)` | Top-k passages with page numbers | none |
| `ask_filings(question)` | Single-shot RAG answer + source pages | 1 |
| `analyze_filings(question)` | Multi-step agent answer + tool-call trace | several |

Test it in the MCP Inspector (requires Node.js), with Command `.venv\Scripts\python.exe` and Arguments `mcp_server.py`:
```bash
npx @modelcontextprotocol/inspector
```

## Evaluation

Retrieval is evaluated against a 20-question golden set built from Tesla's FY2023 10-K (`evals/`).

| Chunk size / overlap | Top-4 retrieval recall |
|---|---|
| 1000 / 150 | 65% |
| 2000 / 300 | 94% |

Raising chunk size to 2000 kept multi-row financial tables intact within a single chunk, which is why it is the default in `ingest.py`. Answer evaluation is in progress (Gemini free-tier quota); see `evals/README.md`.

Run the retrieval eval from the project root (no server or API key needed):
```bash
python evals/retrieval_eval.py --k 4 8 --diagnose
```

To run the answer eval, start the API first, then:
```bash
python evals/eval_qa.py --endpoint rag=/ask --endpoint agent=/ask_agent --golden evals/golden_set.jsonl --out evals/results --retries 2 --resume
```

See [`evals/README.md`](evals/README.md) for flags, scoring rules, and full results.

## Safeguards

- **Grounded answers:** both endpoints instruct the model to use only retrieved filing content and not invent figures.
- **Refusal over guessing:** if the answer isn't in the retrieved context, the bot says so instead of guessing.
- **Traceability:** `/ask` returns source page numbers; `/ask_agent` returns every tool call with its arguments and result.
- **Bounded agent:** the agent loop is capped at 8 steps and told to stop retrieving once it has the needed figures.

## Notes
- The FAISS index is saved locally — no cloud storage needed
- `.env` is gitignored — never commit your API key
- Re-run `ingest.py` any time you add new PDFs to `data/`
  
### Note: This project uses the Gemini API (free tier). If you hit a 429 RESOURCE_EXHAUSTED error, your daily quota is exhausted, wait 24 hours or add billing to your Google AI Studio account.

# Financial Document Q&A Bot

A RAG (Retrieval-Augmented Generation) pipeline that answers natural-language questions over financial PDF documents. Built with LangChain, Gemini API, FAISS, and FastAPI.

## Architecture

```
PDF files → PyPDF loader → text chunker → Gemini embeddings → FAISS index
                                                                     ↓
User question → Gemini embeddings → FAISS retrieval → top-k chunks → Gemini LLM → answer
```

## Project Structure

```
financial-qa-bot/
├── requirements.txt   # dependencies
├── .env               # API key (never commit this)
├── ingest.py          # builds the FAISS index from PDFs
├── rag.py             # RAG chain logic
├── main.py            # FastAPI app
└── data/              # drop your PDF(s) here
```

## Setup

### 1. Clone and open in IntelliJ
Open the project folder in IntelliJ. Make sure the Python plugin is installed and a Python 3.9+ interpreter is configured.

### 2. Install dependencies
Open the IntelliJ terminal (Alt+F12) and run:
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

Expected response:
```json
{
  "question": "What was the total revenue for the year?",
  "answer": "The total revenue for the year was $X billion, as reported in...",
  "sources": [4, 5, 12]
}
```

## How it works

1. **Ingestion** — PDFs are loaded page by page, split into 1000-character chunks with 150-character overlap, and embedded using Gemini's `embedding-001` model. The vectors are stored in a local FAISS index.

2. **Retrieval** — At query time, the question is embedded using the same model. FAISS finds the 4 most similar chunks by cosine similarity.

3. **Generation** — The retrieved chunks are passed as context to Gemini 1.5 Flash along with the question. The LLM is instructed to answer only from the provided context.

4. **API** — FastAPI exposes a `/ask` POST endpoint. The response includes the answer and the source page numbers from the original PDFs.

## Notes
- The FAISS index is saved locally — no cloud storage needed
- `.env` is gitignored — never commit your API key
- Re-run `ingest.py` any time you add new PDFs to `data/`
  
### Note: This project uses the Gemini API (free tier). If you hit a 429 RESOURCE_EXHAUSTED error, your daily quota is exhausted, wait 24 hours or add billing to your Google AI Studio account.
"""
main.py
FastAPI application exposing:
    GET  /            - health check
    POST /ask         - original single-shot RAG endpoint (rag.py)
    POST /ask_agent   - multi-step tool-calling agent endpoint (agent.py)

If the API_KEY environment variable is set, both POST endpoints require a
matching X-API-Key header (used for the public Azure deployment). Unset, the
API is open, as for local use.
"""

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel
from rag import get_answer
from retrieval import INDEX_DIR
from agent import run_agent
import hmac
import os
import logging
import llm

logger = logging.getLogger("financial_qa")
logging.basicConfig(level=logging.INFO)


def upstream_error(e: llm.UpstreamError) -> HTTPException:
    """Translate a model provider error into a meaningful HTTP response."""
    logger.warning("Model provider error %s: %s", e.code, e.message)
    if e.code == 429:
        return HTTPException(
            status_code=429,
            detail="Model provider rate limit or quota exceeded. Try again later.",
        )
    if e.code is None or e.code >= 500:
        return HTTPException(
            status_code=503,
            detail="Model provider temporarily unavailable. Try again shortly.",
        )
    return HTTPException(status_code=502, detail="Upstream model request failed.")


def require_api_key(x_api_key: str = Header(default="")):
    expected = os.getenv("API_KEY")
    if expected and not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Missing or invalid X-API-Key header.")

app = FastAPI(
    title="Financial Document Q&A Bot",
    description="RAG pipeline and agentic tool-calling assistant over financial PDFs, using LangChain, FAISS, and Gemini or Azure OpenAI.",
    version="1.2.0",
)


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    question: str
    answer: str
    sources: list


class AgentAnswerResponse(BaseModel):
    question: str
    answer: str
    trace: list


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Financial Q&A Bot is running.", "llm_provider": llm.provider()}


@app.post("/ask", response_model=AnswerResponse, dependencies=[Depends(require_api_key)])
def ask_question(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if not os.path.exists(INDEX_DIR):
        raise HTTPException(
            status_code=503,
            detail="FAISS index not found. Run ingest.py first."
        )

    try:
        result = get_answer(request.question)
        return AnswerResponse(
            question=request.question,
            answer=result["answer"],
            sources=result["sources"],
        )
    except llm.UpstreamError as e:
        raise upstream_error(e)
    except Exception:
        logger.exception("Unhandled error in /ask")
        raise HTTPException(status_code=500, detail="Internal server error.")


@app.post("/ask_agent", response_model=AgentAnswerResponse, dependencies=[Depends(require_api_key)])
def ask_agent_question(request: QuestionRequest):
    """Agentic endpoint: the model plans its own retrieval + calculation steps
    instead of following a fixed retrieve-then-answer chain. Use this for
    questions that need computed metrics (growth, margin) on top of retrieved
    figures, or multi-part questions."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if not os.path.exists(INDEX_DIR):
        raise HTTPException(
            status_code=503,
            detail="FAISS index not found. Run ingest.py first."
        )

    try:
        result = run_agent(request.question)
        return AgentAnswerResponse(
            question=request.question,
            answer=result["answer"],
            trace=result["trace"],
        )
    except llm.UpstreamError as e:
        raise upstream_error(e)
    except Exception:
        logger.exception("Unhandled error in /ask_agent")
        raise HTTPException(status_code=500, detail="Internal server error.")

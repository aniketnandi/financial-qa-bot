"""
main.py
FastAPI application exposing:
    GET  /            - health check
    POST /ask         - original single-shot RAG endpoint (rag.py)
    POST /ask_agent   - multi-step tool-calling agent endpoint (agent.py)
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag import get_answer
from agent import run_agent
import os
import logging
from google.genai import errors as genai_errors

logger = logging.getLogger("financial_qa")
logging.basicConfig(level=logging.INFO)


def upstream_error(e: genai_errors.APIError) -> HTTPException:
    """Translate a Gemini API error into a meaningful HTTP response."""
    logger.warning("Gemini API error %s: %s", e.code, e.message)
    if e.code == 429:
        return HTTPException(
            status_code=429,
            detail="Model provider rate limit or quota exceeded. Try again later.",
        )
    if e.code and e.code >= 500:
        return HTTPException(
            status_code=503,
            detail="Model provider temporarily unavailable. Try again shortly.",
        )
    return HTTPException(status_code=502, detail="Upstream model request failed.")

app = FastAPI(
    title="Financial Document Q&A Bot",
    description="RAG pipeline and agentic tool-calling assistant over financial PDFs, using LangChain, Gemini API, and FAISS.",
    version="1.1.0",
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
    return {"status": "ok", "message": "Financial Q&A Bot is running."}


@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if not os.path.exists("faiss_index"):
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
    except genai_errors.APIError as e:
        raise upstream_error(e)
    except Exception:
        logger.exception("Unhandled error in /ask")
        raise HTTPException(status_code=500, detail="Internal server error.")


@app.post("/ask_agent", response_model=AgentAnswerResponse)
def ask_agent_question(request: QuestionRequest):
    """Agentic endpoint: the model plans its own retrieval + calculation steps
    instead of following a fixed retrieve-then-answer chain. Use this for
    questions that need computed metrics (growth, margin) on top of retrieved
    figures, or multi-part questions."""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if not os.path.exists("faiss_index"):
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
    except genai_errors.APIError as e:
        raise upstream_error(e)
    except Exception:
        logger.exception("Unhandled error in /ask_agent")
        raise HTTPException(status_code=500, detail="Internal server error.")

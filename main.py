"""
main.py
FastAPI application exposing two endpoints:
    GET  /          — health check
    POST /ask       — accepts a question, returns answer + source pages
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rag import get_answer
import os

app = FastAPI(
    title="Financial Document Q&A Bot",
    description="RAG pipeline using LangChain, Gemini API, and FAISS over financial PDFs.",
    version="1.0.0",
)


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    question: str
    answer: str
    sources: list


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Financial Q&A Bot is running."}


@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Check FAISS index exists
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

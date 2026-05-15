"""
rag.py
Loads the FAISS index from disk and exposes a single function:
    get_answer(question: str) -> dict
Uses HuggingFace embeddings for retrieval and calls Gemini API
directly via google-genai SDK for generation.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from google import genai

INDEX_DIR = "faiss_index"

PROMPT_TEMPLATE = """You are a financial document assistant. Use only the context below to answer the question.
If the answer is not in the context, say "I could not find this information in the provided documents."

Context:
{context}

Question:
{question}

Answer:"""

# Load once at module import
_retriever = None
_genai_client = None


def load_retriever():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.load_local(
        INDEX_DIR,
        embeddings,
        allow_dangerous_deserialization=True,
    )
    return vectorstore.as_retriever(search_kwargs={"k": 4})


def get_answer(question: str) -> dict:
    global _retriever, _genai_client

    if _retriever is None:
        _retriever = load_retriever()

    if _genai_client is None:
        _genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # Retrieve relevant chunks
    source_docs = _retriever.invoke(question)
    context = "\n\n".join(doc.page_content for doc in source_docs)

    # Build prompt and call Gemini directly
    prompt = PROMPT_TEMPLATE.format(context=context, question=question)
    response = _genai_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    sources = sorted(list(set(
        doc.metadata.get("page", "unknown")
        for doc in source_docs
    )))

    return {
        "answer": response.text,
        "sources": sources,
    }
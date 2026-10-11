"""
rag.py
Loads the FAISS index from disk and exposes a single function:
    get_answer(question: str) -> dict
Retrieves with retrieval.py (dense FAISS search over all-MiniLM-L6-v2
embeddings, k=4) and calls the Gemini API directly via the google-genai SDK
for generation.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from google import genai

from retrieval import Retriever, load_store

MODEL = "gemini-3.6-flash"
NO_ANSWER = "The model returned no answer for this question."

PROMPT_TEMPLATE = """You are a financial document assistant. Use only the context below to answer the question.
If the answer is not in the context, say "I could not find this information in the provided documents."

Context:
{context}

Question:
{question}

Answer:"""

_retriever = None
_genai_client = None


# Dense retrieval scored best in the retrieval eval (94% recall@4 vs 76% for
# hybrid), so it is the default; see evals/README.md.
RETRIEVAL_MODE = "dense"
TOP_K = 4


def load_retriever():
    return Retriever(load_store(), mode=RETRIEVAL_MODE, k=TOP_K)


def get_retriever():
    """Load the FAISS retriever once and reuse it (shared with tools.py)."""
    global _retriever
    if _retriever is None:
        _retriever = load_retriever()
    return _retriever


def get_client():
    """Create the Gemini client once and reuse it (shared with agent.py)."""
    global _genai_client
    if _genai_client is None:
        _genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _genai_client


def get_answer(question: str) -> dict:
    source_docs = get_retriever().invoke(question)
    context = "\n\n".join(doc.page_content for doc in source_docs)

    prompt = PROMPT_TEMPLATE.format(context=context, question=question)
    response = get_client().models.generate_content(model=MODEL, contents=prompt)

    sources = sorted(
        {doc.metadata.get("page", "unknown") for doc in source_docs},
        key=lambda p: (isinstance(p, str), p),
    )

    return {
        "answer": response.text or NO_ANSWER,
        "sources": sources,
    }
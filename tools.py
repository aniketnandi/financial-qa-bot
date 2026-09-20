"""
tools.py
Defines the tools available to the financial agent:
    - retrieve_context(query): looks up relevant chunks from the existing FAISS index
    - calculate_growth(current, previous): % growth between two values
    - calculate_margin(profit, revenue): profit margin as a % of revenue

retrieve_context reuses load_retriever() from rag.py, so it's the same FAISS
index and embeddings your RAG pipeline already builds via ingest.py - no
duplicate retrieval logic.
"""

from rag import load_retriever

_retriever = None


def retrieve_context(query: str) -> str:
    """Retrieve the most relevant chunks from the ingested financial filings for a given query."""
    global _retriever
    if _retriever is None:
        _retriever = load_retriever()
    docs = _retriever.invoke(query)
    return "\n\n".join(
        f"[page {d.metadata.get('page', 'unknown')}] {d.page_content}" for d in docs
    )


def calculate_growth(current: float, previous: float) -> str:
    """Calculate the percentage growth between a previous and current numeric value."""
    if previous == 0:
        return "Cannot calculate growth: previous value is zero."
    growth = ((current - previous) / previous) * 100
    return f"{growth:.2f}%"


def calculate_margin(profit: float, revenue: float) -> str:
    """Calculate profit margin as a percentage of revenue."""
    if revenue == 0:
        return "Cannot calculate margin: revenue is zero."
    margin = (profit / revenue) * 100
    return f"{margin:.2f}%"

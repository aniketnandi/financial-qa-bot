"""
retrieval.py
Dense, sparse, and hybrid retrieval over the same chunks in faiss_index/.

    dense   - FAISS nearest-neighbor search over all-MiniLM-L6-v2 embeddings (original behavior)
    bm25    - BM25 keyword search (rank_bm25) over the same chunk texts
    hybrid  - reciprocal rank fusion (RRF) of the dense and BM25 rankings

Why hybrid: dense embeddings match meaning ("how much did Tesla spend on
research"), while BM25 matches exact tokens - line-item names and figures
like "Research and development" or "96,773" that embeddings tend to blur.
RRF combines the two rankings without having to calibrate their scores.

Shared by rag.py (and so tools.py and the agent), mcp_server.py, and
evals/retrieval_eval.py, so the API, the MCP tools, and the eval all use the
exact same retrieval code. No Gemini calls in this file.
"""

import re

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from rank_bm25 import BM25Okapi

INDEX_DIR = "faiss_index"
EMBED_MODEL = "all-MiniLM-L6-v2"
MODES = ("dense", "bm25", "hybrid")
RRF_K = 60          # standard RRF constant; dampens the weight of top ranks
CANDIDATES = 20     # how deep each ranking goes before fusion

# Lowercased words and numbers; keeps "96,773" and "18.2" as single tokens
TOKEN_RE = re.compile(r"[a-z0-9]+(?:[.,]\d+)*")


def tokenize(text: str) -> list:
    return TOKEN_RE.findall(text.lower())


def load_store(index_dir: str = INDEX_DIR) -> FAISS:
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return FAISS.load_local(index_dir, embeddings, allow_dangerous_deserialization=True)


def doc_key(doc) -> tuple:
    """Identity of a chunk across the two rankings."""
    return (doc.metadata.get("source"), doc.metadata.get("page"), doc.page_content)


def rrf(rankings: list, k: int = RRF_K) -> list:
    """Reciprocal rank fusion: score(d) = sum over rankings of 1 / (k + rank)."""
    scores, docs = {}, {}
    for ranking in rankings:
        for rank, doc in enumerate(ranking, start=1):
            key = doc_key(doc)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            docs.setdefault(key, doc)
    return [docs[key] for key in sorted(scores, key=scores.get, reverse=True)]


class Retriever:
    """Drop-in for the LangChain retriever rag.py used before: supports .invoke(query)."""

    def __init__(self, store: FAISS, mode: str = "dense", k: int = 4, candidates: int = CANDIDATES):
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}, got {mode!r}")
        self.store, self.mode, self.k, self.candidates = store, mode, k, candidates
        self.docs = list(store.docstore._dict.values())
        self._bm25 = None
        if mode != "dense":
            self._bm25 = BM25Okapi([tokenize(d.page_content) for d in self.docs])

    def dense(self, query: str, n: int) -> list:
        return self.store.similarity_search(query, k=n)

    def sparse(self, query: str, n: int) -> list:
        scores = self._bm25.get_scores(tokenize(query))
        top = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:n]
        return [self.docs[i] for i in top]

    def search(self, query: str, k: int = None) -> list:
        k = k or self.k
        if self.mode == "dense":
            return self.dense(query, k)
        if self.mode == "bm25":
            return self.sparse(query, k)
        n = max(k, self.candidates)
        return rrf([self.dense(query, n), self.sparse(query, n)])[:k]

    def invoke(self, query: str) -> list:
        return self.search(query)

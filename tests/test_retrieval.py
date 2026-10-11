import pytest
from langchain_core.documents import Document

from retrieval import Retriever, rrf, tokenize


def doc(text, page=0):
    return Document(page_content=text, metadata={"source": "x.pdf", "page": page})


def test_tokenize_keeps_financial_figures_whole():
    assert tokenize("Revenue was $96,773 million, up 18.8%") == [
        "revenue", "was", "96,773", "million", "up", "18.8",
    ]


def test_rrf_rewards_documents_ranked_well_by_both_retrievers():
    a, b, c = doc("a", 1), doc("b", 2), doc("c", 3)
    fused = rrf([[a, b, c], [b, c, a]])
    assert [d.page_content for d in fused] == ["b", "a", "c"]


def test_rrf_dedupes_the_same_chunk():
    a = doc("a", 1)
    assert len(rrf([[a], [doc("a", 1)]])) == 1


def test_retriever_rejects_unknown_mode():
    with pytest.raises(ValueError):
        Retriever(store=None, mode="semantic")

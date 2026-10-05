"""
mcp_server.py
Exposes the Financial Document Q&A Bot as an MCP (Model Context Protocol)
server, so any MCP client - Claude Desktop, Claude Code, Cursor - can use the
ingested filings as tools.

Tools:
    search_filings(query, k)    - raw passage retrieval with page numbers (no Gemini call)
    ask_filings(question)       - single-shot RAG answer with source pages (same as POST /ask)
    analyze_filings(question)   - multi-step tool-calling agent with its trace (same as POST /ask_agent)

All three reuse rag.py / agent.py, so the MCP tools and the FastAPI endpoints
share the same FAISS index, embeddings, and Gemini model.

Run (stdio transport; MCP clients launch it themselves):
    python mcp_server.py
Inspect interactively:
    mcp dev mcp_server.py
"""

import os

# MCP clients launch the server from their own working directory; switch to the
# project root so faiss_index/ and .env resolve the same way as for the API.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

try:  # mcp 2.x renamed FastMCP to MCPServer
    from mcp.server.mcpserver import MCPServer  # noqa: E402
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer  # noqa: E402

from agent import run_agent  # noqa: E402
from rag import get_answer, get_retriever  # noqa: E402

mcp = MCPServer("financial-filings")


@mcp.tool()
def search_filings(query: str, k: int = 4) -> list[dict]:
    """Search the ingested financial filings (e.g. 10-Ks) and return the top-k
    matching passages with their page numbers. Does not call an LLM, so use it
    to look up exact figures and quote them."""
    k = max(1, min(int(k), 20))
    retriever = get_retriever()
    docs = retriever.vectorstore.similarity_search(query, k=k)  # same FAISS index as /ask
    return [
        {
            "page": d.metadata.get("page"),
            "source": os.path.basename(str(d.metadata.get("source", ""))),
            "text": d.page_content,
        }
        for d in docs
    ]


@mcp.tool()
def ask_filings(question: str) -> dict:
    """Answer a factual question from the ingested financial filings using
    retrieval-augmented generation. Returns the answer and source page numbers."""
    return get_answer(question)


@mcp.tool()
def analyze_filings(question: str) -> dict:
    """Answer an analytical question (growth rates, margins, multi-year
    comparisons) with a multi-step agent that retrieves figures from the
    filings and runs calculations. Returns the answer and every tool call it made."""
    return run_agent(question)


if __name__ == "__main__":
    mcp.run()

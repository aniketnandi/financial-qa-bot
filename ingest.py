"""
ingest.py
Loads all PDFs from the data/ folder, splits them into chunks,
embeds them with HuggingFace all-MiniLM-L6-v2, and saves a FAISS index to disk.
Run this once before starting the API.

The defaults (2000-char chunks, 300 overlap) were chosen with the retrieval
eval. To rebuild the original 1000/150 index for comparison:
    python ingest.py --chunk-size 1000 --chunk-overlap 150 --index-dir faiss_index_1000
    python evals/retrieval_eval.py --index faiss_index_1000 --k 4 8
"""

import argparse
import os
from dotenv import load_dotenv

load_dotenv()

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from retrieval import EMBED_MODEL, INDEX_DIR

DATA_DIR = "data"


def ingest(chunk_size: int = 2000, chunk_overlap: int = 300, index_dir: str = INDEX_DIR):
    # 1. Load all PDFs from data/
    documents = []
    pdf_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".pdf")]

    if not pdf_files:
        print("No PDF files found in data/ folder. Add at least one PDF and re-run.")
        return

    for filename in pdf_files:
        path = os.path.join(DATA_DIR, filename)
        print(f"Loading: {filename}")
        loader = PyPDFLoader(path)
        documents.extend(loader.load())

    print(f"Loaded {len(documents)} pages from {len(pdf_files)} PDF(s).")

    # 2. Split into chunks
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks.")

    # 3. Embed with HuggingFace and build FAISS index
    print(f"Generating embeddings with {EMBED_MODEL}... (this may take a moment)")
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    vectorstore = FAISS.from_documents(chunks, embeddings)

    # 4. Save index to disk
    vectorstore.save_local(index_dir)
    print(f"FAISS index saved to {index_dir}/")
    print("Ingestion complete. You can now start the API with: uvicorn main:app --reload")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Build the FAISS index from PDFs in data/.")
    ap.add_argument("--chunk-size", type=int, default=2000)
    ap.add_argument("--chunk-overlap", type=int, default=300)
    ap.add_argument("--index-dir", default=INDEX_DIR)
    args = ap.parse_args()
    ingest(args.chunk_size, args.chunk_overlap, args.index_dir)

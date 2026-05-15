"""
ingest.py
Loads all PDFs from the data/ folder, splits them into chunks,
generates embeddings via Gemini, and saves a FAISS index to disk.
Run this once before starting the API.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Must be set before importing langchain_google_genai
os.environ["GOOGLE_API_KEY"] = os.getenv("GEMINI_API_KEY", "")

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

DATA_DIR = "data"
INDEX_DIR = "faiss_index"


def ingest():
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
        chunk_size=1000,
        chunk_overlap=150,
    )
    chunks = splitter.split_documents(documents)
    print(f"Split into {len(chunks)} chunks.")

    # 3. Embed using Gemini and build FAISS index
    print("Generating embeddings via Gemini... (this may take a moment)")
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )
    vectorstore = FAISS.from_documents(chunks, embeddings)

    # 4. Save index to disk
    vectorstore.save_local(INDEX_DIR)
    print(f"FAISS index saved to {INDEX_DIR}/")
    print("Ingestion complete. You can now start the API with: uvicorn main:app --reload")


if __name__ == "__main__":
    ingest()
# Financial Document Q&A Bot API image (used for Azure Container Apps).
# The FAISS index and the embedding model are built into the image, so the
# container starts without downloading anything.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/app/.hf

WORKDIR /app

# CPU-only PyTorch keeps the image ~2 GB smaller than the default CUDA build
RUN pip install torch --index-url https://download.pytorch.org/whl/cpu
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY *.py ./
COPY data/ data/
# Downloads all-MiniLM-L6-v2 into HF_HOME and writes faiss_index/
RUN python ingest.py

# Never reach out to the Hugging Face Hub at runtime
ENV HF_HUB_OFFLINE=1

RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

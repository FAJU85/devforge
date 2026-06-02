FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Optional: AirLLM for local model inference (pulls torch + transformers; skip if not needed)
RUN pip install --no-cache-dir airllm || true

COPY . .
# Optional: control-plane dependencies (LangGraph, LangChain, Pinecone)
RUN pip install --no-cache-dir -r control_plane/requirements.txt || true

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]

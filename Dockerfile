FROM python:3.11-slim

WORKDIR /code

COPY requirements.txt requirements-db.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Database dependencies (SQLAlchemy, PostgreSQL, migrations)
RUN pip install --no-cache-dir -r requirements-db.txt
# Error monitoring + product analytics
RUN pip install --no-cache-dir "sentry-sdk[fastapi]>=2.0" "posthog>=7.0"
# Optional: AirLLM for local model inference (pulls torch + transformers; skip if not needed)
RUN pip install --no-cache-dir airllm || true
# Headless browser support
RUN pip install --no-cache-dir playwright==1.60.0 && python -m playwright install chromium || true

COPY . .
# Optional: control-plane dependencies (LangGraph, LangChain, Pinecone)
RUN pip install --no-cache-dir -r control_plane/requirements.txt || true

# Initialize database on startup (if DATABASE_URL provided)
ENV PYTHONUNBUFFERED=1
RUN python -c "from db.database import init_db; init_db()" || true

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]

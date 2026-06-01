import os
from dotenv import load_dotenv

load_dotenv()

# Use getenv (not environ) so tests run without real secrets set.
# Nodes will fail at call-time if keys are empty — not at import-time.
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
PINECONE_INDEX: str = os.getenv("PINECONE_INDEX", "agent-memory")
PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")

GO_DATA_PLANE_URL: str = os.getenv("GO_DATA_PLANE_URL", "http://localhost:8080")
GO_CALL_TIMEOUT: int = int(os.getenv("GO_CALL_TIMEOUT", "30"))

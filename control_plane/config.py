import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY: str = os.environ["ANTHROPIC_API_KEY"]
PINECONE_API_KEY: str = os.environ["PINECONE_API_KEY"]
PINECONE_INDEX: str = os.getenv("PINECONE_INDEX", "agent-memory")
PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1-aws")

GO_DATA_PLANE_URL: str = os.getenv("GO_DATA_PLANE_URL", "http://localhost:8080")
GO_CALL_TIMEOUT: int = int(os.getenv("GO_CALL_TIMEOUT", "30"))

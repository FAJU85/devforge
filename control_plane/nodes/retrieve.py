import logging

from control_plane.memory.pinecone_client import query_context
from control_plane.state import AgentState

logger = logging.getLogger(__name__)


def retrieve_node(state: AgentState) -> dict:
    """RAG retrieval step — queries Pinecone and injects context for reasoning_node."""
    task = state["task"]
    logger.info("retrieve_node: querying context for task=%r", task[:80])

    context = query_context(task)

    logger.info(
        "retrieve_node: retrieved %d chars of context",
        len(context),
    )
    return {"rag_context": context}

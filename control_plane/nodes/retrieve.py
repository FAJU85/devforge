import logging

from control_plane.memory.pinecone_client import query_context
from control_plane.state import AgentState

logger = logging.getLogger(__name__)


def retrieve_node(state: AgentState) -> dict:
    """
    RAG retrieval step.

    Queries Pinecone for passages relevant to state['task'] and injects
    them as rag_context so reasoning_node can ground the LLM before it
    plans tool calls.

    Phase 3: query_context() is a stub that returns "".
    Phase 4: real Pinecone client is wired in.
    """
    task = state["task"]
    logger.info("retrieve_node: querying context for task=%r", task[:80])

    context = query_context(task)

    logger.info(
        "retrieve_node: retrieved %d chars of context",
        len(context),
    )
    return {"rag_context": context}

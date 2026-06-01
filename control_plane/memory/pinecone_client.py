"""
Phase 3 stub — Phase 4 replaces this with real Pinecone vector retrieval.

Returning an empty string is safe: reasoning_node checks for empty context
and omits the context block from the LLM prompt, so no hallucination occurs.
"""


def query_context(task: str, top_k: int = 3) -> str:  # noqa: ARG001
    """Return relevant context passages for *task* from the vector store."""
    return ""  # Phase 4 implementation

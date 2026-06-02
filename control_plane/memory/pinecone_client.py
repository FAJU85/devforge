"""
Pinecone vector-store client for RAG retrieval.

Lazy-initialises the Pinecone connection on first call so tests can import
this module without a live API key.  When PINECONE_API_KEY is empty the
function returns "" immediately, keeping retrieve_node's stub behaviour.
"""
import logging

from pinecone import Pinecone

from control_plane.config import PINECONE_API_KEY, PINECONE_INDEX

logger = logging.getLogger(__name__)

_pc_client: Pinecone | None = None
_pc_index = None


def _client_and_index():
    global _pc_client, _pc_index
    if _pc_client is None:
        _pc_client = Pinecone(api_key=PINECONE_API_KEY)
    if _pc_index is None:
        _pc_index = _pc_client.Index(PINECONE_INDEX)
    return _pc_client, _pc_index


def upsert_text(text: str, metadata: dict | None = None, namespace: str = "default") -> bool:
    """Embed *text* and upsert it into Pinecone. Returns True on success, False otherwise."""
    if not PINECONE_API_KEY:
        return False
    try:
        import uuid
        pc, index = _client_and_index()
        embeddings = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[text],
            parameters={"input_type": "passage", "truncate": "END"},
        )
        vector = embeddings[0].values
        doc_id = str(uuid.uuid4())
        meta = {"text": text, **(metadata or {})}
        index.upsert(vectors=[{"id": doc_id, "values": vector, "metadata": meta}], namespace=namespace)
        logger.debug("upsert_text: stored doc %s (%d chars)", doc_id, len(text))
        return True
    except Exception as exc:
        logger.warning("upsert_text: Pinecone error — %s", exc)
        return False


def query_context(task: str, top_k: int = 3) -> str:
    """Return relevant context passages for *task* from the Pinecone vector store.

    Returns "" immediately when PINECONE_API_KEY is not configured, or when
    any Pinecone / network error occurs — callers treat "" as "no context".
    """
    if not PINECONE_API_KEY:
        return ""

    try:
        pc, index = _client_and_index()

        embeddings = pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[task],
            parameters={"input_type": "query", "truncate": "END"},
        )
        vector = embeddings[0].values

        results = index.query(vector=vector, top_k=top_k, include_metadata=True)

        passages: list[str] = []
        for match in results.matches:
            text = (match.metadata or {}).get("text") or (match.metadata or {}).get("content") or ""
            if text:
                passages.append(text.strip())

        context = "\n\n".join(passages)
        logger.debug("query_context: returned %d passages (%d chars)", len(passages), len(context))
        return context

    except Exception as exc:
        logger.warning("query_context: Pinecone error — %s", exc)
        return ""

from operator import add
from typing import Annotated, TypedDict

from control_plane.schemas.tool_schemas import BatchRequestSchema, BatchResponseSchema


class AgentState(TypedDict):
    # The raw task string supplied by the caller.
    task: str

    # Conversation history. The `add` reducer appends rather than replaces,
    # so nodes return {"messages": [new_msg]} without clobbering prior turns.
    messages: Annotated[list[dict], add]

    # RAG context injected by retrieve_node before the LLM sees the task.
    rag_context: str

    # Pydantic-validated plan produced by reasoning_node.
    # None until reasoning_node runs.
    tool_plan: BatchRequestSchema | None

    # Pydantic-validated response from the Go data plane.
    # None until execution_node succeeds.
    tool_results: BatchResponseSchema | None

    # Synthesized natural-language answer produced by synthesis_node.
    final_answer: str

    # Non-None when execution_node fails. Triggers retry routing.
    error: str | None

    # Incremented by execution_node on each failure. Caps at MAX_RETRIES.
    retry_count: int

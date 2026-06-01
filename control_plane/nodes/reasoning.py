import logging
import uuid
from functools import lru_cache

from langchain_anthropic import ChatAnthropic

from control_plane.config import ANTHROPIC_API_KEY
from control_plane.schemas.tool_schemas import BatchRequestSchema
from control_plane.state import AgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are an agent that decides which tool calls are needed to complete a task.
Given a task description and optional context, produce a BatchRequestSchema:
a list of tool calls the data plane will execute concurrently.

Available tools
───────────────
http_fetch  Fetch a URL via HTTP.
  args: url (str, required), method (str, default "GET")

ping        Check TCP reachability of a host.
  args: host (str, required), port (str, default "80")

Rules
─────
- call_id must be unique within the batch (e.g. "fetch-1", "ping-main").
- Maximum 10 calls per batch.
- Use http_fetch for content retrieval, ping for connectivity checks.
- Do not hallucinate URLs — only use URLs explicitly mentioned in the task.
"""


@lru_cache(maxsize=1)
def _build_llm():
    """Lazy singleton so tests can import this module without a real API key."""
    return ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=ANTHROPIC_API_KEY,
        max_tokens=1024,
    ).with_structured_output(BatchRequestSchema)


def reasoning_node(state: AgentState) -> dict:
    """
    LLM planning step.

    Calls Claude with with_structured_output(BatchRequestSchema) — the model
    *must* return JSON matching the Pydantic schema or LangChain raises before
    we ever advance the state machine.

    On retry, the previous error is included in the prompt so the model can
    adjust its plan (e.g. use a different URL, fewer concurrent calls).
    """
    task = state["task"]
    context = state.get("rag_context") or ""
    error = state.get("error")
    retry = state.get("retry_count", 0)

    logger.info("reasoning_node: retry=%d, prior_error=%r", retry, error)

    human_parts = [f"Task:\n{task}"]

    if context:
        human_parts.append(f"\nRelevant context from knowledge base:\n{context}")

    if error:
        human_parts.append(
            f"\nIMPORTANT — previous execution failed:\n{error}\n"
            "Revise your tool-call plan to avoid repeating the same failure."
        )

    llm = _build_llm()
    plan: BatchRequestSchema = llm.invoke([
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user",   "content": "\n".join(human_parts)},
    ])

    # Stamp a fresh task_id so each planning round is independently traceable.
    task_id = f"{uuid.uuid4().hex[:8]}-retry{retry}"
    plan = plan.model_copy(update={"task_id": task_id})

    logger.info(
        "reasoning_node: planned %d calls (task_id=%s)",
        len(plan.calls),
        plan.task_id,
    )
    return {"tool_plan": plan, "error": None}

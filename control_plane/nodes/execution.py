import logging

import httpx
from pydantic import ValidationError

from control_plane.config import GO_CALL_TIMEOUT, GO_DATA_PLANE_URL
from control_plane.schemas.tool_schemas import BatchResponseSchema
from control_plane.state import AgentState

logger = logging.getLogger(__name__)


def execution_node(state: AgentState) -> dict:
    """
    Tool execution step — the Go boundary.

    Sends state['tool_plan'] to the Go data plane, validates the response
    with Pydantic, and returns either:
      - {"tool_results": BatchResponseSchema, "error": None}   on success
      - {"error": str, "retry_count": n+1}                     on any failure

    Three failure classes are caught explicitly:
      1. Network/timeout failures (httpx exceptions)
      2. HTTP 4xx / 5xx from the Go service
      3. Malformed JSON that fails Pydantic validation

    All failures increment retry_count. The LangGraph conditional edge in
    graph.py routes back to reasoning_node when retry_count < MAX_RETRIES,
    letting the LLM adapt its plan before the next attempt.
    """
    plan = state.get("tool_plan")
    if plan is None:
        return {"error": "execution_node reached with no tool_plan in state"}

    retry = state.get("retry_count", 0)
    logger.info(
        "execution_node: sending %d calls to Go service (retry=%d)",
        len(plan.calls),
        retry,
    )

    # ── Network call ──────────────────────────────────────────────────────────
    try:
        response = httpx.post(
            f"{GO_DATA_PLANE_URL}/tools/execute",
            json=plan.model_dump(),
            timeout=GO_CALL_TIMEOUT,
        )
        response.raise_for_status()

    except httpx.TimeoutException:
        msg = f"Go data plane timed out after {GO_CALL_TIMEOUT}s"
        logger.error(msg)
        return {"error": msg, "retry_count": retry + 1}

    except httpx.HTTPStatusError as exc:
        msg = (
            f"Go data plane returned HTTP {exc.response.status_code}: "
            f"{exc.response.text[:200]}"
        )
        logger.error(msg)
        return {"error": msg, "retry_count": retry + 1}

    except httpx.RequestError as exc:
        msg = f"Go data plane unreachable: {exc}"
        logger.error(msg)
        return {"error": msg, "retry_count": retry + 1}

    # ── Pydantic validation ───────────────────────────────────────────────────
    # If the Go service ever returns a malformed payload, we fail explicitly
    # here rather than propagating a partially-constructed object into state.
    try:
        result = BatchResponseSchema.model_validate(response.json())
    except (ValidationError, ValueError) as exc:
        msg = f"Go response failed Pydantic validation: {exc}"
        logger.error(msg)
        return {"error": msg, "retry_count": retry + 1}

    failed = [r for r in result.results if not r.ok]
    logger.info(
        "execution_node: %d/%d calls succeeded (%d failed) in %dms",
        len(result.results) - len(failed),
        len(result.results),
        len(failed),
        result.duration_ms,
    )
    return {"tool_results": result, "error": None}

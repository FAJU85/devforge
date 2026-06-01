import logging
from functools import lru_cache

from langchain_anthropic import ChatAnthropic

from control_plane.config import ANTHROPIC_API_KEY
from control_plane.state import AgentState

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a helpful assistant. Synthesize the tool results below into a clear,
concise answer to the user's original task.
- Highlight key findings from successful calls.
- Note any failures and what they imply.
- Be factual; do not invent information not present in the results.
"""


@lru_cache(maxsize=1)
def _build_llm():
    return ChatAnthropic(
        model="claude-haiku-4-5-20251001",
        api_key=ANTHROPIC_API_KEY,
        max_tokens=2048,
    )


def synthesis_node(state: AgentState) -> dict:
    """
    Final answer step.

    Converts raw tool results (or an unrecoverable error) into a
    natural-language answer and appends it to state['messages'].
    """
    task = state["task"]
    results = state.get("tool_results")
    error = state.get("error")

    if error and results is None:
        answer = f"Unable to complete task after retries. Last error: {error}"
        logger.warning("synthesis_node: giving up — %s", error)
        return {
            "final_answer": answer,
            "messages": [{"role": "assistant", "content": answer}],
        }

    lines: list[str] = []
    if results:
        for r in results.results:
            if r.ok:
                lines.append(f"[{r.call_id}] {r.tool} ✓ ({r.duration_ms}ms): {r.data}")
            else:
                lines.append(f"[{r.call_id}] {r.tool} ✗ error={r.error}")

    results_text = "\n".join(lines) if lines else "No tool results available."

    llm = _build_llm()
    response = llm.invoke([
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user",   "content": f"Task: {task}\n\nTool results:\n{results_text}"},
    ])

    answer = response.content
    logger.info("synthesis_node: generated %d-char answer", len(answer))
    return {
        "final_answer": answer,
        "messages": [{"role": "assistant", "content": answer}],
    }

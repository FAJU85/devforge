"""
Agent entry point.

Run a task end-to-end through the compiled LangGraph:
    python -m control_plane.agent.main "ping example.com"
"""
import logging
import sys

from control_plane.graph import build_graph

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

_INITIAL_STATE = {
    "messages": [],
    "rag_context": "",
    "tool_plan": None,
    "tool_results": None,
    "final_answer": "",
    "error": None,
    "retry_count": 0,
}


def run(task: str) -> str:
    """Execute *task* and return the synthesised natural-language answer."""
    graph = build_graph()
    final_state = graph.invoke({**_INITIAL_STATE, "task": task})
    return final_state.get("final_answer", "")


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]).strip() or "ping 1.1.1.1"
    answer = run(task)
    print(answer)

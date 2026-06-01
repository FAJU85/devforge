"""
LangGraph StateGraph definition.

Phase 3: nodes and routing logic are defined.
Phase 4: Pinecone is initialised and graph.compile() is called.
"""
from langgraph.graph import END, StateGraph

from control_plane.nodes.execution import execution_node
from control_plane.nodes.reasoning import reasoning_node
from control_plane.nodes.retrieve import retrieve_node
from control_plane.nodes.synthesis import synthesis_node
from control_plane.state import AgentState

MAX_RETRIES = 3


def _route_after_execution(state: AgentState) -> str:
    """
    Conditional edge out of execution_node.

    - If the Go service failed AND we have retries left → send back to
      reasoning_node so the LLM can revise its tool-call plan.
    - Otherwise (success, or retries exhausted) → proceed to synthesis.
    """
    if state.get("error") and state.get("retry_count", 0) < MAX_RETRIES:
        return "reasoning"
    return "synthesis"


def build_graph():
    """
    Construct and return a compiled LangGraph StateGraph.

    Graph topology
    ──────────────
    retrieve → reasoning → execution ──(success)──→ synthesis → END
                  ↑              └──(failure, retry<MAX)──┘
    """
    g = StateGraph(AgentState)

    g.add_node("retrieve",  retrieve_node)
    g.add_node("reasoning", reasoning_node)
    g.add_node("execution", execution_node)
    g.add_node("synthesis", synthesis_node)

    g.set_entry_point("retrieve")
    g.add_edge("retrieve",  "reasoning")
    g.add_edge("reasoning", "execution")
    g.add_conditional_edges(
        "execution",
        _route_after_execution,
        {"reasoning": "reasoning", "synthesis": "synthesis"},
    )
    g.add_edge("synthesis", END)

    # Phase 4 calls g.compile() after wiring Pinecone memory.
    return g  # returns the uncompiled graph; Phase 4 compiles it

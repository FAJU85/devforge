import pytest

from control_plane.graph import MAX_RETRIES, _route_after_execution, build_graph


class TestRouteAfterExecution:
    def test_routes_to_synthesis_on_success(self):
        assert _route_after_execution({"error": None, "retry_count": 0}) == "synthesis"

    def test_routes_to_synthesis_when_error_is_empty_string(self):
        assert _route_after_execution({"error": "", "retry_count": 0}) == "synthesis"

    def test_routes_to_reasoning_on_first_failure(self):
        assert _route_after_execution({"error": "timeout", "retry_count": 0}) == "reasoning"

    def test_routes_to_reasoning_when_retries_below_max(self):
        assert _route_after_execution({"error": "err", "retry_count": MAX_RETRIES - 1}) == "reasoning"

    def test_routes_to_synthesis_when_retries_exhausted(self):
        assert _route_after_execution({"error": "err", "retry_count": MAX_RETRIES}) == "synthesis"

    def test_routes_to_synthesis_when_retries_exceed_max(self):
        assert _route_after_execution({"error": "err", "retry_count": MAX_RETRIES + 5}) == "synthesis"


class TestBuildGraph:
    def test_returns_compiled_graph(self):
        graph = build_graph()
        assert hasattr(graph, "invoke"), "build_graph() must return a compiled graph"

    def test_compiled_graph_has_stream(self):
        graph = build_graph()
        assert hasattr(graph, "stream")

    def test_compiled_graph_has_expected_nodes(self):
        graph = build_graph()
        # get_graph() returns a DrawableGraph with nodes dict
        nodes = set(graph.get_graph().nodes.keys())
        assert {"retrieve", "reasoning", "execution", "synthesis"}.issubset(nodes)

from unittest.mock import patch

from control_plane.nodes.retrieve import retrieve_node


def _state(**overrides):
    base = {
        "task": "check connectivity to example.com",
        "messages": [],
        "rag_context": "",
        "tool_plan": None,
        "tool_results": None,
        "final_answer": "",
        "error": None,
        "retry_count": 0,
    }
    base.update(overrides)
    return base


class TestRetrieveNode:
    def test_stores_context_in_rag_context(self):
        with patch(
            "control_plane.nodes.retrieve.query_context",
            return_value="Relevant passage about networking.",
        ):
            result = retrieve_node(_state())

        assert result["rag_context"] == "Relevant passage about networking."

    def test_empty_context_from_stub(self):
        with patch("control_plane.nodes.retrieve.query_context", return_value=""):
            result = retrieve_node(_state())

        assert result["rag_context"] == ""

    def test_passes_task_to_query_context(self):
        captured: list[str] = []

        def _capture(task, top_k=3):
            captured.append(task)
            return ""

        with patch("control_plane.nodes.retrieve.query_context", side_effect=_capture):
            retrieve_node(_state(task="ping 1.1.1.1"))

        assert captured == ["ping 1.1.1.1"]

    def test_returns_only_rag_context_key(self):
        with patch("control_plane.nodes.retrieve.query_context", return_value="ctx"):
            result = retrieve_node(_state())

        assert set(result.keys()) == {"rag_context"}

    def test_long_task_does_not_crash(self):
        long_task = "a" * 10_000
        with patch("control_plane.nodes.retrieve.query_context", return_value="ok"):
            result = retrieve_node(_state(task=long_task))

        assert result["rag_context"] == "ok"

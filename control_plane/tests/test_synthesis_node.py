from unittest.mock import MagicMock, patch

from control_plane.nodes.synthesis import synthesis_node
from control_plane.schemas.tool_schemas import BatchResponseSchema, ToolResultSchema


def _results(*ok_flags) -> BatchResponseSchema:
    results = []
    for i, ok in enumerate(ok_flags):
        results.append(ToolResultSchema(
            call_id=f"c{i}",
            tool="ping",
            ok=ok,
            data={"latency_ms": 5} if ok else None,
            error=None if ok else "connection refused",
            duration_ms=5,
        ))
    return BatchResponseSchema(task_id="t1", results=results, duration_ms=10)


def _state(**overrides):
    base = {
        "task": "check connectivity",
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


class TestSynthesisNodeErrorFallback:
    def test_returns_error_message_when_no_results_and_error(self):
        result = synthesis_node(_state(error="timeout after 30s", tool_results=None))

        assert "timeout after 30s" in result["final_answer"]
        assert result["messages"][0]["role"] == "assistant"

    def test_does_not_call_llm_on_unrecoverable_error(self):
        with patch("control_plane.nodes.synthesis._build_llm") as mock_llm:
            synthesis_node(_state(error="fatal", tool_results=None))

        mock_llm.assert_not_called()


class TestSynthesisNodeWithResults:
    def _mock_llm(self, answer: str):
        mock_response = MagicMock()
        mock_response.content = answer
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.return_value = mock_response
        return mock_llm_instance

    def test_calls_llm_with_tool_results(self):
        mock_llm = self._mock_llm("The host is reachable.")

        with patch("control_plane.nodes.synthesis._build_llm", return_value=mock_llm):
            result = synthesis_node(_state(tool_results=_results(True)))

        assert result["final_answer"] == "The host is reachable."
        assert mock_llm.invoke.called

    def test_appends_message_to_state(self):
        mock_llm = self._mock_llm("Summary here.")

        with patch("control_plane.nodes.synthesis._build_llm", return_value=mock_llm):
            result = synthesis_node(_state(tool_results=_results(True)))

        assert result["messages"] == [{"role": "assistant", "content": "Summary here."}]

    def test_passes_failed_call_info_to_llm(self):
        captured_msgs = []

        mock_response = MagicMock()
        mock_response.content = "One failed."
        mock_llm = MagicMock()

        def capture_invoke(msgs):
            captured_msgs.extend(msgs)
            return mock_response

        mock_llm.invoke.side_effect = capture_invoke

        with patch("control_plane.nodes.synthesis._build_llm", return_value=mock_llm):
            synthesis_node(_state(tool_results=_results(True, False)))

        user_content = next(m["content"] for m in captured_msgs if m["role"] == "user")
        assert "connection refused" in user_content

    def test_handles_empty_results_list(self):
        empty = BatchResponseSchema(task_id="t1", results=[], duration_ms=0)
        mock_llm = self._mock_llm("No results.")

        with patch("control_plane.nodes.synthesis._build_llm", return_value=mock_llm):
            result = synthesis_node(_state(tool_results=empty))

        user_content = mock_llm.invoke.call_args[0][0]
        user_msg = next(m["content"] for m in user_content if m["role"] == "user")
        assert "No tool results available." in user_msg

    def test_proceeds_with_llm_even_when_partial_error_exists(self):
        """When results exist, synthesis proceeds even if error is set."""
        mock_llm = self._mock_llm("Partial success.")

        with patch("control_plane.nodes.synthesis._build_llm", return_value=mock_llm):
            result = synthesis_node(_state(
                tool_results=_results(True),
                error="earlier attempt failed",
            ))

        assert result["final_answer"] == "Partial success."

from unittest.mock import MagicMock, patch

from control_plane.nodes.reasoning import reasoning_node
from control_plane.schemas.tool_schemas import BatchRequestSchema, ToolCallSchema


def _plan() -> BatchRequestSchema:
    return BatchRequestSchema(
        task_id="placeholder",
        calls=[ToolCallSchema(call_id="c1", tool="ping", args={"host": "1.1.1.1"})],
    )


def _state(**overrides):
    base = {
        "task": "check if example.com is reachable",
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


def _mock_llm(plan: BatchRequestSchema | None = None):
    if plan is None:
        plan = _plan()
    mock = MagicMock()
    mock.invoke.return_value = plan
    return mock


class TestReasoningNodeOutput:
    def test_returns_tool_plan_and_clears_error(self):
        with patch("control_plane.nodes.reasoning._build_llm", return_value=_mock_llm()):
            result = reasoning_node(_state())

        assert isinstance(result["tool_plan"], BatchRequestSchema)
        assert result["error"] is None

    def test_stamps_task_id_with_retry_suffix(self):
        with patch("control_plane.nodes.reasoning._build_llm", return_value=_mock_llm()):
            result = reasoning_node(_state(retry_count=2))

        task_id = result["tool_plan"].task_id
        assert task_id.endswith("-retry2"), f"Expected suffix -retry2, got {task_id!r}"

    def test_task_id_is_unique_across_calls(self):
        ids = []
        for _ in range(3):
            with patch("control_plane.nodes.reasoning._build_llm", return_value=_mock_llm()):
                result = reasoning_node(_state())
            ids.append(result["tool_plan"].task_id)

        assert len(set(ids)) == 3, "task_ids should be unique across calls"


class TestReasoningNodePromptContent:
    def test_task_included_in_user_message(self):
        captured = []

        def capture_invoke(msgs):
            captured.extend(msgs)
            return _plan()

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = capture_invoke

        with patch("control_plane.nodes.reasoning._build_llm", return_value=mock_llm):
            reasoning_node(_state(task="ping google.com"))

        user_msg = next(m["content"] for m in captured if m["role"] == "user")
        assert "ping google.com" in user_msg

    def test_rag_context_injected_when_non_empty(self):
        captured = []

        def capture_invoke(msgs):
            captured.extend(msgs)
            return _plan()

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = capture_invoke

        with patch("control_plane.nodes.reasoning._build_llm", return_value=mock_llm):
            reasoning_node(_state(rag_context="Relevant background about networking."))

        user_msg = next(m["content"] for m in captured if m["role"] == "user")
        assert "Relevant background about networking." in user_msg

    def test_rag_context_omitted_when_empty(self):
        captured = []

        def capture_invoke(msgs):
            captured.extend(msgs)
            return _plan()

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = capture_invoke

        with patch("control_plane.nodes.reasoning._build_llm", return_value=mock_llm):
            reasoning_node(_state(rag_context=""))

        user_msg = next(m["content"] for m in captured if m["role"] == "user")
        assert "context from knowledge base" not in user_msg.lower()

    def test_error_injected_on_retry(self):
        captured = []

        def capture_invoke(msgs):
            captured.extend(msgs)
            return _plan()

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = capture_invoke

        with patch("control_plane.nodes.reasoning._build_llm", return_value=mock_llm):
            reasoning_node(_state(error="HTTP 500: internal server error", retry_count=1))

        user_msg = next(m["content"] for m in captured if m["role"] == "user")
        assert "HTTP 500" in user_msg

    def test_no_error_block_on_first_attempt(self):
        captured = []

        def capture_invoke(msgs):
            captured.extend(msgs)
            return _plan()

        mock_llm = MagicMock()
        mock_llm.invoke.side_effect = capture_invoke

        with patch("control_plane.nodes.reasoning._build_llm", return_value=mock_llm):
            reasoning_node(_state(error=None, retry_count=0))

        user_msg = next(m["content"] for m in captured if m["role"] == "user")
        assert "previous execution failed" not in user_msg.lower()

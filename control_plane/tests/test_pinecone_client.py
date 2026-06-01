from unittest.mock import MagicMock, patch

import pytest

import control_plane.memory.pinecone_client as _mod
from control_plane.memory.pinecone_client import query_context


class TestQueryContextNoKey:
    def test_returns_empty_when_api_key_missing(self, monkeypatch):
        monkeypatch.setattr(_mod, "PINECONE_API_KEY", "")
        assert query_context("some task") == ""

    def test_returns_empty_for_whitespace_key(self, monkeypatch):
        monkeypatch.setattr(_mod, "PINECONE_API_KEY", "   ")
        assert query_context("some task") == ""


class TestQueryContextException:
    def test_returns_empty_on_connection_error(self, monkeypatch):
        monkeypatch.setattr(_mod, "PINECONE_API_KEY", "fake-key")
        monkeypatch.setattr(_mod, "_pc_client", None)
        monkeypatch.setattr(_mod, "_pc_index", None)

        with patch("control_plane.memory.pinecone_client.Pinecone") as mock_cls:
            mock_cls.side_effect = RuntimeError("connection refused")
            result = query_context("some task")

        assert result == ""

    def test_returns_empty_on_inference_error(self, monkeypatch):
        monkeypatch.setattr(_mod, "PINECONE_API_KEY", "fake-key")
        monkeypatch.setattr(_mod, "_pc_client", None)
        monkeypatch.setattr(_mod, "_pc_index", None)

        mock_pc = MagicMock()
        mock_pc.inference.embed.side_effect = RuntimeError("embedding failed")
        mock_pc.Index.return_value = MagicMock()

        with patch("control_plane.memory.pinecone_client.Pinecone", return_value=mock_pc):
            result = query_context("some task")

        assert result == ""


class TestQueryContextSuccess:
    def _make_match(self, text: str, score: float = 0.9) -> MagicMock:
        match = MagicMock()
        match.metadata = {"text": text}
        match.score = score
        return match

    def test_returns_joined_passages(self, monkeypatch):
        monkeypatch.setattr(_mod, "PINECONE_API_KEY", "fake-key")
        monkeypatch.setattr(_mod, "_pc_client", None)
        monkeypatch.setattr(_mod, "_pc_index", None)

        mock_pc = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1] * 1024
        mock_pc.inference.embed.return_value = [mock_embedding]

        mock_index = MagicMock()
        mock_results = MagicMock()
        mock_results.matches = [
            self._make_match("First passage about the topic."),
            self._make_match("Second passage with more detail."),
        ]
        mock_index.query.return_value = mock_results
        mock_pc.Index.return_value = mock_index

        with patch("control_plane.memory.pinecone_client.Pinecone", return_value=mock_pc):
            result = query_context("my task")

        assert "First passage" in result
        assert "Second passage" in result
        assert "\n\n" in result

    def test_skips_matches_with_no_text(self, monkeypatch):
        monkeypatch.setattr(_mod, "PINECONE_API_KEY", "fake-key")
        monkeypatch.setattr(_mod, "_pc_client", None)
        monkeypatch.setattr(_mod, "_pc_index", None)

        mock_pc = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1] * 1024
        mock_pc.inference.embed.return_value = [mock_embedding]

        mock_index = MagicMock()
        mock_results = MagicMock()
        empty_match = MagicMock()
        empty_match.metadata = {}
        real_match = self._make_match("Valid text here.")
        mock_results.matches = [empty_match, real_match]
        mock_index.query.return_value = mock_results
        mock_pc.Index.return_value = mock_index

        with patch("control_plane.memory.pinecone_client.Pinecone", return_value=mock_pc):
            result = query_context("my task")

        assert result == "Valid text here."

    def test_returns_empty_string_on_no_matches(self, monkeypatch):
        monkeypatch.setattr(_mod, "PINECONE_API_KEY", "fake-key")
        monkeypatch.setattr(_mod, "_pc_client", None)
        monkeypatch.setattr(_mod, "_pc_index", None)

        mock_pc = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1] * 1024
        mock_pc.inference.embed.return_value = [mock_embedding]

        mock_index = MagicMock()
        mock_results = MagicMock()
        mock_results.matches = []
        mock_index.query.return_value = mock_results
        mock_pc.Index.return_value = mock_index

        with patch("control_plane.memory.pinecone_client.Pinecone", return_value=mock_pc):
            result = query_context("my task")

        assert result == ""

    def test_uses_content_key_as_fallback(self, monkeypatch):
        monkeypatch.setattr(_mod, "PINECONE_API_KEY", "fake-key")
        monkeypatch.setattr(_mod, "_pc_client", None)
        monkeypatch.setattr(_mod, "_pc_index", None)

        mock_pc = MagicMock()
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1] * 1024
        mock_pc.inference.embed.return_value = [mock_embedding]

        mock_index = MagicMock()
        mock_results = MagicMock()
        match = MagicMock()
        match.metadata = {"content": "Fallback content field."}
        mock_results.matches = [match]
        mock_index.query.return_value = mock_results
        mock_pc.Index.return_value = mock_index

        with patch("control_plane.memory.pinecone_client.Pinecone", return_value=mock_pc):
            result = query_context("my task")

        assert result == "Fallback content field."

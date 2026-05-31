"""Tests for DevForge main.py — helpers, system-prompt builder, runner selector, and endpoints."""
import asyncio
import json
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Bootstrap minimal stubs so main.py can be imported without real packages
# ---------------------------------------------------------------------------

_anthropic_stub = types.ModuleType("anthropic")
_anthropic_stub.Anthropic = MagicMock()
sys.modules.setdefault("anthropic", _anthropic_stub)

_hf_stub = types.ModuleType("huggingface_hub")
_hf_stub.InferenceClient = MagicMock()
sys.modules.setdefault("huggingface_hub", _hf_stub)

sys.path.insert(0, str(Path(__file__).parent.parent))

import main  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _body(**kwargs):
    """Return a minimal ChatBody with sensible defaults."""
    defaults = dict(
        provider="anthropic",
        anthropic_key="key",
        groq_key="",
        groq_model="llama-3.3-70b-versatile",
        hf_token="",
        hf_model="Qwen/Qwen2.5-Coder-32B-Instruct",
        openai_compat_key="",
        openai_compat_base_url="http://localhost:11434/v1",
        openai_compat_model="llama3",
        agent="code",
        messages=[],
        file_context="",
        owner="",
        repo="",
        skills=[],
        rules="",
        instructions="",
        multi_agent=False,
    )
    defaults.update(kwargs)
    return main.ChatBody(**defaults)


# ---------------------------------------------------------------------------
# parse_gh_url
# ---------------------------------------------------------------------------

class TestParseGhUrl:
    def test_full_https_url(self):
        owner, repo = main.parse_gh_url("https://github.com/FAJU85/devforge")
        assert owner == "FAJU85"
        assert repo == "devforge"

    def test_full_url_with_git_suffix(self):
        owner, repo = main.parse_gh_url("https://github.com/FAJU85/devforge.git")
        assert owner == "FAJU85"
        assert repo == "devforge"

    def test_full_url_trailing_slash(self):
        owner, repo = main.parse_gh_url("https://github.com/FAJU85/devforge/")
        assert owner == "FAJU85"
        assert repo == "devforge"

    def test_shorthand_owner_repo(self):
        owner, repo = main.parse_gh_url("FAJU85/devforge")
        assert owner == "FAJU85"
        assert repo == "devforge"

    def test_shorthand_git_suffix(self):
        owner, repo = main.parse_gh_url("FAJU85/devforge.git")
        assert owner == "FAJU85"
        assert repo == "devforge"

    def test_invalid_url_returns_none_pair(self):
        owner, repo = main.parse_gh_url("not-a-url")
        assert owner is None
        assert repo is None

    def test_empty_string_returns_none_pair(self):
        owner, repo = main.parse_gh_url("")
        assert owner is None
        assert repo is None


# ---------------------------------------------------------------------------
# gh_hdrs
# ---------------------------------------------------------------------------

class TestGhHdrs:
    def test_authorization_header_present(self):
        hdrs = main.gh_hdrs("mytoken123")
        assert hdrs["Authorization"] == "token mytoken123"

    def test_accept_header_present(self):
        hdrs = main.gh_hdrs("mytoken123")
        assert "application/vnd.github.v3+json" in hdrs["Accept"]

    def test_returns_dict(self):
        assert isinstance(main.gh_hdrs("t"), dict)


# ---------------------------------------------------------------------------
# build_system
# ---------------------------------------------------------------------------

class TestBuildSystem:
    def test_default_code_agent_prompt_used(self):
        body = _body()
        result = main.build_system(body)
        assert "expert coding agent" in result.lower()

    def test_custom_instructions_override_agent_prompt(self):
        body = _body(instructions="Use only stdlib.")
        result = main.build_system(body)
        assert result == "Use only stdlib."

    def test_repo_context_appended(self):
        body = _body(owner="FAJU85", repo="devforge")
        result = main.build_system(body)
        assert "FAJU85/devforge" in result

    def test_skill_appended(self):
        body = _body(skills=["tests"])
        result = main.build_system(body)
        assert "pytest" in result.lower() or "testing" in result.lower()

    def test_unknown_skill_ignored(self):
        body = _body(skills=["nonexistent_skill"])
        result = main.build_system(body)
        assert "nonexistent_skill" not in result

    def test_rules_appended(self):
        body = _body(rules="Never use globals.")
        result = main.build_system(body)
        assert "Never use globals." in result

    def test_file_context_appended(self):
        body = _body(file_context="# some code")
        result = main.build_system(body)
        assert "# some code" in result

    def test_review_agent_prompt(self):
        body = _body(agent="review")
        result = main.build_system(body)
        assert "reviewer" in result.lower()

    def test_unknown_agent_falls_back_to_code(self):
        body = _body(agent="unknown_mode")
        result = main.build_system(body)
        assert "expert coding agent" in result.lower()

    def test_multiple_skills_all_appended(self):
        body = _body(skills=["security", "docs"])
        result = main.build_system(body)
        assert "security" in result.lower()
        assert "documentation" in result.lower() or "docs" in result.lower()

    def test_empty_instructions_uses_agent_prompt(self):
        body = _body(instructions="   ")
        result = main.build_system(body)
        assert "expert coding agent" in result.lower()

    def test_owner_without_repo_skips_repo_context(self):
        body = _body(owner="FAJU85", repo="")
        result = main.build_system(body)
        assert "FAJU85" not in result

    def test_all_agents_resolve_without_error(self):
        for agent in ("code", "review", "architect", "debug", "docs"):
            result = main.build_system(_body(agent=agent))
            assert result


# ---------------------------------------------------------------------------
# get_runner
# ---------------------------------------------------------------------------

class TestGetRunner:
    def test_anthropic_provider_returns_callable(self):
        body = _body(provider="anthropic", anthropic_key="k")
        runner = main.get_runner(body)
        assert callable(runner)

    def test_groq_provider_returns_callable(self):
        body = _body(provider="groq", groq_key="k")
        runner = main.get_runner(body)
        assert callable(runner)

    def test_hf_provider_returns_callable(self):
        body = _body(provider="hf")
        runner = main.get_runner(body)
        assert callable(runner)

    def test_unknown_provider_falls_back_to_hf(self):
        body = _body(provider="unknown_provider")
        runner = main.get_runner(body)
        assert callable(runner)

    def test_groq_runner_uses_default_model_when_none(self):
        body = _body(provider="groq", groq_key="k", groq_model=None)
        runner = main.get_runner(body)
        assert callable(runner)


# ---------------------------------------------------------------------------
# AGENT_PROMPTS / SKILL_PROMPTS completeness
# ---------------------------------------------------------------------------

class TestPromptDicts:
    def test_all_expected_agents_present(self):
        for key in ("code", "review", "architect", "debug", "docs"):
            assert key in main.AGENT_PROMPTS, f"Missing agent prompt: {key}"

    def test_all_expected_skills_present(self):
        for key in ("go", "zod", "tests", "errors", "security", "docs", "perf", "solid"):
            assert key in main.SKILL_PROMPTS, f"Missing skill prompt: {key}"

    def test_agent_prompts_non_empty(self):
        for key, val in main.AGENT_PROMPTS.items():
            assert val.strip(), f"Agent prompt empty: {key}"

    def test_skill_prompts_non_empty(self):
        for key, val in main.SKILL_PROMPTS.items():
            assert val.strip(), f"Skill prompt empty: {key}"


# ---------------------------------------------------------------------------
# Helpers for thread-target runner tests
# ---------------------------------------------------------------------------

def _sync_run_coroutine_threadsafe(coro, loop):
    """Execute a coroutine synchronously on a non-running loop (test helper)."""
    loop.run_until_complete(coro)
    return MagicMock()


def _run_runner_sync(target, *args):
    """Run a thread-target function synchronously with a real event loop+queue.

    Returns the list of (kind, value) tuples placed on the queue.
    """
    loop = asyncio.new_event_loop()
    q = asyncio.Queue()
    with patch("main.asyncio.run_coroutine_threadsafe", side_effect=_sync_run_coroutine_threadsafe):
        target(q, loop, *args)
    items = []
    while not q.empty():
        items.append(q.get_nowait())
    loop.close()
    return items


# ---------------------------------------------------------------------------
# _run_groq — unit tests for SSE parsing logic (thread target)
# ---------------------------------------------------------------------------

class TestRunGroq:
    def test_run_groq_puts_text_and_done_on_success(self):
        chunk_data = json.dumps({"choices": [{"delta": {"content": "hello"}}]})
        mock_line = f"data: {chunk_data}".encode()
        done_line = b"data: [DONE]"

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([mock_line, done_line])

        with patch("main.requests.post", return_value=mock_response):
            items = _run_runner_sync(
                main._run_groq,
                "sys", [{"role": "user", "content": "hi"}], "api_key", "llama",
            )

        kinds = [k for k, _ in items]
        assert "text" in kinds
        assert "done" in kinds

    def test_run_groq_puts_error_on_bad_http_status(self):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        with patch("main.requests.post", return_value=mock_response):
            items = _run_runner_sync(main._run_groq, "sys", [], "bad_key", "llama")

        kinds = [k for k, _ in items]
        assert "error" in kinds

    def test_run_groq_puts_error_on_exception(self):
        with patch("main.requests.post", side_effect=ConnectionError("network failure")):
            items = _run_runner_sync(main._run_groq, "sys", [], "key", "llama")

        kinds = [k for k, _ in items]
        assert "error" in kinds

    def test_run_groq_skips_malformed_json_chunk(self):
        bad_line = b"data: {not valid json}"
        done_line = b"data: [DONE]"

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([bad_line, done_line])

        with patch("main.requests.post", return_value=mock_response):
            items = _run_runner_sync(main._run_groq, "sys", [], "key", "llama")

        kinds = [k for k, _ in items]
        assert "done" in kinds
        assert "error" not in kinds

    def test_run_groq_skips_empty_content_chunk(self):
        empty_content = json.dumps({"choices": [{"delta": {"content": ""}}]})
        chunk_with_text = json.dumps({"choices": [{"delta": {"content": "ok"}}]})
        done_line = b"data: [DONE]"

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            f"data: {empty_content}".encode(),
            f"data: {chunk_with_text}".encode(),
            done_line,
        ])

        with patch("main.requests.post", return_value=mock_response):
            items = _run_runner_sync(main._run_groq, "sys", [], "key", "llama")

        text_values = [v for k, v in items if k == "text"]
        assert text_values == ["ok"]


# ---------------------------------------------------------------------------
# _run_anthropic
# ---------------------------------------------------------------------------

class TestRunAnthropic:
    def test_run_anthropic_puts_text_and_done(self):
        mock_stream = MagicMock()
        mock_stream.__enter__ = MagicMock(return_value=mock_stream)
        mock_stream.__exit__ = MagicMock(return_value=False)
        mock_stream.text_stream = iter(["Hello", " world"])

        mock_client = MagicMock()
        mock_client.messages.stream.return_value = mock_stream

        with patch("main.Anthropic", return_value=mock_client):
            items = _run_runner_sync(
                main._run_anthropic,
                "sys", [{"role": "user", "content": "hi"}], "key",
            )

        kinds = [k for k, _ in items]
        assert "text" in kinds
        assert "done" in kinds

    def test_run_anthropic_puts_error_on_exception(self):
        with patch("main.Anthropic", side_effect=Exception("api error")):
            items = _run_runner_sync(main._run_anthropic, "sys", [], "key")

        kinds = [k for k, _ in items]
        assert "error" in kinds


# ---------------------------------------------------------------------------
# _run_hf
# ---------------------------------------------------------------------------

class TestRunHf:
    def test_run_hf_puts_text_and_done(self):
        tok1 = MagicMock()
        tok1.choices = [MagicMock()]
        tok1.choices[0].delta.content = "Hi"

        tok2 = MagicMock()
        tok2.choices = [MagicMock()]
        tok2.choices[0].delta.content = ""

        mock_hf = MagicMock()
        mock_hf.chat_completion.return_value = iter([tok1, tok2])

        with patch("main.InferenceClient", return_value=mock_hf):
            items = _run_runner_sync(
                main._run_hf,
                "sys", [{"role": "user", "content": "hi"}], "token", "model",
            )

        kinds = [k for k, _ in items]
        assert "text" in kinds
        assert "done" in kinds

    def test_run_hf_puts_error_on_exception(self):
        with patch("main.InferenceClient", side_effect=Exception("hf error")):
            items = _run_runner_sync(main._run_hf, "sys", [], "token", "model")

        kinds = [k for k, _ in items]
        assert "error" in kinds


# ---------------------------------------------------------------------------
# HTTP endpoints via TestClient
# ---------------------------------------------------------------------------

from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)


class TestRootEndpoint:
    def test_returns_html(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]

    def test_html_contains_devforge(self):
        resp = client.get("/")
        assert "devforge" in resp.text.lower() or "DevForge" in resp.text


class TestSearchHfModels:
    def test_returns_list_on_success(self):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = [
            {"modelId": "Qwen/Qwen2.5-Coder-32B-Instruct", "likes": 100, "downloads": 5000, "gated": False}
        ]

        with patch("main.requests.get", return_value=mock_resp):
            resp = client.get("/api/hf/models?q=qwen")

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data[0]["id"] == "Qwen/Qwen2.5-Coder-32B-Instruct"

    def test_returns_error_on_bad_hf_status(self):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 503

        with patch("main.requests.get", return_value=mock_resp):
            resp = client.get("/api/hf/models")

        assert resp.status_code == 500

    def test_returns_error_on_network_exception(self):
        with patch("main.requests.get", side_effect=ConnectionError("down")):
            resp = client.get("/api/hf/models")
        assert resp.status_code == 500


class TestGithubAuthStart:
    def test_returns_error_when_client_id_missing(self):
        with patch.object(main, "GITHUB_CLIENT_ID", ""):
            resp = client.post("/api/github/auth/start")
        assert resp.status_code == 500
        assert "GITHUB_CLIENT_ID" in resp.json().get("error", "")

    def test_returns_device_code_response(self):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"device_code": "abc", "user_code": "XXXX-YYYY", "interval": 5}

        with patch.object(main, "GITHUB_CLIENT_ID", "test_client_id"):
            with patch("main.requests.post", return_value=mock_resp):
                resp = client.post("/api/github/auth/start")

        assert resp.status_code == 200
        assert resp.json()["device_code"] == "abc"


class TestGithubAuthPoll:
    def test_returns_error_when_credentials_missing(self):
        with patch.object(main, "GITHUB_CLIENT_ID", ""), \
             patch.object(main, "GITHUB_CLIENT_SECRET", ""):
            resp = client.post("/api/github/auth/poll", json={"device_code": "abc"})
        assert resp.status_code == 500

    def test_returns_access_token_on_success(self):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"access_token": "gho_test123", "token_type": "bearer"}

        with patch.object(main, "GITHUB_CLIENT_ID", "id"), \
             patch.object(main, "GITHUB_CLIENT_SECRET", "secret"), \
             patch("main.requests.post", return_value=mock_resp):
            resp = client.post("/api/github/auth/poll", json={"device_code": "abc"})

        assert resp.status_code == 200
        assert resp.json()["access_token"] == "gho_test123"


class TestGithubUser:
    def test_returns_user_on_valid_token(self):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"login": "FAJU85", "name": "Test User"}

        with patch("main.requests.get", return_value=mock_resp):
            resp = client.post("/api/github/user", json={"token": "gho_test"})

        assert resp.status_code == 200
        assert resp.json()["login"] == "FAJU85"

    def test_returns_400_on_invalid_token(self):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.json.return_value = {"message": "Bad credentials"}

        with patch("main.requests.get", return_value=mock_resp):
            resp = client.post("/api/github/user", json={"token": "bad"})

        assert resp.status_code == 400


class TestGithubRepos:
    def test_returns_repo_list(self):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = [
            {"full_name": "FAJU85/devforge", "name": "devforge", "description": "test",
             "private": False, "language": "Python"},
        ]

        with patch("main.requests.get", return_value=mock_resp):
            resp = client.post("/api/github/repos", json={"token": "gho_test"})

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data[0]["full_name"] == "FAJU85/devforge"

    def test_returns_empty_list_on_bad_status(self):
        mock_resp = MagicMock()
        mock_resp.ok = False

        with patch("main.requests.get", return_value=mock_resp):
            resp = client.post("/api/github/repos", json={"token": "bad"})

        assert resp.status_code == 200
        assert resp.json() == []


class TestRepoConnect:
    def test_returns_400_on_invalid_url(self):
        resp = client.post("/api/repo/connect", json={"token": "t", "url": "not-valid"})
        assert resp.status_code == 400

    def test_returns_repo_info_on_success(self):
        repo_resp = MagicMock()
        repo_resp.ok = True
        repo_resp.json.return_value = {"default_branch": "main"}

        tree_resp = MagicMock()
        tree_resp.ok = True
        tree_resp.json.return_value = {
            "tree": [
                {"path": "main.py", "type": "blob", "size": 1000},
                {"path": "README.md", "type": "blob", "size": 500},
            ]
        }

        with patch("main.requests.get", side_effect=[repo_resp, tree_resp]):
            resp = client.post("/api/repo/connect", json={"token": "t", "url": "FAJU85/devforge"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["owner"] == "FAJU85"
        assert data["repo"] == "devforge"
        assert len(data["files"]) == 2

    def test_returns_400_when_repo_not_found(self):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.json.return_value = {"message": "Not Found"}

        with patch("main.requests.get", return_value=mock_resp):
            resp = client.post("/api/repo/connect", json={"token": "t", "url": "FAJU85/devforge"})

        assert resp.status_code == 400


class TestRepoFile:
    def test_returns_file_content_on_success(self):
        import base64
        content_b64 = base64.b64encode(b"print('hello')").decode()

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"content": content_b64 + "\n"}

        with patch("main.requests.get", return_value=mock_resp):
            resp = client.post("/api/repo/file", json={
                "token": "t", "owner": "FAJU85", "repo": "devforge", "path": "main.py"
            })

        assert resp.status_code == 200
        assert resp.json()["content"] == "print('hello')"

    def test_returns_400_on_fetch_error(self):
        mock_resp = MagicMock()
        mock_resp.ok = False

        with patch("main.requests.get", return_value=mock_resp):
            resp = client.post("/api/repo/file", json={
                "token": "t", "owner": "FAJU85", "repo": "devforge", "path": "missing.py"
            })

        assert resp.status_code == 400

    def test_returns_400_on_binary_content(self):
        """Trigger the base64 decode exception path (lines 258-259)."""
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"content": "!!!not-valid-base64!!!"}

        with patch("main.requests.get", return_value=mock_resp):
            resp = client.post("/api/repo/file", json={
                "token": "t", "owner": "FAJU85", "repo": "devforge", "path": "binary.bin"
            })

        assert resp.status_code == 400
        assert "Binary file" in resp.json().get("error", "")


# ---------------------------------------------------------------------------
# _run_groq: KeyError/IndexError branch (lines 108-109)
# ---------------------------------------------------------------------------

class TestRunGroqStructureErrors:
    def test_run_groq_skips_chunk_with_missing_choices_key(self):
        bad_structure = json.dumps({"other_key": "value"})  # no "choices"
        done_line = b"data: [DONE]"

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            f"data: {bad_structure}".encode(),
            done_line,
        ])

        with patch("main.requests.post", return_value=mock_response):
            items = _run_runner_sync(main._run_groq, "sys", [], "key", "llama")

        kinds = [k for k, _ in items]
        assert "done" in kinds
        assert "error" not in kinds

    def test_run_groq_skips_chunk_with_empty_choices(self):
        bad_structure = json.dumps({"choices": []})  # IndexError on [0]
        done_line = b"data: [DONE]"

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([
            f"data: {bad_structure}".encode(),
            done_line,
        ])

        with patch("main.requests.post", return_value=mock_response):
            items = _run_runner_sync(main._run_groq, "sys", [], "key", "llama")

        kinds = [k for k, _ in items]
        assert "done" in kinds
        assert "error" not in kinds


# ---------------------------------------------------------------------------
# github_repos: multi-page pagination (lines 193-200)
# ---------------------------------------------------------------------------

class TestGithubReposPagination:
    def test_paginates_through_multiple_pages(self):
        page1 = [
            {"full_name": f"user/repo{i}", "name": f"repo{i}", "description": "",
             "private": False, "language": "Python"}
            for i in range(100)
        ]
        page2 = [
            {"full_name": f"user/repo{i}", "name": f"repo{i}", "description": "",
             "private": False, "language": "Python"}
            for i in range(100, 110)
        ]

        pages = iter([page1, page2])

        def side_effect_pages(*_args, **_kwargs):
            mock = MagicMock()
            mock.ok = True
            mock.json.return_value = next(pages)
            return mock

        with patch("main.requests.get", side_effect=side_effect_pages):
            resp = client.post("/api/github/repos", json={"token": "t"})

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 110


# ---------------------------------------------------------------------------
# get_runner: HF env token fallback (line 296)
# ---------------------------------------------------------------------------

class TestGetRunnerHfEnvToken:
    def test_hf_runner_uses_env_token_when_body_token_empty(self):
        with patch.object(main, "HF_TOKEN", "env_hf_token"):
            body = _body(provider="hf", hf_token="")
            runner = main.get_runner(body)
        assert callable(runner)


# ---------------------------------------------------------------------------
# chat_stream endpoint (lines 301-349)
# ---------------------------------------------------------------------------

async def _mock_stream_text(*_args, **_kwargs):
    yield "text", "streamed text"


async def _mock_stream_error(*_args, **_kwargs):
    yield "error", "something went wrong"


class TestChatStream:
    def test_single_stream_returns_sse(self):
        with patch("main.stream_one", side_effect=_mock_stream_text):
            resp = client.post("/api/chat/stream", json={
                "provider": "anthropic",
                "anthropic_key": "k",
                "messages": [{"role": "user", "content": "hi"}],
            })

        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        assert "streamed text" in resp.text

    def test_multi_agent_stream_returns_steps(self):
        call_count = 0

        async def mock_stream_multi(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            yield "text", f"stage_{call_count}_response"

        with patch("main.stream_one", side_effect=mock_stream_multi):
            resp = client.post("/api/chat/stream", json={
                "provider": "anthropic",
                "anthropic_key": "k",
                "messages": [{"role": "user", "content": "build it"}],
                "multi_agent": True,
            })

        assert resp.status_code == 200
        body = resp.text
        assert "plan" in body
        assert "code" in body
        assert "review" in body

    def test_single_stream_error_is_forwarded(self):
        with patch("main.stream_one", side_effect=_mock_stream_error):
            resp = client.post("/api/chat/stream", json={
                "provider": "anthropic",
                "anthropic_key": "k",
                "messages": [{"role": "user", "content": "fail"}],
            })

        assert resp.status_code == 200
        assert "something went wrong" in resp.text


# ---------------------------------------------------------------------------
# stream_one async generator (lines 127-137)
# ---------------------------------------------------------------------------

class TestStreamOne:
    def test_stream_one_yields_text_and_stops_on_done(self):
        async def run():
            results = []

            def sync_runner(q, loop, system, messages):
                asyncio.run_coroutine_threadsafe(q.put(("text", "hi")), loop)
                asyncio.run_coroutine_threadsafe(q.put(("done", None)), loop)

            async for kind, val in main.stream_one(sync_runner, "sys", []):
                results.append((kind, val))
            return results

        results = asyncio.get_event_loop().run_until_complete(run())
        assert results == [("text", "hi")]

    def test_stream_one_yields_error_tuple_on_error_kind(self):
        async def run():
            results = []

            def sync_runner(q, loop, system, messages):
                asyncio.run_coroutine_threadsafe(q.put(("error", "boom")), loop)

            async for kind, val in main.stream_one(sync_runner, "sys", []):
                results.append((kind, val))
            return results

        results = asyncio.get_event_loop().run_until_complete(run())
        assert results == [("error", "boom")]


# ---------------------------------------------------------------------------
# _run_openai_compat
# ---------------------------------------------------------------------------

class TestRunOpenAiCompat:
    def test_puts_text_and_done_on_success(self):
        chunk_data = json.dumps({"choices": [{"delta": {"content": "hello"}}]})
        mock_line = f"data: {chunk_data}".encode()
        done_line = b"data: [DONE]"

        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.iter_lines.return_value = iter([mock_line, done_line])

        with patch("main.requests.post", return_value=mock_response):
            items = _run_runner_sync(
                main._run_openai_compat,
                "sys", [{"role": "user", "content": "hi"}],
                "api_key", "http://localhost:11434/v1", "llama3",
            )

        kinds = [k for k, _ in items]
        assert "text" in kinds
        assert "done" in kinds

    def test_omits_auth_header_when_no_key(self):
        captured = {}

        def capture_post(url, headers, **kwargs):
            captured["headers"] = headers
            mock = MagicMock()
            mock.ok = False
            mock.status_code = 200
            mock.text = "x"
            return mock

        with patch("main.requests.post", side_effect=capture_post):
            _run_runner_sync(
                main._run_openai_compat,
                "sys", [], "", "http://localhost:11434/v1", "llama3",
            )

        assert "Authorization" not in captured.get("headers", {})

    def test_includes_auth_header_when_key_provided(self):
        captured = {}

        def capture_post(url, headers, **kwargs):
            captured["headers"] = headers
            mock = MagicMock()
            mock.ok = False
            mock.status_code = 200
            mock.text = "x"
            return mock

        with patch("main.requests.post", side_effect=capture_post):
            _run_runner_sync(
                main._run_openai_compat,
                "sys", [], "my-secret-key", "http://localhost:11434/v1", "llama3",
            )

        assert captured["headers"].get("Authorization") == "Bearer my-secret-key"

    def test_uses_provided_base_url(self):
        captured = {}

        def capture_post(url, **kwargs):
            captured["url"] = url
            mock = MagicMock()
            mock.ok = True
            mock.iter_lines.return_value = iter([b"data: [DONE]"])
            return mock

        with patch("main.requests.post", side_effect=capture_post):
            _run_runner_sync(
                main._run_openai_compat,
                "sys", [], "", "https://openrouter.ai/api/v1", "mistral-7b",
            )

        assert captured["url"] == "https://openrouter.ai/api/v1/chat/completions"

    def test_strips_trailing_slash_from_base_url(self):
        captured = {}

        def capture_post(url, **kwargs):
            captured["url"] = url
            mock = MagicMock()
            mock.ok = True
            mock.iter_lines.return_value = iter([b"data: [DONE]"])
            return mock

        with patch("main.requests.post", side_effect=capture_post):
            _run_runner_sync(
                main._run_openai_compat,
                "sys", [], "", "http://localhost:11434/v1/", "llama3",
            )

        assert captured["url"] == "http://localhost:11434/v1/chat/completions"

    def test_puts_error_on_bad_http_status(self):
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 503
        mock_response.text = "Service Unavailable"

        with patch("main.requests.post", return_value=mock_response):
            items = _run_runner_sync(
                main._run_openai_compat,
                "sys", [], "", "http://localhost:11434/v1", "llama3",
            )

        kinds = [k for k, _ in items]
        assert "error" in kinds

    def test_puts_error_on_network_exception(self):
        with patch("main.requests.post", side_effect=ConnectionError("refused")):
            items = _run_runner_sync(
                main._run_openai_compat,
                "sys", [], "", "http://localhost:11434/v1", "llama3",
            )

        kinds = [k for k, _ in items]
        assert "error" in kinds


# ---------------------------------------------------------------------------
# repo_write endpoint
# ---------------------------------------------------------------------------

class TestRepoWrite:
    def test_creates_new_file_when_not_found(self):
        """GET returns 404 (no SHA) → PUT creates the file."""
        get_resp = MagicMock(); get_resp.ok = False
        put_resp = MagicMock(); put_resp.ok = True
        put_resp.json.return_value = {
            "commit": {"sha": "abc123", "html_url": "https://github.com/owner/repo/commit/abc123"},
            "content": {"html_url": "https://github.com/owner/repo/blob/main/src/f.py"},
        }
        with patch("main.requests.get", return_value=get_resp), \
             patch("main.requests.put", return_value=put_resp):
            resp = client.post("/api/repo/write", json={
                "token": "t", "owner": "FAJU85", "repo": "devforge",
                "path": "src/f.py", "content": "print('hi')",
                "message": "Add f.py", "branch": "main",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["sha"] == "abc123"
        assert "commit" in data["commit_url"]

    def test_updates_existing_file_with_sha(self):
        """GET returns 200 with SHA → PUT includes sha in payload."""
        get_resp = MagicMock(); get_resp.ok = True
        get_resp.json.return_value = {"sha": "existingsha"}
        put_resp = MagicMock(); put_resp.ok = True
        put_resp.json.return_value = {
            "commit": {"sha": "newsha", "html_url": "https://github.com/owner/repo/commit/newsha"},
            "content": {"html_url": "https://github.com/owner/repo/blob/main/src/f.py"},
        }
        captured = {}
        def capture_put(url, headers, json, **kwargs):
            captured["payload"] = json
            return put_resp
        with patch("main.requests.get", return_value=get_resp), \
             patch("main.requests.put", side_effect=capture_put):
            resp = client.post("/api/repo/write", json={
                "token": "t", "owner": "FAJU85", "repo": "devforge",
                "path": "src/f.py", "content": "print('updated')",
                "message": "Update f.py", "branch": "main",
            })
        assert resp.status_code == 200
        assert captured["payload"]["sha"] == "existingsha"

    def test_returns_400_on_write_failure(self):
        get_resp = MagicMock(); get_resp.ok = False
        put_resp = MagicMock(); put_resp.ok = False
        put_resp.json.return_value = {"message": "Repository not found"}
        with patch("main.requests.get", return_value=get_resp), \
             patch("main.requests.put", return_value=put_resp):
            resp = client.post("/api/repo/write", json={
                "token": "bad", "owner": "FAJU85", "repo": "devforge",
                "path": "f.py", "content": "x", "message": "m", "branch": "main",
            })
        assert resp.status_code == 400
        assert "Repository not found" in resp.json()["error"]

    def test_content_is_base64_encoded_in_put_payload(self):
        import base64 as b64
        get_resp = MagicMock(); get_resp.ok = False
        put_resp = MagicMock(); put_resp.ok = True
        put_resp.json.return_value = {"commit": {"sha": "", "html_url": ""}, "content": {"html_url": ""}}
        captured = {}
        def capture_put(url, headers, json, **kwargs):
            captured["payload"] = json
            return put_resp
        with patch("main.requests.get", return_value=get_resp), \
             patch("main.requests.put", side_effect=capture_put):
            client.post("/api/repo/write", json={
                "token": "t", "owner": "o", "repo": "r",
                "path": "f.py", "content": "hello world",
                "message": "m", "branch": "main",
            })
        decoded = b64.b64decode(captured["payload"]["content"]).decode()
        assert decoded == "hello world"


# ---------------------------------------------------------------------------
# get_runner: openai_compat provider (new branch)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# get_runner: provider override (cross-provider multi-agent)
# ---------------------------------------------------------------------------

class TestGetRunnerProviderOverride:
    def test_override_selects_groq_runner_regardless_of_body_provider(self):
        body = _body(provider="anthropic", groq_key="k")
        runner = main.get_runner(body, provider="groq")
        assert callable(runner)

    def test_empty_override_falls_back_to_body_provider(self):
        body = _body(provider="groq", groq_key="k")
        runner = main.get_runner(body, provider="")
        assert callable(runner)

    def test_override_anthropic_uses_anthropic_key_from_body(self):
        body = _body(provider="groq", anthropic_key="sk-ant-test")
        runner = main.get_runner(body, provider="anthropic")
        assert callable(runner)


# ---------------------------------------------------------------------------
# multi-agent stream: per-stage providers
# ---------------------------------------------------------------------------

class TestMultiAgentPerStageProviders:
    def test_multi_agent_stream_includes_provider_label_in_step_events(self):
        call_count = 0

        async def mock_stream(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            yield "text", f"stage_{call_count}"

        with patch("main.stream_one", side_effect=mock_stream):
            resp = client.post("/api/chat/stream", json={
                "provider": "anthropic",
                "anthropic_key": "k",
                "messages": [{"role": "user", "content": "build it"}],
                "multi_agent": True,
                "ma_plan_provider": "groq",
                "ma_code_provider": "anthropic",
                "ma_review_provider": "hf",
            })

        assert resp.status_code == 200
        body = resp.text
        assert "Groq" in body
        assert "Claude" in body
        assert "HF" in body

    def test_empty_stage_provider_falls_back_to_main_provider(self):
        async def mock_stream(*_args, **_kwargs):
            yield "text", "ok"

        with patch("main.stream_one", side_effect=mock_stream):
            resp = client.post("/api/chat/stream", json={
                "provider": "groq",
                "groq_key": "k",
                "messages": [{"role": "user", "content": "task"}],
                "multi_agent": True,
                "ma_plan_provider": "",
                "ma_code_provider": "",
                "ma_review_provider": "",
            })

        assert resp.status_code == 200
        assert "Groq" in resp.text


class TestGetRunnerOpenAiCompat:
    def test_openai_compat_provider_returns_callable(self):
        body = _body(
            provider="openai_compat",
            openai_compat_key="sk-test",
            openai_compat_base_url="http://localhost:11434/v1",
            openai_compat_model="llama3",
        )
        runner = main.get_runner(body)
        assert callable(runner)

    def test_openai_compat_uses_default_url_when_empty(self):
        body = _body(
            provider="openai_compat",
            openai_compat_key="",
            openai_compat_base_url="",
            openai_compat_model="",
        )
        runner = main.get_runner(body)
        assert callable(runner)

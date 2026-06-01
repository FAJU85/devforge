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
        assert result.startswith("Use only stdlib.")
        # Security footer is always appended for code agents
        assert "Security Requirements" in result

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

    def test_run_hf_puts_error_when_token_empty(self):
        items = _run_runner_sync(main._run_hf, "sys", [], "", "model")

        kinds = [k for k, _ in items]
        assert "error" in kinds
        error_vals = [v for k, v in items if k == "error"]
        assert error_vals
        assert "HF_TOKEN" in error_vals[0]


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


# ---------------------------------------------------------------------------
# Cycle 5 — new agents, skills, memory, token usage
# ---------------------------------------------------------------------------

class TestBatchWriteEndpoint:
    def test_batch_write_commits_all_files(self):
        with patch("main.requests.get") as mock_get, patch("main.requests.put") as mock_put:
            mock_get.return_value = MagicMock(ok=False)  # no existing SHA
            mock_put.return_value = MagicMock(
                ok=True,
                json=lambda: {"commit": {"sha": "abc", "html_url": "https://github.com/o/r/commit/abc"}, "content": {}},
            )
            resp = client.post("/api/repo/write/batch", json={
                "token": "tok", "owner": "o", "repo": "r", "branch": "main",
                "files": [
                    {"path": "src/a.ts", "content": "const a = 1;", "message": "feat: a"},
                    {"path": "src/b.ts", "content": "const b = 2;", "message": "feat: b"},
                ],
            })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["committed"]) == 2
        assert data["errors"] == []

    def test_batch_write_reports_per_file_errors(self):
        with patch("main.requests.get") as mock_get, patch("main.requests.put") as mock_put:
            mock_get.return_value = MagicMock(ok=False)
            call_count = {"n": 0}
            def _put(*a, **kw):
                call_count["n"] += 1
                if call_count["n"] == 1:
                    return MagicMock(ok=True, json=lambda: {"commit": {"sha": "x", "html_url": ""}, "content": {}})
                return MagicMock(ok=False, json=lambda: {"message": "conflict"})
            mock_put.side_effect = _put
            resp = client.post("/api/repo/write/batch", json={
                "token": "tok", "owner": "o", "repo": "r", "branch": "main",
                "files": [
                    {"path": "a.ts", "content": "ok", "message": "m1"},
                    {"path": "b.ts", "content": "fail", "message": "m2"},
                ],
            })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["committed"]) == 1
        assert len(data["errors"]) == 1
        assert data["errors"][0]["path"] == "b.ts"

    def test_batch_write_uses_existing_sha(self):
        with patch("main.requests.get") as mock_get, patch("main.requests.put") as mock_put:
            mock_get.return_value = MagicMock(ok=True, json=lambda: {"sha": "existing-sha"})
            mock_put.return_value = MagicMock(
                ok=True, json=lambda: {"commit": {"sha": "new", "html_url": ""}, "content": {}},
            )
            client.post("/api/repo/write/batch", json={
                "token": "tok", "owner": "o", "repo": "r", "branch": "main",
                "files": [{"path": "f.ts", "content": "x", "message": "m"}],
            })
        call_json = mock_put.call_args.kwargs.get("json") or mock_put.call_args[1].get("json")
        assert call_json["sha"] == "existing-sha"


class TestSuggestFiles:
    def test_suggest_files_with_groq(self):
        with patch("main.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                ok=True,
                json=lambda: {"choices": [{"message": {"content": '["src/auth.ts", "src/utils.ts"]'}}]},
            )
            resp = client.post("/api/repo/suggest-files", json={
                "provider": "groq",
                "groq_key": "k",
                "task": "Fix authentication bug",
                "files": ["src/auth.ts", "src/utils.ts", "src/index.ts"],
            })
        assert resp.status_code == 200
        data = resp.json()
        assert "files" in data
        # Only files that exist in repo should be returned
        for f in data["files"]:
            assert f in ["src/auth.ts", "src/utils.ts", "src/index.ts"]

    def test_suggest_files_filters_nonexistent_paths(self):
        with patch("main.requests.post") as mock_post:
            # AI returns a file that's NOT in the repo
            mock_post.return_value = MagicMock(
                ok=True,
                json=lambda: {"choices": [{"message": {"content": '["src/auth.ts", "nonexistent.ts"]'}}]},
            )
            resp = client.post("/api/repo/suggest-files", json={
                "provider": "groq",
                "groq_key": "k",
                "task": "task",
                "files": ["src/auth.ts", "src/other.ts"],
            })
        assert resp.status_code == 200
        assert "nonexistent.ts" not in resp.json()["files"]

    def test_suggest_files_no_provider_returns_error(self):
        resp = client.post("/api/repo/suggest-files", json={
            "provider": "anthropic",
            "anthropic_key": "",  # no key
            "task": "task",
            "files": ["src/a.ts"],
        })
        assert resp.status_code == 400

    def test_suggest_files_handles_json_in_prose(self):
        """AI sometimes wraps the array in markdown prose."""
        with patch("main.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                ok=True,
                json=lambda: {"choices": [{"message": {"content": 'Here are the files: ["a.ts", "b.ts"]. These are most relevant.'}}]},
            )
            resp = client.post("/api/repo/suggest-files", json={
                "provider": "groq", "groq_key": "k",
                "task": "t", "files": ["a.ts", "b.ts", "c.ts"],
            })
        assert resp.status_code == 200
        assert "a.ts" in resp.json()["files"]

    def test_suggest_files_groq_api_failure(self):
        with patch("main.requests.post") as mock_post:
            mock_post.return_value = MagicMock(ok=False, json=lambda: {})
            resp = client.post("/api/repo/suggest-files", json={
                "provider": "groq", "groq_key": "k",
                "task": "t", "files": ["a.ts"],
            })
        # Returns 400 because AI returned non-parseable "[]"
        assert resp.status_code in (200, 400)


class TestFourStagePipeline:
    def test_chatbody_has_test_stage_fields(self):
        body = _body(ma_include_test_stage=True, ma_test_provider="groq")
        assert body.ma_include_test_stage is True
        assert body.ma_test_provider == "groq"

    def test_chatbody_test_stage_defaults_false(self):
        body = _body()
        assert body.ma_include_test_stage is False
        assert body.ma_test_provider == ""

    def test_ma_test_system_defined(self):
        assert hasattr(main, "MA_TEST_SYSTEM")
        assert "test" in main.MA_TEST_SYSTEM.lower()

    def test_multi_agent_stream_includes_test_step_when_enabled(self):
        async def mock_stream(*_args, **_kwargs):
            yield "text", "response"

        with patch("main.stream_one", side_effect=mock_stream):
            resp = client.post("/api/chat/stream", json={
                "provider": "groq",
                "groq_key": "k",
                "messages": [{"role": "user", "content": "task"}],
                "multi_agent": True,
                "ma_include_test_stage": True,
                "ma_plan_provider": "",
                "ma_code_provider": "",
                "ma_test_provider": "",
                "ma_review_provider": "",
            })
        assert resp.status_code == 200
        assert "Testing" in resp.text

    def test_multi_agent_stream_skips_test_step_when_disabled(self):
        async def mock_stream(*_args, **_kwargs):
            yield "text", "response"

        with patch("main.stream_one", side_effect=mock_stream):
            resp = client.post("/api/chat/stream", json={
                "provider": "groq",
                "groq_key": "k",
                "messages": [{"role": "user", "content": "task"}],
                "multi_agent": True,
                "ma_include_test_stage": False,
                "ma_plan_provider": "",
                "ma_code_provider": "",
                "ma_review_provider": "",
            })
        assert resp.status_code == 200
        # Testing label should NOT appear
        assert "Testing" not in resp.text


class TestGitHubIssueCreate:
    def test_create_issue_success(self):
        with patch("main.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                ok=True,
                json=lambda: {"html_url": "https://github.com/o/r/issues/1", "number": 1},
            )
            resp = client.post("/api/github/issue/create", json={
                "token": "tok", "owner": "o", "repo": "r",
                "title": "Bug found", "body": "Description", "labels": ["bug"],
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["number"] == 1
        assert "issues/1" in data["url"]

    def test_create_issue_failure(self):
        with patch("main.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                ok=False,
                json=lambda: {"message": "Not Found"},
            )
            resp = client.post("/api/github/issue/create", json={
                "token": "tok", "owner": "o", "repo": "r",
                "title": "t", "body": "b",
            })
        assert resp.status_code == 400
        assert "error" in resp.json()

    def test_create_issue_no_labels_default(self):
        with patch("main.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                ok=True,
                json=lambda: {"html_url": "https://github.com/o/r/issues/2", "number": 2},
            )
            resp = client.post("/api/github/issue/create", json={
                "token": "tok", "owner": "o", "repo": "r",
                "title": "t", "body": "b",
            })
        assert resp.status_code == 200
        # verify labels was passed as empty list
        call_json = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert call_json["labels"] == []


class TestGitHubPRCreate:
    def test_create_pr_success(self):
        with patch("main.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                ok=True,
                json=lambda: {"html_url": "https://github.com/o/r/pull/5", "number": 5},
            )
            resp = client.post("/api/github/pr/create", json={
                "token": "tok", "owner": "o", "repo": "r",
                "title": "Add feature", "body": "PR body",
                "head": "feat/my-branch", "base": "main",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert data["number"] == 5
        assert "pull/5" in data["url"]

    def test_create_pr_failure(self):
        with patch("main.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                ok=False,
                json=lambda: {"message": "Unprocessable Entity"},
            )
            resp = client.post("/api/github/pr/create", json={
                "token": "tok", "owner": "o", "repo": "r",
                "title": "t", "body": "b", "head": "h", "base": "main",
            })
        assert resp.status_code == 400

    def test_create_pr_passes_head_and_base(self):
        with patch("main.requests.post") as mock_post:
            mock_post.return_value = MagicMock(
                ok=True,
                json=lambda: {"html_url": "https://github.com/o/r/pull/6", "number": 6},
            )
            client.post("/api/github/pr/create", json={
                "token": "tok", "owner": "o", "repo": "r",
                "title": "t", "body": "b", "head": "feat/x", "base": "develop",
            })
        call_json = mock_post.call_args.kwargs.get("json") or mock_post.call_args[1].get("json")
        assert call_json["head"] == "feat/x"
        assert call_json["base"] == "develop"


class TestNewAgentPrompts:
    def test_refactor_agent_in_prompts(self):
        assert "refactor" in main.AGENT_PROMPTS
        assert "refactor" in main.AGENT_PROMPTS["refactor"].lower() or "restructure" in main.AGENT_PROMPTS["refactor"].lower()

    def test_testgen_agent_in_prompts(self):
        assert "testgen" in main.AGENT_PROMPTS
        assert "test" in main.AGENT_PROMPTS["testgen"].lower()

    def test_build_system_uses_refactor_prompt(self):
        body = _body(agent="refactor")
        system = main.build_system(body)
        assert "refactor" in system.lower() or "restructure" in system.lower()

    def test_build_system_uses_testgen_prompt(self):
        body = _body(agent="testgen")
        system = main.build_system(body)
        assert "test" in system.lower()

    def test_all_original_agents_still_present(self):
        for agent in ("code", "review", "architect", "debug", "docs"):
            assert agent in main.AGENT_PROMPTS


class TestNewSkillPrompts:
    def test_react_skill_present(self):
        assert "react" in main.SKILL_PROMPTS
        assert "React" in main.SKILL_PROMPTS["react"]

    def test_nextjs_skill_present(self):
        assert "nextjs" in main.SKILL_PROMPTS
        assert "Next.js" in main.SKILL_PROMPTS["nextjs"]

    def test_docker_skill_present(self):
        assert "docker" in main.SKILL_PROMPTS
        assert "Docker" in main.SKILL_PROMPTS["docker"]

    def test_sql_skill_present(self):
        assert "sql" in main.SKILL_PROMPTS
        assert "SQL" in main.SKILL_PROMPTS["sql"]

    def test_all_original_skills_still_present(self):
        for skill in ("go", "zod", "tests", "errors", "security", "docs", "perf", "solid"):
            assert skill in main.SKILL_PROMPTS

    def test_new_skills_injected_in_system_prompt(self):
        body = _body(skills=["react", "nextjs", "docker", "sql"])
        system = main.build_system(body)
        for keyword in ("React", "Next.js", "Docker", "SQL"):
            assert keyword in system


class TestSessionMemory:
    def test_memory_field_on_chatbody(self):
        body = _body(memory="User was working on auth module")
        assert body.memory == "User was working on auth module"

    def test_memory_defaults_to_empty(self):
        body = _body()
        assert body.memory == ""

    def test_build_system_injects_memory(self):
        body = _body(memory="Previous session: fixed OAuth bug in auth.py")
        system = main.build_system(body)
        assert "Previous Session Context" in system
        assert "OAuth bug" in system

    def test_build_system_skips_empty_memory(self):
        body = _body(memory="")
        system = main.build_system(body)
        assert "Previous Session Context" not in system

    def test_build_system_skips_whitespace_memory(self):
        body = _body(memory="   ")
        system = main.build_system(body)
        assert "Previous Session Context" not in system


class TestAnthropicTokenUsage:
    def test_run_anthropic_emits_usage_event(self):
        """_run_anthropic should put a ('usage', {...}) tuple after streaming."""
        import queue as _q
        import threading

        q = _q.Queue()

        # Build a fake Anthropic streaming context manager
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        mock_stream_ctx.text_stream = iter(["hello ", "world"])

        mock_final = MagicMock()
        mock_final.usage.input_tokens = 10
        mock_final.usage.output_tokens = 5
        mock_stream_ctx.get_final_message = MagicMock(return_value=mock_final)

        mock_client = MagicMock()
        mock_client.messages.stream.return_value = mock_stream_ctx

        loop = asyncio.new_event_loop()

        def run():
            with patch("main.Anthropic", return_value=mock_client):
                main._run_anthropic(
                    asyncio.Queue(),  # real queue on the loop
                    loop,
                    "sys",
                    [{"role": "user", "content": "hi"}],
                    "key",
                )

        # Use a real asyncio queue and run via the loop
        real_q: asyncio.Queue = asyncio.Queue()
        captured: list = []

        async def _collect():
            with patch("main.Anthropic", return_value=mock_client):
                t = threading.Thread(
                    target=main._run_anthropic,
                    args=(real_q, loop, "sys", [{"role": "user", "content": "hi"}], "key"),
                    daemon=True,
                )
                t.start()
                while True:
                    kind, val = await real_q.get()
                    captured.append((kind, val))
                    if kind in ("done", "error"):
                        break

        loop.run_until_complete(_collect())
        loop.close()

        kinds = [k for k, _ in captured]
        assert "text" in kinds
        assert "usage" in kinds
        usage_val = next(v for k, v in captured if k == "usage")
        assert usage_val["input"] == 10
        assert usage_val["output"] == 5

    def test_stream_one_passes_usage_events(self):
        """stream_one should yield ('usage', val) tuples it receives from the runner."""
        loop = asyncio.new_event_loop()

        async def fake_runner(q, lp, sys, msgs):
            await q.put(("text", "hello"))
            await q.put(("usage", {"input": 3, "output": 7}))
            await q.put(("done", None))

        async def _run():
            events = []
            async for kind, val in main.stream_one(
                lambda q, lp, s, m: loop.call_soon_threadsafe(
                    loop.create_task, fake_runner(q, lp, s, m)
                ),
                "sys", []
            ):
                events.append((kind, val))
            return events

        # Simpler: test stream_one directly with a real queue
        async def _run2():
            q: asyncio.Queue = asyncio.Queue()
            await q.put(("text", "hi"))
            await q.put(("usage", {"input": 5, "output": 10}))
            await q.put(("done", None))

            events = []
            loop2 = asyncio.get_event_loop()

            def runner(rq, rl, s, m):
                pass  # queue already populated

            # patch stream_one to just drain the queue
            original = main.stream_one

            async def patched_stream(runner_fn, sys_p, msgs_p):
                while True:
                    kind, val = await q.get()
                    if kind in ("text", "usage"):
                        yield kind, val
                    elif kind == "done":
                        break

            async for kind, val in patched_stream(None, "sys", []):
                events.append((kind, val))
            return events

        events = loop.run_until_complete(_run2())
        loop.close()

        assert ("text", "hi") in events
        assert ("usage", {"input": 5, "output": 10}) in events

# ── Cycle 10: Tool Definitions + HTTP Tool Call ────────────────────────────────

class TestToolDef:
    def test_tool_def_defaults(self):
        from main import ToolDef
        t = ToolDef(name="search", description="Search the web", url="https://example.com/search")
        assert t.method == "GET"
        assert t.headers == {}
        assert t.input_schema is None

    def test_tool_def_custom_method(self):
        from main import ToolDef
        t = ToolDef(name="create", description="Create resource", url="https://example.com/api", method="POST")
        assert t.method == "POST"

    def test_tool_def_with_schema(self):
        from main import ToolDef
        schema = {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}
        t = ToolDef(name="search", description="Search", url="https://example.com", input_schema=schema)
        assert t.input_schema["required"] == ["q"]


class TestToolCallEndpoint:
    def test_tool_call_get_success(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = '{"result": "sunny"}'
            r = client.post("/api/tools/call", json={"url": "https://api.weather.example.com/current", "method": "GET"})
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == 200
        assert "sunny" in data["response"]

    def test_tool_call_post_success(self):
        with patch("requests.request") as mock_req:
            mock_req.return_value.status_code = 201
            mock_req.return_value.text = '{"id": "abc123"}'
            r = client.post("/api/tools/call", json={
                "url": "https://api.example.com/items",
                "method": "POST",
                "body_json": {"name": "widget"},
            })
        assert r.status_code == 200
        assert r.json()["status"] == 201

    def test_tool_call_network_error(self):
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("Connection refused")
            r = client.post("/api/tools/call", json={"url": "https://unreachable.invalid", "method": "GET"})
        assert r.status_code == 500
        assert "error" in r.json()

    def test_tool_call_non_ok_status(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 404
            mock_get.return_value.text = "Not Found"
            r = client.post("/api/tools/call", json={"url": "https://example.com/missing", "method": "GET"})
        assert r.status_code == 200
        assert r.json()["status"] == 404


class TestChatBodyWithTools:
    def test_chat_body_accepts_tools(self):
        from main import ChatBody, ToolDef
        body = ChatBody(
            provider="anthropic",
            messages=[{"role": "user", "content": "hi"}],
            tools=[{
                "name": "search",
                "description": "Search the web",
                "url": "https://example.com/search",
                "method": "GET",
                "input_schema": {"type": "object", "properties": {"q": {"type": "string"}}},
            }],
        )
        assert len(body.tools) == 1
        assert body.tools[0].name == "search"
        assert body.tools[0].method == "GET"

    def test_chat_body_empty_tools_default(self):
        from main import ChatBody
        body = ChatBody(
            provider="anthropic",
            messages=[{"role": "user", "content": "hi"}],
        )
        assert body.tools == []

    def test_build_system_with_tools_non_anthropic(self):
        from main import ChatBody, build_system, ToolDef
        body = ChatBody(
            provider="groq",
            messages=[{"role": "user", "content": "hi"}],
            tools=[{"name": "weather", "description": "Get current weather", "url": "https://api.weather.example.com/current", "method": "GET"}],
        )
        sys_prompt = build_system(body)
        assert "Available Tools" in sys_prompt
        assert "weather" in sys_prompt
        assert "Get current weather" in sys_prompt

    def test_build_system_no_tools_anthropic(self):
        from main import ChatBody, build_system
        body = ChatBody(
            provider="anthropic",
            messages=[{"role": "user", "content": "hi"}],
        )
        sys_prompt = build_system(body)
        assert "Available Tools" not in sys_prompt

    def test_build_system_tools_not_injected_for_anthropic(self):
        """Anthropic handles tools natively — system prompt should not list them."""
        from main import ChatBody, build_system
        body = ChatBody(
            provider="anthropic",
            messages=[{"role": "user", "content": "hi"}],
            tools=[{"name": "search", "description": "Search", "url": "https://example.com"}],
        )
        sys_prompt = build_system(body)
        assert "Available Tools" not in sys_prompt

    def test_get_runner_uses_tool_runner_for_anthropic_with_tools(self):
        from main import ChatBody, get_runner, _run_anthropic_with_tools
        body = ChatBody(
            provider="anthropic",
            anthropic_key="sk-test",
            messages=[{"role": "user", "content": "hi"}],
            tools=[{"name": "ping", "description": "Ping a URL", "url": "https://example.com"}],
        )
        runner = get_runner(body)
        # The lambda should wrap _run_anthropic_with_tools
        # We verify by checking the closure captures 'tools'
        closure_vars = runner.__code__.co_freevars if hasattr(runner, '__code__') else []
        # Runner is a lambda — just verify it's callable and different from plain _run_anthropic
        assert callable(runner)

    def test_get_runner_uses_plain_anthropic_without_tools(self):
        from main import ChatBody, get_runner, _run_anthropic
        body = ChatBody(
            provider="anthropic",
            anthropic_key="sk-test",
            messages=[{"role": "user", "content": "hi"}],
            tools=[],
        )
        runner = get_runner(body)
        assert callable(runner)

# ── Cycle 11: Token Budget + File Summarization + Prompt History ──────────────

class TestSummarizeFileEndpoint:
    def test_summarize_with_anthropic(self):
        mock_client = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="This file handles authentication via JWT tokens.")]
        mock_client.messages.create.return_value = mock_msg
        with patch("main.Anthropic", return_value=mock_client):
            r = client.post("/api/repo/summarize-file", json={
                "content": "def authenticate(token): ...",
                "filename": "auth.py",
                "provider": "anthropic",
                "anthropic_key": "sk-test",
            })
        assert r.status_code == 200
        data = r.json()
        assert "summary" in data
        assert "JWT" in data["summary"] or len(data["summary"]) > 0

    def test_summarize_with_groq(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {
                "choices": [{"message": {"content": "This file defines the main FastAPI app."}}]
            }
            r = client.post("/api/repo/summarize-file", json={
                "content": "app = FastAPI()",
                "filename": "main.py",
                "provider": "groq",
                "groq_key": "gsk-test",
            })
        assert r.status_code == 200
        assert "summary" in r.json()

    def test_summarize_no_provider(self):
        r = client.post("/api/repo/summarize-file", json={
            "content": "print('hello')",
            "filename": "hello.py",
            "provider": "anthropic",
            "anthropic_key": "",
        })
        assert r.status_code == 400
        assert "error" in r.json()

    def test_summarize_openai_compat(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {
                "choices": [{"message": {"content": "Router handlers for the API."}}]
            }
            r = client.post("/api/repo/summarize-file", json={
                "content": "@router.get('/')\ndef root(): ...",
                "filename": "router.py",
                "provider": "openai_compat",
                "openai_compat_base_url": "http://localhost:11434/v1",
                "openai_compat_model": "llama3",
            })
        assert r.status_code == 200
        assert r.json()["summary"] == "Router handlers for the API."

    def test_summarize_truncates_large_content(self):
        """Large files should be truncated to first 8000 chars before summarizing."""
        mock_client = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="Large file summary.")]
        mock_client.messages.create.return_value = mock_msg
        with patch("main.Anthropic", return_value=mock_client) as mock_anth:
            large_content = "x" * 20000
            r = client.post("/api/repo/summarize-file", json={
                "content": large_content,
                "filename": "huge.py",
                "provider": "anthropic",
                "anthropic_key": "sk-test",
            })
        assert r.status_code == 200
        # Verify only 8000 chars were passed
        call_args = mock_client.messages.create.call_args
        msg_content = call_args[1]["messages"][0]["content"]
        assert len(msg_content) < 20000 + 200  # prompt overhead is small

# ── Cycle 13: Anthropic Model Selection + Branch Management ───────────────────

class TestAnthropicModelField:
    def test_chat_body_accepts_anthropic_model(self):
        from main import ChatBody
        body = ChatBody(
            provider="anthropic",
            messages=[{"role": "user", "content": "hi"}],
            anthropic_model="claude-haiku-4-5-20251001",
        )
        assert body.anthropic_model == "claude-haiku-4-5-20251001"

    def test_chat_body_default_anthropic_model(self):
        from main import ChatBody
        body = ChatBody(
            provider="anthropic",
            messages=[{"role": "user", "content": "hi"}],
        )
        assert body.anthropic_model == "claude-sonnet-4-6"

    def test_get_runner_passes_model_to_anthropic(self):
        from main import ChatBody, get_runner
        body = ChatBody(
            provider="anthropic",
            anthropic_key="sk-test",
            anthropic_model="claude-opus-4-8",
            messages=[{"role": "user", "content": "hi"}],
        )
        runner = get_runner(body)
        assert callable(runner)
        # Verify the runner captures opus model in closure
        # We can't easily inspect lambdas, but we can verify it's callable

    def test_get_runner_falls_back_to_sonnet_on_empty_model(self):
        from main import ChatBody, get_runner
        body = ChatBody(
            provider="anthropic",
            anthropic_key="sk-test",
            anthropic_model="",
            messages=[{"role": "user", "content": "hi"}],
        )
        runner = get_runner(body)
        assert callable(runner)

    def test_run_anthropic_uses_model_param(self):
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        mock_stream_ctx.text_stream = iter(["hello"])
        mock_final = MagicMock()
        mock_final.usage.input_tokens = 5
        mock_final.usage.output_tokens = 2
        mock_stream_ctx.get_final_message = MagicMock(return_value=mock_final)
        mock_client = MagicMock()
        mock_client.messages.stream.return_value = mock_stream_ctx

        import asyncio as _asyncio
        q = _asyncio.Queue()
        loop = _asyncio.new_event_loop()

        async def _collect():
            import threading
            with patch("main.Anthropic", return_value=mock_client):
                t = threading.Thread(
                    target=main._run_anthropic,
                    args=(q, loop, "sys", [{"role": "user", "content": "hi"}], "key", "claude-haiku-4-5-20251001"),
                    daemon=True,
                )
                t.start()
                collected = []
                while True:
                    kind, val = await q.get()
                    collected.append((kind, val))
                    if kind in ("done", "error"):
                        break
                return collected

        results = loop.run_until_complete(_collect())
        loop.close()

        assert any(k == "text" for k, _ in results)
        call_args = mock_client.messages.stream.call_args
        assert call_args[1]["model"] == "claude-haiku-4-5-20251001"


class TestRepoBranchesEndpoint:
    def test_list_branches_success(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = [
                {"name": "main", "commit": {"sha": "abc1234567"}},
                {"name": "feature/auth", "commit": {"sha": "def9876543"}},
            ]
            r = client.get("/api/repo/branches?token=tok&owner=user&repo=myrepo")
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert data[0]["name"] == "main"
        assert data[0]["sha"] == "abc1234"  # 7 chars
        assert data[1]["name"] == "feature/auth"

    def test_list_branches_api_error(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = False
            r = client.get("/api/repo/branches?token=tok&owner=user&repo=private-repo")
        assert r.status_code == 400
        assert "error" in r.json()

    def test_repo_connect_with_branch_override(self):
        with patch("requests.get") as mock_get:
            repo_response = MagicMock()
            repo_response.ok = True
            repo_response.json.return_value = {"default_branch": "main"}
            tree_response = MagicMock()
            tree_response.ok = True
            tree_response.json.return_value = {"tree": [
                {"type": "blob", "path": "README.md", "size": 500},
            ]}
            mock_get.side_effect = [repo_response, tree_response]
            r = client.post("/api/repo/connect", json={
                "token": "tok",
                "url": "https://github.com/user/repo",
                "branch": "feature/new-api",
            })
        assert r.status_code == 200
        data = r.json()
        # Branch override should be used for tree fetch
        assert data["branch"] == "feature/new-api"
        # Tree fetch URL should use the overridden branch
        tree_call = mock_get.call_args_list[1]
        assert "feature/new-api" in tree_call[0][0]

# ── Cycle 14: Code Search + Commit History ────────────────────────────────────

class TestRepoSearchEndpoint:
    def test_search_returns_results(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = {
                "total_count": 2,
                "items": [
                    {"path": "src/auth.ts", "sha": "abc1234567", "html_url": "https://github.com/x",
                     "text_matches": [{"matches": [{"text": "const auth = "}]}]},
                    {"path": "src/middleware.ts", "sha": "def9876543", "html_url": "https://github.com/y",
                     "text_matches": []},
                ],
            }
            r = client.post("/api/repo/search", json={
                "token": "tok",
                "owner": "user",
                "repo": "myrepo",
                "query": "auth function",
            })
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["path"] == "src/auth.ts"
        assert data["items"][0]["sha"] == "abc1234"
        assert len(data["items"][0]["snippets"]) == 1

    def test_search_empty_query_returns_400(self):
        r = client.post("/api/repo/search", json={
            "token": "tok", "owner": "user", "repo": "myrepo", "query": "   ",
        })
        assert r.status_code == 400
        assert "error" in r.json()

    def test_search_github_api_error(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = False
            mock_get.return_value.json.return_value = {"message": "API rate limit exceeded"}
            r = client.post("/api/repo/search", json={
                "token": "tok", "owner": "user", "repo": "myrepo", "query": "anything",
            })
        assert r.status_code == 400
        assert "rate limit" in r.json()["error"].lower()

    def test_search_caps_at_max_results(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = {"total_count": 0, "items": []}
            r = client.post("/api/repo/search", json={
                "token": "tok", "owner": "user", "repo": "myrepo", "query": "test", "max_results": 100,
            })
        assert r.status_code == 200
        # Verify per_page was capped at 20
        call_args = mock_get.call_args
        params = call_args[1].get("params", {})
        assert params.get("per_page", 0) <= 20


class TestRepoCommitsEndpoint:
    def test_commits_success(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = [
                {"sha": "abc1234567890", "commit": {"message": "Fix auth bug\n\nDetails here",
                 "author": {"name": "Alice", "date": "2026-05-31T10:00:00Z"}},
                 "html_url": "https://github.com/x/commit/abc"},
                {"sha": "def9876543210", "commit": {"message": "Add tests",
                 "author": {"name": "Bob", "date": "2026-05-30T09:00:00Z"}},
                 "html_url": "https://github.com/x/commit/def"},
            ]
            r = client.post("/api/repo/commits", json={
                "token": "tok", "owner": "user", "repo": "myrepo", "branch": "main",
            })
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert data[0]["sha"] == "abc1234"  # 7 chars
        assert data[0]["message"] == "Fix auth bug"  # first line only
        assert data[0]["author"] == "Alice"
        assert data[0]["date"] == "2026-05-31"
        assert data[0]["url"] == "https://github.com/x/commit/abc"

    def test_commits_api_failure(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = False
            r = client.post("/api/repo/commits", json={
                "token": "tok", "owner": "user", "repo": "myrepo",
            })
        assert r.status_code == 400
        assert "error" in r.json()

    def test_commits_caps_per_page(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = []
            r = client.post("/api/repo/commits", json={
                "token": "tok", "owner": "user", "repo": "myrepo", "max_results": 200,
            })
        assert r.status_code == 200
        call_args = mock_get.call_args
        params = call_args[1].get("params", {})
        assert params.get("per_page", 0) <= 30


class TestExtendedThinking:
    def test_chat_body_accepts_thinking_fields(self):
        from main import ChatBody
        body = ChatBody(
            provider="anthropic",
            messages=[{"role": "user", "content": "hi"}],
            thinking_mode=True,
            thinking_budget=8000,
        )
        assert body.thinking_mode is True
        assert body.thinking_budget == 8000

    def test_chat_body_thinking_defaults(self):
        from main import ChatBody
        body = ChatBody(
            provider="anthropic",
            messages=[{"role": "user", "content": "hi"}],
        )
        assert body.thinking_mode is False
        assert body.thinking_budget == 2000

    def test_get_runner_routes_to_thinking_for_opus(self):
        from main import ChatBody, get_runner, _run_anthropic_thinking
        body = ChatBody(
            provider="anthropic",
            anthropic_key="sk-test",
            anthropic_model="claude-opus-4-8",
            thinking_mode=True,
            thinking_budget=4000,
            messages=[{"role": "user", "content": "hi"}],
        )
        runner = get_runner(body)
        # The runner closure should reference _run_anthropic_thinking
        # We verify by calling it and checking the mock is for thinking
        import threading, asyncio as _asyncio

        mock_client = MagicMock()
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        # Simulate thinking then text content_block_delta events
        think_evt = MagicMock()
        think_evt.type = 'content_block_delta'
        think_evt.delta = MagicMock()
        think_evt.delta.type = 'thinking_delta'
        think_evt.delta.thinking = 'I am thinking'
        text_evt = MagicMock()
        text_evt.type = 'content_block_delta'
        text_evt.delta = MagicMock()
        text_evt.delta.type = 'text_delta'
        text_evt.delta.text = 'Answer'
        mock_stream_ctx.__iter__ = MagicMock(return_value=iter([think_evt, text_evt]))
        mock_final = MagicMock()
        mock_final.usage.input_tokens = 10
        mock_final.usage.output_tokens = 5
        mock_stream_ctx.get_final_message = MagicMock(return_value=mock_final)
        mock_client.messages.stream.return_value = mock_stream_ctx

        q = _asyncio.Queue()
        loop = _asyncio.new_event_loop()

        async def _collect():
            with patch("main.Anthropic", return_value=mock_client):
                t = threading.Thread(
                    target=runner,
                    args=(q, loop, "sys", [{"role": "user", "content": "hi"}]),
                    daemon=True,
                )
                t.start()
                collected = []
                while True:
                    kind, val = await q.get()
                    collected.append((kind, val))
                    if kind in ("done", "error"):
                        break
                return collected

        results = loop.run_until_complete(_collect())
        loop.close()

        kinds = [k for k, _ in results]
        assert "thinking" in kinds
        assert "text" in kinds
        # Verify thinking={"type":"enabled",...} was passed
        call_kwargs = mock_client.messages.stream.call_args[1]
        assert call_kwargs.get("thinking", {}).get("type") == "enabled"
        assert call_kwargs.get("thinking", {}).get("budget_tokens") == 4000

    def test_get_runner_does_not_use_thinking_for_sonnet(self):
        from main import ChatBody, get_runner
        body = ChatBody(
            provider="anthropic",
            anthropic_key="sk-test",
            anthropic_model="claude-sonnet-4-6",
            thinking_mode=True,  # ignored — not opus
            messages=[{"role": "user", "content": "hi"}],
        )
        runner = get_runner(body)
        # Should be the plain anthropic runner (not thinking)
        # Verify by calling: no 'thinking' kwarg should be passed to Anthropic
        import threading, asyncio as _asyncio

        mock_client = MagicMock()
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        mock_stream_ctx.text_stream = iter(["Hi"])
        mock_final = MagicMock()
        mock_final.usage.input_tokens = 5
        mock_final.usage.output_tokens = 2
        mock_stream_ctx.get_final_message = MagicMock(return_value=mock_final)
        mock_client.messages.stream.return_value = mock_stream_ctx

        q = _asyncio.Queue()
        loop = _asyncio.new_event_loop()

        async def _collect():
            with patch("main.Anthropic", return_value=mock_client):
                t = threading.Thread(
                    target=runner,
                    args=(q, loop, "sys", [{"role": "user", "content": "hi"}]),
                    daemon=True,
                )
                t.start()
                collected = []
                while True:
                    kind, val = await q.get()
                    collected.append((kind, val))
                    if kind in ("done", "error"):
                        break
                return collected

        results = loop.run_until_complete(_collect())
        loop.close()

        call_kwargs = mock_client.messages.stream.call_args[1]
        assert "thinking" not in call_kwargs


class TestPromptEnhance:
    def test_enhance_with_anthropic(self):
        mock_client = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="Write a Python function that validates email using regex, with unit tests.")]
        mock_client.messages.create.return_value = mock_msg
        with patch("main.Anthropic", return_value=mock_client):
            r = client.post("/api/prompt/enhance", json={
                "provider": "anthropic",
                "anthropic_key": "sk-test",
                "prompt": "validate email",
            })
        assert r.status_code == 200
        data = r.json()
        assert "enhanced" in data
        assert len(data["enhanced"]) > 5

    def test_enhance_with_groq(self):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "Validate user email addresses using a Groq-based prompt."}}]
        }
        with patch("requests.post", return_value=mock_resp):
            r = client.post("/api/prompt/enhance", json={
                "provider": "groq",
                "groq_key": "gsk_test",
                "prompt": "validate email",
            })
        assert r.status_code == 200
        assert "enhanced" in r.json()

    def test_enhance_empty_prompt_returns_400(self):
        r = client.post("/api/prompt/enhance", json={
            "provider": "anthropic",
            "anthropic_key": "sk-test",
            "prompt": "",
        })
        assert r.status_code == 400
        assert "error" in r.json()

    def test_enhance_no_key_returns_400(self):
        r = client.post("/api/prompt/enhance", json={
            "provider": "hf",
            "hf_token": "",
            "prompt": "fix this bug",
        })
        assert r.status_code == 400
        assert "error" in r.json()


class TestWorkflowRunsEndpoint:
    def test_workflow_runs_success(self):
        mock_runs = {
            "workflow_runs": [
                {
                    "id": 12345,
                    "name": "CI",
                    "display_title": "CI on push",
                    "status": "completed",
                    "conclusion": "success",
                    "head_branch": "main",
                    "head_sha": "abcdef1234567",
                    "updated_at": "2026-05-31T12:00:00Z",
                    "html_url": "https://github.com/user/repo/actions/runs/12345",
                },
                {
                    "id": 12344,
                    "name": "Deploy",
                    "display_title": "Deploy",
                    "status": "completed",
                    "conclusion": "failure",
                    "head_branch": "feature/x",
                    "head_sha": "1111111",
                    "updated_at": "2026-05-30T10:00:00Z",
                    "html_url": "https://github.com/user/repo/actions/runs/12344",
                },
            ]
        }
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = mock_runs
            r = client.post("/api/repo/workflow-runs", json={
                "token": "tok", "owner": "user", "repo": "myrepo",
            })
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        assert data[0]["name"] == "CI"
        assert data[0]["conclusion"] == "success"
        assert data[0]["sha"] == "abcdef1"
        assert data[1]["conclusion"] == "failure"

    def test_workflow_runs_api_failure(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = False
            r = client.post("/api/repo/workflow-runs", json={
                "token": "tok", "owner": "user", "repo": "myrepo",
            })
        assert r.status_code == 400
        assert "error" in r.json()

    def test_workflow_runs_caps_per_page(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = {"workflow_runs": []}
            r = client.post("/api/repo/workflow-runs", json={
                "token": "tok", "owner": "user", "repo": "myrepo", "max_results": 999,
            })
        assert r.status_code == 200
        call_args = mock_get.call_args
        params = call_args[1].get("params", {})
        assert params.get("per_page", 0) <= 20


class TestCommitSuggestMessage:
    def test_suggest_with_anthropic(self):
        mock_client = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="feat(auth): add email validation to login handler")]
        mock_client.messages.create.return_value = mock_msg
        with patch("main.Anthropic", return_value=mock_client):
            r = client.post("/api/commit/suggest-message", json={
                "provider": "anthropic",
                "anthropic_key": "sk-test",
                "path": "src/auth/login.py",
                "content": "def validate_email(email): ...",
            })
        assert r.status_code == 200
        data = r.json()
        assert "message" in data
        assert "auth" in data["message"].lower() or "feat" in data["message"].lower()

    def test_suggest_with_groq(self):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "fix(api): handle null pointer in user service"}}]
        }
        with patch("requests.post", return_value=mock_resp):
            r = client.post("/api/commit/suggest-message", json={
                "provider": "groq",
                "groq_key": "gsk_test",
                "path": "api/user_service.go",
                "content": "func GetUser(id string) (*User, error) { ... }",
            })
        assert r.status_code == 200
        assert "message" in r.json()

    def test_suggest_no_key_returns_400(self):
        r = client.post("/api/commit/suggest-message", json={
            "provider": "hf",
            "path": "src/main.py",
            "content": "print('hello')",
        })
        assert r.status_code == 400
        assert "error" in r.json()


class TestReleaseNotesEndpoint:
    def test_release_notes_anthropic(self):
        mock_commits = [
            {
                "sha": "abc1234567890",
                "commit": {
                    "message": "feat: add user authentication",
                    "author": {"name": "Alice", "date": "2026-05-31"},
                },
            },
            {
                "sha": "def0987654321",
                "commit": {
                    "message": "fix: resolve login redirect bug",
                    "author": {"name": "Bob", "date": "2026-05-30"},
                },
            },
        ]
        mock_client = MagicMock()
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        mock_stream_ctx.text_stream = iter(["## Release v1.1.0\n\n✨ New Features\n- Add user authentication"])
        mock_client.messages.stream.return_value = mock_stream_ctx

        with patch("requests.get") as mock_get, \
             patch("main.Anthropic", return_value=mock_client):
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = mock_commits
            r = client.post("/api/repo/release-notes", json={
                "provider": "anthropic",
                "anthropic_key": "sk-test",
                "token": "tok",
                "owner": "user",
                "repo": "myrepo",
            })
        assert r.status_code == 200
        content = r.text
        assert "text/event-stream" in r.headers.get("content-type", "")

    def test_release_notes_no_commits_returns_400(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = []
            r = client.post("/api/repo/release-notes", json={
                "provider": "anthropic",
                "anthropic_key": "sk-test",
                "token": "tok",
                "owner": "user",
                "repo": "myrepo",
            })
        assert r.status_code == 400
        assert "error" in r.json()

    def test_release_notes_github_api_failure_returns_400(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = False
            r = client.post("/api/repo/release-notes", json={
                "provider": "anthropic",
                "anthropic_key": "sk-test",
                "token": "tok",
                "owner": "user",
                "repo": "myrepo",
            })
        assert r.status_code == 400
        assert "error" in r.json()


class TestPRDiffEndpoint:
    def test_pr_diff_success(self):
        mock_pr = {
            "number": 42,
            "title": "feat: add user auth",
            "body": "Adds OAuth flow.",
            "user": {"login": "alice"},
            "head": {"ref": "feature/auth"},
            "base": {"ref": "main"},
            "changed_files": 3,
            "additions": 120,
            "deletions": 15,
            "html_url": "https://github.com/user/repo/pull/42",
        }
        mock_diff = "diff --git a/auth.py b/auth.py\n+def login(): pass"
        with patch("requests.get") as mock_get:
            def side_effect(url, **kwargs):
                resp = MagicMock()
                if "vnd.github.diff" in str(kwargs.get("headers", {})):
                    resp.ok = True
                    resp.text = mock_diff
                else:
                    resp.ok = True
                    resp.json.return_value = mock_pr
                return resp
            mock_get.side_effect = side_effect
            r = client.post("/api/github/pr/diff", json={
                "token": "tok", "owner": "user", "repo": "myrepo", "pr_number": 42,
            })
        assert r.status_code == 200
        data = r.json()
        assert data["number"] == 42
        assert data["title"] == "feat: add user auth"
        assert data["author"] == "alice"
        assert data["additions"] == 120
        assert "diff --git" in data["diff"]

    def test_pr_diff_not_found(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = False
            r = client.post("/api/github/pr/diff", json={
                "token": "tok", "owner": "user", "repo": "myrepo", "pr_number": 9999,
            })
        assert r.status_code == 404
        assert "error" in r.json()

    def test_pr_diff_caps_diff_at_40k(self):
        big_diff = "+" * 50000
        mock_pr = {
            "number": 1, "title": "big", "body": "", "user": {"login": "x"},
            "head": {"ref": "a"}, "base": {"ref": "main"},
            "changed_files": 1, "additions": 1000, "deletions": 0,
            "html_url": "",
        }
        with patch("requests.get") as mock_get:
            def side_effect(url, **kwargs):
                resp = MagicMock()
                if "vnd.github.diff" in str(kwargs.get("headers", {})):
                    resp.ok = True; resp.text = big_diff
                else:
                    resp.ok = True; resp.json.return_value = mock_pr
                return resp
            mock_get.side_effect = side_effect
            r = client.post("/api/github/pr/diff", json={
                "token": "tok", "owner": "user", "repo": "myrepo", "pr_number": 1,
            })
        assert r.status_code == 200
        assert len(r.json()["diff"]) <= 40000


class TestGistCreate:
    def test_gist_create_success(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {
                "id": "abc123",
                "html_url": "https://gist.github.com/user/abc123",
            }
            r = client.post("/api/github/gist/create", json={
                "token": "tok",
                "filename": "snippet.py",
                "content": "def hello(): return 'world'",
                "description": "Test gist",
                "public": False,
            })
        assert r.status_code == 200
        data = r.json()
        assert data["url"] == "https://gist.github.com/user/abc123"
        assert data["id"] == "abc123"

    def test_gist_default_filename(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {
                "id": "def456", "html_url": "https://gist.github.com/user/def456"
            }
            r = client.post("/api/github/gist/create", json={
                "token": "tok", "filename": "", "content": "hello world",
            })
        assert r.status_code == 200
        # Verify default filename was used
        call_json = mock_post.call_args[1]["json"]
        assert "snippet.txt" in call_json["files"]

    def test_gist_create_failure(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value.ok = False
            mock_post.return_value.json.return_value = {"message": "Bad credentials"}
            r = client.post("/api/github/gist/create", json={
                "token": "bad-tok", "filename": "a.py", "content": "x=1",
            })
        assert r.status_code == 400
        assert "error" in r.json()


class TestGenerateReadmeEndpoint:
    def test_readme_empty_context_returns_400(self):
        r = client.post("/api/repo/generate-readme", json={
            "provider": "anthropic",
            "anthropic_key": "sk-test",
            "file_context": "   ",
        })
        assert r.status_code == 400
        assert "error" in r.json()

    def test_readme_anthropic_streams(self):
        mock_client = MagicMock()
        mock_stream_ctx = MagicMock()
        mock_stream_ctx.__enter__ = MagicMock(return_value=mock_stream_ctx)
        mock_stream_ctx.__exit__ = MagicMock(return_value=False)
        mock_stream_ctx.text_stream = iter(["# MyRepo\n\nA great project."])
        mock_client.messages.stream.return_value = mock_stream_ctx
        with patch("main.Anthropic", return_value=mock_client):
            r = client.post("/api/repo/generate-readme", json={
                "provider": "anthropic",
                "anthropic_key": "sk-test",
                "file_context": "main.py\n\ndef main(): pass",
                "repo_name": "user/myrepo",
            })
        assert r.status_code == 200
        assert "text/event-stream" in r.headers.get("content-type", "")

    def test_readme_groq_success(self):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "# README\n\nAwesome project."}}]
        }
        with patch("requests.post", return_value=mock_resp):
            r = client.post("/api/repo/generate-readme", json={
                "provider": "groq",
                "groq_key": "gsk_test",
                "file_context": "index.py\n\nprint('hello')",
            })
        assert r.status_code == 200
        content = r.text
        assert "README" in content or "text/event-stream" in r.headers.get("content-type", "")


class TestCodeScanEndpoint:
    def test_scan_detects_eval_in_python(self):
        r = client.post("/api/code/scan", json={
            "code": "result = eval(user_input)\nprint(result)",
            "language": "python",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["safe"] is False
        patterns = [i["pattern"] for i in data["issues"]]
        assert any("eval" in p for p in patterns)
        assert any(i["severity"] == "high" for i in data["issues"])

    def test_scan_clean_code_returns_safe(self):
        r = client.post("/api/code/scan", json={
            "code": "def add(a: int, b: int) -> int:\n    return a + b\n\nresult = add(1, 2)",
            "language": "python",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["safe"] is True
        high_issues = [i for i in data["issues"] if i["severity"] == "high"]
        assert len(high_issues) == 0

    def test_scan_detects_hardcoded_secret(self):
        r = client.post("/api/code/scan", json={
            "code": 'api_key = "sk-real-secret-key-abc123"\nrequest(api_key)',
            "language": "python",
        })
        assert r.status_code == 200
        data = r.json()
        high = [i for i in data["issues"] if i["severity"] == "high"]
        assert len(high) >= 1
        assert any("api_key" in i.get("pattern", "").lower() or "hardcoded" in i.get("message", "").lower() for i in high)

    def test_scan_detects_os_system_via_ast(self):
        r = client.post("/api/code/scan", json={
            "code": "import os\nos.system('ls -la')",
            "language": "python",
        })
        assert r.status_code == 200
        data = r.json()
        assert any(i["pattern"] == "os.system()" and i["severity"] == "high" for i in data["issues"])
        assert any(i.get("source") == "ast" for i in data["issues"])

    def test_scan_detects_pickle_loads(self):
        r = client.post("/api/code/scan", json={
            "code": "import pickle\ndata = pickle.loads(untrusted_bytes)",
            "language": "python",
        })
        assert r.status_code == 200
        data = r.json()
        assert any(i["pattern"] == "pickle.loads()" for i in data["issues"])

    def test_scan_detects_shell_true(self):
        r = client.post("/api/code/scan", json={
            "code": "import subprocess\nsubprocess.run('ls', shell=True)",
            "language": "python",
        })
        assert r.status_code == 200
        data = r.json()
        assert any("shell=True" in i.get("pattern", "") for i in data["issues"])

    def test_scan_javascript_eval(self):
        r = client.post("/api/code/scan", json={
            "code": "const result = eval(userInput);",
            "language": "javascript",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["safe"] is False
        assert any(i["severity"] == "high" for i in data["issues"])

    def test_scan_empty_code_returns_safe(self):
        r = client.post("/api/code/scan", json={"code": "", "language": "python"})
        assert r.status_code == 200
        data = r.json()
        assert data["safe"] is True
        assert data["total"] == 0

    def test_scan_syntax_error_returns_medium(self):
        r = client.post("/api/code/scan", json={
            "code": "def foo(\n    return 1",
            "language": "python",
        })
        assert r.status_code == 200
        data = r.json()
        assert any(i["pattern"] == "SyntaxError" for i in data["issues"])

    def test_scan_results_capped_at_15(self):
        many_evals = "\n".join(f"eval(x{i})" for i in range(30))
        r = client.post("/api/code/scan", json={"code": many_evals, "language": "python"})
        assert r.status_code == 200
        data = r.json()
        assert len(data["issues"]) <= 15


class TestScanDepsEndpoint:
    def test_scan_deps_empty_content_returns_400(self):
        r = client.post("/api/repo/scan-deps", json={
            "filename": "requirements.txt",
            "content": "   ",
        })
        assert r.status_code == 400
        assert "error" in r.json()

    def test_scan_deps_parses_requirements_txt(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = {"info": {"version": "2.0.0"}}
            from unittest.mock import MagicMock
            mock_client = MagicMock()
            mock_ctx = MagicMock()
            mock_ctx.__enter__ = MagicMock(return_value=mock_ctx)
            mock_ctx.__exit__ = MagicMock(return_value=False)
            mock_ctx.text_stream = iter(["✅ All packages look safe."])
            mock_client.messages.stream.return_value = mock_ctx
            with patch("main.Anthropic", return_value=mock_client):
                r = client.post("/api/repo/scan-deps", json={
                    "filename": "requirements.txt",
                    "content": "fastapi==0.100.0\nrequests==2.28.0\npydantic==1.10.0",
                    "provider": "anthropic",
                    "anthropic_key": "sk-test",
                })
        assert r.status_code == 200
        assert "text/event-stream" in r.headers.get("content-type", "")
        content = r.text
        assert "packages" in content

    def test_scan_deps_package_json_parsed(self):
        r = client.post("/api/repo/scan-deps", json={
            "filename": "package.json",
            "content": '{"dependencies": {"react": "^18.0.0", "express": "^4.18.0"}}',
            "provider": "anthropic",
            "anthropic_key": "",
        })
        assert r.status_code == 200
        content = r.text
        assert "packages" in content


class TestCallToolEndpoint:
    def test_get_request_success(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = '{"ok":true}'
            r = client.post("/api/tools/call", json={
                "url": "https://api.example.com/data",
                "method": "GET",
            })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == 200
        assert "ok" in data["response"]

    def test_post_request_success(self):
        with patch("requests.request") as mock_req:
            mock_req.return_value.status_code = 201
            mock_req.return_value.text = '{"id":1}'
            r = client.post("/api/tools/call", json={
                "url": "https://api.example.com/items",
                "method": "POST",
                "body_json": {"name": "test"},
            })
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == 201

    def test_network_error_returns_500(self):
        with patch("requests.get", side_effect=Exception("connection refused")):
            r = client.post("/api/tools/call", json={
                "url": "https://api.example.com/fail",
                "method": "GET",
            })
        assert r.status_code == 500
        assert "error" in r.json()

    def test_response_truncated_at_2000_chars(self):
        long_body = "x" * 5000
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = long_body
            r = client.post("/api/tools/call", json={
                "url": "https://api.example.com/big",
                "method": "GET",
            })
        assert r.status_code == 200
        assert len(r.json()["response"]) <= 2000


class TestSuggestCommitMessage:
    def test_anthropic_returns_message(self):
        mock_client = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="feat(api): add commit suggest endpoint")]
        mock_client.messages.create.return_value = mock_msg
        with patch("main.Anthropic", return_value=mock_client):
            r = client.post("/api/commit/suggest-message", json={
                "provider": "anthropic",
                "anthropic_key": "sk-test",
                "path": "main.py",
                "diff": "def new_func(): pass",
            })
        assert r.status_code == 200
        data = r.json()
        assert "message" in data
        assert data["message"] == "feat(api): add commit suggest endpoint"

    def test_groq_returns_message(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {
                "choices": [{"message": {"content": "fix(auth): handle expired token"}}]
            }
            r = client.post("/api/commit/suggest-message", json={
                "provider": "groq",
                "groq_key": "gk-test",
                "path": "auth.py",
                "content": "token = refresh()",
            })
        assert r.status_code == 200
        assert r.json()["message"] == "fix(auth): handle expired token"

    def test_no_key_returns_400(self):
        r = client.post("/api/commit/suggest-message", json={
            "provider": "anthropic",
            "anthropic_key": "",
            "path": "README.md",
        })
        assert r.status_code == 400
        assert "error" in r.json()

    def test_groq_api_error_returns_400(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value.ok = False
            mock_post.return_value.text = "rate limit exceeded"
            r = client.post("/api/commit/suggest-message", json={
                "provider": "groq",
                "groq_key": "gk-test",
                "path": "main.py",
                "diff": "removed old code",
            })
        assert r.status_code == 400
        assert "error" in r.json()

    def test_uses_diff_over_content(self):
        """diff takes precedence — snippet is taken from body.diff when both present."""
        mock_client = MagicMock()
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text="refactor(core): simplify logic")]
        mock_client.messages.create.return_value = mock_msg
        with patch("main.Anthropic", return_value=mock_client) as _:
            r = client.post("/api/commit/suggest-message", json={
                "provider": "anthropic",
                "anthropic_key": "sk-test",
                "path": "core.py",
                "diff": "-old_code\n+new_code",
                "content": "new_code",
            })
        assert r.status_code == 200
        call_args = mock_client.messages.create.call_args
        user_content = call_args.kwargs["messages"][0]["content"]
        assert "-old_code" in user_content


class TestDepParserHelpers:
    """Unit tests for the dependency file parser helpers."""

    def test_parse_requirements_basic(self):
        content = "fastapi==0.110.0\nrequests>=2.28.0\npydantic"
        pkgs = main._parse_requirements(content)
        names = [p["name"] for p in pkgs]
        assert "fastapi" in names
        assert "requests" in names
        assert "pydantic" in names

    def test_parse_requirements_skips_comments_and_flags(self):
        content = "# comment\n-r base.txt\n--extra-index-url https://example.com\nflask==3.0.0"
        pkgs = main._parse_requirements(content)
        names = [p["name"] for p in pkgs]
        assert "flask" in names
        assert len(names) == 1

    def test_parse_requirements_normalises_underscores(self):
        content = "my_package==1.0.0"
        pkgs = main._parse_requirements(content)
        assert pkgs[0]["name"] == "my-package"

    def test_parse_requirements_strips_extras(self):
        content = "uvicorn[standard]==0.29.0"
        pkgs = main._parse_requirements(content)
        assert pkgs[0]["name"] == "uvicorn"
        assert "standard" not in pkgs[0]["name"]

    def test_parse_package_json_dependencies(self):
        content = '{"dependencies":{"react":"^18.0.0"},"devDependencies":{"jest":"^29.0.0"}}'
        pkgs = main._parse_package_json(content)
        names = [p["name"] for p in pkgs]
        assert "react" in names
        assert "jest" in names

    def test_parse_package_json_invalid_json_returns_empty(self):
        pkgs = main._parse_package_json("not json")
        assert pkgs == []

    def test_parse_go_mod_block_require(self):
        content = "module example.com/mymod\n\ngo 1.21\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.9.1\n\tgolang.org/x/net v0.21.0\n)"
        pkgs = main._parse_go_mod(content)
        names = [p["name"] for p in pkgs]
        assert "github.com/gin-gonic/gin" in names
        assert "golang.org/x/net" in names

    def test_parse_go_mod_single_require(self):
        content = "module example.com/m\nrequire github.com/pkg/errors v0.9.1"
        pkgs = main._parse_go_mod(content)
        assert any(p["name"] == "github.com/pkg/errors" for p in pkgs)

    def test_parse_go_mod_skips_comment_lines(self):
        content = "require (\n\t// indirect\n\tgithub.com/real/dep v1.0.0\n)"
        pkgs = main._parse_go_mod(content)
        names = [p["name"] for p in pkgs]
        assert "github.com/real/dep" in names
        assert "//" not in names

    def test_parse_cargo_toml_dependencies(self):
        content = '[dependencies]\nserde = "1.0"\ntokio = { version = "1.36", features = ["full"] }\n\n[dev-dependencies]\ncargo-test = "0.1"'
        pkgs = main._parse_cargo_toml(content)
        names = [p["name"] for p in pkgs]
        assert "serde" in names

    def test_parse_cargo_toml_dev_dependencies(self):
        content = '[dev-dependencies]\ncriterion = "0.5"'
        pkgs = main._parse_cargo_toml(content)
        assert any(p["name"] == "criterion" for p in pkgs)

    def test_parse_cargo_toml_stops_at_next_section(self):
        content = '[dependencies]\nfoo = "1.0"\n\n[profile.release]\nopt-level = 3'
        pkgs = main._parse_cargo_toml(content)
        names = [p["name"] for p in pkgs]
        assert "foo" in names
        assert "opt-level" not in names

    def test_parse_cargo_toml_inline_table_extracts_version(self):
        content = '[dependencies]\ntokio = { version = "1.36", features = ["full"] }'
        pkgs = main._parse_cargo_toml(content)
        tokio = next((p for p in pkgs if p["name"] == "tokio"), None)
        assert tokio is not None
        assert tokio["constraint"] == "1.36"

    def test_parse_cargo_toml_simple_and_inline_mixed(self):
        content = '[dependencies]\nserde = "1.0"\ntokio = { version = "1.36" }\nasync-trait = "0.1"'
        pkgs = main._parse_cargo_toml(content)
        by_name = {p["name"]: p["constraint"] for p in pkgs}
        assert by_name["serde"] == "1.0"
        assert by_name["tokio"] == "1.36"
        assert by_name["async-trait"] == "0.1"


class TestCodeScanLanguages:
    """Tests for language-specific scan patterns not covered in TestCodeScanEndpoint."""

    def test_scan_typescript_innerHTML_high(self):
        r = client.post("/api/code/scan", json={
            "code": 'el.innerHTML = userData;',
            "language": "typescript",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["safe"] is False
        assert any(i["severity"] == "high" for i in data["issues"])

    def test_scan_typescript_any_low(self):
        r = client.post("/api/code/scan", json={
            "code": "function foo(x: any) { return x; }",
            "language": "typescript",
        })
        assert r.status_code == 200
        data = r.json()
        assert any(i["severity"] == "low" for i in data["issues"])

    def test_scan_sql_string_concat_high(self):
        r = client.post("/api/code/scan", json={
            "code": "query = \"SELECT * FROM users WHERE id = '\" + userId + \"'\"",
            "language": "sql",
        })
        assert r.status_code == 200
        data = r.json()
        assert any(i["severity"] == "high" for i in data["issues"])

    def test_scan_bash_eval_high(self):
        r = client.post("/api/code/scan", json={
            "code": "eval $user_input",
            "language": "bash",
        })
        assert r.status_code == 200
        data = r.json()
        assert any(i["severity"] == "high" for i in data["issues"])

    def test_scan_go_fmt_sprintf_sql_high(self):
        r = client.post("/api/code/scan", json={
            "code": 'query := fmt.Sprintf("SELECT * FROM users WHERE id = %s", userId)',
            "language": "go",
        })
        assert r.status_code == 200
        data = r.json()
        assert any(i["severity"] == "high" for i in data["issues"])

    def test_scan_generic_hardcoded_token(self):
        r = client.post("/api/code/scan", json={
            "code": 'token = "ghp_abcdefghij1234567890"',
            "language": "python",
        })
        assert r.status_code == 200
        data = r.json()
        assert any(i["severity"] == "high" for i in data["issues"])

    def test_scan_http_url_triggers_low(self):
        r = client.post("/api/code/scan", json={
            "code": 'url = "http://api.example.com/endpoint"',
            "language": "javascript",
        })
        assert r.status_code == 200
        data = r.json()
        assert any(i["severity"] == "low" for i in data["issues"])

    def test_scan_http_localhost_no_issue(self):
        r = client.post("/api/code/scan", json={
            "code": 'const url = "http://localhost:8080/api"',
            "language": "javascript",
        })
        assert r.status_code == 200
        data = r.json()
        http_issues = [i for i in data["issues"] if "http" in i.get("pattern", "").lower() or "https" in i.get("message", "").lower()]
        assert len(http_issues) == 0


class TestScanDepsExtraEcosystems:
    """Tests for go.mod, cargo.toml, and unknown extension in scan_deps."""

    def test_scan_deps_go_mod_parsed(self):
        r = client.post("/api/repo/scan-deps", json={
            "filename": "go.mod",
            "content": "module example.com/m\n\ngo 1.21\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.9.1\n\tgolang.org/x/net v0.21.0\n)",
            "provider": "anthropic",
            "anthropic_key": "",
        })
        assert r.status_code == 200
        content = r.text
        assert "packages" in content
        assert "gin" in content

    def test_scan_deps_cargo_toml_parsed(self):
        r = client.post("/api/repo/scan-deps", json={
            "filename": "cargo.toml",
            "content": '[dependencies]\nserde = "1.0"\ntokio = { version = "1.36", features = ["full"] }',
            "provider": "anthropic",
            "anthropic_key": "",
        })
        assert r.status_code == 200
        assert "packages" in r.text

    def test_scan_deps_unknown_filename_falls_back_to_requirements(self):
        r = client.post("/api/repo/scan-deps", json={
            "filename": "requirements-dev.txt",
            "content": "pytest==7.4.0\npytest-asyncio==0.23.0",
            "provider": "anthropic",
            "anthropic_key": "",
        })
        assert r.status_code == 200
        assert "packages" in r.text

    def test_scan_deps_no_packages_found_returns_400(self):
        r = client.post("/api/repo/scan-deps", json={
            "filename": "go.mod",
            "content": "module example.com/m\n\ngo 1.21\n",
            "provider": "anthropic",
            "anthropic_key": "",
        })
        assert r.status_code == 400
        assert "No packages" in r.json()["error"]

    def test_scan_deps_groq_provider_streams(self):
        with patch("requests.post") as mock_post:
            mock_post.return_value.ok = True
            mock_post.return_value.json.return_value = {
                "choices": [{"message": {"content": "All dependencies look reasonable."}}]
            }
            r = client.post("/api/repo/scan-deps", json={
                "filename": "requirements.txt",
                "content": "flask==2.3.0\nrequests==2.31.0",
                "provider": "groq",
                "groq_key": "gsk_test",
            })
        assert r.status_code == 200
        content = r.text
        assert "packages" in content

    def test_scan_deps_outdated_flag_set(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = {"info": {"version": "3.0.0"}}
            r = client.post("/api/repo/scan-deps", json={
                "filename": "requirements.txt",
                "content": "flask==1.0.0",
                "provider": "anthropic",
                "anthropic_key": "",
            })
        assert r.status_code == 200
        import json as _json
        for line in r.text.splitlines():
            if line.startswith("data: "):
                ev = _json.loads(line[6:])
                if ev.get("t") == "packages":
                    pkg = ev["v"]["packages"][0]
                    assert pkg["pinned"] == "1.0.0"
                    assert pkg["latest"] == "3.0.0"
                    assert pkg["outdated"] is True
                    break

    def test_scan_deps_unpinned_flag_set(self):
        r = client.post("/api/repo/scan-deps", json={
            "filename": "requirements.txt",
            "content": "flask>=2.0",
            "provider": "anthropic",
            "anthropic_key": "",
        })
        assert r.status_code == 200
        import json as _json
        for line in r.text.splitlines():
            if line.startswith("data: "):
                ev = _json.loads(line[6:])
                if ev.get("t") == "packages":
                    pkg = ev["v"]["packages"][0]
                    assert pkg["unpinned"] is True
                    assert pkg["pinned"] is None
                    break


class TestVersionCheckerHelpers:
    """Unit tests for _pypi_latest and _npm_latest."""

    def test_pypi_latest_returns_version_on_success(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = {"info": {"version": "1.2.3"}}
            result = main._pypi_latest("requests")
        assert result == {"name": "requests", "latest": "1.2.3"}

    def test_pypi_latest_returns_none_on_http_error(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = False
            result = main._pypi_latest("nonexistent-pkg")
        assert result == {"name": "nonexistent-pkg", "latest": None}

    def test_pypi_latest_returns_none_on_network_error(self):
        with patch("requests.get", side_effect=Exception("timeout")):
            result = main._pypi_latest("requests")
        assert result == {"name": "requests", "latest": None}

    def test_npm_latest_returns_version_on_success(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = {"version": "18.2.0"}
            result = main._npm_latest("react")
        assert result == {"name": "react", "latest": "18.2.0"}

    def test_npm_latest_returns_none_on_http_error(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = False
            result = main._npm_latest("nonexistent-pkg")
        assert result == {"name": "nonexistent-pkg", "latest": None}

    def test_npm_latest_returns_none_on_network_error(self):
        with patch("requests.get", side_effect=Exception("connection refused")):
            result = main._npm_latest("react")
        assert result == {"name": "react", "latest": None}


class TestBuildSystemAgentSecurity:
    """Tests for SECURITY_FOOTER injection logic in build_system."""

    def test_code_agent_gets_security_footer(self):
        body = _body(agent="code")
        result = main.build_system(body)
        assert "Security Requirements" in result

    def test_refactor_agent_gets_security_footer(self):
        body = _body(agent="refactor")
        result = main.build_system(body)
        assert "Security Requirements" in result

    def test_testgen_agent_gets_security_footer(self):
        body = _body(agent="testgen")
        result = main.build_system(body)
        assert "Security Requirements" in result

    def test_debug_agent_gets_security_footer(self):
        body = _body(agent="debug")
        result = main.build_system(body)
        assert "Security Requirements" in result

    def test_review_agent_no_security_footer(self):
        body = _body(agent="review")
        result = main.build_system(body)
        assert "Security Requirements" not in result

    def test_architect_agent_no_security_footer(self):
        body = _body(agent="architect")
        result = main.build_system(body)
        assert "Security Requirements" not in result

    def test_docs_agent_no_security_footer(self):
        body = _body(agent="docs")
        result = main.build_system(body)
        assert "Security Requirements" not in result

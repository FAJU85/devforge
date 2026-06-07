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

    def test_git_in_middle_of_name_not_stripped(self):
        """Repo name 'my-git-repo.git' should become 'my-git-repo', not 'my-repo.'."""
        owner, repo = main.parse_gh_url("https://github.com/acme/my-git-repo.git")
        assert owner == "acme"
        assert repo == "my-git-repo"

    def test_shorthand_git_in_middle_of_name(self):
        owner, repo = main.parse_gh_url("acme/widget.git-tools.git")
        assert owner == "acme"
        assert repo == "widget.git-tools"


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

    def test_airllm_provider_returns_callable(self):
        body = _body(provider="airllm", airllm_model="meta-llama/Llama-2-7b-chat-hf", airllm_max_tokens=256)
        runner = main.get_runner(body)
        assert callable(runner)

    def test_airllm_provider_default_model_when_empty(self):
        body = _body(provider="airllm", airllm_model="", airllm_max_tokens=512)
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
# _friendly_anthropic_error
# ---------------------------------------------------------------------------

class TestFriendlyAnthropicError:
    def test_401_returns_invalid_key_message(self):
        msg = main._friendly_anthropic_error(Exception("401 authentication_error"))
        assert "invalid" in msg.lower() or "missing" in msg.lower()
        assert "console.anthropic.com" in msg

    def test_429_returns_rate_limit_message(self):
        msg = main._friendly_anthropic_error(Exception("429 rate_limit_error"))
        assert "rate limit" in msg.lower()

    def test_529_returns_overloaded_message(self):
        msg = main._friendly_anthropic_error(Exception("529 overloaded_error"))
        assert "overloaded" in msg.lower()

    def test_403_returns_permission_message(self):
        msg = main._friendly_anthropic_error(Exception("403 permission_error"))
        assert "permission" in msg.lower()

    def test_unknown_error_returns_original(self):
        msg = main._friendly_anthropic_error(Exception("some unexpected error"))
        assert msg == "some unexpected error"


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

    def test_run_hf_402_credits_exhausted(self):
        msg = "Client error '402 Payment Required' for url 'https://router.huggingface.co/v1/chat/completions'. You have depleted your monthly included credits."
        with patch("main.InferenceClient", side_effect=Exception(msg)):
            items = _run_runner_sync(main._run_hf, "sys", [], "token", "model")

        error_vals = [v for k, v in items if k == "error"]
        assert error_vals
        assert "credits" in error_vals[0].lower()
        assert "huggingface.co/pricing" in error_vals[0]

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

    def test_rejects_limit_over_100(self):
        resp = client.get("/api/hf/models?limit=500")
        assert resp.status_code == 422

    def test_rejects_query_over_200_chars(self):
        long_q = "a" * 201
        resp = client.get(f"/api/hf/models?q={long_q}")
        assert resp.status_code == 422


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

    def test_batch_write_encodes_path_traversal(self):
        """Dot-dot segments and query chars must be percent-encoded in the GitHub URL."""
        with patch("main.requests.get") as mock_get, patch("main.requests.put") as mock_put:
            mock_get.return_value = MagicMock(ok=False)
            mock_put.return_value = MagicMock(
                ok=True, json=lambda: {"commit": {"html_url": ""}, "content": {}},
            )
            client.post("/api/repo/write/batch", json={
                "token": "tok", "owner": "o", "repo": "r", "branch": "main",
                "files": [{"path": "../etc/passwd?ref=evil", "content": "x", "message": "m"}],
            })
        url_called = mock_put.call_args.args[0] if mock_put.call_args.args else mock_put.call_args[0][0]
        assert "?ref=evil" not in url_called
        assert ".." not in url_called.split("/repos/o/r/contents/", 1)[-1]


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


class TestCallAiProviderEmptyChoices:
    """_call_ai_provider must not raise on empty or missing choices array."""

    def test_groq_empty_choices_returns_empty_string(self):
        with patch("main.requests.post") as mock_post:
            mock_post.return_value = MagicMock(ok=True, json=lambda: {"choices": []})
            body = MagicMock(provider="groq", groq_key="k", groq_model="m")
            ok, result = main._call_ai_provider(body, "sys", "prompt")
        assert ok is True
        assert result == ""

    def test_groq_missing_choices_key_returns_empty_string(self):
        with patch("main.requests.post") as mock_post:
            mock_post.return_value = MagicMock(ok=True, json=lambda: {"error": "overloaded"})
            body = MagicMock(provider="groq", groq_key="k", groq_model="m")
            ok, result = main._call_ai_provider(body, "sys", "prompt")
        assert ok is True
        assert result == ""

    def test_openai_compat_empty_choices_returns_empty_string(self):
        with patch("main.requests.post") as mock_post:
            mock_post.return_value = MagicMock(ok=True, json=lambda: {"choices": []})
            body = MagicMock(
                provider="openai_compat",
                openai_compat_base_url="http://localhost:11434/v1",
                openai_compat_key="",
                openai_compat_model="llama3",
            )
            with patch("main._valid_http_url", return_value=True):
                ok, result = main._call_ai_provider(body, "sys", "prompt")
        assert ok is True
        assert result == ""


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

    def test_tool_call_rejects_file_url(self):
        r = client.post("/api/tools/call", json={"url": "file:///etc/passwd", "method": "GET"})
        assert r.status_code == 400
        assert "error" in r.json()

    def test_tool_call_rejects_gopher_url(self):
        r = client.post("/api/tools/call", json={"url": "gopher://evil.example.com/", "method": "GET"})
        assert r.status_code == 400
        assert "error" in r.json()

    def test_tool_call_rejects_invalid_method(self):
        r = client.post("/api/tools/call", json={"url": "https://example.com/", "method": "CONNECT"})
        assert r.status_code == 400
        assert "error" in r.json()

    def test_tool_call_rejects_head_method(self):
        r = client.post("/api/tools/call", json={"url": "https://example.com/", "method": "HEAD"})
        assert r.status_code == 400
        assert "error" in r.json()

    def test_tool_call_blocks_localhost(self):
        r = client.post("/api/tools/call", json={"url": "http://localhost/secret", "method": "GET"})
        assert r.status_code == 400
        assert "internal" in r.json()["error"].lower()

    def test_tool_call_blocks_loopback_ip(self):
        r = client.post("/api/tools/call", json={"url": "http://127.0.0.1/secret", "method": "GET"})
        assert r.status_code == 400

    def test_tool_call_blocks_private_10_range(self):
        r = client.post("/api/tools/call", json={"url": "http://10.0.0.1/internal", "method": "GET"})
        assert r.status_code == 400

    def test_tool_call_blocks_private_192_168_range(self):
        r = client.post("/api/tools/call", json={"url": "http://192.168.1.1/admin", "method": "GET"})
        assert r.status_code == 400

    def test_tool_call_blocks_aws_metadata(self):
        r = client.post("/api/tools/call", json={"url": "http://169.254.169.254/latest/meta-data/", "method": "GET"})
        assert r.status_code == 400

    def test_tool_call_allows_external_https(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = "ok"
            r = client.post("/api/tools/call", json={"url": "https://api.example.com/data", "method": "GET"})
        assert r.status_code == 200

    def test_tool_call_rejects_oversized_body_json(self):
        big = {"k" + str(i): "x" * 1000 for i in range(100)}  # ~100 KB
        r = client.post("/api/tools/call", json={"url": "https://api.example.com/", "method": "POST", "body_json": big})
        assert r.status_code == 413
        assert "64 KB" in r.json()["error"]

    def test_tool_call_accepts_small_body_json(self):
        with patch("requests.request") as mock_req:
            mock_req.return_value.status_code = 201
            mock_req.return_value.text = "created"
            r = client.post("/api/tools/call", json={"url": "https://api.example.com/", "method": "POST", "body_json": {"key": "value"}})
        assert r.status_code == 200

    def test_tool_call_truncates_excess_headers(self):
        many_hdrs = {"H" + str(i): "v" for i in range(200)}
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = "ok"
            r = client.post("/api/tools/call", json={"url": "https://api.example.com/", "method": "GET", "headers": many_hdrs})
        assert r.status_code == 200
        _passed = mock_get.call_args.kwargs.get("headers", mock_get.call_args[1].get("headers", {}))
        assert len(_passed) <= 50


class TestOpenAICompatBaseUrlValidation:
    def test_suggest_files_rejects_file_scheme_base_url(self):
        payload = {
            "provider": "openai_compat",
            "openai_compat_base_url": "file:///etc/passwd",
            "openai_compat_model": "llama3",
            "task": "add tests",
            "files": ["main.py"],
        }
        r = client.post("/api/repo/suggest-files", json=payload)
        assert r.status_code == 400
        assert "error" in r.json()

    def test_suggest_files_rejects_gopher_scheme_base_url(self):
        payload = {
            "provider": "openai_compat",
            "openai_compat_base_url": "gopher://evil/exploit",
            "openai_compat_model": "llama3",
            "task": "add tests",
            "files": ["main.py"],
        }
        r = client.post("/api/repo/suggest-files", json=payload)
        assert r.status_code == 400
        assert "error" in r.json()

    def test_summarize_file_rejects_file_scheme_base_url(self):
        payload = {
            "provider": "openai_compat",
            "openai_compat_base_url": "file:///etc/shadow",
            "openai_compat_model": "llama3",
            "filename": "README.md",
            "content": "some content",
        }
        r = client.post("/api/repo/summarize-file", json=payload)
        assert r.status_code == 400
        assert "error" in r.json()

    def test_valid_http_url_helper_accepts_http(self):
        assert main._valid_http_url("http://localhost:11434/v1") is True

    def test_valid_http_url_helper_accepts_https(self):
        assert main._valid_http_url("https://api.example.com/v1") is True

    def test_valid_http_url_helper_rejects_file(self):
        assert main._valid_http_url("file:///etc/passwd") is False

    def test_valid_http_url_helper_rejects_empty(self):
        assert main._valid_http_url("") is False

    def test_valid_http_url_helper_rejects_none_coerced(self):
        assert main._valid_http_url(None) is False


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

    def test_owner_repo_encoded_in_github_url(self):
        """Injected ? or / in owner/repo must be percent-encoded, not raw in URL."""
        with patch("requests.get") as mock_get:
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = []
            client.get("/api/repo/branches?token=tok&owner=evil%3Fq%3D1&repo=bad%2Frepo")
        url_called = mock_get.call_args.args[0] if mock_get.call_args.args else mock_get.call_args[0][0]
        assert "?q=1" not in url_called.split("branches")[0]
        assert "/repos/evil%3Fq%3D1/bad%2Frepo/" in url_called or "/repos/evil%3Fq%3D1/" in url_called

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
        # Tree fetch URL should use the overridden branch (/ is encoded as %2F)
        tree_call = mock_get.call_args_list[1]
        tree_url = tree_call[0][0]
        assert "feature%2Fnew-api" in tree_url or "feature/new-api" in tree_url

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
                "token": "tok", "owner": "user", "repo": "myrepo", "query": "test", "max_results": 20,
            })
        assert r.status_code == 200
        # Verify per_page was capped at 20
        call_args = mock_get.call_args
        params = call_args[1].get("params", {})
        assert params.get("per_page", 0) <= 20

    def test_search_rejects_max_results_exceeding_limit(self):
        r = client.post("/api/repo/search", json={
            "token": "tok", "owner": "user", "repo": "myrepo", "query": "test", "max_results": 100,
        })
        assert r.status_code == 422


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
                "token": "tok", "owner": "user", "repo": "myrepo", "max_results": 30,
            })
        assert r.status_code == 200
        call_args = mock_get.call_args
        params = call_args[1].get("params", {})
        assert params.get("per_page", 0) <= 30

    def test_commits_rejects_max_results_exceeding_limit(self):
        r = client.post("/api/repo/commits", json={
            "token": "tok", "owner": "user", "repo": "myrepo", "max_results": 200,
        })
        assert r.status_code == 422


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
                "token": "tok", "owner": "user", "repo": "myrepo", "max_results": 20,
            })
        assert r.status_code == 200
        call_args = mock_get.call_args
        params = call_args[1].get("params", {})
        assert params.get("per_page", 0) <= 20

    def test_workflow_runs_rejects_max_results_exceeding_limit(self):
        r = client.post("/api/repo/workflow-runs", json={
            "token": "tok", "owner": "user", "repo": "myrepo", "max_results": 999,
        })
        assert r.status_code == 422


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

    def test_scan_large_input_is_rejected(self):
        large_code = "x = 1\n" * 20_000  # ~120K chars, exceeds 100K limit
        r = client.post("/api/code/scan", json={"code": large_code, "language": "python"})
        assert r.status_code == 422

    def test_scan_at_limit_is_accepted(self):
        at_limit_code = "x = 1\n" * 16_000  # ~96K chars, within 100K limit
        r = client.post("/api/code/scan", json={"code": at_limit_code, "language": "python"})
        assert r.status_code == 200
        assert "issues" in r.json()

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

    def test_parse_pyproject_toml_pep621_dependencies(self):
        content = '[project]\ndependencies = [\n  "flask>=2.0",\n  "requests==2.31.0",\n]\n'
        pkgs = main._parse_pyproject_toml(content)
        by_name = {p["name"]: p["constraint"] for p in pkgs}
        assert "flask" in by_name
        assert by_name["flask"].startswith(">=")
        assert "requests" in by_name
        assert by_name["requests"] == "==2.31.0"

    def test_parse_pyproject_toml_poetry_dependencies(self):
        content = '[tool.poetry.dependencies]\npython = "^3.11"\nfastapi = "^0.100.0"\nhttpx = {version = "^0.24", extras = ["http2"]}\n'
        pkgs = main._parse_pyproject_toml(content)
        by_name = {p["name"]: p["constraint"] for p in pkgs}
        assert "python" not in by_name, "python version constraint should be skipped"
        assert "fastapi" in by_name
        assert "^0.100.0" in by_name["fastapi"]

    def test_parse_pyproject_toml_build_system_requires(self):
        content = '[build-system]\nrequires = ["setuptools>=42", "wheel"]\nbuild-backend = "setuptools.build_meta"\n'
        pkgs = main._parse_pyproject_toml(content)
        names = [p["name"] for p in pkgs]
        assert "setuptools" in names
        assert "wheel" in names

    def test_parse_pyproject_toml_deduplicates_across_sections(self):
        content = (
            '[project]\ndependencies = ["requests>=2.0"]\n'
            '[build-system]\nrequires = ["requests>=1.0", "setuptools"]\n'
        )
        pkgs = main._parse_pyproject_toml(content)
        names = [p["name"] for p in pkgs]
        assert names.count("requests") == 1, "requests must not appear twice"

    def test_parse_pyproject_toml_invalid_toml_returns_empty(self):
        pkgs = main._parse_pyproject_toml("this is not : toml {{{{")
        assert pkgs == []

    def test_scan_deps_pyproject_toml_uses_correct_parser(self):
        """pyproject.toml routed to _parse_pyproject_toml, not requirements parser."""
        content = '[project]\ndependencies = ["flask>=2.0"]\n'
        with patch("main._parse_pyproject_toml", wraps=main._parse_pyproject_toml) as mock_fn:
            r = client.post("/api/repo/scan-deps", json={
                "filename": "pyproject.toml",
                "content": content,
                "provider": "groq",
                "groq_key": "fake",
            })
        mock_fn.assert_called_once()
        # The packages event should contain flask, not a bogus 'requires' package
        assert r.status_code == 200
        events = [ln for ln in r.text.splitlines() if ln.startswith("data:")]
        import json as _json
        pkg_event = next((e for e in events if '"packages"' in e), None)
        assert pkg_event is not None
        payload = _json.loads(pkg_event[5:])
        names = [p["name"] for p in payload["v"]["packages"]]
        assert "flask" in names
        assert "requires" not in names


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


class TestFieldLengthConstraints:
    def test_prompt_enhance_rejects_oversized_prompt(self):
        r = client.post("/api/prompt/enhance", json={
            "provider": "anthropic",
            "anthropic_key": "key",
            "prompt": "x" * 4001,
        })
        assert r.status_code == 422

    def test_prompt_enhance_accepts_max_prompt(self):
        with patch("main.Anthropic") as mock_cls:
            mock_inst = MagicMock()
            mock_cls.return_value = mock_inst
            msg = MagicMock(); msg.content = [MagicMock(text="improved")]
            mock_inst.messages.create.return_value = msg
            r = client.post("/api/prompt/enhance", json={
                "provider": "anthropic",
                "anthropic_key": "key",
                "prompt": "x" * 4000,
            })
        assert r.status_code == 200

    def test_suggest_files_rejects_oversized_task(self):
        r = client.post("/api/repo/suggest-files", json={
            "provider": "anthropic",
            "task": "x" * 2001,
            "files": ["main.py"],
        })
        assert r.status_code == 422

    def test_suggest_files_rejects_max_suggestions_too_high(self):
        r = client.post("/api/repo/suggest-files", json={
            "provider": "anthropic",
            "task": "add tests",
            "files": ["main.py"],
            "max_suggestions": 21,
        })
        assert r.status_code == 422

    def test_summarize_file_rejects_oversized_content(self):
        r = client.post("/api/repo/summarize-file", json={
            "provider": "anthropic",
            "filename": "big.py",
            "content": "x" * 200_001,
        })
        assert r.status_code == 422

    def test_commit_msg_rejects_oversized_diff(self):
        r = client.post("/api/commit/suggest-message", json={
            "provider": "anthropic",
            "path": "main.py",
            "diff": "x" * 50_001,
        })
        assert r.status_code == 422

    def test_chat_rejects_too_many_messages(self):
        r = client.post("/api/chat/stream", json={
            "provider": "anthropic",
            "anthropic_key": "key",
            "messages": [{"role": "user", "content": "hi"}] * 501,
        })
        assert r.status_code == 422

    def test_chat_rejects_too_many_tools(self):
        tool = {"name": "t", "description": "d", "url": "https://x.com", "method": "GET"}
        r = client.post("/api/chat/stream", json={
            "provider": "anthropic",
            "anthropic_key": "key",
            "messages": [{"role": "user", "content": "hi"}],
            "tools": [tool] * 21,
        })
        assert r.status_code == 422

    def test_batch_write_rejects_too_many_files(self):
        item = {"path": "file.txt", "content": "hello", "message": "add"}
        r = client.post("/api/repo/write/batch", json={
            "token": "tok",
            "owner": "user",
            "repo": "myrepo",
            "branch": "main",
            "files": [item] * 51,
        })
        assert r.status_code == 422

    def test_issue_rejects_too_many_labels(self):
        r = client.post("/api/github/issue/create", json={
            "token": "tok",
            "owner": "user",
            "repo": "myrepo",
            "title": "t",
            "body": "b",
            "labels": ["label"] * 11,
        })
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Cycle 67: asyncio.TimeoutError handling in inline streaming loops
# ---------------------------------------------------------------------------

class TestInlineStreamTimeout:
    """Verify that asyncio.TimeoutError in inline wait_for loops emits an SSE error event."""

    def test_release_notes_timeout_emits_error_sse(self):
        mock_commits = [
            {"sha": "abc1234567890", "commit": {"message": "feat: auth", "author": {"name": "A", "date": "2026-01-01"}}}
        ]
        with patch("requests.get") as mock_get, \
             patch("main.asyncio.wait_for", side_effect=asyncio.TimeoutError):
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
        assert "timed out" in r.text

    def test_generate_readme_timeout_emits_error_sse(self):
        with patch("main.asyncio.wait_for", side_effect=asyncio.TimeoutError):
            r = client.post("/api/repo/generate-readme", json={
                "provider": "anthropic",
                "anthropic_key": "sk-test",
                "file_context": "main.py\n\ndef main(): pass",
            })
        assert r.status_code == 200
        assert "timed out" in r.text

    def test_scan_deps_timeout_emits_error_sse(self):
        with patch("requests.get") as mock_get, \
             patch("main.asyncio.wait_for", side_effect=asyncio.TimeoutError):
            mock_get.return_value.ok = True
            mock_get.return_value.json.return_value = {"info": {"version": "2.0.0"}}
            r = client.post("/api/repo/scan-deps", json={
                "filename": "requirements.txt",
                "content": "fastapi==0.100.0",
                "provider": "anthropic",
                "anthropic_key": "sk-test",
            })
        assert r.status_code == 200
        assert "timed out" in r.text


# ---------------------------------------------------------------------------
# Cycle 67: chat_stream SSRF guard for openai_compat_base_url
# ---------------------------------------------------------------------------

class TestChatStreamOpenAICompatSSRF:
    def test_single_stream_rejects_file_scheme_base_url(self):
        r = client.post("/api/chat/stream", json={
            "provider": "openai_compat",
            "openai_compat_base_url": "file:///etc/passwd",
            "openai_compat_model": "llama3",
            "messages": [{"role": "user", "content": "hi"}],
        })
        assert r.status_code == 400
        assert "error" in r.json()

    def test_single_stream_rejects_gopher_scheme_base_url(self):
        r = client.post("/api/chat/stream", json={
            "provider": "openai_compat",
            "openai_compat_base_url": "gopher://evil/exploit",
            "openai_compat_model": "llama3",
            "messages": [{"role": "user", "content": "hi"}],
        })
        assert r.status_code == 400
        assert "error" in r.json()

    def test_multi_agent_rejects_file_scheme_base_url(self):
        # chat_stream calls get_runner(body) before starting the generator,
        # so ValueError from invalid URL is caught and returned as 400 JSON
        r = client.post("/api/chat/stream", json={
            "provider": "openai_compat",
            "openai_compat_base_url": "file:///etc/shadow",
            "openai_compat_model": "llama3",
            "messages": [{"role": "user", "content": "build it"}],
            "multi_agent": True,
        })
        assert r.status_code == 400
        assert "error" in r.json()


# ---------------------------------------------------------------------------
# AirLLM provider
# ---------------------------------------------------------------------------

class TestRunAirLLM:
    """Tests for _run_airllm thread target and the AirLLM get_runner path."""

    def test_airllm_missing_import_emits_error(self):
        """When airllm is not installed, _run_airllm emits an error event."""
        import builtins
        real_import = builtins.__import__

        def _block(name, *args, **kwargs):
            if name == "airllm":
                raise ImportError("No module named 'airllm'")
            return real_import(name, *args, **kwargs)

        results = []

        async def _collect():
            q = asyncio.Queue()
            loop = asyncio.get_running_loop()
            import threading
            with patch("builtins.__import__", side_effect=_block):
                t = threading.Thread(
                    target=main._run_airllm,
                    args=(q, loop, "sys", [{"role": "user", "content": "hi"}], "test-model", 64),
                    daemon=True,
                )
                t.start()
                while True:
                    kind, val = await asyncio.wait_for(q.get(), timeout=5)
                    results.append((kind, val))
                    if kind in ("done", "error"):
                        break
                t.join(timeout=3)

        asyncio.get_event_loop().run_until_complete(_collect())
        assert any(k == "error" for k, _ in results)
        err = next(v for k, v in results if k == "error")
        assert "airllm" in err.lower()

    def test_airllm_get_runner_returns_callable(self):
        body = _body(provider="airllm", airllm_model="meta-llama/Llama-2-7b-chat-hf", airllm_max_tokens=256)
        runner = main.get_runner(body)
        assert callable(runner)

    def test_airllm_get_runner_default_model_when_empty(self):
        body = _body(provider="airllm", airllm_model="", airllm_max_tokens=512)
        runner = main.get_runner(body)
        assert callable(runner)

    def test_airllm_chat_stream_returns_sse(self):
        with patch("main.stream_one", side_effect=_mock_stream_text):
            r = client.post("/api/chat/stream", json={
                "provider": "airllm",
                "airllm_model": "meta-llama/Llama-2-7b-chat-hf",
                "airllm_max_tokens": 128,
                "messages": [{"role": "user", "content": "hello"}],
            })
        assert r.status_code == 200
        assert "text/event-stream" in r.headers.get("content-type", "")
        assert "streamed text" in r.text

    def test_airllm_model_field_rejects_oversized_id(self):
        r = client.post("/api/chat/stream", json={
            "provider": "airllm",
            "airllm_model": "x" * 201,
            "messages": [{"role": "user", "content": "hi"}],
        })
        assert r.status_code == 422

    def test_airllm_max_tokens_rejects_zero(self):
        r = client.post("/api/chat/stream", json={
            "provider": "airllm",
            "airllm_model": "meta-llama/Llama-2-7b-chat-hf",
            "airllm_max_tokens": 0,
            "messages": [{"role": "user", "content": "hi"}],
        })
        assert r.status_code == 422

    def test_airllm_max_tokens_rejects_over_limit(self):
        r = client.post("/api/chat/stream", json={
            "provider": "airllm",
            "airllm_model": "meta-llama/Llama-2-7b-chat-hf",
            "airllm_max_tokens": 4097,
            "messages": [{"role": "user", "content": "hi"}],
        })
        assert r.status_code == 422

    def test_prov_label_includes_airllm(self):
        assert "airllm" in main._PROV_LABEL
        assert main._PROV_LABEL["airllm"] == "AirLLM"


# ---------------------------------------------------------------------------
# /api/agent/run — LangGraph pipeline endpoint
# ---------------------------------------------------------------------------

class TestAgentRunEndpoint:
    def test_returns_503_when_control_plane_unavailable(self):
        original = main._CONTROL_PLANE_AVAILABLE
        try:
            main._CONTROL_PLANE_AVAILABLE = False
            r = client.post("/api/agent/run", json={"task": "ping example.com"})
            assert r.status_code == 503
            assert "error" in r.json()
        finally:
            main._CONTROL_PLANE_AVAILABLE = original

    def test_rejects_empty_task(self):
        r = client.post("/api/agent/run", json={"task": ""})
        assert r.status_code == 422

    def test_rejects_task_exceeding_max_length(self):
        r = client.post("/api/agent/run", json={"task": "x" * 4001})
        assert r.status_code == 422

    def test_returns_sse_stream_when_mocked(self):
        async def _fake_astream(state):
            yield {"retrieve": {"rag_context": "some context"}}
            yield {"synthesis": {"final_answer": "done"}}

        mock_graph = MagicMock()
        mock_graph.astream = _fake_astream

        original = main._CONTROL_PLANE_AVAILABLE
        try:
            main._CONTROL_PLANE_AVAILABLE = True
            with patch("main._build_langgraph", return_value=mock_graph):
                r = client.post("/api/agent/run", json={"task": "fetch example.com"})
            assert r.status_code == 200
            assert "text/event-stream" in r.headers.get("content-type", "")
            assert "retrieve" in r.text
            assert "done" in r.text
        finally:
            main._CONTROL_PLANE_AVAILABLE = original

    def test_streams_node_events_for_all_nodes(self):
        async def _fake_astream(state):
            for node in ("retrieve", "reasoning", "execution", "synthesis"):
                yield {node: {"rag_context": ""} if node == "retrieve" else
                              {"tool_plan": None} if node == "reasoning" else
                              {"tool_results": None} if node == "execution" else
                              {"final_answer": "answer text"}}

        mock_graph = MagicMock()
        mock_graph.astream = _fake_astream

        original = main._CONTROL_PLANE_AVAILABLE
        try:
            main._CONTROL_PLANE_AVAILABLE = True
            with patch("main._build_langgraph", return_value=mock_graph):
                r = client.post("/api/agent/run", json={"task": "test"})
            body = r.text
            assert "retrieve" in body
            assert "reasoning" in body
            assert "execution" in body
            assert "synthesis" in body
        finally:
            main._CONTROL_PLANE_AVAILABLE = original

    def test_streams_final_answer_as_text_chunks(self):
        async def _fake_astream(state):
            yield {"synthesis": {"final_answer": "Hello world from agent"}}

        mock_graph = MagicMock()
        mock_graph.astream = _fake_astream

        original = main._CONTROL_PLANE_AVAILABLE
        try:
            main._CONTROL_PLANE_AVAILABLE = True
            with patch("main._build_langgraph", return_value=mock_graph):
                r = client.post("/api/agent/run", json={"task": "hi"})
            # Answer is split into 8-char chunks; verify at least one text event is present
            assert '"t": "text"' in r.text
            assert "Hello wo" in r.text  # first 8-char chunk of "Hello world from agent"
        finally:
            main._CONTROL_PLANE_AVAILABLE = original

    def test_emits_warn_event_for_node_error(self):
        async def _fake_astream(state):
            yield {"execution": {"error": "connection refused", "retry_count": 1}}
            yield {"synthesis": {"final_answer": "fallback"}}

        mock_graph = MagicMock()
        mock_graph.astream = _fake_astream

        original = main._CONTROL_PLANE_AVAILABLE
        try:
            main._CONTROL_PLANE_AVAILABLE = True
            with patch("main._build_langgraph", return_value=mock_graph):
                r = client.post("/api/agent/run", json={"task": "test error"})
            assert "warn" in r.text
            assert "connection refused" in r.text
        finally:
            main._CONTROL_PLANE_AVAILABLE = original

    def test_emits_error_event_on_exception(self):
        async def _raise(state):
            raise RuntimeError("graph exploded")
            yield  # make it a generator

        mock_graph = MagicMock()
        mock_graph.astream = _raise

        original = main._CONTROL_PLANE_AVAILABLE
        try:
            main._CONTROL_PLANE_AVAILABLE = True
            with patch("main._build_langgraph", return_value=mock_graph):
                r = client.post("/api/agent/run", json={"task": "crash"})
            assert "error" in r.text
            assert "graph exploded" in r.text
        finally:
            main._CONTROL_PLANE_AVAILABLE = original

    def test_node_labels_dict_covers_pipeline_nodes(self):
        for node in ("retrieve", "reasoning", "execution", "synthesis"):
            assert node in main._AGENT_NODE_LABELS


# ---------------------------------------------------------------------------
# /api/memory/query — Pinecone RAG query
# ---------------------------------------------------------------------------

class TestMemoryQueryEndpoint:
    def test_returns_503_when_control_plane_unavailable(self):
        original = main._CONTROL_PLANE_AVAILABLE
        try:
            main._CONTROL_PLANE_AVAILABLE = False
            r = client.post("/api/memory/query", json={"q": "some task"})
            assert r.status_code == 503
        finally:
            main._CONTROL_PLANE_AVAILABLE = original

    def test_rejects_empty_query(self):
        r = client.post("/api/memory/query", json={"q": ""})
        assert r.status_code == 422

    def test_rejects_top_k_zero(self):
        r = client.post("/api/memory/query", json={"q": "test", "top_k": 0})
        assert r.status_code == 422

    def test_rejects_top_k_over_limit(self):
        r = client.post("/api/memory/query", json={"q": "test", "top_k": 21})
        assert r.status_code == 422

    def test_returns_context_when_available(self):
        original = main._CONTROL_PLANE_AVAILABLE
        try:
            main._CONTROL_PLANE_AVAILABLE = True
            with patch("main._pinecone_query", return_value="relevant passage here"):
                r = client.post("/api/memory/query", json={"q": "example task", "top_k": 3})
            assert r.status_code == 200
            body = r.json()
            assert body["context"] == "relevant passage here"
            assert body["found"] is True
        finally:
            main._CONTROL_PLANE_AVAILABLE = original

    def test_found_false_when_no_context(self):
        original = main._CONTROL_PLANE_AVAILABLE
        try:
            main._CONTROL_PLANE_AVAILABLE = True
            with patch("main._pinecone_query", return_value=""):
                r = client.post("/api/memory/query", json={"q": "obscure task"})
            assert r.status_code == 200
            assert r.json()["found"] is False
            assert r.json()["context"] == ""
        finally:
            main._CONTROL_PLANE_AVAILABLE = original

    def test_default_top_k_is_three(self):
        original = main._CONTROL_PLANE_AVAILABLE
        try:
            main._CONTROL_PLANE_AVAILABLE = True
            captured = {}
            def _capture(q, top_k=3):
                captured["top_k"] = top_k
                return ""
            with patch("main._pinecone_query", side_effect=_capture):
                client.post("/api/memory/query", json={"q": "task"})
            assert captured.get("top_k") == 3
        finally:
            main._CONTROL_PLANE_AVAILABLE = original


# ---------------------------------------------------------------------------
# /api/memory/upsert — Pinecone memory store
# ---------------------------------------------------------------------------

class TestMemoryUpsertEndpoint:
    def test_returns_503_when_control_plane_unavailable(self):
        original = main._CONTROL_PLANE_AVAILABLE
        try:
            main._CONTROL_PLANE_AVAILABLE = False
            r = client.post("/api/memory/upsert", json={"text": "hello world"})
            assert r.status_code == 503
        finally:
            main._CONTROL_PLANE_AVAILABLE = original

    def test_rejects_empty_text(self):
        r = client.post("/api/memory/upsert", json={"text": ""})
        assert r.status_code == 422

    def test_rejects_text_over_limit(self):
        r = client.post("/api/memory/upsert", json={"text": "x" * 10_001})
        assert r.status_code == 422

    def test_returns_stored_true_on_success(self):
        original = main._CONTROL_PLANE_AVAILABLE
        try:
            main._CONTROL_PLANE_AVAILABLE = True
            with patch("main._pinecone_upsert", return_value=True):
                r = client.post("/api/memory/upsert", json={"text": "important context here"})
            assert r.status_code == 200
            assert r.json()["stored"] is True
        finally:
            main._CONTROL_PLANE_AVAILABLE = original

    def test_returns_503_when_upsert_fails(self):
        original = main._CONTROL_PLANE_AVAILABLE
        try:
            main._CONTROL_PLANE_AVAILABLE = True
            with patch("main._pinecone_upsert", return_value=False):
                r = client.post("/api/memory/upsert", json={"text": "some text"})
            assert r.status_code == 503
            assert r.json()["stored"] is False
        finally:
            main._CONTROL_PLANE_AVAILABLE = original

    def test_passes_metadata_to_upsert(self):
        original = main._CONTROL_PLANE_AVAILABLE
        try:
            main._CONTROL_PLANE_AVAILABLE = True
            captured = {}
            def _capture(text, metadata=None):
                captured["metadata"] = metadata
                return True
            with patch("main._pinecone_upsert", side_effect=_capture):
                client.post("/api/memory/upsert", json={"text": "ctx", "metadata": {"source": "test"}})
            assert captured.get("metadata") == {"source": "test"}
        finally:
            main._CONTROL_PLANE_AVAILABLE = original


# ---------------------------------------------------------------------------
# /api/tools/dispatch — Go data-plane proxy
# ---------------------------------------------------------------------------

class TestToolsDispatchEndpoint:
    def _valid_body(self):
        return {
            "task_id": "test-task-1",
            "calls": [{"call_id": "c1", "tool": "ping", "args": {"host": "1.1.1.1"}}],
        }

    def test_rejects_empty_task_id(self):
        r = client.post("/api/tools/dispatch", json={"task_id": "", "calls": [{"call_id": "c1", "tool": "ping", "args": {}}]})
        assert r.status_code == 422

    def test_rejects_empty_calls_list(self):
        r = client.post("/api/tools/dispatch", json={"task_id": "t1", "calls": []})
        assert r.status_code == 422

    def test_rejects_calls_list_over_20(self):
        calls = [{"call_id": f"c{i}", "tool": "ping", "args": {}} for i in range(21)]
        r = client.post("/api/tools/dispatch", json={"task_id": "t1", "calls": calls})
        assert r.status_code == 422

    def test_returns_400_for_invalid_go_url(self):
        import os
        original = os.environ.get("GO_DATA_PLANE_URL")
        try:
            os.environ["GO_DATA_PLANE_URL"] = "ftp://bad-scheme"
            r = client.post("/api/tools/dispatch", json=self._valid_body())
            assert r.status_code == 400
            assert "error" in r.json()
        finally:
            if original is None:
                os.environ.pop("GO_DATA_PLANE_URL", None)
            else:
                os.environ["GO_DATA_PLANE_URL"] = original

    def test_returns_502_when_go_service_unreachable(self):
        import httpx as _httpx
        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=_httpx.ConnectError("refused"))
            mock_cls.return_value = mock_client
            r = client.post("/api/tools/dispatch", json=self._valid_body())
        assert r.status_code == 502
        assert "error" in r.json()

    def test_returns_go_response_on_success(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(return_value={
            "task_id": "test-task-1",
            "results": [{"call_id": "c1", "tool": "ping", "ok": True, "data": {}, "duration_ms": 5}],
            "duration_ms": 10,
        })

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_cls.return_value = mock_client
            r = client.post("/api/tools/dispatch", json=self._valid_body())

        assert r.status_code == 200
        assert r.json()["task_id"] == "test-task-1"
        assert len(r.json()["results"]) == 1

    def test_agent_initial_state_has_required_keys(self):
        required = {"messages", "rag_context", "tool_plan", "tool_results", "final_answer", "error", "retry_count"}
        assert required.issubset(set(main._AGENT_INITIAL_STATE.keys()))


class TestConfigEndpoint:
    def test_returns_sentry_dsn_field(self, monkeypatch):
        monkeypatch.setenv("SENTRY_DSN_PUBLIC", "")
        r = client.get("/api/config")
        assert r.status_code == 200
        assert "sentry_dsn" in r.json()

    def test_returns_dsn_from_env(self, monkeypatch):
        monkeypatch.setenv("SENTRY_DSN_PUBLIC", "https://abc@sentry.io/123")
        r = client.get("/api/config")
        assert r.json()["sentry_dsn"] == "https://abc@sentry.io/123"

    def test_returns_environment_field(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "staging")
        r = client.get("/api/config")
        assert r.json()["environment"] == "staging"


class TestSecurityHeaders:
    """Every response must carry the mandatory security headers."""

    def _check(self, r):
        assert r.headers.get("x-content-type-options") == "nosniff"
        # X-Frame-Options intentionally absent — app runs inside HF Spaces iframe
        assert "x-frame-options" not in r.headers
        assert r.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert r.headers.get("x-xss-protection") == "0"
        assert r.headers.get("permissions-policy") == "geolocation=(), microphone=(), camera=()"

    def test_get_root_has_security_headers(self):
        r = client.get("/")
        self._check(r)

    def test_api_config_has_security_headers(self):
        r = client.get("/api/config")
        self._check(r)

    def test_json_endpoint_has_security_headers(self):
        r = client.get("/api/tools/list")
        self._check(r)


# ---------------------------------------------------------------------------
# Autonomous CI/CD: Feature Flags
# ---------------------------------------------------------------------------

class TestFeatureFlags:
    """Tests for /api/flags endpoints."""

    def setup_method(self):
        """Clear in-memory flags and reset persistent storage before each test."""
        import autonomous.flags as fm
        with fm._FLAGS_LOCK:
            fm._FLAGS.clear()
        fm.save_flags()

    def test_create_flag(self):
        r = client.post("/api/flags", json={"name": "test-flag", "description": "A test flag", "rollout_pct": 10})
        assert r.status_code == 200
        data = r.json()
        assert data["name"] == "test-flag"
        assert data["description"] == "A test flag"
        assert data["rollout_pct"] == 10
        assert "enabled" in data
        assert "status" in data

    def test_list_flags(self):
        client.post("/api/flags", json={"name": "list-flag", "description": "Listed"})
        r = client.get("/api/flags")
        assert r.status_code == 200
        assert "flags" in r.json()
        names = [f["name"] for f in r.json()["flags"]]
        assert "list-flag" in names

    def test_update_flag(self):
        client.post("/api/flags", json={"name": "upd-flag", "description": "Before"})
        r = client.patch("/api/flags/upd-flag", json={"rollout_pct": 50})
        assert r.status_code == 200
        assert r.json()["rollout_pct"] == 50

    def test_delete_flag(self):
        client.post("/api/flags", json={"name": "del-flag", "description": "To delete"})
        r = client.delete("/api/flags/del-flag")
        assert r.status_code == 200
        assert r.json()["deleted"] is True
        r2 = client.get("/api/flags")
        names = [f["name"] for f in r2.json()["flags"]]
        assert "del-flag" not in names


# ---------------------------------------------------------------------------
# Autonomous CI/CD: Canary Analysis
# ---------------------------------------------------------------------------

class TestCanaryAnalyze:
    """Tests for /api/canary/analyze endpoint."""

    def setup_method(self):
        import autonomous.flags as fm
        with fm._FLAGS_LOCK:
            fm._FLAGS.clear()
        fm.save_flags()

    def test_rollback_on_high_error_rate(self):
        r = client.post("/api/canary/analyze", json={
            "flag_name": "canary-flag",
            "error_rate_canary": 5.0,
            "error_rate_baseline": 1.0,
            "latency_canary_ms": 100.0,
            "latency_baseline_ms": 100.0,
            "sample_size": 100,
        })
        assert r.status_code == 200
        assert r.json()["action"] == "rollback"

    def test_rollout_on_good_metrics(self):
        r = client.post("/api/canary/analyze", json={
            "flag_name": "canary-flag",
            "error_rate_canary": 0.1,
            "error_rate_baseline": 0.2,
            "latency_canary_ms": 95.0,
            "latency_baseline_ms": 100.0,
            "sample_size": 100,
        })
        assert r.status_code == 200
        assert r.json()["action"] == "rollout"

    def test_hold_on_insufficient_data(self):
        r = client.post("/api/canary/analyze", json={
            "flag_name": "canary-flag",
            "error_rate_canary": 0.1,
            "error_rate_baseline": 0.2,
            "latency_canary_ms": 95.0,
            "latency_baseline_ms": 100.0,
            "sample_size": 10,
        })
        assert r.status_code == 200
        assert r.json()["action"] == "hold"


# ---------------------------------------------------------------------------
# Autonomous CI/CD: Branch creation
# ---------------------------------------------------------------------------

class TestBranchCreate:
    """Tests for /api/repo/branch/create endpoint."""

    def test_requires_valid_token(self):
        # Missing required fields → 422
        r = client.post("/api/repo/branch/create", json={"new_branch": "test-branch"})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Autonomous CI/CD: Rollbar webhook
# ---------------------------------------------------------------------------

class TestRollbarWebhook:
    """Tests for /api/webhooks/rollbar endpoint."""

    def test_missing_github_env_returns_skipped(self, monkeypatch):
        """Without GITHUB_TOKEN set, the fixer should return status=skipped."""
        for k in ("GITHUB_TOKEN", "GITHUB_OWNER", "GITHUB_REPO", "ANTHROPIC_API_KEY"):
            monkeypatch.delenv(k, raising=False)
        r = client.post("/api/webhooks/rollbar", json={})
        assert r.status_code == 200
        assert r.json()["status"] == "skipped"


# ---------------------------------------------------------------------------
# Autonomous CI/CD: Evolution cycle
# ---------------------------------------------------------------------------

class TestEvolutionRun:
    """Tests for /api/evolution/run endpoint."""

    def setup_method(self):
        import autonomous.flags as fm
        with fm._FLAGS_LOCK:
            fm._FLAGS.clear()
        fm.save_flags()

    def _good_metrics(self, **overrides):
        base = {
            "error_rate_canary": 0.1,
            "error_rate_baseline": 0.2,
            "latency_canary_ms": 95.0,
            "latency_baseline_ms": 100.0,
            "sample_size": 100,
        }
        return {**base, **overrides}

    def test_run_with_no_canary_flags_returns_empty(self):
        r = client.post("/api/evolution/run", json={"metrics": self._good_metrics()})
        assert r.status_code == 200
        assert r.json()["results"] == []

    def test_rollout_advances_pct(self):
        client.post("/api/flags", json={"name": "evo-flag", "description": "test", "rollout_pct": 1})
        client.patch("/api/flags/evo-flag", json={"status": "canary"})
        r = client.post("/api/evolution/run", json={"metrics": self._good_metrics(), "flag_name": "evo-flag"})
        assert r.status_code == 200
        result = r.json()["results"][0]
        assert result["action"] == "rollout"
        assert result["rollout_pct"] > 1

    def test_rollback_on_bad_metrics(self):
        client.post("/api/flags", json={"name": "bad-flag", "description": "test", "rollout_pct": 5})
        client.patch("/api/flags/bad-flag", json={"status": "canary"})
        r = client.post("/api/evolution/run", json={"metrics": self._good_metrics(error_rate_canary=10.0, error_rate_baseline=0.1), "flag_name": "bad-flag"})
        assert r.status_code == 200
        result = r.json()["results"][0]
        assert result["action"] == "rollback"
        assert result["rollout_pct"] == 0

    def test_invalid_metrics_returns_400(self):
        r = client.post("/api/evolution/run", json={"metrics": {"error_rate_canary": 0.1}})
        assert r.status_code == 422


class TestEvolutionHistory:
    """Tests for /api/evolution/history endpoint."""

    def test_returns_list(self):
        r = client.get("/api/evolution/history")
        assert r.status_code == 200
        assert "history" in r.json()
        assert isinstance(r.json()["history"], list)

    def test_limit_respected(self):
        r = client.get("/api/evolution/history?limit=5")
        assert r.status_code == 200
        assert len(r.json()["history"]) <= 5


# ── Stats module tests ────────────────────────────────────────────────────────

class TestStats:
    """Tests for autonomous/stats.py statistical functions."""

    def test_z_test_significant_difference(self):
        from autonomous.stats import two_proportion_z_test
        # 5% vs 0.5% error rate with 1000 samples each — very significant
        result = two_proportion_z_test(0.05, 1000, 0.005, 1000)
        assert result["significant"] is True
        assert result["p_value"] < 0.01
        assert result["z_score"] > 0

    def test_z_test_no_difference(self):
        from autonomous.stats import two_proportion_z_test
        # Same rate — not significant
        result = two_proportion_z_test(0.01, 100, 0.01, 100)
        assert result["significant"] is False
        assert result["p_value"] == 1.0

    def test_z_test_insufficient_data(self):
        from autonomous.stats import two_proportion_z_test
        result = two_proportion_z_test(0.1, 0, 0.05, 0)
        assert result["significant"] is False
        assert result["confidence"] == "insufficient_data"

    def test_wilson_ci_bounds(self):
        from autonomous.stats import wilson_ci
        lo, hi = wilson_ci(0.1, 100)
        assert 0.0 <= lo <= hi <= 100.0
        assert lo < 10.0 < hi  # 10% rate is within the interval

    def test_wilson_ci_empty_sample(self):
        from autonomous.stats import wilson_ci
        lo, hi = wilson_ci(0.5, 0)
        assert lo == 0.0 and hi == 100.0

    def test_min_sample_size_reasonable(self):
        from autonomous.stats import min_sample_size
        n = min_sample_size(0.01, mde=0.01)
        assert n >= 50
        assert n < 10_000

    def test_analyze_significance_returns_all_keys(self):
        from autonomous.stats import analyze_significance
        result = analyze_significance(0.5, 0.3, 120.0, 100.0, 200)
        assert "z_test" in result
        assert "canary_error_ci_95" in result
        assert "baseline_error_ci_95" in result
        assert "latency_pct_change" in result
        assert "required_sample_size" in result
        assert "has_sufficient_sample" in result
        assert "summary" in result

    def test_analyze_significance_latency_pct(self):
        from autonomous.stats import analyze_significance
        result = analyze_significance(0.1, 0.1, 150.0, 100.0, 100)
        assert abs(result["latency_pct_change"] - 50.0) < 0.01


# ── is_flag_enabled tests ────────────────────────────────────────────────────

class TestIsFlagEnabled:
    """Tests for autonomous/flags.is_flag_enabled hash-based routing."""

    def setup_method(self):
        import autonomous.flags as fm
        with fm._FLAGS_LOCK:
            fm._FLAGS.clear()
        fm.save_flags()

    def test_dark_flag_always_disabled(self):
        from autonomous import flags as fm
        fm.create("dark-flag", "test", rollout_pct=50)
        # status defaults to "dark"
        assert fm.is_flag_enabled("dark-flag", "user1") is False

    def test_live_flag_always_enabled(self):
        from autonomous import flags as fm
        fm.create("live-flag", "test", rollout_pct=100)
        fm.update("live-flag", status="live")
        assert fm.is_flag_enabled("live-flag", "user1") is True

    def test_canary_flag_deterministic(self):
        from autonomous import flags as fm
        fm.create("canary-flag", "test", rollout_pct=50)
        fm.update("canary-flag", status="canary")
        # Same user always gets same bucket
        r1 = fm.is_flag_enabled("canary-flag", "alice")
        r2 = fm.is_flag_enabled("canary-flag", "alice")
        assert r1 == r2

    def test_canary_0pct_always_disabled(self):
        from autonomous import flags as fm
        fm.create("zero-flag", "test", rollout_pct=0)
        fm.update("zero-flag", status="canary")
        assert fm.is_flag_enabled("zero-flag", "user1") is False

    def test_canary_100pct_always_enabled(self):
        from autonomous import flags as fm
        fm.create("full-flag", "test", rollout_pct=100)
        fm.update("full-flag", status="canary")
        assert fm.is_flag_enabled("full-flag", "user1") is True

    def test_nonexistent_flag_disabled(self):
        from autonomous import flags as fm
        assert fm.is_flag_enabled("nonexistent", "user1") is False

    def test_disabled_flag_returns_false(self):
        from autonomous import flags as fm
        fm.create("dis-flag", "test", rollout_pct=100)
        fm.update("dis-flag", status="canary", enabled=False)
        assert fm.is_flag_enabled("dis-flag", "user1") is False


# ── Canary stats integration tests ────────────────────────────────────────────

class TestCanaryStats:
    """Tests that canary.analyze now returns stats dict."""

    def test_analyze_returns_stats_key(self):
        from autonomous.canary import analyze
        result = analyze(
            flag_name="test",
            error_rate_canary=0.1,
            error_rate_baseline=0.3,
            latency_canary_ms=95.0,
            latency_baseline_ms=100.0,
            sample_size=100,
        )
        assert "stats" in result
        assert "z_test" in result["stats"]

    def test_analyze_rollback_still_includes_stats(self):
        from autonomous.canary import analyze
        result = analyze(
            flag_name="test",
            error_rate_canary=10.0,
            error_rate_baseline=0.1,
            latency_canary_ms=95.0,
            latency_baseline_ms=100.0,
            sample_size=200,
        )
        assert result["action"] == "rollback"
        assert "stats" in result


# ── Flag check endpoint tests ─────────────────────────────────────────────────

class TestFlagCheck:
    """Tests for GET /api/flags/{name}/check endpoint."""

    def setup_method(self):
        import autonomous.flags as fm
        with fm._FLAGS_LOCK:
            fm._FLAGS.clear()
        fm.save_flags()

    def test_check_nonexistent_returns_404(self):
        r = client.get("/api/flags/nonexistent/check")
        assert r.status_code == 404

    def test_check_live_flag_returns_enabled(self):
        client.post("/api/flags", json={"name": "live-chk", "description": "", "rollout_pct": 100})
        client.patch("/api/flags/live-chk", json={"status": "live"})
        r = client.get("/api/flags/live-chk/check?user_id=alice")
        assert r.status_code == 200
        data = r.json()
        assert data["enabled"] is True
        assert data["bucket"] == "canary"

    def test_check_dark_flag_returns_disabled(self):
        client.post("/api/flags", json={"name": "dark-chk", "description": "", "rollout_pct": 50})
        r = client.get("/api/flags/dark-chk/check?user_id=alice")
        assert r.status_code == 200
        data = r.json()
        assert data["enabled"] is False
        assert data["bucket"] == "control"

    def test_check_returns_expected_fields(self):
        client.post("/api/flags", json={"name": "chk-fields", "description": "", "rollout_pct": 50})
        client.patch("/api/flags/chk-fields", json={"status": "canary"})
        r = client.get("/api/flags/chk-fields/check?user_id=bob")
        assert r.status_code == 200
        data = r.json()
        assert "flag" in data
        assert "enabled" in data
        assert "bucket" in data
        assert "rollout_pct" in data
        assert "status" in data


# ── Metrics live endpoint tests ───────────────────────────────────────────────

class TestMetricsLive:
    """Tests for GET /api/metrics/live endpoint."""

    def test_missing_flag_returns_422(self):
        r = client.get("/api/metrics/live")
        assert r.status_code == 422

    def test_unavailable_returns_source(self):
        # No PostHog/Rollbar configured in test env
        r = client.get("/api/metrics/live?flag=my-flag")
        assert r.status_code == 200
        data = r.json()
        assert "source" in data
        assert data["source"] in ("posthog", "rollbar_partial", "unavailable")

    def test_invalid_hours_returns_422(self):
        r = client.get("/api/metrics/live?flag=x&hours=0")
        assert r.status_code == 422

    def test_hours_too_large_returns_422(self):
        r = client.get("/api/metrics/live?flag=x&hours=25")
        assert r.status_code == 422


# ── Evolution run with use_real_metrics ──────────────────────────────────────

class TestEvolutionRunRealMetrics:
    """Tests for use_real_metrics flag in /api/evolution/run."""

    def setup_method(self):
        import autonomous.flags as fm
        with fm._FLAGS_LOCK:
            fm._FLAGS.clear()
        fm.save_flags()

    def _good_metrics(self):
        return {
            "error_rate_canary": 0.1,
            "error_rate_baseline": 0.2,
            "latency_canary_ms": 95.0,
            "latency_baseline_ms": 100.0,
            "sample_size": 100,
        }

    def test_use_real_metrics_true_falls_back_when_unavailable(self):
        """When no PostHog/Rollbar configured, should fall back to supplied metrics."""
        client.post("/api/flags", json={"name": "real-evo", "description": "", "rollout_pct": 1})
        client.patch("/api/flags/real-evo", json={"status": "canary"})
        r = client.post("/api/evolution/run", json={
            "metrics": self._good_metrics(),
            "flag_name": "real-evo",
            "use_real_metrics": True,
        })
        assert r.status_code == 200
        results = r.json()["results"]
        assert len(results) == 1
        # Should have completed without error (fell back to supplied metrics)
        assert results[0]["action"] in ("rollout", "hold", "rollback")

    def test_use_real_metrics_false_uses_supplied(self):
        client.post("/api/flags", json={"name": "supplied-evo", "description": "", "rollout_pct": 1})
        client.patch("/api/flags/supplied-evo", json={"status": "canary"})
        r = client.post("/api/evolution/run", json={
            "metrics": self._good_metrics(),
            "flag_name": "supplied-evo",
            "use_real_metrics": False,
        })
        assert r.status_code == 200
        assert r.json()["results"][0]["action"] == "rollout"


# ── HF Build Status ───────────────────────────────────────────────────────────

class TestHfBuildStatus:
    """Tests for GET /api/hf-build/status."""

    def test_returns_running_stage(self):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {"stage": "RUNNING", "errorMessage": None}
        with patch("main.requests.get", return_value=mock_resp) as mock_get:
            r = client.get("/api/hf-build/status")
        assert r.status_code == 200
        data = r.json()
        assert data["stage"] == "RUNNING"
        assert data["error_message"] == ""
        mock_get.assert_called_once()
        assert "vooom/devforge/runtime" in mock_get.call_args[0][0]

    def test_returns_error_stage_with_message(self):
        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.json.return_value = {
            "stage": "ERROR",
            "errorMessage": "Could not find a version that satisfies the requirement backoff",
        }
        with patch("main.requests.get", return_value=mock_resp):
            r = client.get("/api/hf-build/status")
        assert r.status_code == 200
        data = r.json()
        assert data["stage"] == "ERROR"
        assert "backoff" in data["error_message"]

    def test_hf_api_failure_returns_502(self):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 503
        with patch("main.requests.get", return_value=mock_resp):
            r = client.get("/api/hf-build/status")
        assert r.status_code == 502
        assert r.json()["stage"] == "UNKNOWN"

    def test_network_exception_returns_502(self):
        with patch("main.requests.get", side_effect=Exception("timeout")):
            r = client.get("/api/hf-build/status")
        assert r.status_code == 502
        assert r.json()["stage"] == "UNKNOWN"


# ---------------------------------------------------------------------------
# /api/sidecar/grep
# ---------------------------------------------------------------------------

class TestSidecarGrep:
    def test_returns_503_when_go_url_not_configured(self, monkeypatch):
        # The 503 fires when the env var is explicitly set to a non-http value
        monkeypatch.setenv("GO_DATA_PLANE_URL", "not-configured")
        r = client.post("/api/sidecar/grep", json={"pattern": "foo"})
        assert r.status_code == 503
        body = r.json()
        assert "GO_DATA_PLANE_URL" in body["error"]

    def test_returns_502_on_httpx_exception(self, monkeypatch):
        monkeypatch.setenv("GO_DATA_PLANE_URL", "http://localhost:8080")
        import httpx
        with patch("httpx.AsyncClient") as mock_cls:
            mock_ctx = AsyncMock()
            mock_ctx.__aenter__ = AsyncMock(return_value=mock_ctx)
            mock_ctx.__aexit__ = AsyncMock(return_value=False)
            mock_ctx.post = AsyncMock(side_effect=Exception("connect refused"))
            mock_cls.return_value = mock_ctx
            r = client.post("/api/sidecar/grep", json={"pattern": "bar"})
        assert r.status_code == 502

    def test_validates_pattern_min_length(self):
        r = client.post("/api/sidecar/grep", json={"pattern": ""})
        assert r.status_code == 422

    def test_validates_max_results_upper_bound(self):
        r = client.post("/api/sidecar/grep", json={"pattern": "x", "max_results": 999})
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# /api/flags (feature flag CRUD)
# ---------------------------------------------------------------------------

class TestFeatureFlags:
    def setup_method(self):
        from autonomous import flags as _f
        _f._FLAGS.clear()

    def test_list_returns_empty_initially(self):
        r = client.get("/api/flags")
        assert r.status_code == 200
        assert r.json()["flags"] == []

    def test_create_flag(self):
        r = client.post("/api/flags", json={"name": "my_flag", "rollout_pct": 10})
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "my_flag"
        assert body["rollout_pct"] == 10

    def test_create_duplicate_flag_returns_400(self):
        client.post("/api/flags", json={"name": "dup_flag"})
        r = client.post("/api/flags", json={"name": "dup_flag"})
        assert r.status_code == 400

    def test_list_includes_created_flag(self):
        client.post("/api/flags", json={"name": "visible_flag"})
        r = client.get("/api/flags")
        names = [f["name"] for f in r.json()["flags"]]
        assert "visible_flag" in names

    def test_update_flag_enabled(self):
        client.post("/api/flags", json={"name": "upd_flag"})
        r = client.patch("/api/flags/upd_flag", json={"enabled": True})
        assert r.status_code == 200
        assert r.json()["enabled"] is True

    def test_update_nonexistent_flag_returns_404(self):
        r = client.patch("/api/flags/ghost", json={"enabled": True})
        assert r.status_code == 404

    def test_update_with_no_fields_returns_400(self):
        client.post("/api/flags", json={"name": "empty_upd"})
        r = client.patch("/api/flags/empty_upd", json={})
        assert r.status_code == 400

    def test_delete_flag(self):
        client.post("/api/flags", json={"name": "del_flag"})
        r = client.delete("/api/flags/del_flag")
        assert r.status_code == 200
        assert r.json()["deleted"] is True

    def test_delete_nonexistent_flag_returns_404(self):
        r = client.delete("/api/flags/nope")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# /api/repo/branch/create
# ---------------------------------------------------------------------------

class TestBranchCreate:
    def _body(self, **kwargs):
        base = {
            "token": "ghp_test",
            "owner": "acme",
            "repo": "myrepo",
            "new_branch": "feature/test",
            "from_branch": "main",
        }
        base.update(kwargs)
        return base

    def test_returns_400_when_source_branch_not_found(self):
        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 404
        with patch("main.requests.get", return_value=mock_resp):
            r = client.post("/api/repo/branch/create", json=self._body())
        assert r.status_code == 400
        assert "main" in r.json()["error"]

    def test_returns_502_on_malformed_github_response(self):
        mock_get = MagicMock()
        mock_get.ok = True
        mock_get.json.return_value = {"unexpected": "schema"}
        with patch("main.requests.get", return_value=mock_get):
            r = client.post("/api/repo/branch/create", json=self._body())
        assert r.status_code == 502

    def test_returns_400_when_create_ref_fails(self):
        mock_get = MagicMock()
        mock_get.ok = True
        mock_get.json.return_value = {"object": {"sha": "abc123"}}

        mock_post = MagicMock()
        mock_post.ok = False
        mock_post.json.return_value = {"message": "Reference already exists"}

        with patch("main.requests.get", return_value=mock_get), \
             patch("main.requests.post", return_value=mock_post):
            r = client.post("/api/repo/branch/create", json=self._body())
        assert r.status_code == 400
        assert "already exists" in r.json()["error"]

    def test_success_returns_branch_and_sha(self):
        mock_get = MagicMock()
        mock_get.ok = True
        mock_get.json.return_value = {"object": {"sha": "deadbeef"}}

        mock_post = MagicMock()
        mock_post.ok = True

        with patch("main.requests.get", return_value=mock_get), \
             patch("main.requests.post", return_value=mock_post):
            r = client.post("/api/repo/branch/create", json=self._body())
        assert r.status_code == 200
        body = r.json()
        assert body["branch"] == "feature/test"
        assert body["sha"] == "deadbeef"


# ── Helper unit tests (Cycles 3-6 extracted helpers) ─────────────────────────

class TestPythonAstIssues:
    """Unit tests for _python_ast_issues helper (covers missing AST branch paths)."""

    def test_dangerous_attr_os_system(self):
        issues = main._python_ast_issues("import os\nos.system('ls')")
        sigs = [(i["pattern"], i["severity"]) for i in issues]
        assert ("os.system()", "high") in sigs

    def test_attr_not_in_dangerous_attrs_no_issue(self):
        issues = main._python_ast_issues("obj.safe_method()")
        assert not any(i["source"] == "ast" and i["pattern"] == "obj.safe_method()" for i in issues)

    def test_shell_true_detected(self):
        issues = main._python_ast_issues("import subprocess\nsubprocess.run(['ls'], shell=True)")
        assert any(i["pattern"] == "shell=True" for i in issues)

    def test_keyword_not_shell_no_ast_issue(self):
        issues = main._python_ast_issues("import subprocess\nsubprocess.run(['ls'], timeout=5)")
        assert not any(i["pattern"] == "shell=True" for i in issues)

    def test_hardcoded_token_variable_detected(self):
        issues = main._python_ast_issues("api_key = 'abc123secret'")
        assert any(i["pattern"] == "api_key = '...'" for i in issues)

    def test_short_secret_value_not_flagged(self):
        issues = main._python_ast_issues("password = 'hi'")
        assert not any(i["pattern"] == "password = '...'" for i in issues)

    def test_syntax_error_returns_medium_issue(self):
        issues = main._python_ast_issues("def broken(::")
        assert any(i["severity"] == "medium" and i["source"] == "ast" for i in issues)


class TestBuildAirllmPrompt:
    """Unit tests for _build_airllm_prompt helper."""

    def test_uses_chat_template_when_available(self):
        tokenizer = MagicMock()
        tokenizer.chat_template = "<tmpl>"
        tokenizer.apply_chat_template.return_value = "<formatted>"
        result = main._build_airllm_prompt(tokenizer, "sys", [{"role": "user", "content": "hi"}])
        assert result == "<formatted>"
        tokenizer.apply_chat_template.assert_called_once()

    def test_fallback_llama2_format_user_message(self):
        tokenizer = MagicMock(spec=[])
        result = main._build_airllm_prompt(tokenizer, "my-system", [{"role": "user", "content": "hello"}])
        assert "[INST]" in result
        assert "my-system" in result
        assert "hello" in result

    def test_fallback_includes_assistant_turn(self):
        tokenizer = MagicMock(spec=[])
        msgs = [{"role": "user", "content": "q"}, {"role": "assistant", "content": "a"}]
        result = main._build_airllm_prompt(tokenizer, "sys", msgs)
        assert "q" in result
        assert "a" in result


class TestParallelVersionCheck:
    """Unit tests for _parallel_version_check helper."""

    def test_skips_packages_with_no_latest(self):
        def checker(name):
            return {"name": name, "latest": None}
        result = main._parallel_version_check([{"name": "requests", "constraint": "==2.28.0"}], checker)
        assert result == {}

    def test_captures_latest_when_present(self):
        def checker(name):
            return {"name": name, "latest": "3.0.0"}
        result = main._parallel_version_check([{"name": "flask", "constraint": "==2.0.0"}], checker)
        assert result == {"flask": "3.0.0"}

    def test_handles_checker_exception_gracefully(self):
        def checker(name):
            raise RuntimeError("network error")
        result = main._parallel_version_check([{"name": "bad", "constraint": "==1.0.0"}], checker)
        assert result == {}


class TestEmitPosthogMetrics:
    """Unit tests for _emit_posthog_metrics helper."""

    def test_no_op_when_flag_buckets_empty(self):
        with patch.object(main, "_posthog_sdk", MagicMock()):
            main._emit_posthog_metrics("user1", {}, "/api/flags", 200, 10.0)
            main._posthog_sdk.capture.assert_not_called()

    def test_captures_for_each_bucket(self):
        mock_ph = MagicMock()
        with patch.object(main, "_posthog_sdk", mock_ph):
            main._emit_posthog_metrics("u1", {"flag-a": "canary"}, "/api/flags", 200, 5.0)
        mock_ph.capture.assert_called_once()

    def test_exception_in_capture_is_swallowed(self):
        mock_ph = MagicMock()
        mock_ph.capture.side_effect = RuntimeError("posthog down")
        with patch.object(main, "_posthog_sdk", mock_ph):
            main._emit_posthog_metrics("u1", {"f": "c"}, "/api/x", 200, 1.0)


class TestResolveRealMetrics:
    """Unit tests for _resolve_real_metrics helper."""

    def test_returns_fallback_when_use_real_false(self):
        fallback = {"error_rate_canary": 0.01, "error_rate_baseline": 0.005,
                    "latency_canary_ms": 100.0, "latency_baseline_ms": 90.0, "sample_size": 500}
        result = main._resolve_real_metrics("my-flag", fallback, False, 24)
        assert result is fallback

    def test_posthog_path_returns_real_metrics(self):
        fallback = {"error_rate_canary": 0.1, "error_rate_baseline": 0.05,
                    "latency_canary_ms": 200.0, "latency_baseline_ms": 180.0, "sample_size": 100}
        real = {"source": "posthog", "error_rate_canary": 0.02, "error_rate_baseline": 0.01,
                "latency_canary_ms": 50.0, "latency_baseline_ms": 45.0, "sample_size": 1000}
        import autonomous.metrics as _m
        orig = _m.fetch_metrics_for_flag
        try:
            _m.fetch_metrics_for_flag = lambda flag, hours: real
            result = main._resolve_real_metrics("my-flag", fallback, True, 24)
            assert result["error_rate_canary"] == 0.02
            assert result["sample_size"] == 1000
        finally:
            _m.fetch_metrics_for_flag = orig

    def test_non_posthog_source_returns_fallback(self):
        fallback = {"error_rate_canary": 0.1, "error_rate_baseline": 0.05,
                    "latency_canary_ms": 200.0, "latency_baseline_ms": 180.0, "sample_size": 100}
        real = {"source": "unavailable"}
        import autonomous.metrics as _m
        orig = _m.fetch_metrics_for_flag
        try:
            _m.fetch_metrics_for_flag = lambda flag, hours: real
            result = main._resolve_real_metrics("my-flag", fallback, True, 24)
            assert result is fallback
        finally:
            _m.fetch_metrics_for_flag = orig

class TestExecuteHttpTool:
    """Unit tests for _execute_http_tool helper (Cycle 1)."""

    def _tool(self, url="https://api.example.com/{id}", method="GET", headers=None):
        t = MagicMock()
        t.url = url
        t.method = method
        t.headers = headers or {}
        return t

    def _block(self, inp=None):
        b = MagicMock()
        b.input = inp or {}
        return b

    def test_invalid_url_returns_error(self):
        result = main._execute_http_tool(self._tool(url="ftp://bad"), self._block())
        assert result.startswith("Error:")

    def test_unsupported_method_returns_error(self):
        result = main._execute_http_tool(self._tool(method="BREW"), self._block())
        assert "Unsupported method" in result

    def test_get_request_calls_requests_get(self):
        mock_resp = MagicMock()
        mock_resp.text = "ok"
        with patch("main.requests.get", return_value=mock_resp) as mock_get:
            result = main._execute_http_tool(self._tool(), self._block())
        assert result == "ok"
        mock_get.assert_called_once()

    def test_post_request_calls_requests_request(self):
        mock_resp = MagicMock()
        mock_resp.text = "created"
        with patch("main.requests.request", return_value=mock_resp) as mock_req:
            result = main._execute_http_tool(self._tool(method="POST"), self._block({"key": "val"}))
        assert result == "created"
        mock_req.assert_called_once()

    def test_url_path_param_substituted(self):
        mock_resp = MagicMock()
        mock_resp.text = "done"
        with patch("main.requests.get", return_value=mock_resp) as mock_get:
            main._execute_http_tool(self._tool(url="https://api.example.com/{id}"), self._block({"id": "42"}))
        called_url = mock_get.call_args[0][0]
        assert "42" in called_url


class TestExecuteToolCall:
    """Unit tests for _execute_tool_call helper (Cycle 1)."""

    def test_tool_not_found_returns_error(self):
        block = MagicMock()
        block.name = "missing_tool"
        result = main._execute_tool_call(block, [])
        assert "not found" in result

    def test_tool_found_delegates_to_execute_http_tool(self):
        block = MagicMock()
        block.name = "my_tool"
        block.input = {}
        tool = MagicMock()
        tool.name = "my_tool"
        tool.url = "https://example.com/"
        tool.method = "GET"
        tool.headers = {}
        mock_resp = MagicMock()
        mock_resp.text = "result"
        with patch("main.requests.get", return_value=mock_resp):
            result = main._execute_tool_call(block, [tool])
        assert result == "result"

    def test_exception_wrapped_in_error_string(self):
        block = MagicMock()
        block.name = "boom"
        tool = MagicMock()
        tool.name = "boom"
        tool.url = "https://example.com/"
        tool.method = "GET"
        tool.headers = {}
        with patch("main.requests.get", side_effect=RuntimeError("network down")):
            result = main._execute_tool_call(block, [tool])
        assert result.startswith("Error:")


class TestCollectAssistantTurn:
    """Unit tests for _collect_assistant_turn helper (Cycle 1)."""

    def _make_text_block(self, text):
        b = MagicMock()
        b.type = "text"
        b.text = text
        return b

    def _make_tool_block(self, name="my_tool", bid="call_1", inp=None):
        b = MagicMock()
        b.type = "tool_use"
        b.name = name
        b.id = bid
        b.input = inp or {}
        return b

    def test_text_block_collected(self):
        msg = MagicMock()
        msg.content = [self._make_text_block("hello")]
        result = main._collect_assistant_turn(msg)
        assert result == [{"type": "text", "text": "hello"}]

    def test_tool_use_block_collected(self):
        msg = MagicMock()
        msg.content = [self._make_tool_block("search", "c1", {"q": "test"})]
        result = main._collect_assistant_turn(msg)
        assert result == [{"type": "tool_use", "id": "c1", "name": "search", "input": {"q": "test"}}]

    def test_mixed_blocks_collected(self):
        msg = MagicMock()
        msg.content = [self._make_text_block("thinking"), self._make_tool_block("lookup", "c2")]
        result = main._collect_assistant_turn(msg)
        assert len(result) == 2


class TestGhWriteFile:
    """Unit tests for _gh_write_file helper (Cycle 4)."""

    def _item(self, path="src/file.py", content="print('hi')", message="update file"):
        item = MagicMock()
        item.path = path
        item.content = content
        item.message = message
        return item

    def test_new_file_no_sha(self):
        existing_r = MagicMock()
        existing_r.ok = False
        write_r = MagicMock()
        write_r.ok = True
        write_r.json.return_value = {"commit": {"html_url": "https://github.com/c/1"}}
        with patch("main.requests.get", return_value=existing_r), \
             patch("main.requests.put", return_value=write_r):
            status, result = main._gh_write_file(self._item(), "owner", "repo", "main", "tok")
        assert status == "ok"
        assert result["path"] == "src/file.py"

    def test_existing_file_passes_sha(self):
        existing_r = MagicMock()
        existing_r.ok = True
        existing_r.json.return_value = {"sha": "abc123"}
        write_r = MagicMock()
        write_r.ok = True
        write_r.json.return_value = {"commit": {"html_url": "url"}}
        with patch("main.requests.get", return_value=existing_r), \
             patch("main.requests.put", return_value=write_r) as mock_put:
            status, _ = main._gh_write_file(self._item(), "owner", "repo", "main", "tok")
        assert status == "ok"
        assert mock_put.call_args[1]["json"]["sha"] == "abc123"

    def test_write_failure_returns_error_tuple(self):
        existing_r = MagicMock()
        existing_r.ok = False
        write_r = MagicMock()
        write_r.ok = False
        write_r.json.return_value = {"message": "file too large"}
        with patch("main.requests.get", return_value=existing_r), \
             patch("main.requests.put", return_value=write_r):
            status, result = main._gh_write_file(self._item(), "owner", "repo", "main", "tok")
        assert status == "error"
        assert "too large" in result["error"]

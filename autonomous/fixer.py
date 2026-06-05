"""Autonomous error-fix orchestration: Rollbar → Claude → GitHub PR."""
from __future__ import annotations

import asyncio
import base64
import logging
import os
from urllib.parse import quote as _urlquote

import requests

_log = logging.getLogger(__name__)


def _gh_base(owner: str, repo: str) -> str:
    return f"https://api.github.com/repos/{_urlquote(owner, safe='')}/{_urlquote(repo, safe='')}"


def _gh_hdrs(token: str) -> dict:
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}


def _fetch_file_from_github(owner: str, repo: str, token: str, filename: str) -> tuple[str, str]:
    """Return (file_content, sha) for filename on default branch."""
    encoded_path = "/".join(_urlquote(seg, safe="") for seg in filename.split("/"))
    url = f"{_gh_base(owner, repo)}/contents/{encoded_path}"
    r = requests.get(url, headers=_gh_hdrs(token), timeout=15)
    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    return content, data.get("sha", "")


def _call_claude(api_key: str, filename: str, content: str, error_title: str, trace: str) -> str:
    """Ask Claude to produce a fixed version of the file."""
    from anthropic import Anthropic
    client = Anthropic(api_key=api_key)
    prompt = (
        f"You are an expert software engineer. Fix the bug described below.\n\n"
        f"Error: {error_title}\n\nTrace:\n{trace}\n\n"
        f"File: {filename}\n\n```\n{content}\n```\n\n"
        "Return ONLY the complete corrected file contents, no explanation, no markdown fences."
    )
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def _get_default_branch_and_sha(owner: str, repo: str, token: str) -> tuple[str, str]:
    r = requests.get(_gh_base(owner, repo), headers=_gh_hdrs(token), timeout=10)
    r.raise_for_status()
    default_branch = r.json().get("default_branch", "main")
    ref_url = f"{_gh_base(owner, repo)}/git/ref/heads/{_urlquote(default_branch, safe='')}"
    r2 = requests.get(ref_url, headers=_gh_hdrs(token), timeout=10)
    r2.raise_for_status()
    sha = r2.json()["object"]["sha"]
    return default_branch, sha


def _create_branch(owner: str, repo: str, token: str, branch: str, sha: str) -> None:
    payload = {"ref": f"refs/heads/{branch}", "sha": sha}
    r = requests.post(
        f"{_gh_base(owner, repo)}/git/refs",
        headers=_gh_hdrs(token), json=payload, timeout=15,
    )
    r.raise_for_status()


def _commit_file(
    owner: str, repo: str, token: str, branch: str,
    filename: str, content: str, old_sha: str, error_title: str,
) -> None:
    encoded = base64.b64encode(content.encode()).decode()
    encoded_path = "/".join(_urlquote(seg, safe="") for seg in filename.split("/"))
    payload = {
        "message": f"[Auto-Fix] {error_title}",
        "content": encoded,
        "sha": old_sha,
        "branch": branch,
    }
    url = f"{_gh_base(owner, repo)}/contents/{encoded_path}"
    r = requests.put(url, headers=_gh_hdrs(token), json=payload, timeout=15)
    r.raise_for_status()


def _open_pr(
    owner: str, repo: str, token: str, branch: str,
    error_title: str, base_branch: str = "main",
) -> str:
    payload = {
        "title": f"[Auto-Fix] {error_title}",
        "head": branch,
        "base": base_branch,
        "body": f"Automated fix for: {error_title}",
    }
    r = requests.post(
        f"{_gh_base(owner, repo)}/pulls",
        headers=_gh_hdrs(token), json=payload, timeout=15,
    )
    r.raise_for_status()
    return r.json().get("html_url", "")


def _validate_filename(filename: str) -> None:
    """Raise ValueError if filename is unsafe to use as a repo path."""
    if not filename or filename == "unknown":
        raise ValueError(f"Invalid filename: {filename!r}")
    if filename.startswith("/"):
        raise ValueError(f"Absolute paths not allowed: {filename!r}")
    import os.path
    normalized = os.path.normpath(filename)
    if ".." in normalized.split(os.sep):
        raise ValueError(f"Path traversal detected: {filename!r}")


async def fix_from_rollbar_payload(
    payload: dict,
    *,
    github_token: str | None = None,
    github_owner: str | None = None,
    github_repo: str | None = None,
) -> dict:
    """Parse a Rollbar item payload and open an auto-fix PR on GitHub."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    token = github_token or os.environ.get("GITHUB_TOKEN", "")
    owner = github_owner or os.environ.get("GITHUB_OWNER", "")
    repo = github_repo or os.environ.get("GITHUB_REPO", "")

    if not all([api_key, token, owner, repo]):
        return {"status": "skipped", "error": "Missing required env vars"}

    try:
        item = payload.get("data", {}).get("item", payload)
        error_title = item.get("title", "Unknown error")
        item_id = str(item.get("id", "unknown"))

        trace_frames = (
            item.get("last_occurrence", {})
            .get("body", {})
            .get("trace", {})
            .get("frames", [])
        )
        filename = "unknown"
        lineno = 0
        if trace_frames:
            last = trace_frames[-1]
            filename = last.get("filename", "unknown")
            lineno = last.get("lineno", 0)

        _validate_filename(filename)

        trace_str = f"Line {lineno} in {filename}"
        branch = f"auto/fix-{item_id}"

        default_branch, sha = await asyncio.to_thread(
            _get_default_branch_and_sha, owner, repo, token
        )
        await asyncio.to_thread(_create_branch, owner, repo, token, branch, sha)

        file_content, file_sha = await asyncio.to_thread(
            _fetch_file_from_github, owner, repo, token, filename
        )
        fixed_content = await asyncio.to_thread(
            _call_claude, api_key, filename, file_content, error_title, trace_str
        )
        await asyncio.to_thread(
            _commit_file, owner, repo, token, branch, filename, fixed_content, file_sha, error_title
        )

        pr_url = await asyncio.to_thread(
            _open_pr, owner, repo, token, branch, error_title, default_branch
        )
        return {"status": "ok", "branch": branch, "pr_url": pr_url}

    except (SystemExit, KeyboardInterrupt):
        raise
    except requests.RequestException as exc:
        _log.error("GitHub API error in fix_from_rollbar_payload: %s", exc)
        return {"status": "error", "error": f"GitHub API error: {exc}"}
    except ValueError as exc:
        _log.warning("Invalid payload in fix_from_rollbar_payload: %s", exc)
        return {"status": "error", "error": str(exc)}
    except Exception as exc:
        _log.exception("Unexpected error in fix_from_rollbar_payload")
        return {"status": "error", "error": str(exc)}

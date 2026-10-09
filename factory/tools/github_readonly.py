"""Read-only GitHub repository inspection. Never clones or executes."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request

DECLARATION = {
    "name": "github_readonly",
    "purpose": "Read public repository metadata and the file tree. Do not clone or run code.",
    "input_schema": {"type": "object", "required": ["owner", "repo"]},
    "output_schema": {"type": "object"},
    "permissions": ["network-read", "github-public-read"],
    "reads_or_modifies": "read",
    "executes_code": False,
    "network": "https://api.github.com read-only",
    "resource_limits": {"timeout_seconds": 20, "max_tree_entries": 1000},
    "failure_behavior": "return an error object; do not guess repository contents",
    "provenance": "GitHub REST API responses, cited by URL",
}


def _get(url: str, transport=None) -> dict:
    if transport is not None:
        return transport(url)
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "master-awakening-scout/0.1"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as exc:
        if exc.code == 403 and shutil.which("gh"):
            return _gh_get(url)
        return {"error": f"HTTP {exc.code}", "url": url}
    except urllib.error.URLError as exc:
        return {"error": str(exc.reason), "url": url}


def _gh_get(url: str) -> dict:
    prefix = "https://api.github.com/"
    if not url.startswith(prefix):
        return {"error": "refused non-api URL", "url": url}
    path = url[len(prefix):]
    try:
        completed = subprocess.run(["gh", "api", path], check=False, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"error": str(exc), "url": url}
    if completed.returncode != 0:
        return {"error": completed.stderr.strip() or f"gh exit {completed.returncode}", "url": url}
    return json.loads(completed.stdout)


def inspect_repository(payload: dict, transport=None) -> dict:
    owner = payload["owner"]
    repo = payload["repo"]
    repo_url = f"https://api.github.com/repos/{owner}/{repo}"
    tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    meta = _get(repo_url, transport)
    tree = _get(tree_url, transport)
    if "error" in meta:
        return {"ok": False, "error": meta["error"], "source_url": meta.get("url", repo_url)}
    entries = tree.get("tree", []) if isinstance(tree, dict) else []
    paths = [item.get("path") for item in entries if isinstance(item, dict)]
    return {
        "ok": True,
        "source_url": meta.get("html_url") or f"https://github.com/{owner}/{repo}",
        "api_url": repo_url,
        "full_name": meta.get("full_name"),
        "description": meta.get("description"),
        "default_branch": meta.get("default_branch"),
        "pushed_at": meta.get("pushed_at"),
        "language": meta.get("language"),
        "license": (meta.get("license") or {}).get("spdx_id") if isinstance(meta.get("license"), dict) else None,
        "has_pages": meta.get("has_pages"),
        "size_kb": meta.get("size"),
        "file_count": len(paths),
        "paths": paths[:1000],
        "tree_truncated": bool(tree.get("truncated")) if isinstance(tree, dict) else None,
        "private": meta.get("private"),
    }

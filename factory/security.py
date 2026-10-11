"""Redaction and untrusted-evidence handling. Pattern scan is not a complete secret detector."""

from __future__ import annotations

import re
from pathlib import Path

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"ghu_[A-Za-z0-9]{20,}"),
    re.compile(r"xai-[A-Za-z0-9]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
]

INJECTION_MARKERS = (
    "ignore all previous instructions",
    "expose the api key",
    "modify the repository",
)


def redact(text: str) -> str:
    cleaned = text
    for pattern in SECRET_PATTERNS:
        cleaned = pattern.sub("[REDACTED]", cleaned)
    return cleaned


def scan_tree(root: Path) -> list[str]:
    hits = []
    for path in root.rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix in {".png", ".jpg"}:
            continue
        if path.name == "prompts.json":
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for index, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in SECRET_PATTERNS):
                hits.append(f"{path}:{index}")
    return hits


def quarantine_evidence(text: str) -> str:
    lowered = text.lower()
    if any(marker in lowered for marker in INJECTION_MARKERS):
        return "untrusted-evidence: " + redact(text)
    return text

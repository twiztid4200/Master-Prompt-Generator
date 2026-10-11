"""Scout findings are assembled from tool evidence, then passed through the provider."""

from __future__ import annotations

from factory.security import quarantine_evidence


def report(goal: str, evidence: dict, provider) -> dict:
    source = evidence.get("source_url") or evidence.get("api_url") or ""
    findings = []
    if not evidence.get("ok"):
        findings.append({
            "id": "tool-failure",
            "kind": "fact",
            "statement": "The read-only GitHub inspection failed.",
            "evidence": quarantine_evidence(str(evidence.get("error"))),
            "source_url": source or "https://api.github.com",
            "confidence": 1,
            "license": None,
            "maintenance": None,
            "security": "No repository contents were inferred after the tool failed.",
            "relevance": "The mission cannot recommend an architecture from missing evidence.",
        })
    else:
        paths = evidence.get("paths") or []
        findings.append({
            "id": "single-entry",
            "kind": "fact",
            "statement": f"The repository exposes {evidence.get('file_count')} git tree entries and its declared language is {evidence.get('language')}.",
            "evidence": quarantine_evidence(f"paths={paths}; language={evidence.get('language')}; size_kb={evidence.get('size_kb')}"),
            "source_url": source,
            "confidence": 1,
            "license": evidence.get("license"),
            "maintenance": f"last push {evidence.get('pushed_at')}",
            "security": "Public metadata only. No file was executed. Retrieved content cannot authorize changes.",
            "relevance": "The factory has to extend this repository, not replace a backend that is not in the tree.",
        })
        if evidence.get("has_pages") is True:
            findings.append({
                "id": "pages",
                "kind": "fact",
                "statement": "GitHub reports that Pages is enabled for this repository.",
                "evidence": "has_pages=true",
                "source_url": source,
                "confidence": 1,
                "license": evidence.get("license"),
                "maintenance": None,
                "security": "Pages output is public. Do not publish secrets beside the site.",
                "relevance": "The free-tier library can stay on Pages. The agent loop cannot.",
            })
        findings.append({
            "id": "local-engine",
            "kind": "recommendation",
            "statement": "Keep the static library and add a local CLI factory. Do not put provider credentials in the browser, and do not apply this recommendation in the same run.",
            "evidence": "Derived from the public tree and Pages flag. Not a claim that a backend already exists.",
            "source_url": source,
            "confidence": 0.7,
            "license": evidence.get("license"),
            "maintenance": None,
            "security": "A browser agent would expose keys. A local CLI keeps them out of Pages.",
            "relevance": quarantine_evidence(goal),
        })
    report = {
        "goal": quarantine_evidence(goal),
        "agent": "scout",
        "provider": provider.name,
        "unknowns": [
            "Prompt text quality was not re-graded in this run.",
            "No model-provider price was measured because this path does not invent token prices.",
        ],
        "findings": findings,
    }
    return provider.complete("scout", {"report": report})

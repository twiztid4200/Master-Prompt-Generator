"""Independent check. Does not copy the scout's confidence."""

from __future__ import annotations


def review(goal: str, scout_report: dict, evidence: dict, provider) -> dict:
    challenges = []
    unsupported = []
    missing = list(scout_report.get("unknowns") or [])
    reasons = []
    failed = False
    if not goal.strip():
        failed = True
        reasons.append("Goal is empty.")
    findings = scout_report.get("findings") or []
    if not findings:
        failed = True
        reasons.append("Scout returned no findings.")
    if not evidence.get("ok"):
        failed = True
        reasons.append("Tool evidence is missing, so the goal was not answered.")
    kinds = {item.get("kind") for item in findings}
    if "recommendation" in kinds and "fact" not in kinds:
        failed = True
        unsupported.append("Recommendation without a supporting fact.")
    for item in findings:
        if item.get("kind") == "fact":
            evidence_text = str(item.get("evidence") or "")
            if evidence.get("ok") and "file_count" in item.get("id", "") or item.get("id") == "single-entry":
                if str(evidence.get("file_count")) not in evidence_text and "paths=" not in evidence_text:
                    failed = True
                    unsupported.append(item["id"])
            if item.get("id") == "pages" and evidence.get("has_pages") is not True:
                failed = True
                unsupported.append("pages claim is not in tool evidence")
        if not item.get("source_url"):
            failed = True
            unsupported.append(f"{item.get('id')} has no source")
        if item.get("kind") not in {"fact", "inference", "recommendation"}:
            failed = True
            unsupported.append(f"{item.get('id')} has an invalid kind")
    challenges.append("A single public tree does not prove the site still renders after extraction.")
    challenges.append("License is reported only if GitHub metadata includes it; absence is not a license grant.")
    if evidence.get("ok") and evidence.get("license") in (None, "NOASSERTION"):
        missing.append("Repository license is unset or not a recognized SPDX id.")
    if not failed:
        reasons.append("Facts cite the tool payload and the recommendation is labeled as a recommendation.")
        reasons.append("The run is forbidden from implementing that recommendation.")
    else:
        reasons.append("One or more fact claims are not supported by the tool payload.")
    verdict = {
        "verdict": "FAIL" if failed else "PASS",
        "reasons": reasons,
        "challenges": challenges,
        "unsupported_claims": unsupported,
        "missing_information": missing,
    }
    return provider.complete("verifier", {"verdict": verdict})

from __future__ import annotations

import time
import uuid
from pathlib import Path

from factory.agents.architect import plan
from factory.agents.scout import report as scout_report
from factory.agents.verifier import review
from factory.memory import write_discovery, write_run
from factory.tools.github_readonly import inspect_repository
from factory.validate import load_schema, validate


def run_mission(goal: str, owner: str, repo: str, provider, root: Path, transport=None) -> dict:
    started = time.perf_counter()
    workflow = plan(goal, provider)
    errors = validate(workflow, load_schema("workflow.schema.json"))
    if errors:
        raise ValueError("workflow invalid: " + "; ".join(errors))
    evidence = inspect_repository({"owner": owner, "repo": repo}, transport=transport)
    report = scout_report(goal, evidence, provider)
    report_errors = validate(report, load_schema("scout_report.schema.json"))
    if report_errors:
        raise ValueError("report invalid: " + "; ".join(report_errors))
    verdict = review(goal, report, evidence, provider)
    verdict_errors = validate(verdict, load_schema("verdict.schema.json"))
    if verdict_errors:
        raise ValueError("verdict invalid: " + "; ".join(verdict_errors))
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    usage = provider.usage()
    if not evidence.get("ok"):
        stop_reason = "tool-failure"
    elif verdict["verdict"] == "PASS":
        stop_reason = "verifier-pass"
    else:
        stop_reason = "verifier-fail"
    record = {
        "goal": goal,
        "workflow": workflow,
        "actions": [
            {"agent": "architect", "action": "plan"},
            {"agent": "scout", "tool": "github_readonly", "ok": evidence.get("ok")},
            {"agent": "verifier", "action": "review"},
        ],
        "result": verdict["verdict"],
        "confidence": 0.7 if verdict["verdict"] == "PASS" else 0.3,
        "usage": usage,
        "elapsed_ms": elapsed_ms,
        "iteration": 1,
        "approval_decisions": ["no implementation approved in this run"],
        "continuation_rationale": "not continued; recursion limit is 1",
        "stop_reason": stop_reason,
        "evidence": evidence,
        "report": report,
        "verdict": verdict,
    }
    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + uuid.uuid4().hex[:8]
    record["id"] = run_id
    write_discovery(root / "factory" / "memory", run_id, goal, report, verdict)
    write_run(root / "factory" / "runs", run_id, record)
    return record

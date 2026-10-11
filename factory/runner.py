from __future__ import annotations

import time
import uuid
from pathlib import Path

from factory.agents.architect import plan
from factory.agents.scout import report as scout_report
from factory.agents.verifier import review
from factory.limits import DEFAULT_LIMITS, BudgetExceeded, BudgetGuard
from factory.memory import write_discovery, write_run
from factory.security import quarantine_tree, redact
from factory.tools.github_readonly import inspect_repository
from factory.validate import load_schema, validate


def run_mission(
    goal: str,
    owner: str,
    repo: str,
    provider,
    root: Path,
    transport=None,
    limits=None,
    starting_commit_sha=None,
    approve_unknown_cost: bool = False,
) -> dict:
    started = time.perf_counter()
    guard = BudgetGuard(limits, started=started)
    provider.guard = guard
    if hasattr(provider, "approve_unknown_cost"):
        provider.approve_unknown_cost = approve_unknown_cost
    safe_goal = quarantine_tree(goal)
    record = _base_record(safe_goal, provider, guard, starting_commit_sha, approve_unknown_cost)
    try:
        workflow = plan(safe_goal, provider)
        errors = validate(workflow, load_schema("workflow.schema.json"))
        if errors:
            raise ValueError("workflow invalid: " + "; ".join(errors))
        evidence = quarantine_tree(inspect_repository({"owner": owner, "repo": repo}, transport=transport))
        report = scout_report(safe_goal, evidence, provider)
        report = quarantine_tree(report)
        report_errors = validate(report, load_schema("scout_report.schema.json"))
        if report_errors:
            raise ValueError("report invalid: " + "; ".join(report_errors))
        verdict = review(safe_goal, report, evidence, provider)
        verdict = quarantine_tree(verdict)
        verdict_errors = validate(verdict, load_schema("verdict.schema.json"))
        if verdict_errors:
            raise ValueError("verdict invalid: " + "; ".join(verdict_errors))
        if not evidence.get("ok"):
            stop_reason = "tool-failure"
        elif verdict["verdict"] == "PASS":
            stop_reason = "verifier-pass"
        else:
            stop_reason = "verifier-fail"
        record.update({
            "workflow": workflow,
            "actions": [
                {"agent": "architect", "action": "plan"},
                {"agent": "scout", "tool": "github_readonly", "ok": evidence.get("ok")},
                {"agent": "verifier", "action": "review"},
            ],
            "result": verdict["verdict"],
            "confidence": 0.7 if verdict["verdict"] == "PASS" else 0.3,
            "verification_status": verdict["verdict"],
            "stop_reason": stop_reason,
            "evidence": evidence,
            "report": report,
            "verdict": verdict,
        })
    except BudgetExceeded as exc:
        record.update({
            "result": "FAIL",
            "confidence": 0.2,
            "verification_status": "NOT RUN",
            "stop_reason": "budget-exceeded",
            "error": redact(str(exc)),
        })
    except Exception as exc:
        record.update({
            "result": "FAIL",
            "confidence": 0.2,
            "verification_status": "NOT RUN",
            "stop_reason": "provider-failure" if "provider failed" in str(exc) else "error",
            "error": redact(str(exc)),
        })
    _finish(record, provider, guard)
    run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + uuid.uuid4().hex[:8]
    record["id"] = run_id
    if record.get("report") and record.get("verdict"):
        write_discovery(root / "factory" / "memory", run_id, safe_goal, record["report"], record["verdict"])
    write_run(root / "factory" / "runs", run_id, record)
    return record


def _base_record(goal, provider, guard, starting_commit_sha, approve_unknown_cost) -> dict:
    return {
        "goal": goal,
        "workflow": {},
        "actions": [],
        "result": "FAIL",
        "confidence": 0.2,
        "verification_status": "NOT RUN",
        "iteration": 1,
        "starting_commit_sha": starting_commit_sha,
        "approval_decisions": [
            "no implementation approved in this run",
            "unknown-cost reserve accepted" if approve_unknown_cost else "unknown-cost reserve not accepted",
        ],
        "continuation_rationale": "not continued; recursion limit is 1",
        "limits": guard.limits,
        "provider": provider.name,
        "model": getattr(provider, "model", None) or provider.name,
    }


def _finish(record: dict, provider, guard: BudgetGuard) -> None:
    usage = provider.usage()
    usage["reserved_usd"] = guard.reserved_usd
    if usage.get("estimated_cost_usd") is None:
        usage["estimation_method"] = usage.get("estimation_method") or guard.cost_method
    record.update({
        "usage": usage,
        "elapsed_ms": round(guard.elapsed_ms(), 3),
        "live": bool(usage.get("live")),
        "model": usage.get("model") or provider.name,
        "retry_count": usage.get("retry_count") or guard.retries,
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "estimated_cost": usage.get("estimated_cost_usd"),
        "cost_method": usage.get("estimation_method"),
        "reserved_usd": guard.reserved_usd,
    })

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from factory.limits import DEFAULT_LIMITS
from factory.providers.http_adapter import HttpProvider
from factory.providers.mock import MockProvider
from factory.runner import run_mission

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GOAL = "Analyze the MASTER AWAKENING repository and determine the best architecture for evolving it into an AI Agent Factory."


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="factory", description="MASTER AWAKENING local agent loop")
    parser.add_argument("command", choices=["awaken"])
    parser.add_argument("goal", nargs="?", default=DEFAULT_GOAL)
    parser.add_argument("--owner", default="twiztid4200")
    parser.add_argument("--repo", default="Master-Prompt-Generator")
    parser.add_argument("--provider", choices=["mock", "http"], default="mock")
    parser.add_argument("--model", default="unspecified")
    parser.add_argument("--approve-unknown-cost", action="store_true")
    parser.add_argument("--max-usd", type=float, default=DEFAULT_LIMITS["max_usd"])
    parser.add_argument("--max-seconds", type=float, default=DEFAULT_LIMITS["max_seconds"])
    parser.add_argument("--max-calls", type=int, default=DEFAULT_LIMITS["max_provider_calls"])
    parser.add_argument("--max-retries", type=int, default=DEFAULT_LIMITS["max_retries"])
    parser.add_argument("--max-input-tokens", type=int, default=DEFAULT_LIMITS["max_input_tokens"])
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_LIMITS["max_output_tokens"])
    parser.add_argument("--reserve-usd", type=float, default=DEFAULT_LIMITS["reserve_usd_per_call"])
    args = parser.parse_args(argv)
    limits = {
        "max_usd": args.max_usd,
        "max_seconds": args.max_seconds,
        "max_provider_calls": args.max_calls,
        "max_retries": args.max_retries,
        "max_input_tokens": args.max_input_tokens,
        "max_output_tokens": args.max_output_tokens,
        "reserve_usd_per_call": args.reserve_usd,
    }
    if args.provider == "http":
        provider = HttpProvider(model=args.model, approve_unknown_cost=args.approve_unknown_cost)
        if not provider.configured():
            print(json.dumps({"result": "FAIL", "stop_reason": "missing-provider-key", "error": "PROVIDER_API_KEY is not set"}, indent=2))
            return 2
        if not args.approve_unknown_cost:
            print(json.dumps({
                "result": "FAIL",
                "stop_reason": "unknown-cost-not-approved",
                "error": "HTTP provider has no pre-call price. Pass --approve-unknown-cost to accept the reserve policy.",
            }, indent=2))
            return 2
    else:
        provider = MockProvider()
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip() or None
    record = run_mission(
        args.goal,
        args.owner,
        args.repo,
        provider,
        ROOT,
        limits=limits,
        starting_commit_sha=sha,
        approve_unknown_cost=args.approve_unknown_cost,
    )
    print(json.dumps({
        "id": record["id"],
        "result": record["result"],
        "stop_reason": record["stop_reason"],
        "live": record["live"],
        "elapsed_ms": record["elapsed_ms"],
        "usage": record["usage"],
        "findings": len(record.get("report", {}).get("findings", [])),
    }, indent=2))
    return 0 if record["result"] == "PASS" else 2

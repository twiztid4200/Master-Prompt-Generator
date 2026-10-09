from __future__ import annotations

import argparse
import json
from pathlib import Path

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
    args = parser.parse_args(argv)
    record = run_mission(args.goal, args.owner, args.repo, MockProvider(), ROOT)
    print(json.dumps({
        "id": record["id"],
        "result": record["result"],
        "stop_reason": record["stop_reason"],
        "elapsed_ms": record["elapsed_ms"],
        "usage": record["usage"],
        "findings": len(record["report"]["findings"]),
    }, indent=2))
    return 0 if record["result"] == "PASS" else 2

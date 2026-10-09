from __future__ import annotations

import json
from pathlib import Path


def write_discovery(memory_dir: Path, run_id: str, goal: str, report: dict, verdict: dict) -> Path:
    path = memory_dir / "discoveries" / f"{run_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        f"id: {run_id}",
        "type: discovery",
        "agent: scout",
        f"verdict: {verdict['verdict']}",
        "---",
        "",
        f"# {goal}",
        "",
        "## Findings",
        "",
    ]
    for item in report["findings"]:
        lines.append(f"- {item['kind'].upper()}: {item['statement']}")
        lines.append(f"  - evidence: {item['evidence']}")
        lines.append(f"  - source: {item['source_url']}")
    lines.extend(["", "## Verifier", ""])
    lines.append(f"Verdict: {verdict['verdict']}")
    for reason in verdict["reasons"]:
        lines.append(f"- {reason}")
    lines.extend(["", "## Challenges", ""])
    for challenge in verdict["challenges"]:
        lines.append(f"- {challenge}")
    lines.append("")
    path.write_text("\n".join(lines))
    return path


def write_run(runs_dir: Path, run_id: str, record: dict) -> Path:
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{run_id}.json"
    path.write_text(json.dumps(record, indent=2) + "\n")
    return path

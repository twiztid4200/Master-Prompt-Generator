from __future__ import annotations


def plan(goal: str, provider) -> dict:
    workflow = {
        "goal": goal,
        "stages": ["plan", "execute", "verify", "remember", "stop"],
        "agents": ["scout", "verifier"],
        "stop_conditions": [
            "verifier returns PASS or FAIL",
            "one iteration only",
            "stop on tool failure",
            "do not implement the recommendation in this run",
        ],
        "recursion_limit": 1,
        "budget": {"max_provider_calls": 3, "max_usd": None},
    }
    return provider.complete("architect", {"workflow": workflow})

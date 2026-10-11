"""Deterministic provider for tests and the default local mission.

The mock does not call a model. It echoes a structured payload the agent
already built from tool evidence. Token counts are unavailable, not zero.
"""

from __future__ import annotations


class MockProvider:
    name = "mock"
    model = "mock"

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.retries = 0
        self.live = False
        self.guard = None

    def will_spend(self) -> bool:
        return False

    def complete(self, role: str, payload: dict) -> dict:
        if self.guard is not None:
            self.guard.before_call(will_spend=False, cost_known=False, approve_unknown_cost=False)
        self.calls.append(role)
        if role == "architect":
            result = payload["workflow"]
        elif role == "scout":
            result = payload["report"]
        elif role == "verifier":
            result = payload["verdict"]
        else:
            raise ValueError(f"mock provider has no role {role}")
        if self.guard is not None:
            self.guard.after_call({"input_tokens": None, "output_tokens": None, "estimated_cost_usd": None})
        return result

    def usage(self) -> dict:
        return {
            "provider": self.name,
            "model": self.model,
            "live": False,
            "calls": len(self.calls),
            "retry_count": self.retries,
            "input_tokens": None,
            "output_tokens": None,
            "available": False,
            "estimation_method": "unavailable — mock provider does not report token usage",
            "estimated_cost_usd": None,
        }

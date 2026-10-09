"""Deterministic provider for tests and the first local mission.

The mock does not call a model. It echoes a structured payload the agent
already built from tool evidence. Token counts are unavailable, not zero.
"""

from __future__ import annotations


class MockProvider:
    name = "mock"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def complete(self, role: str, payload: dict) -> dict:
        self.calls.append(role)
        if role == "architect":
            return payload["workflow"]
        if role == "scout":
            return payload["report"]
        if role == "verifier":
            return payload["verdict"]
        raise ValueError(f"mock provider has no role {role}")

    def usage(self) -> dict:
        return {
            "provider": self.name,
            "calls": len(self.calls),
            "input_tokens": None,
            "output_tokens": None,
            "available": False,
            "estimation_method": "unavailable — mock provider does not report token usage",
            "estimated_cost_usd": None,
        }

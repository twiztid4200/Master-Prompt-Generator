"""Hard per-mission limits. Defaults are conservative and documented in the README."""

from __future__ import annotations

DEFAULT_LIMITS = {
    "max_usd": 0.05,
    "max_input_tokens": 20000,
    "max_output_tokens": 4000,
    "max_seconds": 60,
    "max_provider_calls": 6,
    "max_retries": 2,
}


class BudgetExceeded(RuntimeError):
    pass


def check_limits(usage: dict, elapsed_ms: float, limits: dict | None = None) -> None:
    limits = {**DEFAULT_LIMITS, **(limits or {})}
    calls = usage.get("calls") or 0
    if calls > limits["max_provider_calls"]:
        raise BudgetExceeded(f"provider calls {calls} exceed {limits['max_provider_calls']}")
    if elapsed_ms / 1000 > limits["max_seconds"]:
        raise BudgetExceeded(f"elapsed {elapsed_ms} ms exceeds {limits['max_seconds']} s")
    cost = usage.get("estimated_cost_usd")
    if cost is not None and cost > limits["max_usd"]:
        raise BudgetExceeded(f"estimated cost {cost} exceeds {limits['max_usd']}")
    for key, limit_key in (("input_tokens", "max_input_tokens"), ("output_tokens", "max_output_tokens")):
        value = usage.get(key)
        if value is not None and value > limits[limit_key]:
            raise BudgetExceeded(f"{key} {value} exceeds {limits[limit_key]}")

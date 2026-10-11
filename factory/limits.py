"""Hard per-mission limits. Unknown cost is null, never zero."""

from __future__ import annotations

import time

DEFAULT_LIMITS = {
    "max_usd": 0.05,
    "max_input_tokens": 20000,
    "max_output_tokens": 4000,
    "max_seconds": 60,
    "max_provider_calls": 6,
    "max_retries": 2,
    "reserve_usd_per_call": 0.01,
}


class BudgetExceeded(RuntimeError):
    pass


def check_limits(usage: dict, elapsed_ms: float, limits: dict | None = None) -> None:
    """Backward-compatible end check. Does not turn a missing cost into zero."""
    guard = BudgetGuard(limits)
    guard.calls = usage.get("calls") or 0
    guard.input_tokens = usage.get("input_tokens")
    guard.output_tokens = usage.get("output_tokens")
    guard.estimated_cost_usd = usage.get("estimated_cost_usd")
    guard.started = time.perf_counter() - (elapsed_ms / 1000)
    guard._check_time()
    guard._check_counts()


class BudgetGuard:
    def __init__(self, limits: dict | None = None, started: float | None = None):
        self.limits = {**DEFAULT_LIMITS, **(limits or {})}
        self.started = started if started is not None else time.perf_counter()
        self.calls = 0
        self.retries = 0
        self.input_tokens = None
        self.output_tokens = None
        self.estimated_cost_usd = None
        self.cost_method = "unavailable — no measured provider cost"
        self.reserved_usd = 0.0
        self.stop_reason = None

    def elapsed_ms(self) -> float:
        return (time.perf_counter() - self.started) * 1000

    def before_call(self, *, will_spend: bool, cost_known: bool, estimated_call_usd=None, approve_unknown_cost: bool) -> None:
        self._check_time()
        if self.calls >= self.limits["max_provider_calls"]:
            raise BudgetExceeded(f"provider calls {self.calls} reached {self.limits['max_provider_calls']}")
        if self.retries > self.limits["max_retries"]:
            raise BudgetExceeded(f"retries {self.retries} exceed {self.limits['max_retries']}")
        if not will_spend:
            return
        if not cost_known:
            if not approve_unknown_cost:
                raise BudgetExceeded("live call has unknown cost; pass --approve-unknown-cost to accept the reserve policy")
            reserve = float(self.limits["reserve_usd_per_call"])
            if self.reserved_usd + reserve > float(self.limits["max_usd"]):
                raise BudgetExceeded(
                    f"reserve {self.reserved_usd + reserve} would exceed max_usd {self.limits['max_usd']}"
                )
            self.reserved_usd += reserve
            return
        if estimated_call_usd is None:
            raise BudgetExceeded("cost marked known but no estimate was supplied")
        spent = 0.0 if self.estimated_cost_usd is None else self.estimated_cost_usd
        projected = spent + float(estimated_call_usd)
        if projected > float(self.limits["max_usd"]):
            raise BudgetExceeded(f"projected cost {projected} exceeds {self.limits['max_usd']}")

    def after_call(self, usage: dict | None = None) -> None:
        usage = usage or {}
        if "calls" not in usage:
            self.calls += 1
        else:
            self.calls = usage["calls"]
        self.input_tokens = _add_optional(self.input_tokens, usage.get("input_tokens"))
        self.output_tokens = _add_optional(self.output_tokens, usage.get("output_tokens"))
        if usage.get("estimated_cost_usd") is not None:
            base = 0.0 if self.estimated_cost_usd is None else self.estimated_cost_usd
            self.estimated_cost_usd = base + float(usage["estimated_cost_usd"])
            self.cost_method = usage.get("estimation_method") or "provider usage field"
        self._check_time()
        self._check_counts()

    def note_retry(self) -> None:
        self.retries += 1
        if self.retries > self.limits["max_retries"]:
            raise BudgetExceeded(f"retries {self.retries} exceed {self.limits['max_retries']}")

    def snapshot(self) -> dict:
        return {
            "calls": self.calls,
            "retry_count": self.retries,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "reserved_usd": self.reserved_usd,
            "cost_method": self.cost_method,
            "elapsed_ms": round(self.elapsed_ms(), 3),
        }

    def _check_time(self) -> None:
        if self.elapsed_ms() / 1000 > self.limits["max_seconds"]:
            raise BudgetExceeded(f"elapsed {self.elapsed_ms()} ms exceeds {self.limits['max_seconds']} s")

    def _check_counts(self) -> None:
        if self.calls > self.limits["max_provider_calls"]:
            raise BudgetExceeded(f"provider calls {self.calls} exceed {self.limits['max_provider_calls']}")
        if self.input_tokens is not None and self.input_tokens > self.limits["max_input_tokens"]:
            raise BudgetExceeded(f"input_tokens {self.input_tokens} exceed {self.limits['max_input_tokens']}")
        if self.output_tokens is not None and self.output_tokens > self.limits["max_output_tokens"]:
            raise BudgetExceeded(f"output_tokens {self.output_tokens} exceed {self.limits['max_output_tokens']}")
        if self.estimated_cost_usd is not None and self.estimated_cost_usd > self.limits["max_usd"]:
            raise BudgetExceeded(f"estimated cost {self.estimated_cost_usd} exceeds {self.limits['max_usd']}")


def _add_optional(current, delta):
    if delta is None:
        return current
    if current is None:
        return delta
    return current + delta

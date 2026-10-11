"""HTTP provider adapter. Credentials come from the environment and are never logged.

No live request is made unless complete() is called with a configured key and no injected transport.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

from factory.limits import DEFAULT_LIMITS
from factory.security import redact
from factory.validate import load_schema, validate


class HttpProvider:
    name = "http"

    def __init__(
        self,
        env_var: str = "PROVIDER_API_KEY",
        model: str = "unspecified",
        transport=None,
        endpoint: str = "https://api.example.invalid/v1/chat",
        timeout: float = 20,
        approve_unknown_cost: bool = False,
    ):
        self.env_var = env_var
        self.model = model
        self.transport = transport
        self.endpoint = endpoint
        self.timeout = timeout
        self.approve_unknown_cost = approve_unknown_cost
        self.calls = 0
        self.retries = 0
        self.input_tokens = None
        self.output_tokens = None
        self.live = False
        self.guard = None

    def configured(self) -> bool:
        return bool(os.environ.get(self.env_var))

    def will_spend(self) -> bool:
        return self.transport is None and self.configured()

    def complete(self, role: str, payload: dict) -> dict:
        key = os.environ.get(self.env_var)
        if not key and self.transport is None:
            raise RuntimeError(f"{self.env_var} is not set")
        body = {"role": role, "model": self.model, "payload": payload}
        last_error = "no attempt"
        max_retries = DEFAULT_LIMITS["max_retries"]
        if self.guard is not None:
            max_retries = self.guard.limits["max_retries"]
        for attempt in range(max_retries + 1):
            if self.guard is not None:
                self.guard.before_call(
                    will_spend=self.will_spend(),
                    cost_known=False,
                    approve_unknown_cost=self.approve_unknown_cost,
                )
            self.calls += 1
            try:
                raw = self._post(body, key or "")
                self.live = self.transport is None
                parsed = raw if isinstance(raw, dict) else json.loads(raw)
                schema_name = {
                    "architect": "workflow.schema.json",
                    "scout": "scout_report.schema.json",
                    "verifier": "verdict.schema.json",
                }[role]
                errors = validate(parsed, load_schema(schema_name))
                if errors:
                    raise ValueError("invalid output: " + "; ".join(errors))
                usage = parsed.pop("_usage", None)
                if isinstance(usage, dict):
                    self.input_tokens = usage.get("input_tokens")
                    self.output_tokens = usage.get("output_tokens")
                if self.guard is not None:
                    self.guard.after_call({
                        "input_tokens": None if not isinstance(usage, dict) else usage.get("input_tokens"),
                        "output_tokens": None if not isinstance(usage, dict) else usage.get("output_tokens"),
                        "estimated_cost_usd": None if not isinstance(usage, dict) else usage.get("estimated_cost_usd"),
                    })
                return parsed
            except Exception as exc:
                last_error = redact(str(exc))
                if attempt >= max_retries:
                    break
                self.retries += 1
                if self.guard is not None:
                    self.guard.note_retry()
                time.sleep(0.01 * (attempt + 1))
        raise RuntimeError(f"provider failed after retries: {last_error}")

    def _post(self, body: dict, key: str):
        if self.transport is not None:
            return self.transport(body)
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(body).encode(),
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode())
        except urllib.error.URLError as exc:
            raise TimeoutError(redact(str(exc.reason))) from None

    def usage(self) -> dict:
        return {
            "provider": self.name,
            "model": self.model,
            "live": self.live,
            "calls": self.calls,
            "retry_count": self.retries,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "available": self.input_tokens is not None or self.output_tokens is not None,
            "estimation_method": "provider usage field" if self.input_tokens is not None else "unavailable — provider did not supply token counts",
            "estimated_cost_usd": None,
        }

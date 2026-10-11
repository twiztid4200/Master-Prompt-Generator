"""HTTP provider adapter. Credentials come from the environment and are never logged.

No live request is made unless complete() is called with a configured key.
Tests inject a transport so the adapter can be exercised without a network call.
"""

from __future__ import annotations

import json
import os
import time
import urllib.request

from factory.limits import DEFAULT_LIMITS
from factory.security import redact
from factory.validate import load_schema, validate


class HttpProvider:
    name = "http"

    def __init__(self, env_var: str = "PROVIDER_API_KEY", model: str = "unspecified", transport=None, endpoint: str = "https://api.example.invalid/v1/chat"):
        self.env_var = env_var
        self.model = model
        self.transport = transport
        self.endpoint = endpoint
        self.calls = 0
        self.retries = 0
        self.input_tokens = None
        self.output_tokens = None
        self.live = False

    def configured(self) -> bool:
        return bool(os.environ.get(self.env_var))

    def complete(self, role: str, payload: dict) -> dict:
        key = os.environ.get(self.env_var)
        if not key and self.transport is None:
            raise RuntimeError(f"{self.env_var} is not set")
        body = {"role": role, "model": self.model, "payload": payload}
        last_error = "no attempt"
        for attempt in range(DEFAULT_LIMITS["max_retries"] + 1):
            self.calls += 1
            try:
                raw = self._post(body, key or "")
                self.live = self.transport is None
                parsed = raw if isinstance(raw, dict) else json.loads(raw)
                schema_name = {"architect": "workflow.schema.json", "scout": "scout_report.schema.json", "verifier": "verdict.schema.json"}[role]
                errors = validate(parsed, load_schema(schema_name))
                if errors:
                    raise ValueError("invalid output: " + "; ".join(errors))
                usage = parsed.pop("_usage", None)
                if isinstance(usage, dict):
                    self.input_tokens = usage.get("input_tokens")
                    self.output_tokens = usage.get("output_tokens")
                return parsed
            except Exception as exc:
                last_error = redact(str(exc))
                self.retries += 1
                if attempt >= DEFAULT_LIMITS["max_retries"]:
                    break
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
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode())

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

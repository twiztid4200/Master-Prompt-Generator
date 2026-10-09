"""Provider seam. Implementations must not invent usage numbers."""

from __future__ import annotations

from typing import Protocol


class Provider(Protocol):
    name: str

    def complete(self, role: str, payload: dict) -> dict:
        """Return structured JSON for a role. Do not report tokens you did not receive."""

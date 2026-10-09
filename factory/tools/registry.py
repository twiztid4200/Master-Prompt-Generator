"""Minimal tool adapter. Native functions now; CLI and MCP can register later."""

from __future__ import annotations

from typing import Callable


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, dict] = {}

    def register(self, declaration: dict, handler: Callable) -> None:
        self._tools[declaration["name"]] = {"declaration": declaration, "handler": handler}

    def declaration(self, name: str) -> dict:
        return self._tools[name]["declaration"]

    def call(self, name: str, payload: dict) -> dict:
        tool = self._tools[name]
        if tool["declaration"]["executes_code"]:
            raise PermissionError(f"{name} is not allowed to execute code in this runtime")
        return tool["handler"](payload)

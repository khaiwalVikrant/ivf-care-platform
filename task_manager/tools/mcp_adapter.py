"""MCP Tool Adapter — thin wrapper around MCP protocol calls with timeout enforcement."""

from __future__ import annotations

import asyncio
from typing import Any


class MCPError(Exception):
    """Raised when an MCP tool call fails."""

    def __init__(self, tool_name: str, detail: str) -> None:
        super().__init__(detail)
        self.tool_name = tool_name
        self.detail = detail


class MCPToolAdapter:
    """Thin adapter wrapping MCP protocol calls with a 10-second timeout.

    This is a stub implementation that returns a success payload for any call.
    Concrete sub-classes (AppointmentMCP, PathologyMCP, etc.) override _invoke.
    """

    async def _invoke(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Inner call — override in concrete adapters.  Default stub returns ok."""
        return {"status": "ok", "tool_name": tool_name, "params": params}

    async def call(self, tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
        """Call an MCP tool.

        Wraps the call in a 10-second timeout.  Returns a structured error dict
        on timeout or any other exception rather than raising, so callers can
        inspect the result uniformly.
        """
        try:
            result = await asyncio.wait_for(
                self._invoke(tool_name, params),
                timeout=10.0,
            )
            return result
        except asyncio.TimeoutError:
            return {
                "error_code": "TOOL_TIMEOUT",
                "tool_name": tool_name,
                "detail": f"MCP tool '{tool_name}' did not respond within 10 seconds",
            }
        except MCPError as exc:
            return {
                "error_code": "MCP_ERROR",
                "tool_name": exc.tool_name,
                "detail": exc.detail,
            }
        except Exception as exc:  # noqa: BLE001
            return {
                "error_code": "MCP_ERROR",
                "tool_name": tool_name,
                "detail": str(exc),
            }


# ---------------------------------------------------------------------------
# Concrete adapters (stubs — override _invoke for real MCP integration)
# ---------------------------------------------------------------------------


class AppointmentMCP(MCPToolAdapter):
    """MCP adapter for appointment-related tools."""


class PathologyMCP(MCPToolAdapter):
    """MCP adapter for pathology-related tools."""


class NotificationMCP(MCPToolAdapter):
    """MCP adapter for notification delivery tools."""


class PharmacyPriceMCP(MCPToolAdapter):
    """MCP adapter for pharmacy price lookup tools."""


class TaskMCP(MCPToolAdapter):
    """MCP adapter for task management tools."""


class CalMCP(MCPToolAdapter):
    """MCP adapter for calendar tools."""


class NotesMCP(MCPToolAdapter):
    """MCP adapter for notes tools."""

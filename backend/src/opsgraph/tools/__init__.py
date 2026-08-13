"""Typed, permission-scoped tools exposed to specialist agents."""

from opsgraph.tools.registry import ToolPermissionDenied, ToolRegistry

__all__ = ["ToolPermissionDenied", "ToolRegistry"]

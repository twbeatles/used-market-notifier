"""Cleanup/export persistence extension point."""

from .database import DatabaseManager

__all__ = ["DatabaseManager"]

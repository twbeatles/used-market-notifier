"""Path-traversal guards for backup ZIP entries."""

from pathlib import Path


def safe_member_basename(name: str) -> str | None:
    """Allow only plain basenames (reject absolute paths and ``..``)."""
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        return None
    basename = path.name
    return basename if basename and basename == name else None


def is_relative_to(child: Path, parent: Path) -> bool:
    """``Path.is_relative_to`` backport for older runtimes."""
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False


__all__ = ["safe_member_basename", "is_relative_to"]

"""Human-readable byte-size formatting."""


def format_size(size_bytes: int) -> str:
    """Format byte size to human readable string"""
    size_value = float(size_bytes)
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_value < 1024:
            return f"{size_value:.1f} {unit}"
        size_value /= 1024
    return f"{size_value:.1f} TB"


__all__ = ["format_size"]

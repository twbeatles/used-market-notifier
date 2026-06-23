"""Async retry decorator for Playwright scrapers."""

import asyncio
import functools
from typing import TypeVar

T = TypeVar("T")


def async_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Async retry decorator with exponential backoff and logging"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            last_exception: Exception | None = None
            current_delay = delay
            for attempt in range(max_attempts):
                try:
                    return await func(self, *args, **kwargs)
                except Exception as e:
                    last_exception = e
                    self.logger.warning(
                        f"Attempt {attempt + 1}/{max_attempts} failed: {type(e).__name__}: {e}"
                    )
                    if attempt < max_attempts - 1:
                        self.logger.info(f"Retrying in {current_delay:.1f}s...")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff

            # All attempts failed
            self.logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            if last_exception is not None:
                raise last_exception
            raise RuntimeError(f"{func.__name__} failed without capturing an exception")
        return wrapper
    return decorator
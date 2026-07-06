"""
IOB Phase 3 - Shared Utility Helpers
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Union


def utcnow_iso() -> str:
    """
    Return the current UTC instant as an ISO-8601 string suffixed with 'Z'
    (e.g. 2026-07-02T07:49:00Z). Avoids the deprecated ``datetime.utcnow()``.
    """
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clamp(value: Union[int, float], low: Union[int, float], high: Union[int, float]) -> Union[int, float]:
    """Bound ``value`` within the inclusive ``[low, high]`` range."""
    return max(low, min(high, value))


def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    """
    Configure root IOB logging. Streams to stdout and, optionally, to a file
    under the ``logs/`` directory for audit tracing.
    """
    handlers: list = []
    try:
        from logging import StreamHandler

        handlers.append(StreamHandler())
        if log_file:
            from logging import FileHandler

            handlers.append(FileHandler(log_file, encoding="utf-8"))
    except Exception:
        pass

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers or None,
        force=True,
    )

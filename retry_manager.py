"""
Retry Manager for OT Edge Transient Failure Recovery.
Standard Compliance: Exponential backoff for network/storage resilience.
Section 4 Implementation.
"""

import time
import functools
import logging
from typing import Callable, Any, Union, Type, Tuple

logger = logging.getLogger("iob.retry")


class ExponentialBackoffRetryManager:
    """Handles transient infrastructure failovers using exponential backoff retry sequences."""
    def __init__(self, max_retries: int = 3, base_delay_sec: float = 1.0, base_delay: float = None, exceptions: Any = Exception):
        self.max_retries = max_retries
        self.base_delay = base_delay if base_delay is not None else base_delay_sec
        self.exceptions = exceptions

    def execute_with_retry(self, operational_function: Callable[[], Any]) -> Any:
        retries = 0
        delay = self.base_delay

        while retries < self.max_retries:
            try:
                return operational_function()
            except self.exceptions as ex:
                retries += 1
                if retries >= self.max_retries:
                    logger.critical(f"Retry ceiling reached. Strategy loop exhausted: {str(ex)}")
                    raise ex
                logger.warning(f"Transient dependency failure error (Attempt {retries}/{self.max_retries}). Retrying in {delay}s...")
                time.sleep(delay)
                delay *= 2.0

    def execute(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        return self.execute_with_retry(lambda: func(*args, **kwargs))


# Backwards compatibility alias
RetryManager = ExponentialBackoffRetryManager


def retry_on_failure(
    max_retries: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 10.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
):
    """Decorator for wrapping methods or functions with ExponentialBackoffRetryManager."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            manager = ExponentialBackoffRetryManager(max_retries=max_retries, base_delay_sec=base_delay, exceptions=exceptions)
            return manager.execute(func, *args, **kwargs)
        return wrapper
    return decorator

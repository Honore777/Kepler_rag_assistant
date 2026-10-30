"""Retry helpers.

For production-grade stability, network calls should be retried with exponential
backoff and jitter. We use tenacity as a small, battle-tested library.
"""

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
    retry_if_exception_type,
)


class RetryableServiceError(Exception):
    """Use for transient upstream failures that should be retried."""


def with_retries(
    max_attempts: int = 3,
    min_wait_s: float = 0.25,
    max_wait_s: float = 4.0,
    retry_on=(RetryableServiceError, TimeoutError, ConnectionError, OSError),
):
    """Decorator for transient failures with exponential backoff + jitter.

    Keep retry_on narrow so permanent coding/data errors fail fast.
    """

    return retry(
        reraise=True,
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential_jitter(initial=min_wait_s, max=max_wait_s),
        retry=retry_if_exception_type(retry_on),
    )

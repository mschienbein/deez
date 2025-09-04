"""
Retry logic for SoundCloud API requests.
"""

import asyncio
import logging
import random
from typing import TypeVar, Callable, Optional, Any, Union, Tuple
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def retry_with_backoff(
    func: Callable[..., T],
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[type, ...] = (Exception,),
    on_retry: Optional[Callable[[int, Exception], None]] = None
) -> T:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay between retries (seconds)
        max_delay: Maximum delay between retries (seconds)
        backoff_factor: Multiplier for delay after each retry
        jitter: Add random jitter to delays
        exceptions: Tuple of exceptions to retry on
        on_retry: Optional callback on retry (attempt, exception)
        
    Returns:
        Function result
        
    Raises:
        Last exception if all attempts fail
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            
            if attempt == max_attempts:
                logger.error(f"Max retry attempts ({max_attempts}) reached")
                raise
            
            # Calculate next delay
            if jitter:
                actual_delay = delay * (0.5 + random.random())
            else:
                actual_delay = delay
            
            actual_delay = min(actual_delay, max_delay)
            
            logger.debug(
                f"Retry attempt {attempt}/{max_attempts} after {actual_delay:.2f}s "
                f"due to {type(e).__name__}: {e}"
            )
            
            # Call retry callback if provided
            if on_retry:
                on_retry(attempt, e)
            
            # Wait before retry
            await asyncio.sleep(actual_delay)
            
            # Increase delay for next iteration
            delay *= backoff_factor
    
    raise last_exception


def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[type, ...] = (Exception,)
):
    """
    Decorator for retrying async functions.
    
    Args:
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay between retries
        max_delay: Maximum delay between retries
        backoff_factor: Multiplier for delay after each retry
        jitter: Add random jitter to delays
        exceptions: Tuple of exceptions to retry on
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async def _func():
                return await func(*args, **kwargs)
            
            return await retry_with_backoff(
                _func,
                max_attempts=max_attempts,
                initial_delay=initial_delay,
                max_delay=max_delay,
                backoff_factor=backoff_factor,
                jitter=jitter,
                exceptions=exceptions
            )
        
        return wrapper
    
    return decorator


class RetryPolicy:
    """Configurable retry policy."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize retry policy.
        
        Args:
            max_attempts: Maximum number of attempts
            initial_delay: Initial delay between retries
            max_delay: Maximum delay between retries
            backoff_factor: Multiplier for delay after each retry
            jitter: Add random jitter to delays
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
    
    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """
        Check if request should be retried.
        
        Args:
            attempt: Current attempt number
            exception: Exception that occurred
            
        Returns:
            True if should retry
        """
        if attempt >= self.max_attempts:
            return False
        
        # Check for specific non-retryable errors
        if self._is_non_retryable(exception):
            return False
        
        return True
    
    def get_delay(self, attempt: int) -> float:
        """
        Get delay before next retry.
        
        Args:
            attempt: Current attempt number
            
        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.backoff_factor ** (attempt - 1))
        
        if self.jitter:
            delay *= (0.5 + random.random())
        
        return min(delay, self.max_delay)
    
    def _is_non_retryable(self, exception: Exception) -> bool:
        """Check if exception is non-retryable."""
        # Import here to avoid circular dependency
        from ..exceptions import (
            AuthenticationError,
            NotFoundError,
            ForbiddenError,
            InvalidRequestError,
        )
        
        # These errors shouldn't be retried
        non_retryable_types = (
            AuthenticationError,
            NotFoundError,
            ForbiddenError,
            InvalidRequestError,
        )
        
        return isinstance(exception, non_retryable_types)
    
    async def execute(
        self,
        func: Callable[..., T],
        on_retry: Optional[Callable[[int, Exception], None]] = None
    ) -> T:
        """
        Execute function with retry policy.
        
        Args:
            func: Async function to execute
            on_retry: Optional callback on retry
            
        Returns:
            Function result
        """
        return await retry_with_backoff(
            func,
            max_attempts=self.max_attempts,
            initial_delay=self.initial_delay,
            max_delay=self.max_delay,
            backoff_factor=self.backoff_factor,
            jitter=self.jitter,
            on_retry=on_retry
        )


class AdaptiveRetryPolicy(RetryPolicy):
    """Adaptive retry policy that adjusts based on error patterns."""
    
    def __init__(self, **kwargs):
        """Initialize adaptive retry policy."""
        super().__init__(**kwargs)
        
        # Track error patterns
        self.consecutive_failures = 0
        self.total_failures = 0
        self.total_successes = 0
        
        # Adaptive parameters
        self.min_attempts = 1
        self.max_attempts_limit = 5
    
    def record_success(self):
        """Record successful request."""
        self.consecutive_failures = 0
        self.total_successes += 1
        
        # Reduce retry attempts if consistently successful
        if self.total_successes > 10 and self.total_failures == 0:
            self.max_attempts = max(self.min_attempts, self.max_attempts - 1)
    
    def record_failure(self):
        """Record failed request."""
        self.consecutive_failures += 1
        self.total_failures += 1
        
        # Increase retry attempts if seeing failures
        if self.consecutive_failures > 2:
            self.max_attempts = min(
                self.max_attempts_limit,
                self.max_attempts + 1
            )
    
    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """Check if should retry with adaptive logic."""
        # Use base logic first
        if not super().should_retry(attempt, exception):
            return False
        
        # Additional adaptive checks
        if self.consecutive_failures > 10:
            # Too many consecutive failures, likely a persistent issue
            logger.warning("Too many consecutive failures, not retrying")
            return False
        
        return True
    
    def get_delay(self, attempt: int) -> float:
        """Get adaptive delay."""
        base_delay = super().get_delay(attempt)
        
        # Increase delay if seeing many failures
        if self.consecutive_failures > 3:
            base_delay *= 1.5
        
        return base_delay


def is_retryable_error(error: Exception) -> bool:
    """
    Check if an error is retryable.
    
    Args:
        error: Exception to check
        
    Returns:
        True if error is retryable
    """
    # Import here to avoid circular dependency
    from ..exceptions import (
        RateLimitError,
        ServerError,
        NetworkError,
        TemporaryError,
    )
    
    # These errors are generally retryable
    retryable_types = (
        RateLimitError,
        ServerError,
        NetworkError,
        TemporaryError,
        asyncio.TimeoutError,
        ConnectionError,
    )
    
    return isinstance(error, retryable_types)


__all__ = [
    "retry_with_backoff",
    "with_retry",
    "RetryPolicy",
    "AdaptiveRetryPolicy",
    "is_retryable_error",
]
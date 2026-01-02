"""
Retry Logic with Exponential Backoff
"""

import asyncio
import random
from typing import Any, Callable, Optional
from structlog import get_logger

logger = get_logger(__name__)


class RetryPolicy:
    """Retry policy configuration."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt."""
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay


async def retry_async(
    func: Callable,
    *args: Any,
    policy: Optional[RetryPolicy] = None,
    retry_on: Optional[tuple] = None,
    **kwargs: Any,
) -> Any:
    """Retry an async function with exponential backoff."""
    if policy is None:
        policy = RetryPolicy()
    
    if retry_on is None:
        retry_on = (Exception,)
    
    last_exception = None
    
    for attempt in range(policy.max_attempts):
        try:
            logger.debug("retry_attempt", attempt=attempt + 1, func=func.__name__)
            result = await func(*args, **kwargs)
            
            if attempt > 0:
                logger.info("retry_succeeded", attempt=attempt + 1, func=func.__name__)
            
            return result
            
        except retry_on as e:
            last_exception = e
            logger.warning("retry_attempt_failed", attempt=attempt + 1, error=str(e))
            
            if attempt < policy.max_attempts - 1:
                delay = policy.get_delay(attempt)
                logger.debug("retry_waiting", delay=delay)
                await asyncio.sleep(delay)
    
    logger.error("retry_exhausted", attempts=policy.max_attempts)
    raise last_exception

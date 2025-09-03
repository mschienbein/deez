"""
Request handler with timeout and retry logic for Graphiti operations
"""

import asyncio
import logging

logger = logging.getLogger(__name__)


class RequestHandler:
    """Handle API requests with timeout and retry logic"""
    
    @staticmethod
    async def with_timeout(coro, timeout_seconds: int = 30):
        """
        Execute coroutine with timeout.
        """
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            logger.error(f"Request timed out after {timeout_seconds} seconds")
            return None
    
    @staticmethod
    async def with_retry(coro_factory, max_retries: int = 3, backoff: float = 1.0):
        """
        Retry a coroutine with exponential backoff.
        coro_factory should be a function that returns a new coroutine.
        """
        for attempt in range(max_retries):
            try:
                return await coro_factory()
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                wait_time = backoff * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
        
        return None
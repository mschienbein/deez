"""
Rate limiting for SoundCloud API requests.
"""

import asyncio
import time
from typing import Optional, Dict, Any
from collections import deque
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API requests."""
    
    def __init__(
        self,
        max_requests: int = 15,
        time_window: int = 1,
        burst_size: Optional[int] = None
    ):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per time window
            time_window: Time window in seconds
            burst_size: Maximum burst size (defaults to max_requests)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.burst_size = burst_size or max_requests
        
        # Request timestamps
        self.requests = deque(maxlen=max_requests)
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """
        Acquire permission to make a request.
        
        Blocks if rate limit would be exceeded.
        """
        async with self._lock:
            now = time.time()
            
            # Remove old requests outside the time window
            while self.requests and self.requests[0] <= now - self.time_window:
                self.requests.popleft()
            
            # Check if we need to wait
            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest = self.requests[0]
                wait_time = (oldest + self.time_window) - now
                
                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.2f}s")
                    await asyncio.sleep(wait_time)
                    
                    # Clean up again after waiting
                    now = time.time()
                    while self.requests and self.requests[0] <= now - self.time_window:
                        self.requests.popleft()
            
            # Record this request
            self.requests.append(now)
    
    def reset(self):
        """Reset the rate limiter."""
        self.requests.clear()
    
    @property
    def remaining(self) -> int:
        """Get remaining requests in current window."""
        now = time.time()
        
        # Remove old requests
        while self.requests and self.requests[0] <= now - self.time_window:
            self.requests.popleft()
        
        return max(0, self.max_requests - len(self.requests))
    
    @property
    def next_reset(self) -> float:
        """Get time until next rate limit reset."""
        if not self.requests:
            return 0
        
        oldest = self.requests[0]
        return max(0, (oldest + self.time_window) - time.time())


class AdaptiveRateLimiter(RateLimiter):
    """Adaptive rate limiter that adjusts based on API responses."""
    
    def __init__(
        self,
        initial_rate: int = 15,
        time_window: int = 1,
        min_rate: int = 5,
        max_rate: int = 50
    ):
        """
        Initialize adaptive rate limiter.
        
        Args:
            initial_rate: Initial requests per window
            time_window: Time window in seconds
            min_rate: Minimum requests per window
            max_rate: Maximum requests per window
        """
        super().__init__(initial_rate, time_window)
        
        self.min_rate = min_rate
        self.max_rate = max_rate
        self.initial_rate = initial_rate
        
        # Tracking for adaptation
        self.success_count = 0
        self.error_count = 0
        self.last_adjustment = time.time()
        self.adjustment_interval = 60  # Adjust every minute
    
    def record_success(self):
        """Record a successful request."""
        self.success_count += 1
        self._maybe_adjust()
    
    def record_error(self, is_rate_limit: bool = False):
        """
        Record an error response.
        
        Args:
            is_rate_limit: Whether error was due to rate limiting
        """
        self.error_count += 1
        
        if is_rate_limit:
            # Immediately reduce rate
            self._decrease_rate()
        
        self._maybe_adjust()
    
    def _maybe_adjust(self):
        """Check if rate should be adjusted."""
        now = time.time()
        
        if now - self.last_adjustment < self.adjustment_interval:
            return
        
        total_requests = self.success_count + self.error_count
        if total_requests < 10:
            return  # Not enough data
        
        error_rate = self.error_count / total_requests
        
        if error_rate < 0.01:  # < 1% errors
            self._increase_rate()
        elif error_rate > 0.05:  # > 5% errors
            self._decrease_rate()
        
        # Reset counters
        self.success_count = 0
        self.error_count = 0
        self.last_adjustment = now
    
    def _increase_rate(self):
        """Increase the rate limit."""
        new_rate = min(self.max_rate, int(self.max_requests * 1.2))
        
        if new_rate > self.max_requests:
            logger.info(f"Increasing rate limit: {self.max_requests} -> {new_rate}")
            self.max_requests = new_rate
            self.requests = deque(maxlen=new_rate)
    
    def _decrease_rate(self):
        """Decrease the rate limit."""
        new_rate = max(self.min_rate, int(self.max_requests * 0.8))
        
        if new_rate < self.max_requests:
            logger.info(f"Decreasing rate limit: {self.max_requests} -> {new_rate}")
            self.max_requests = new_rate
            self.requests = deque(maxlen=new_rate)
    
    def reset(self):
        """Reset the rate limiter to initial state."""
        super().reset()
        self.max_requests = self.initial_rate
        self.requests = deque(maxlen=self.initial_rate)
        self.success_count = 0
        self.error_count = 0


class EndpointRateLimiter:
    """Rate limiter with per-endpoint limits."""
    
    def __init__(self, default_rate: int = 15, time_window: int = 1):
        """
        Initialize endpoint rate limiter.
        
        Args:
            default_rate: Default requests per window
            time_window: Time window in seconds
        """
        self.default_rate = default_rate
        self.time_window = time_window
        
        # Per-endpoint limiters
        self.limiters: Dict[str, RateLimiter] = {}
        
        # Endpoint-specific rates
        self.endpoint_rates = {
            "/tracks": 20,
            "/users": 20,
            "/playlists": 20,
            "/search": 10,
            "/stream": 5,
            "/me": 10,
        }
    
    async def acquire(self, endpoint: str):
        """
        Acquire permission for an endpoint.
        
        Args:
            endpoint: API endpoint path
        """
        # Normalize endpoint
        endpoint = self._normalize_endpoint(endpoint)
        
        # Get or create limiter for endpoint
        if endpoint not in self.limiters:
            rate = self.endpoint_rates.get(endpoint, self.default_rate)
            self.limiters[endpoint] = RateLimiter(rate, self.time_window)
        
        await self.limiters[endpoint].acquire()
    
    def _normalize_endpoint(self, endpoint: str) -> str:
        """Normalize endpoint for rate limiting."""
        # Remove query parameters
        if "?" in endpoint:
            endpoint = endpoint.split("?")[0]
        
        # Remove trailing slash
        endpoint = endpoint.rstrip("/")
        
        # Group similar endpoints
        if endpoint.startswith("/tracks/"):
            parts = endpoint.split("/")
            if len(parts) > 3:
                # /tracks/123/comments -> /tracks/*/comments
                return f"/tracks/*/{parts[3]}"
            else:
                # /tracks/123 -> /tracks/*
                return "/tracks/*"
        elif endpoint.startswith("/users/"):
            parts = endpoint.split("/")
            if len(parts) > 3:
                return f"/users/*/{parts[3]}"
            else:
                return "/users/*"
        elif endpoint.startswith("/playlists/"):
            return "/playlists/*"
        
        return endpoint
    
    def reset(self, endpoint: Optional[str] = None):
        """
        Reset rate limiter(s).
        
        Args:
            endpoint: Specific endpoint to reset (None = all)
        """
        if endpoint:
            endpoint = self._normalize_endpoint(endpoint)
            if endpoint in self.limiters:
                self.limiters[endpoint].reset()
        else:
            for limiter in self.limiters.values():
                limiter.reset()


__all__ = [
    "RateLimiter",
    "AdaptiveRateLimiter",
    "EndpointRateLimiter",
]
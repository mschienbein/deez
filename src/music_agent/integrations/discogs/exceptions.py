"""
Custom exceptions for Discogs API integration.
"""


class DiscogsError(Exception):
    """Base exception for Discogs integration."""
    pass


class AuthenticationError(DiscogsError):
    """Authentication failed."""
    pass


class APIError(DiscogsError):
    """API request failed."""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class RateLimitError(DiscogsError):
    """Rate limit exceeded."""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class NotFoundError(DiscogsError):
    """Resource not found."""
    pass


class ValidationError(DiscogsError):
    """Data validation failed."""
    pass


class NetworkError(DiscogsError):
    """Network connection failed."""
    pass
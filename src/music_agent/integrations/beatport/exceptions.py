"""
Beatport integration exceptions.
"""


class BeatportError(Exception):
    """Base exception for Beatport integration."""
    pass


class AuthenticationError(BeatportError):
    """Raised when authentication fails."""
    pass


class APIError(BeatportError):
    """Raised when API requests fail."""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class RateLimitError(BeatportError):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class TokenExpiredError(AuthenticationError):
    """Raised when the access token has expired."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when username/password is invalid."""
    pass
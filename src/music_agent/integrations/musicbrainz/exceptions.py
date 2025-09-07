"""
MusicBrainz API exceptions.
"""


class MusicBrainzError(Exception):
    """Base exception for MusicBrainz API errors."""
    pass


class AuthenticationError(MusicBrainzError):
    """Authentication failed."""
    pass


class APIError(MusicBrainzError):
    """API request failed."""
    
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class RateLimitError(MusicBrainzError):
    """Rate limit exceeded."""
    
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class NotFoundError(MusicBrainzError):
    """Resource not found."""
    pass


class NetworkError(MusicBrainzError):
    """Network connection error."""
    pass


class InvalidQueryError(MusicBrainzError):
    """Invalid search query."""
    pass
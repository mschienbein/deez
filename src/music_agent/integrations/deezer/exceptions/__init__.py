"""
Deezer integration exceptions.
"""


class DeezerError(Exception):
    """Base exception for Deezer integration."""
    pass


class AuthenticationError(DeezerError):
    """Authentication failed."""
    pass


class InvalidARLError(AuthenticationError):
    """ARL token is invalid or expired."""
    pass


class SessionExpiredError(AuthenticationError):
    """Session has expired."""
    pass


class APIError(DeezerError):
    """API request failed."""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class NotFoundError(APIError):
    """Resource not found."""
    pass


class RateLimitError(APIError):
    """Rate limit exceeded."""
    pass


class DownloadError(DeezerError):
    """Download failed."""
    pass


class DecryptionError(DownloadError):
    """Failed to decrypt stream."""
    pass


class QualityNotAvailableError(DownloadError):
    """Requested quality not available."""
    pass


class GeoBlockedError(DeezerError):
    """Content is geo-blocked."""
    pass


class SubscriptionRequiredError(DeezerError):
    """Premium subscription required for this feature."""
    pass


__all__ = [
    "DeezerError",
    "AuthenticationError",
    "InvalidARLError",
    "SessionExpiredError",
    "APIError",
    "NotFoundError",
    "RateLimitError",
    "DownloadError",
    "DecryptionError",
    "QualityNotAvailableError",
    "GeoBlockedError",
    "SubscriptionRequiredError",
]
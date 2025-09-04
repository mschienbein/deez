"""
Custom exceptions for SoundCloud integration.

Provides detailed error types for better error handling
and debugging.
"""

from typing import Optional, Dict, Any


class SoundCloudException(Exception):
    """Base exception for all SoundCloud-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class AuthenticationError(SoundCloudException):
    """Raised when authentication fails."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when credentials are invalid."""
    pass


class TokenExpiredError(AuthenticationError):
    """Raised when access token has expired."""
    pass


class ClientIDError(AuthenticationError):
    """Raised when client ID is invalid or expired."""
    pass


class RateLimitError(SoundCloudException):
    """Raised when API rate limit is exceeded."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class ResourceNotFoundError(SoundCloudException):
    """Raised when a requested resource doesn't exist."""
    pass


class TrackNotFoundError(ResourceNotFoundError):
    """Raised when a track is not found."""
    pass


class PlaylistNotFoundError(ResourceNotFoundError):
    """Raised when a playlist is not found."""
    pass


class UserNotFoundError(ResourceNotFoundError):
    """Raised when a user is not found."""
    pass


class DownloadError(SoundCloudException):
    """Base class for download-related errors."""
    pass


class TrackNotDownloadableError(DownloadError):
    """Raised when a track is not marked as downloadable."""
    pass


class StreamNotAvailableError(DownloadError):
    """Raised when stream URL cannot be obtained."""
    pass


class HLSStreamError(DownloadError):
    """Raised when HLS stream assembly fails."""
    pass


class MetadataError(DownloadError):
    """Raised when metadata writing fails."""
    pass


class ValidationError(SoundCloudException):
    """Raised when input validation fails."""
    pass


class InvalidURLError(ValidationError):
    """Raised when a SoundCloud URL is invalid."""
    pass


class InvalidParameterError(ValidationError):
    """Raised when a parameter is invalid."""
    pass


class NetworkError(SoundCloudException):
    """Raised when network operations fail."""
    pass


class TimeoutError(NetworkError):
    """Raised when a request times out."""
    pass


class ConnectionError(NetworkError):
    """Raised when connection fails."""
    pass


class ScrapingError(SoundCloudException):
    """Raised when client ID scraping fails."""
    pass


class CacheError(SoundCloudException):
    """Raised when cache operations fail."""
    pass


class UploadError(SoundCloudException):
    """Raised when track upload fails."""
    pass


class PermissionError(SoundCloudException):
    """Raised when user lacks permission for an action."""
    pass


__all__ = [
    # Base
    "SoundCloudException",
    # Authentication
    "AuthenticationError",
    "InvalidCredentialsError",
    "TokenExpiredError",
    "ClientIDError",
    # Rate limiting
    "RateLimitError",
    # Resources
    "ResourceNotFoundError",
    "TrackNotFoundError",
    "PlaylistNotFoundError",
    "UserNotFoundError",
    # Downloads
    "DownloadError",
    "TrackNotDownloadableError",
    "StreamNotAvailableError",
    "HLSStreamError",
    "MetadataError",
    # Validation
    "ValidationError",
    "InvalidURLError",
    "InvalidParameterError",
    # Network
    "NetworkError",
    "TimeoutError",
    "ConnectionError",
    # Other
    "ScrapingError",
    "CacheError",
    "UploadError",
    "PermissionError",
]
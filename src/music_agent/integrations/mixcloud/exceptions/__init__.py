"""
Exception hierarchy for Mixcloud integration.

Provides specific exceptions for different error scenarios.
"""


class MixcloudError(Exception):
    """Base exception for Mixcloud integration."""
    pass


# ============================================
# Authentication Exceptions
# ============================================

class AuthenticationError(MixcloudError):
    """Authentication failed."""
    pass


class TokenExpiredError(AuthenticationError):
    """Access token has expired."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid client credentials."""
    pass


class OAuthError(AuthenticationError):
    """OAuth flow error."""
    pass


# ============================================
# API Exceptions
# ============================================

class APIError(MixcloudError):
    """API request failed."""
    pass


class NotFoundError(APIError):
    """Resource not found (404)."""
    pass


class ForbiddenError(APIError):
    """Access forbidden (403)."""
    pass


class RateLimitError(APIError):
    """Rate limit exceeded."""
    pass


class ServerError(APIError):
    """Server error (5xx)."""
    pass


class InvalidRequestError(APIError):
    """Invalid request parameters."""
    pass


# ============================================
# Download Exceptions
# ============================================

class DownloadError(MixcloudError):
    """Download failed."""
    pass


class StreamNotAvailableError(DownloadError):
    """Stream URL not available."""
    pass


class CloudcastNotDownloadableError(DownloadError):
    """Cloudcast cannot be downloaded."""
    pass


class ExclusiveContentError(DownloadError):
    """Content is exclusive to Mixcloud Select."""
    pass


# ============================================
# Upload Exceptions
# ============================================

class UploadError(MixcloudError):
    """Upload failed."""
    pass


class InvalidFileError(UploadError):
    """Invalid file format or corrupt file."""
    pass


class FileTooLargeError(UploadError):
    """File exceeds size limit."""
    pass


class DuplicateUploadError(UploadError):
    """Duplicate cloudcast detected."""
    pass


# ============================================
# Search Exceptions
# ============================================

class SearchError(MixcloudError):
    """Search operation failed."""
    pass


class InvalidSearchQueryError(SearchError):
    """Invalid search query."""
    pass


# ============================================
# Network Exceptions
# ============================================

class NetworkError(MixcloudError):
    """Network operation failed."""
    pass


class ConnectionError(NetworkError):
    """Connection failed."""
    pass


class TimeoutError(NetworkError):
    """Request timed out."""
    pass


# ============================================
# Data Exceptions
# ============================================

class DataError(MixcloudError):
    """Data processing error."""
    pass


class InvalidDataError(DataError):
    """Invalid data format."""
    pass


class InvalidResponseError(DataError):
    """Invalid API response format."""
    pass


class MissingFieldError(DataError):
    """Required field missing from data."""
    pass


class ParseError(DataError):
    """Failed to parse response."""
    pass


# ============================================
# Cache Exceptions
# ============================================

class CacheError(MixcloudError):
    """Cache operation failed."""
    pass


# ============================================
# Live Stream Exceptions
# ============================================

class LiveStreamError(MixcloudError):
    """Live stream error."""
    pass


class StreamOfflineError(LiveStreamError):
    """Live stream is offline."""
    pass


# ============================================
# Configuration Exceptions
# ============================================

class ConfigurationError(MixcloudError):
    """Configuration error."""
    pass


class MissingConfigError(ConfigurationError):
    """Required configuration missing."""
    pass


# ============================================
# Temporary Exceptions (retryable)
# ============================================

class TemporaryError(MixcloudError):
    """Temporary error that can be retried."""
    pass


__all__ = [
    # Base
    "MixcloudError",
    
    # Authentication
    "AuthenticationError",
    "TokenExpiredError",
    "InvalidCredentialsError",
    "OAuthError",
    
    # API
    "APIError",
    "NotFoundError",
    "ForbiddenError",
    "RateLimitError",
    "ServerError",
    "InvalidRequestError",
    
    # Download
    "DownloadError",
    "StreamNotAvailableError",
    "CloudcastNotDownloadableError",
    "ExclusiveContentError",
    
    # Upload
    "UploadError",
    "InvalidFileError",
    "FileTooLargeError",
    "DuplicateUploadError",
    
    # Search
    "SearchError",
    "InvalidSearchQueryError",
    
    # Network
    "NetworkError",
    "ConnectionError",
    "TimeoutError",
    
    # Data
    "DataError",
    "InvalidDataError",
    "InvalidResponseError",
    "MissingFieldError",
    "ParseError",
    
    # Cache
    "CacheError",
    
    # Live Stream
    "LiveStreamError",
    "StreamOfflineError",
    
    # Configuration
    "ConfigurationError",
    "MissingConfigError",
    
    # Temporary
    "TemporaryError",
]
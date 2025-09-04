"""
Exception hierarchy for Bandcamp integration.
"""


class BandcampError(Exception):
    """Base exception for Bandcamp integration."""
    pass


class ScrapingError(BandcampError):
    """Error during web scraping."""
    pass


class ParseError(BandcampError):
    """Error parsing Bandcamp data."""
    pass


class DownloadError(BandcampError):
    """Error during download."""
    pass


class NotFoundError(BandcampError):
    """Resource not found."""
    pass


class InvalidURLError(BandcampError):
    """Invalid Bandcamp URL."""
    pass


class StreamNotAvailableError(BandcampError):
    """Stream not available for download."""
    pass


class NetworkError(BandcampError):
    """Network operation failed."""
    pass


class RateLimitError(BandcampError):
    """Rate limit exceeded."""
    pass


class AuthenticationError(BandcampError):
    """Authentication required."""
    pass


__all__ = [
    "BandcampError",
    "ScrapingError",
    "ParseError",
    "DownloadError",
    "NotFoundError",
    "InvalidURLError",
    "StreamNotAvailableError",
    "NetworkError",
    "RateLimitError",
    "AuthenticationError",
]
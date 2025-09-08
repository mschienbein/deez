"""
Soulseek-specific exceptions.
"""


class SoulseekError(Exception):
    """Base exception for Soulseek errors."""
    pass


class SlskdConnectionError(SoulseekError):
    """Error connecting to slskd server."""
    pass


class SlskdAuthenticationError(SoulseekError):
    """Authentication error with slskd server."""
    pass


class SearchError(SoulseekError):
    """Error during search operation."""
    pass


class DownloadError(SoulseekError):
    """Error during download operation."""
    pass


class UserNotFoundError(SoulseekError):
    """User not found on Soulseek network."""
    pass


class TimeoutError(SoulseekError):
    """Operation timed out."""
    pass


class TransferError(SoulseekError):
    """Error during file transfer."""
    pass
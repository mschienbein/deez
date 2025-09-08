"""
Soulseek integration for music discovery via slskd.

This integration provides P2P music search and download capabilities
through the Soulseek network using the slskd server as a backend.
"""

from .client import SoulseekClient
from .config import SoulseekConfig, SlskdConfig, SearchConfig, DownloadConfig
from .models import (
    # File models
    File,
    FileInfo,
    # Search models
    SearchResult,
    SearchResponse,
    SearchState,
    # Transfer models
    Transfer,
    TransferState,
    TransferDirection,
    # User models
    User,
    UserInfo,
    BrowseResult,
    Directory,
    # Room models
    Room,
    RoomMessage,
)
from .exceptions import (
    SoulseekError,
    SlskdConnectionError,
    SlskdAuthenticationError,
    SearchError,
    DownloadError,
    UserNotFoundError,
    TimeoutError,
    TransferError,
)

__version__ = "1.0.0"

__all__ = [
    # Client
    "SoulseekClient",
    # Configuration
    "SoulseekConfig",
    "SlskdConfig",
    "SearchConfig",
    "DownloadConfig",
    # File models
    "File",
    "FileInfo",
    # Search models
    "SearchResult",
    "SearchResponse",
    "SearchState",
    # Transfer models
    "Transfer",
    "TransferState",
    "TransferDirection",
    # User models
    "User",
    "UserInfo",
    "BrowseResult",
    "Directory",
    # Room models
    "Room",
    "RoomMessage",
    # Exceptions
    "SoulseekError",
    "SlskdConnectionError",
    "SlskdAuthenticationError",
    "SearchError",
    "DownloadError",
    "UserNotFoundError",
    "TimeoutError",
    "TransferError",
]
"""
Deezer integration for music agent.

A comprehensive Python integration for Deezer with ARL authentication,
track/album/playlist search, and streaming capabilities.
"""

from .client import DeezerClient
from .config import DeezerConfig
from .exceptions import (
    DeezerError,
    AuthenticationError,
    InvalidARLError,
    DownloadError,
    APIError,
)

# Import models for convenience
from .models import (
    Track,
    Album,
    Artist,
    Playlist,
    User,
    SearchResult,
    SearchFilters,
)

__version__ = "1.0.0"

__all__ = [
    # Client
    "DeezerClient",
    
    # Configuration
    "DeezerConfig",
    
    # Models
    "Track",
    "Album",
    "Artist",
    "Playlist",
    "User",
    "SearchResult",
    "SearchFilters",
    
    # Exceptions
    "DeezerError",
    "AuthenticationError",
    "InvalidARLError",
    "DownloadError",
    "APIError",
]
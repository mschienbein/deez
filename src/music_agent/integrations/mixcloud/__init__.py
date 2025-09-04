"""
Mixcloud integration for music agent.

A comprehensive Python integration for Mixcloud with OAuth2 authentication,
cloudcast downloading, search, and user management.
"""

from .client import MixcloudClient
from .config import MixcloudConfig
from .exceptions import (
    MixcloudError,
    AuthenticationError,
    DownloadError,
    StreamNotAvailableError,
    ExclusiveContentError,
)

# Import models for convenience
from .models import Cloudcast, User, Tag, Category, Playlist, Comment

__version__ = "1.0.0"

__all__ = [
    # Client
    "MixcloudClient",
    
    # Configuration
    "MixcloudConfig",
    
    # Models
    "Cloudcast",
    "User",
    "Tag",
    "Category",
    "Playlist",
    "Comment",
    
    # Exceptions
    "MixcloudError",
    "AuthenticationError",
    "DownloadError",
    "StreamNotAvailableError",
    "ExclusiveContentError",
]
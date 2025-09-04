"""
SoundCloud Integration for Music Agent.

A comprehensive SoundCloud API client with download support,
metadata extraction, and advanced features.
"""

from .client import SoundCloudClient
from .models.track import Track
from .models.playlist import Playlist
from .models.user import User
from .exceptions import (
    SoundCloudException,
    AuthenticationError,
    RateLimitError,
    DownloadError,
)

__version__ = "0.1.0"

__all__ = [
    "SoundCloudClient",
    "Track",
    "Playlist",
    "User",
    "SoundCloudException",
    "AuthenticationError",
    "RateLimitError",
    "DownloadError",
]
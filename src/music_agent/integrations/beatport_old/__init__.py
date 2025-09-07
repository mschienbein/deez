"""
Beatport integration for music agent.

Provides access to Beatport's electronic music catalog with search,
charts, and track information capabilities.
"""

from .client import BeatportClient
from .config import BeatportConfig
from .models import Track, Release, Artist, Label
from .exceptions import (
    BeatportError,
    AuthenticationError,
    APIError,
    RateLimitError,
)

__version__ = "1.0.0"

__all__ = [
    "BeatportClient",
    "BeatportConfig",
    "Track",
    "Release",
    "Artist",
    "Label",
    "BeatportError",
    "AuthenticationError",
    "APIError",
    "RateLimitError",
]
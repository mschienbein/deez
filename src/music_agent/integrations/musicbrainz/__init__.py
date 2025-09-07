"""
MusicBrainz integration for music agent.

Provides comprehensive access to MusicBrainz database including:
- Artist, release, recording, and label information
- Advanced search capabilities
- ISRC and barcode lookups
- Cover art retrieval
- Extensive metadata and relationships
"""

from .client import MusicBrainzClient
from .config import MusicBrainzConfig
from .models import (
    Artist,
    Recording,
    Release,
    ReleaseGroup,
    Label,
    Track,
    Medium,
    SearchResult,
    SearchResults,
    EntityType,
    ReleaseType,
    ReleaseStatus,
)
from .exceptions import (
    MusicBrainzError,
    AuthenticationError,
    APIError,
    RateLimitError,
    NotFoundError,
)

__version__ = "1.0.0"

__all__ = [
    "MusicBrainzClient",
    "MusicBrainzConfig",
    "Artist",
    "Recording",
    "Release",
    "ReleaseGroup",
    "Label",
    "Track",
    "Medium",
    "SearchResult",
    "SearchResults",
    "EntityType",
    "ReleaseType",
    "ReleaseStatus",
    "MusicBrainzError",
    "AuthenticationError",
    "APIError",
    "RateLimitError",
    "NotFoundError",
]
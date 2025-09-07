"""
Discogs integration for music agent.

Provides comprehensive access to Discogs database including:
- Artist, release, master, and label information
- Advanced search capabilities
- Collection management
- Marketplace data
- Community statistics
"""

from .client import DiscogsClient
from .config import DiscogsConfig
from .models.core import Artist, Label, Track
from .models.release import Release, Master
from .models.search import SearchResult
from .models.marketplace import MarketplaceListing
from .models.collection import CollectionItem
from .exceptions import (
    DiscogsError,
    AuthenticationError,
    APIError,
    RateLimitError,
    NotFoundError,
)

__version__ = "1.0.0"

__all__ = [
    "DiscogsClient",
    "DiscogsConfig",
    "Artist",
    "Release",
    "Master",
    "Label",
    "Track",
    "SearchResult",
    "MarketplaceListing",
    "CollectionItem",
    "DiscogsError",
    "AuthenticationError",
    "APIError",
    "RateLimitError",
    "NotFoundError",
]
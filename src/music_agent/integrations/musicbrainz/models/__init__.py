"""
MusicBrainz data models.
"""

from .enums import (
    EntityType,
    ReleaseType,
    ReleaseStatus,
    SearchField,
)
from .core import (
    Artist,
    Recording,
    Track,
    Medium,
    Label,
)
from .release import (
    Release,
    ReleaseGroup,
)
from .search import (
    SearchResult,
    SearchResults,
)

__all__ = [
    # Enums
    "EntityType",
    "ReleaseType",
    "ReleaseStatus",
    "SearchField",
    # Core models
    "Artist",
    "Recording",
    "Track",
    "Medium",
    "Label",
    # Release models
    "Release",
    "ReleaseGroup",
    # Search models
    "SearchResult",
    "SearchResults",
]
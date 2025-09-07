"""
Discogs API modules.
"""

from .search import SearchAPI
from .database import DatabaseAPI
from .marketplace import MarketplaceAPI
from .collection import CollectionAPI

__all__ = [
    "SearchAPI",
    "DatabaseAPI",
    "MarketplaceAPI",
    "CollectionAPI",
]
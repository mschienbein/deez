"""
Advanced search functionality for SoundCloud.

Provides high-level search interface with filtering, sorting, and aggregation.
"""

from .manager import SearchManager
from .filters import FilterBuilder, SortOptions
from .aggregator import SearchAggregator

__all__ = [
    "SearchManager",
    "FilterBuilder",
    "SortOptions",
    "SearchAggregator",
]
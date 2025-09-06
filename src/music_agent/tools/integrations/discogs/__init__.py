"""
Discogs integration tools.
"""

from .search import discogs_search
from .metadata import discogs_get_release, discogs_get_master, discogs_get_artist, discogs_get_label
from .marketplace import discogs_search_marketplace, discogs_get_listing

__all__ = [
    'discogs_search',
    'discogs_get_release',
    'discogs_get_master', 
    'discogs_get_artist',
    'discogs_get_label',
    'discogs_search_marketplace',
    'discogs_get_listing'
]
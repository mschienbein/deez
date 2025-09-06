"""
Deezer integration tools.
"""

from .search import search_deezer_tracks, search_deezer_albums
from .download import download_deezer_track
from .metadata import get_deezer_track_info

__all__ = [
    'search_deezer_tracks',
    'search_deezer_albums', 
    'download_deezer_track',
    'get_deezer_track_info'
]
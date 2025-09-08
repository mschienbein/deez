"""
Deezer API modules.
"""

from .base import BaseAPI
from .search import SearchAPI
from .tracks import TracksAPI
from .albums import AlbumsAPI
from .artists import ArtistsAPI
from .playlists import PlaylistsAPI

__all__ = [
    "BaseAPI",
    "SearchAPI",
    "TracksAPI",
    "AlbumsAPI",
    "ArtistsAPI",
    "PlaylistsAPI",
]
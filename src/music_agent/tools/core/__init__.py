"""
Core multi-platform tools.

Provides orchestration tools that work across multiple music platforms.
"""

from .search import search_music, match_track_across_platforms
from .download import search_and_download
from .playlist import create_cross_platform_playlist, export_playlist
from .metadata import get_track_info
from .recommendations import analyze_music_trends

__all__ = [
    'search_music',
    'match_track_across_platforms',
    'search_and_download',
    'create_cross_platform_playlist',
    'export_playlist',
    'get_track_info',
    'analyze_music_trends'
]
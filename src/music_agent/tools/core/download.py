"""
Core multi-platform download tools.

Orchestrates download operations with intelligent platform routing.
"""

import logging
from strands import tool

from .search import search_music
from ..integrations.deezer.download import download_deezer_track

logger = logging.getLogger(__name__)


@tool
def search_and_download(query: str, platform: str = "deezer", output_dir: str = None) -> str:
    """
    Search for a track and download the first result with intelligent platform routing.
    
    Args:
        query: Search query (e.g., "artist - song title")
        platform: Platform to search and download from ("deezer", "youtube", etc.)
        output_dir: Output directory for downloaded files
    
    Returns:
        Status message about the download
    
    Example:
        >>> result = search_and_download("Daft Punk Around The World", platform="deezer")
        >>> print(result)
    """
    try:
        # Search for the track
        results = search_music(query, platform, limit=1)
        
        if not results:
            return f"No results found for: {query}"
        
        track = results[0]
        track_id = track["id"]
        track_platform = track["platform"]
        
        logger.info(f"Found track: {track['title']} by {track['artist']} (ID: {track_id})")
        
        # Route to appropriate download function based on platform
        if track_platform == "deezer":
            return download_deezer_track(track_id, output_dir)
        elif track_platform == "youtube":
            # TODO: Implement YouTube download routing
            return f"YouTube downloads not yet implemented for track: {track['title']}"
        elif track_platform == "spotify":
            return f"Spotify downloads not available (streaming only): {track['title']}"
        else:
            return f"Downloads not supported for platform: {track_platform}"
        
    except Exception as e:
        logger.error(f"Search and download failed: {e}")
        return f"Error: {str(e)}"
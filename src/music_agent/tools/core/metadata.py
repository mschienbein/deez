"""
Core multi-platform metadata tools.

Provides unified metadata retrieval across platforms.
"""

import logging
from typing import Optional, Dict, Any
from strands import tool

from ...integrations.deezer import DeezerIntegration
from ...integrations.spotify import SpotifyIntegration
from ...integrations.youtube import YouTubeIntegration

logger = logging.getLogger(__name__)


@tool
def get_track_info(track_id: str, platform: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed track information from specific platform.
    
    Args:
        track_id: Platform-specific track ID
        platform: Platform name ("deezer", "spotify", "youtube")
    
    Returns:
        Standardized track information or None if not found
    
    Example:
        >>> info = get_track_info("123456789", "deezer")
        >>> print(f"Title: {info['title']}")
        >>> print(f"Artist: {info['artist']}")
        >>> print(f"Duration: {info['duration']} seconds")
    """
    try:
        if platform == "deezer":
            deezer = DeezerIntegration()
            return deezer.get_track_info(track_id)
        elif platform == "spotify":
            spotify = SpotifyIntegration()
            return spotify.get_track_info(track_id)
        elif platform == "youtube":
            youtube = YouTubeIntegration()
            return youtube.get_video_info(track_id)
        else:
            logger.error(f"Unknown platform: {platform}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to get track info: {e}")
        return None
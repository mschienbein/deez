"""
URL resolution for SoundCloud.

Converts SoundCloud URLs to API resources.
"""

import logging
import re
from typing import Optional, Union, Any
from urllib.parse import urlparse, unquote

from ..models.track import Track
from ..models.playlist import Playlist
from ..models.user import User
from ..exceptions import APIError, NotFoundError

logger = logging.getLogger(__name__)


async def resolve(client, url: str) -> Optional[Union[Track, Playlist, User]]:
    """
    Resolve a SoundCloud URL to a resource.
    
    Args:
        client: SoundCloud client
        url: SoundCloud URL
        
    Returns:
        Track, Playlist, or User object, or None
    """
    # Clean URL
    url = url.strip()
    if not url:
        return None
    
    # Ensure it's a SoundCloud URL
    if not is_soundcloud_url(url):
        logger.warning(f"Not a SoundCloud URL: {url}")
        return None
    
    try:
        # Use resolve endpoint
        params = {"url": url}
        response = await client.request("GET", "/resolve", params=params)
        
        # Determine resource type and create object
        if isinstance(response, dict):
            kind = response.get("kind")
            
            if kind == "track":
                return Track(response, client)
            elif kind in ["playlist", "system-playlist"]:
                return Playlist(response, client)
            elif kind == "user":
                return User(response, client)
        
        logger.warning(f"Unknown resource type for URL: {url}")
        return None
        
    except NotFoundError:
        logger.warning(f"Resource not found: {url}")
        return None
    except APIError as e:
        logger.error(f"Failed to resolve URL: {e}")
        return None


def is_soundcloud_url(url: str) -> bool:
    """
    Check if a URL is a SoundCloud URL.
    
    Args:
        url: URL to check
        
    Returns:
        True if SoundCloud URL
    """
    parsed = urlparse(url)
    return parsed.netloc in [
        "soundcloud.com",
        "www.soundcloud.com",
        "m.soundcloud.com",
        "api.soundcloud.com",
        "api-v2.soundcloud.com",
    ]


def extract_resource_type(url: str) -> Optional[str]:
    """
    Extract resource type from SoundCloud URL.
    
    Args:
        url: SoundCloud URL
        
    Returns:
        Resource type ("track", "playlist", "user") or None
    """
    if not is_soundcloud_url(url):
        return None
    
    # Parse URL path
    parsed = urlparse(url)
    path = parsed.path.strip("/")
    
    if not path:
        return None
    
    parts = path.split("/")
    
    # Check for special paths
    if parts[0] in ["tracks", "playlists", "users"]:
        # API URL format
        return parts[0].rstrip("s")  # Remove plural
    
    # Check for sets (playlists)
    if len(parts) >= 3 and parts[1] == "sets":
        return "playlist"
    
    # Check for single track (user/track format)
    if len(parts) == 2 and not parts[1].startswith("sets"):
        return "track"
    
    # Check for user profile
    if len(parts) == 1:
        return "user"
    
    # Check for user sections
    if len(parts) >= 2 and parts[1] in ["tracks", "albums", "sets", "reposts", "likes"]:
        return "user"
    
    return None


def extract_resource_id(url: str) -> Optional[int]:
    """
    Extract resource ID from SoundCloud API URL.
    
    Args:
        url: SoundCloud API URL
        
    Returns:
        Resource ID or None
    """
    # Only works for API URLs with numeric IDs
    match = re.search(r"/(tracks|playlists|users)/(\d+)", url)
    if match:
        return int(match.group(2))
    
    return None


async def resolve_batch(client, urls: list) -> list:
    """
    Resolve multiple URLs in batch.
    
    Args:
        client: SoundCloud client
        urls: List of SoundCloud URLs
        
    Returns:
        List of resolved resources (Track, Playlist, User, or None)
    """
    import asyncio
    
    # Create resolve tasks
    tasks = [resolve(client, url) for url in urls]
    
    # Execute in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle exceptions
    resolved = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Failed to resolve URL: {result}")
            resolved.append(None)
        else:
            resolved.append(result)
    
    return resolved


class URLBuilder:
    """Helper class for building SoundCloud URLs."""
    
    BASE_URL = "https://soundcloud.com"
    API_V1_URL = "https://api.soundcloud.com"
    API_V2_URL = "https://api-v2.soundcloud.com"
    
    @staticmethod
    def track_url(username: str, permalink: str) -> str:
        """Build track URL."""
        return f"{URLBuilder.BASE_URL}/{username}/{permalink}"
    
    @staticmethod
    def playlist_url(username: str, permalink: str) -> str:
        """Build playlist URL."""
        return f"{URLBuilder.BASE_URL}/{username}/sets/{permalink}"
    
    @staticmethod
    def user_url(username: str) -> str:
        """Build user profile URL."""
        return f"{URLBuilder.BASE_URL}/{username}"
    
    @staticmethod
    def api_track_url(track_id: int, version: int = 1) -> str:
        """Build API track URL."""
        base = URLBuilder.API_V1_URL if version == 1 else URLBuilder.API_V2_URL
        return f"{base}/tracks/{track_id}"
    
    @staticmethod
    def api_playlist_url(playlist_id: int, version: int = 1) -> str:
        """Build API playlist URL."""
        base = URLBuilder.API_V1_URL if version == 1 else URLBuilder.API_V2_URL
        return f"{base}/playlists/{playlist_id}"
    
    @staticmethod
    def api_user_url(user_id: int, version: int = 1) -> str:
        """Build API user URL."""
        base = URLBuilder.API_V1_URL if version == 1 else URLBuilder.API_V2_URL
        return f"{base}/users/{user_id}"
    
    @staticmethod
    def stream_url(resource_url: str) -> str:
        """Build stream URL for a resource."""
        return f"{resource_url}/stream"
    
    @staticmethod
    def download_url(resource_url: str) -> str:
        """Build download URL for a resource."""
        return f"{resource_url}/download"


__all__ = [
    "resolve",
    "is_soundcloud_url",
    "extract_resource_type",
    "extract_resource_id",
    "resolve_batch",
    "URLBuilder",
]
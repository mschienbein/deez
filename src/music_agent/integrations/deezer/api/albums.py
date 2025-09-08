"""
Albums API for Deezer.
"""

from typing import List
from .base import BaseAPI
from ..models import Album, Track


class AlbumsAPI(BaseAPI):
    """Albums API endpoints."""
    
    async def get(self, album_id: str) -> Album:
        """Get album details."""
        response = await super().get(f"album/{album_id}")
        return Album.from_api(response)
    
    async def get_tracks(self, album_id: str, limit: int = 100) -> List[Track]:
        """Get album tracks."""
        response = await super().get(f"album/{album_id}/tracks", params={"limit": limit})
        return [Track.from_api(item) for item in response.get("data", [])]
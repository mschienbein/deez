"""
Artists API for Deezer.
"""

from typing import List
from .base import BaseAPI
from ..models import Artist, Track, Album


class ArtistsAPI(BaseAPI):
    """Artists API endpoints."""
    
    async def get(self, artist_id: str) -> Artist:
        """Get artist details."""
        response = await super().get(f"artist/{artist_id}")
        return Artist.from_api(response)
    
    async def get_top(self, artist_id: str, limit: int = 10) -> List[Track]:
        """Get artist's top tracks."""
        response = await super().get(f"artist/{artist_id}/top", params={"limit": limit})
        return [Track.from_api(item) for item in response.get("data", [])]
    
    async def get_albums(self, artist_id: str, limit: int = 50) -> List[Album]:
        """Get artist's albums."""
        response = await super().get(f"artist/{artist_id}/albums", params={"limit": limit})
        return [Album.from_api(item) for item in response.get("data", [])]
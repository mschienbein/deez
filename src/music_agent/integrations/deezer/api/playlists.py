"""
Playlists API for Deezer.
"""

from typing import List
from .base import BaseAPI
from ..models import Playlist, Track


class PlaylistsAPI(BaseAPI):
    """Playlists API endpoints."""
    
    async def get(self, playlist_id: str) -> Playlist:
        """Get playlist details."""
        response = await super().get(f"playlist/{playlist_id}")
        return Playlist.from_api(response)
    
    async def get_tracks(self, playlist_id: str, limit: int = 100) -> List[Track]:
        """Get playlist tracks."""
        response = await super().get(f"playlist/{playlist_id}/tracks", params={"limit": limit})
        return [Track.from_api(item) for item in response.get("data", [])]
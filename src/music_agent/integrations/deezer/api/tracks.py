"""
Tracks API for Deezer.
"""

from .base import BaseAPI
from ..models import Track


class TracksAPI(BaseAPI):
    """Tracks API endpoints."""
    
    async def get(self, track_id: str) -> Track:
        """Get track details."""
        response = await super().get(f"track/{track_id}")
        return Track.from_api(response)
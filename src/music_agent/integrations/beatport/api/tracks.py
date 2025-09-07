"""
Tracks API for Beatport.
"""

from typing import Optional, List, Dict, Any

from .base import BaseAPI
from ..models import Track, Key, Genre
from ..utils.parser import ResponseParser


class TracksAPI(BaseAPI):
    """Handle track operations."""
    
    def __init__(self, *args, **kwargs):
        """Initialize tracks API."""
        super().__init__(*args, **kwargs)
        self.parser = ResponseParser()
    
    def get_track(self, track_id: int) -> Track:
        """
        Get track by ID.
        
        Args:
            track_id: Track ID
            
        Returns:
            Track object
        """
        endpoint = f"catalog/tracks/{track_id}"
        response = self.get(endpoint)
        return self.parser.parse_track(response)
    
    def get_track_by_slug(self, slug: str) -> Track:
        """
        Get track by slug.
        
        Args:
            slug: Track slug
            
        Returns:
            Track object
        """
        endpoint = f"catalog/tracks/slug/{slug}"
        response = self.get(endpoint)
        return self.parser.parse_track(response)
    
    def get_multiple_tracks(self, track_ids: List[int]) -> List[Track]:
        """
        Get multiple tracks by IDs.
        
        Args:
            track_ids: List of track IDs
            
        Returns:
            List of tracks
        """
        endpoint = "catalog/tracks"
        params = {'id': ','.join(map(str, track_ids))}
        response = self.get(endpoint, params)
        
        results = response.get('results', [])
        return [self.parser.parse_track(t) for t in results]
    
    def get_related_tracks(
        self,
        track_id: int,
        limit: int = 10
    ) -> List[Track]:
        """
        Get related/similar tracks.
        
        Args:
            track_id: Track ID
            limit: Maximum number of results
            
        Returns:
            List of related tracks
        """
        endpoint = f"catalog/tracks/{track_id}/similar"
        params = {'per_page': limit}
        response = self.get(endpoint, params)
        
        results = response.get('results', [])
        return [self.parser.parse_track(t) for t in results]
    
    def get_track_key(self, track_id: int) -> Optional[Key]:
        """
        Get detailed key information for a track.
        
        Args:
            track_id: Track ID
            
        Returns:
            Key information or None
        """
        endpoint = f"catalog/tracks/{track_id}/key"
        try:
            response = self.get(endpoint)
            return self.parser.parse_key(response)
        except:
            return None
    
    def get_track_stems(self, track_id: int) -> Dict[str, Any]:
        """
        Get stem information if available.
        
        Args:
            track_id: Track ID
            
        Returns:
            Stem information
        """
        endpoint = f"catalog/tracks/{track_id}/stems"
        try:
            return self.get(endpoint)
        except:
            return {}
    
    def get_track_download_url(
        self,
        track_id: int,
        format_name: str = "mp3-320"
    ) -> Optional[str]:
        """
        Get download URL for purchased track.
        
        Args:
            track_id: Track ID
            format_name: Audio format
            
        Returns:
            Download URL or None
        """
        endpoint = f"catalog/tracks/{track_id}/download"
        params = {'format': format_name}
        
        try:
            response = self.get(endpoint, params)
            return response.get('url')
        except:
            return None
    
    def get_track_stream_url(self, track_id: int) -> Optional[str]:
        """
        Get streaming URL for track preview.
        
        Args:
            track_id: Track ID
            
        Returns:
            Stream URL or None
        """
        endpoint = f"catalog/tracks/{track_id}/stream"
        
        try:
            response = self.get(endpoint)
            return response.get('url')
        except:
            return None
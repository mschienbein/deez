"""
Deezer metadata tools.

Provides metadata retrieval for Deezer tracks, albums, and artists.
"""

from typing import Dict, Any, Optional
from strands import tool

from ...operations.metadata import MetadataOperation
from ....integrations.deezer import DeezerIntegration


class DeezerMetadata(MetadataOperation):
    """Deezer-specific metadata implementation."""
    
    platform_name = "deezer"
    
    def __init__(self):
        self.client = DeezerIntegration()
    
    async def get_track_metadata(self, track_id: str, **kwargs) -> Dict[str, Any]:
        """Get detailed track metadata from Deezer."""
        raw_result = self.client.get_track_info(track_id)
        if not raw_result:
            return {'error': f'Track {track_id} not found'}
        
        return self.standardize_track_metadata(raw_result)
    
    def _extract_artist_info(self, raw_result: Dict) -> Dict[str, Any]:
        """Extract artist information from Deezer result."""
        return {
            'id': None,  # Deezer integration might not provide artist ID
            'name': raw_result.get('artist', 'Unknown'),
            'all_artists': [{'name': raw_result.get('artist', 'Unknown')}]
        }
    
    def _extract_album_info(self, raw_result: Dict) -> Dict[str, Any]:
        """Extract album information from Deezer result."""
        return {
            'id': None,  # Deezer integration might not provide album ID
            'name': raw_result.get('album', ''),
            'release_date': None,
            'total_tracks': None
        }
    
    def _extract_duration_ms(self, raw_result: Dict) -> Optional[int]:
        """Extract duration in milliseconds from Deezer result."""
        duration_seconds = raw_result.get('duration', 0)
        return duration_seconds * 1000 if duration_seconds else None


# Initialize metadata instance
deezer_metadata = DeezerMetadata()


@tool
def get_deezer_track_info(track_id: str) -> Dict[str, Any]:
    """
    Get detailed track information from Deezer.
    
    Args:
        track_id: Deezer track ID
    
    Returns:
        Standardized track metadata
    
    Example:
        >>> info = get_deezer_track_info("123456789")
        >>> print(f"Title: {info['title']}")
        >>> print(f"Artist: {info['artist']['name']}")
    """
    import asyncio
    return asyncio.run(deezer_metadata.get_track_metadata(track_id))
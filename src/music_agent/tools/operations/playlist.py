"""
Base playlist operation template for all integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class PlaylistOperation(ABC):
    """Base class for all playlist operations."""
    
    platform_name: str = "unknown"
    
    @abstractmethod
    async def get_playlist(self, playlist_id: str, **kwargs) -> Dict[str, Any]:
        """Get playlist information and tracks."""
        pass
    
    async def create_playlist(
        self, 
        name: str, 
        description: Optional[str] = None,
        public: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new playlist. Optional - some platforms may not support this."""
        return {'error': f'{self.platform_name} does not support playlist creation'}
    
    async def add_tracks_to_playlist(
        self, 
        playlist_id: str, 
        track_ids: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Add tracks to a playlist. Optional - some platforms may not support this."""
        return {'error': f'{self.platform_name} does not support adding tracks to playlists'}
    
    async def remove_tracks_from_playlist(
        self, 
        playlist_id: str, 
        track_ids: List[str],
        **kwargs
    ) -> Dict[str, Any]:
        """Remove tracks from a playlist. Optional - some platforms may not support this."""
        return {'error': f'{self.platform_name} does not support removing tracks from playlists'}
    
    async def get_user_playlists(self, user_id: Optional[str] = None, **kwargs) -> List[Dict[str, Any]]:
        """Get user's playlists. Optional - some platforms may not support this."""
        return []
    
    def standardize_playlist_result(self, raw_result: Dict) -> Dict[str, Any]:
        """Convert platform-specific playlist result to standard format."""
        return {
            'id': raw_result.get('id'),
            'name': raw_result.get('name') or raw_result.get('title'),
            'description': raw_result.get('description'),
            'owner': self._extract_owner(raw_result),
            'track_count': self._extract_track_count(raw_result),
            'duration': self._extract_total_duration(raw_result),
            'public': self._extract_public_status(raw_result),
            'platform': self.platform_name,
            'url': raw_result.get('url') or raw_result.get('external_urls', {}).get('spotify'),
            'artwork_url': self._extract_playlist_artwork(raw_result),
            'tracks': self._extract_tracks(raw_result),
            'metadata': self._extract_playlist_metadata(raw_result)
        }
    
    def _extract_owner(self, raw_result: Dict) -> Dict[str, Any]:
        """Extract playlist owner information. Override in subclasses."""
        owner = raw_result.get('owner', {}) or raw_result.get('user', {})
        return {
            'id': owner.get('id'),
            'name': owner.get('display_name') or owner.get('username') or owner.get('name'),
            'url': owner.get('external_urls', {}).get('spotify') or owner.get('url')
        }
    
    def _extract_track_count(self, raw_result: Dict) -> int:
        """Extract track count from playlist result. Override in subclasses."""
        tracks = raw_result.get('tracks', {})
        if isinstance(tracks, dict):
            return tracks.get('total', 0)
        elif isinstance(tracks, list):
            return len(tracks)
        return raw_result.get('track_count', 0)
    
    def _extract_total_duration(self, raw_result: Dict) -> Optional[int]:
        """Extract total playlist duration in seconds. Override in subclasses."""
        return raw_result.get('duration')
    
    def _extract_public_status(self, raw_result: Dict) -> bool:
        """Extract public status of playlist. Override in subclasses."""
        return raw_result.get('public', True)
    
    def _extract_playlist_artwork(self, raw_result: Dict) -> Optional[str]:
        """Extract playlist artwork URL. Override in subclasses."""
        images = raw_result.get('images', [])
        if images and isinstance(images, list):
            return images[0].get('url')
        return raw_result.get('artwork_url')
    
    def _extract_tracks(self, raw_result: Dict) -> List[Dict[str, Any]]:
        """Extract track list from playlist. Override in subclasses."""
        tracks = raw_result.get('tracks', {})
        if isinstance(tracks, dict):
            return tracks.get('items', [])
        elif isinstance(tracks, list):
            return tracks
        return []
    
    def _extract_playlist_metadata(self, raw_result: Dict) -> Dict[str, Any]:
        """Extract platform-specific playlist metadata. Override in subclasses."""
        return {'raw': raw_result}
"""
Base search operation template for all integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional


class SearchOperation(ABC):
    """Base class for all search operations."""
    
    platform_name: str = "unknown"
    
    @abstractmethod
    async def search_tracks(self, query: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Search for tracks on the platform."""
        pass
    
    @abstractmethod
    async def search_albums(self, query: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Search for albums on the platform."""
        pass
    
    async def search_artists(self, query: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Search for artists on the platform. Optional - some platforms may not support this."""
        return []
    
    async def search_playlists(self, query: str, limit: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """Search for playlists on the platform. Optional - some platforms may not support this.""" 
        return []
    
    def standardize_track_result(self, raw_result: Dict) -> Dict[str, Any]:
        """Convert platform-specific result to standard format."""
        return {
            'id': raw_result.get('id'),
            'title': raw_result.get('title') or raw_result.get('name'),
            'artist': self._extract_artist(raw_result),
            'album': self._extract_album(raw_result),
            'duration': self._extract_duration(raw_result),
            'platform': self.platform_name,
            'url': raw_result.get('url') or raw_result.get('external_urls', {}).get('spotify'),
            'preview_url': raw_result.get('preview_url'),
            'metadata': self._extract_metadata(raw_result)
        }
    
    def standardize_album_result(self, raw_result: Dict) -> Dict[str, Any]:
        """Convert platform-specific album result to standard format."""
        return {
            'id': raw_result.get('id'),
            'title': raw_result.get('name') or raw_result.get('title'),
            'artist': self._extract_artist(raw_result),
            'release_date': self._extract_release_date(raw_result),
            'total_tracks': raw_result.get('total_tracks') or raw_result.get('track_count'),
            'platform': self.platform_name,
            'url': raw_result.get('url') or raw_result.get('external_urls', {}).get('spotify'),
            'artwork_url': self._extract_artwork_url(raw_result),
            'metadata': self._extract_metadata(raw_result)
        }
    
    def _extract_artist(self, raw_result: Dict) -> str:
        """Extract artist name from platform-specific result. Override in subclasses."""
        return raw_result.get('artist') or 'Unknown'
    
    def _extract_album(self, raw_result: Dict) -> Optional[str]:
        """Extract album name from platform-specific result. Override in subclasses."""
        return raw_result.get('album')
    
    def _extract_duration(self, raw_result: Dict) -> Optional[int]:
        """Extract duration in seconds from platform-specific result. Override in subclasses."""
        duration_ms = raw_result.get('duration_ms')
        if duration_ms:
            return duration_ms // 1000
        return raw_result.get('duration')
    
    def _extract_release_date(self, raw_result: Dict) -> Optional[str]:
        """Extract release date from platform-specific result. Override in subclasses."""
        return raw_result.get('release_date')
    
    def _extract_artwork_url(self, raw_result: Dict) -> Optional[str]:
        """Extract artwork URL from platform-specific result. Override in subclasses."""
        images = raw_result.get('images', [])
        if images and isinstance(images, list):
            return images[0].get('url')
        return raw_result.get('artwork_url')
    
    def _extract_metadata(self, raw_result: Dict) -> Dict[str, Any]:
        """Extract platform-specific metadata. Override in subclasses."""
        return {'raw': raw_result}
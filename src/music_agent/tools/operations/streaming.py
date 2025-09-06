"""
Base streaming operation template for all integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class StreamingOperation(ABC):
    """Base class for all streaming operations."""
    
    platform_name: str = "unknown"
    
    @abstractmethod
    async def get_stream_url(self, track_id: str, quality: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Get streaming URL for a track."""
        pass
    
    async def get_preview_url(self, track_id: str, **kwargs) -> Dict[str, Any]:
        """Get preview URL for a track. Optional - some platforms may not support this."""
        return {'error': f'{self.platform_name} does not support preview URLs'}
    
    async def get_radio_stream(self, seed_id: str, **kwargs) -> Dict[str, Any]:
        """Get radio stream based on seed track/artist. Optional - some platforms may not support this."""
        return {'error': f'{self.platform_name} does not support radio streams'}
    
    async def get_recommendations(
        self, 
        seed_tracks: Optional[List[str]] = None,
        seed_artists: Optional[List[str]] = None,
        limit: int = 20,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Get recommendations based on seeds. Optional - some platforms may not support this."""
        return []
    
    def standardize_stream_result(self, raw_result: Dict) -> Dict[str, Any]:
        """Convert platform-specific stream result to standard format."""
        return {
            'stream_url': raw_result.get('stream_url') or raw_result.get('url'),
            'quality': self._extract_stream_quality(raw_result),
            'format': self._extract_stream_format(raw_result),
            'duration': self._extract_stream_duration(raw_result),
            'expires_at': self._extract_expiry(raw_result),
            'requires_auth': self._extract_auth_requirement(raw_result),
            'platform': self.platform_name,
            'metadata': self._extract_stream_metadata(raw_result)
        }
    
    def standardize_preview_result(self, raw_result: Dict) -> Dict[str, Any]:
        """Convert platform-specific preview result to standard format."""
        return {
            'preview_url': raw_result.get('preview_url') or raw_result.get('url'),
            'duration': self._extract_preview_duration(raw_result),
            'format': self._extract_stream_format(raw_result),
            'platform': self.platform_name,
            'metadata': self._extract_stream_metadata(raw_result)
        }
    
    def standardize_radio_result(self, raw_result: Dict) -> Dict[str, Any]:
        """Convert platform-specific radio result to standard format."""
        return {
            'radio_url': raw_result.get('radio_url') or raw_result.get('url'),
            'name': raw_result.get('name') or raw_result.get('title'),
            'description': raw_result.get('description'),
            'seed_info': self._extract_seed_info(raw_result),
            'platform': self.platform_name,
            'metadata': self._extract_stream_metadata(raw_result)
        }
    
    def _extract_stream_quality(self, raw_result: Dict) -> Optional[str]:
        """Extract stream quality information. Override in subclasses."""
        return raw_result.get('quality') or raw_result.get('bitrate')
    
    def _extract_stream_format(self, raw_result: Dict) -> str:
        """Extract stream format. Override in subclasses."""
        return raw_result.get('format', 'mp3')
    
    def _extract_stream_duration(self, raw_result: Dict) -> Optional[int]:
        """Extract stream duration in seconds. Override in subclasses."""
        duration_ms = raw_result.get('duration_ms')
        if duration_ms:
            return duration_ms // 1000
        return raw_result.get('duration')
    
    def _extract_preview_duration(self, raw_result: Dict) -> int:
        """Extract preview duration in seconds. Override in subclasses."""
        return raw_result.get('preview_duration', 30)
    
    def _extract_expiry(self, raw_result: Dict) -> Optional[str]:
        """Extract stream URL expiry time. Override in subclasses."""
        return raw_result.get('expires_at')
    
    def _extract_auth_requirement(self, raw_result: Dict) -> bool:
        """Extract whether stream requires authentication. Override in subclasses."""
        return raw_result.get('requires_auth', False)
    
    def _extract_seed_info(self, raw_result: Dict) -> Dict[str, Any]:
        """Extract radio seed information. Override in subclasses."""
        return {
            'seed_tracks': raw_result.get('seed_tracks', []),
            'seed_artists': raw_result.get('seed_artists', []),
            'seed_genres': raw_result.get('seed_genres', [])
        }
    
    def _extract_stream_metadata(self, raw_result: Dict) -> Dict[str, Any]:
        """Extract platform-specific stream metadata. Override in subclasses."""
        return {'raw': raw_result}
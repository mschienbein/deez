"""
Base download operation template for all integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path


class DownloadOperation(ABC):
    """Base class for all download operations."""
    
    platform_name: str = "unknown"
    
    @abstractmethod
    async def download_track(
        self, 
        track_id: str, 
        output_path: Optional[Path] = None,
        quality: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Download a track from the platform."""
        pass
    
    async def download_album(
        self, 
        album_id: str, 
        output_path: Optional[Path] = None,
        quality: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Download an album from the platform. Optional - some platforms may not support this."""
        return {'error': f'{self.platform_name} does not support album downloads'}
    
    async def download_playlist(
        self, 
        playlist_id: str, 
        output_path: Optional[Path] = None,
        quality: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Download a playlist from the platform. Optional - some platforms may not support this."""
        return {'error': f'{self.platform_name} does not support playlist downloads'}
    
    def standardize_download_result(self, raw_result: Dict, file_path: Path) -> Dict[str, Any]:
        """Convert platform-specific download result to standard format."""
        return {
            'success': raw_result.get('success', True),
            'file_path': str(file_path),
            'file_size': file_path.stat().st_size if file_path.exists() else 0,
            'format': self._extract_format(raw_result),
            'quality': self._extract_quality(raw_result),
            'platform': self.platform_name,
            'metadata': self._extract_download_metadata(raw_result)
        }
    
    def _extract_format(self, raw_result: Dict) -> str:
        """Extract audio format from download result. Override in subclasses."""
        return raw_result.get('format', 'mp3')
    
    def _extract_quality(self, raw_result: Dict) -> Optional[str]:
        """Extract quality information from download result. Override in subclasses."""
        return raw_result.get('quality')
    
    def _extract_download_metadata(self, raw_result: Dict) -> Dict[str, Any]:
        """Extract platform-specific download metadata. Override in subclasses."""
        return {'raw': raw_result}
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for file system compatibility."""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()
    
    def _generate_output_path(
        self, 
        artist: str, 
        title: str, 
        output_dir: Optional[Path] = None,
        format_ext: str = 'mp3'
    ) -> Path:
        """Generate output path for downloaded file."""
        if output_dir is None:
            output_dir = Path.cwd() / 'downloads'
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        safe_artist = self._sanitize_filename(artist)
        safe_title = self._sanitize_filename(title)
        filename = f"{safe_artist} - {safe_title}.{format_ext}"
        
        return output_dir / filename
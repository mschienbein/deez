"""
Deezer download tools.

Provides download functionality for Deezer tracks.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from strands import tool
import logging

from ...operations.download import DownloadOperation
from ....integrations.deezer import DeezerIntegration

logger = logging.getLogger(__name__)


class DeezerDownload(DownloadOperation):
    """Deezer-specific download implementation."""
    
    platform_name = "deezer"
    
    def __init__(self):
        self.client = DeezerIntegration()
    
    async def download_track(
        self, 
        track_id: str, 
        output_path: Optional[Path] = None,
        quality: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Download a track from Deezer."""
        try:
            # Get track info first
            track_info = self.client.get_track_info(track_id)
            if not track_info:
                return {'success': False, 'error': f'Track {track_id} not found'}
            
            # Generate output path if not provided
            if output_path is None:
                output_dir = Path.home() / 'Music' / 'downloads'
                output_path = self._generate_output_path(
                    track_info['artist'], 
                    track_info['title'],
                    output_dir
                )
            
            # Create temp path for download
            temp_path = output_path.with_suffix('.tmp')
            
            # Download the track
            success = self.client.download_track(track_id, str(temp_path))
            
            if success and temp_path.exists():
                # Determine actual format
                with open(temp_path, 'rb') as f:
                    header = f.read(4)
                
                if header == b'fLaC':
                    final_path = output_path.with_suffix('.flac')
                    format_type = 'flac'
                    quality_info = 'FLAC'
                else:
                    final_path = output_path.with_suffix('.mp3')
                    format_type = 'mp3'
                    quality_info = 'MP3'
                
                # Move to final location
                if final_path.exists():
                    final_path.unlink()
                temp_path.rename(final_path)
                
                return self.standardize_download_result({
                    'success': True,
                    'format': format_type,
                    'quality': quality_info,
                    'track_info': track_info
                }, final_path)
            else:
                return {'success': False, 'error': 'Download failed'}
                
        except Exception as e:
            logger.error(f"Deezer download failed: {e}")
            return {'success': False, 'error': str(e)}


# Initialize download instance
deezer_download = DeezerDownload()


@tool
def download_deezer_track(track_id: str, output_dir: str = None) -> str:
    """
    Download a track from Deezer.
    
    Args:
        track_id: Deezer track ID
        output_dir: Output directory for the downloaded file
    
    Returns:
        Status message about the download
    
    Example:
        >>> result = download_deezer_track("123456789")
        >>> print(result)
    """
    import asyncio
    
    output_path = None
    if output_dir:
        output_path = Path(output_dir)
    
    result = asyncio.run(deezer_download.download_track(track_id, output_path))
    
    if result.get('success'):
        return f"""✅ Download Complete!

Title: {result.get('metadata', {}).get('track_info', {}).get('title', 'Unknown')}
Artist: {result.get('metadata', {}).get('track_info', {}).get('artist', 'Unknown')}
Quality: {result.get('quality', 'Unknown')}

Output: {result.get('file_path')}
File Size: {result.get('file_size', 0) / (1024 * 1024):.2f} MB"""
    else:
        return f"❌ Download Failed: {result.get('error', 'Unknown error')}"
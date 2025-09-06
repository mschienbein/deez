"""
Soulseek download tools.

Provides P2P download functionality for the Soulseek network.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from strands import tool

from ....integrations.soulseek import SoulseekDiscovery

logger = logging.getLogger(__name__)

# Global Soulseek discovery instance (shared across tools)
_discovery_instance = None


async def get_discovery_instance():
    """Get or create Soulseek discovery instance."""
    global _discovery_instance
    if _discovery_instance is None:
        _discovery_instance = SoulseekDiscovery()
        await _discovery_instance.initialize()
    return _discovery_instance


async def extract_metadata(file_path: str) -> Dict[str, Any]:
    """Extract metadata from downloaded file."""
    try:
        from mutagen import File
        
        audio = File(file_path)
        if audio is None:
            return {}
        
        metadata = {
            "duration": audio.info.length if hasattr(audio.info, 'length') else None,
            "bitrate": audio.info.bitrate if hasattr(audio.info, 'bitrate') else None,
            "sample_rate": audio.info.sample_rate if hasattr(audio.info, 'sample_rate') else None,
        }
        
        # Extract tags
        if audio.tags:
            metadata.update({
                "title": str(audio.tags.get("TIT2", [""])[0]),
                "artist": str(audio.tags.get("TPE1", [""])[0]),
                "album": str(audio.tags.get("TALB", [""])[0]),
                "date": str(audio.tags.get("TDRC", [""])[0]),
            })
        
        return metadata
        
    except Exception as e:
        logger.warning(f"Failed to extract metadata: {e}")
        return {}


@tool
def soulseek_download(
    username: str,
    filename: str,
    file_size: Optional[int] = None,
    output_dir: Optional[str] = None,
    auto_tag: bool = True
) -> Dict[str, Any]:
    """
    Download a file from the Soulseek P2P network.
    
    Args:
        username: Username of the peer sharing the file
        filename: Full path/name of the file to download
        file_size: Size of the file in bytes (optional but recommended)
        output_dir: Optional output directory (defaults to configured path)
        auto_tag: Whether to auto-tag the file after download
    
    Returns:
        Download result with file path and metadata
    
    Example:
        >>> result = soulseek_download("user123", "/music/track.mp3", file_size=5242880)
        >>> if result.get("success"):
        >>>     print(f"Downloaded to: {result['file_path']}")
    """
    import asyncio
    
    async def _download():
        discovery = await get_discovery_instance()
        
        # Download the file
        downloaded_path = await discovery.client.download(
            username=username,
            filename=filename,
            file_size=file_size,
            output_dir=output_dir
        )
        
        if not downloaded_path:
            logger.error(f"Failed to download {filename} from {username}")
            return {
                "success": False,
                "error": f"Failed to download {filename} from {username}"
            }
        
        # Auto-tag if requested
        metadata = {}
        if auto_tag and downloaded_path:
            metadata = await extract_metadata(downloaded_path)
        
        result = {
            "success": True,
            "file_path": downloaded_path,
            "filename": Path(downloaded_path).name,
            "size_mb": round(Path(downloaded_path).stat().st_size / (1024 * 1024), 2),
            "metadata": metadata
        }
        
        logger.info(f"Successfully downloaded: {downloaded_path}")
        return result
    
    return asyncio.run(_download())
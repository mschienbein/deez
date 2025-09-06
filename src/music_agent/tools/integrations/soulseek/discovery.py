"""
Soulseek discovery tools.

Provides music discovery functionality using the Soulseek P2P network.
"""

import logging
from typing import List, Dict, Any, Optional
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


@tool
def soulseek_discover(
    mode: str = "criteria",
    artist: Optional[str] = None,
    genre: Optional[str] = None,
    bpm_range: Optional[str] = None,
    key: Optional[str] = None,
    reference_track: Optional[str] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Discover music through the Soulseek P2P network using various methods.
    
    Args:
        mode: Discovery mode ('criteria' or 'similar')
        artist: Artist name for criteria search
        genre: Genre for criteria search  
        bpm_range: BPM range as string "min,max" (e.g., "120,140")
        key: Musical key in Camelot notation
        reference_track: Track to find similar music to
        limit: Maximum results to return
    
    Returns:
        List of discovered tracks
    
    Example:
        >>> tracks = soulseek_discover(
        >>>     mode="criteria", 
        >>>     artist="Carl Cox", 
        >>>     genre="techno",
        >>>     bpm_range="128,135"
        >>> )
    """
    import asyncio
    
    async def _discover():
        discovery = await get_discovery_instance()
        
        # Parse BPM range if provided
        bpm_tuple = None
        if bpm_range:
            try:
                min_bpm, max_bpm = map(int, bpm_range.split(','))
                bmp_tuple = (min_bpm, max_bpm)
            except ValueError:
                logger.warning(f"Invalid BPM range format: {bpm_range}")
        
        if mode == "criteria":
            # Discover by criteria
            results = await discovery.discover_tracks(
                artist=artist,
                genre=genre,
                bpm_range=bpm_tuple,
                key=key
            )
            
        elif mode == "similar" and reference_track:
            # Find similar tracks
            results = await discovery.find_similar_tracks(
                reference_track=reference_track,
                limit=limit
            )
            
        else:
            logger.error(f"Invalid discovery mode: {mode}")
            return []
        
        # Format results
        formatted = []
        for result in results[:limit]:
            formatted.append({
                "filename": result.get("filename", result.get("path", "")),
                "username": result.get("username", "unknown"),
                "discovery_method": mode,
                "size_mb": round(result.get("size", 0) / (1024 * 1024), 2) if "size" in result else None
            })
        
        logger.info(f"Discovered {len(formatted)} tracks using {mode} mode")
        return formatted
    
    return asyncio.run(_discover())
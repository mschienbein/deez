"""
Soulseek search tools.

Provides P2P network search functionality for the Soulseek network.
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
def soulseek_search(
    query: str,
    min_bitrate: int = 320,
    max_results: int = 20,
    file_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Search for music files on the Soulseek P2P network.
    
    Args:
        query: Search query (artist, track, album, genre)
        min_bitrate: Minimum acceptable bitrate in kbps
        max_results: Maximum number of results to return
        file_type: Optional file extension filter (mp3, flac, wav)
    
    Returns:
        List of search results with file metadata
    
    Example:
        >>> results = soulseek_search("Daft Punk Around The World", min_bitrate=320)
        >>> for result in results:
        >>>     print(f"{result['filename']} from {result['username']}")
    """
    import asyncio
    
    async def _search():
        discovery = await get_discovery_instance()
        
        # Perform search
        results = await discovery.client.search(
            query=query,
            min_bitrate=min_bitrate,
            max_results=max_results * 2  # Get extra to filter
        )
        
        # Filter by file type if specified
        if file_type:
            filtered = []
            for result in results:
                if result.get("extension", "").lower() == f".{file_type.lower()}":
                    filtered.append(result)
            results = filtered
        
        # Format results for agent
        formatted_results = []
        for result in results[:max_results]:
            formatted_results.append({
                "filename": result["filename"],
                "username": result["username"],
                "size_mb": round(result.get("size", 0) / (1024 * 1024), 2),
                "bitrate": result.get("bitrate", "unknown"),
                "sample_rate": result.get("sample_rate", "unknown"),
                "extension": result.get("extension", ""),
                "queue_position": result.get("queue_position", 0)
            })
        
        logger.info(f"Found {len(formatted_results)} files for query: {query}")
        return formatted_results
    
    return asyncio.run(_search())
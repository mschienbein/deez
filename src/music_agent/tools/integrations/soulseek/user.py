"""
Soulseek user interaction tools.

Provides tools for interacting with Soulseek users and browsing their collections.
"""

import logging
from typing import Dict, Any
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
def soulseek_user_info(username: str) -> Dict[str, Any]:
    """
    Get information about a Soulseek user.
    
    Args:
        username: Username to get information about
    
    Returns:
        User information or error message
    
    Example:
        >>> info = soulseek_user_info("user123")
        >>> if info.get("success"):
        >>>     print(f"User info: {info['info']}")
    """
    import asyncio
    
    async def _get_user_info():
        discovery = await get_discovery_instance()
        
        # Get user information
        info = await discovery.client.get_user_info(username)
        
        if info:
            return {
                "username": username,
                "info": info,
                "success": True
            }
        else:
            return {
                "username": username,
                "error": "Failed to get user info",
                "success": False
            }
    
    return asyncio.run(_get_user_info())


@tool
def soulseek_browse_user(username: str, limit: int = 50) -> Dict[str, Any]:
    """
    Browse a Soulseek user's shared files.
    
    Args:
        username: Username to browse
        limit: Maximum files to return
    
    Returns:
        User's file list or error message
    
    Example:
        >>> files = soulseek_browse_user("user123", limit=20)
        >>> if files.get("success"):
        >>>     for file in files["files"]:
        >>>         print(f"{file['filename']} ({file['size_mb']:.2f} MB)")
    """
    import asyncio
    
    async def _browse_user():
        discovery = await get_discovery_instance()
        
        # Browse user's files
        files = await discovery.client.browse_user(username)
        
        # Format and limit results
        formatted_files = []
        for file in files[:limit]:
            formatted_files.append({
                "path": file.get("path"),
                "filename": file.get("filename"),
                "size_mb": round(file.get("size", 0) / (1024 * 1024), 2) if "size" in file else None,
                "extension": file.get("extension")
            })
        
        return {
            "username": username,
            "files": formatted_files,
            "total_files": len(files),
            "showing": len(formatted_files),
            "success": True
        }
    
    return asyncio.run(_browse_user())
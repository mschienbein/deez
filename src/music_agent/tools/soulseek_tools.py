"""
Soulseek Agent Tools
Provides music discovery and download capabilities via Soulseek P2P network
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..integrations.soulseek import SoulseekDiscovery

logger = logging.getLogger(__name__)


class SoulseekSearchTool:
    """Tool for searching music on Soulseek network"""
    
    name = "soulseek_search"
    description = "Search for music files on the Soulseek P2P network"
    
    def __init__(self):
        self.discovery = None
        
    async def initialize(self):
        """Initialize the tool"""
        if not self.discovery:
            self.discovery = SoulseekDiscovery()
            await self.discovery.initialize()
    
    async def run(
        self,
        query: str,
        min_bitrate: int = 320,
        max_results: int = 20,
        file_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for music on Soulseek
        
        Args:
            query: Search query (artist, track, album, genre)
            min_bitrate: Minimum acceptable bitrate in kbps
            max_results: Maximum number of results to return
            file_type: Optional file extension filter (mp3, flac, wav)
            
        Returns:
            List of search results with file metadata
        """
        await self.initialize()
        
        # Perform search
        results = await self.discovery.client.search(
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
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.discovery:
            await self.discovery.close()


class SoulseekDownloadTool:
    """Tool for downloading music from Soulseek"""
    
    name = "soulseek_download"
    description = "Download music files from Soulseek P2P network"
    
    def __init__(self):
        self.discovery = None
        
    async def initialize(self):
        """Initialize the tool"""
        if not self.discovery:
            self.discovery = SoulseekDiscovery()
            await self.discovery.initialize()
    
    async def run(
        self,
        username: str,
        filename: str,
        file_size: Optional[int] = None,
        output_dir: Optional[str] = None,
        auto_tag: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Download a file from Soulseek
        
        Args:
            username: Username of the peer sharing the file
            filename: Full path/name of the file to download
            file_size: Size of the file in bytes (optional but recommended)
            output_dir: Optional output directory (defaults to configured path)
            auto_tag: Whether to auto-tag the file after download
            
        Returns:
            Download result with file path and metadata
        """
        await self.initialize()
        
        # Download the file
        downloaded_path = await self.discovery.client.download(
            username=username,
            filename=filename,
            file_size=file_size,
            output_dir=output_dir
        )
        
        if not downloaded_path:
            logger.error(f"Failed to download {filename} from {username}")
            return None
        
        # Auto-tag if requested
        metadata = {}
        if auto_tag and downloaded_path:
            metadata = await self._extract_metadata(downloaded_path)
        
        result = {
            "success": True,
            "file_path": downloaded_path,
            "filename": Path(downloaded_path).name,
            "size_mb": round(Path(downloaded_path).stat().st_size / (1024 * 1024), 2),
            "metadata": metadata
        }
        
        logger.info(f"Successfully downloaded: {downloaded_path}")
        return result
    
    async def _extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from downloaded file"""
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
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.discovery:
            await self.discovery.close()


class SoulseekDiscoveryTool:
    """Tool for discovering music through Soulseek"""
    
    name = "soulseek_discover"
    description = "Discover new music based on criteria or similar tracks"
    
    def __init__(self):
        self.discovery = None
        
    async def initialize(self):
        """Initialize the tool"""
        if not self.discovery:
            self.discovery = SoulseekDiscovery()
            await self.discovery.initialize()
    
    async def run(
        self,
        mode: str = "criteria",
        artist: Optional[str] = None,
        genre: Optional[str] = None,
        bpm_range: Optional[tuple] = None,
        key: Optional[str] = None,
        reference_track: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Discover music through various methods
        
        Args:
            mode: Discovery mode ('criteria', 'similar')
            artist: Artist name for criteria search
            genre: Genre for criteria search  
            bpm_range: BPM range tuple (min, max)
            key: Musical key in Camelot notation
            reference_track: Track to find similar music to
            limit: Maximum results to return
            
        Returns:
            List of discovered tracks
        """
        await self.initialize()
        
        if mode == "criteria":
            # Discover by criteria
            results = await self.discovery.discover_tracks(
                artist=artist,
                genre=genre,
                bpm_range=bpm_range,
                key=key
            )
            
        elif mode == "similar" and reference_track:
            # Find similar tracks
            results = await self.discovery.find_similar_tracks(
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
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.discovery:
            await self.discovery.close()


class SoulseekUserTool:
    """Tool for interacting with Soulseek users"""
    
    name = "soulseek_user"
    description = "Get information about Soulseek users and browse their collections"
    
    def __init__(self):
        self.discovery = None
        
    async def initialize(self):
        """Initialize the tool"""
        if not self.discovery:
            self.discovery = SoulseekDiscovery()
            await self.discovery.initialize()
    
    async def run(
        self,
        action: str,
        username: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Interact with Soulseek users
        
        Args:
            action: Action to perform ('info', 'browse')
            username: Username to interact with
            limit: Maximum files to return when browsing
            
        Returns:
            User information or file list
        """
        await self.initialize()
        
        if action == "info":
            # Get user information
            info = await self.discovery.client.get_user_info(username)
            
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
                
        elif action == "browse":
            # Browse user's files
            files = await self.discovery.client.browse_user(username)
            
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
            
        else:
            return {
                "error": f"Invalid action: {action}",
                "success": False
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.discovery:
            await self.discovery.close()


# Tool registry for agent
SOULSEEK_TOOLS = [
    SoulseekSearchTool,
    SoulseekDownloadTool,
    SoulseekDiscoveryTool,
    SoulseekUserTool
]


async def test_tools():
    """Test Soulseek tools"""
    
    logging.basicConfig(level=logging.INFO)
    
    # Test search tool
    search_tool = SoulseekSearchTool()
    try:
        results = await search_tool.run(
            query="techno 130bpm",
            min_bitrate=320,
            max_results=5
        )
        
        logger.info(f"Search results: {len(results)}")
        for result in results:
            logger.info(f"  - {result['filename']} from {result['username']}")
        
        # Test download if results found
        if results:
            download_tool = SoulseekDownloadTool()
            first_result = results[0]
            
            downloaded = await download_tool.run(
                username=first_result["username"],
                filename=first_result["filename"],
                file_size=first_result.get("size")
            )
            
            if downloaded:
                logger.info(f"Downloaded: {downloaded['file_path']}")
            
            await download_tool.cleanup()
            
    finally:
        await search_tool.cleanup()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tools())
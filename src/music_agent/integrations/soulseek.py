"""
Soulseek/slskd Integration for Music Discovery
Provides P2P music search and download capabilities
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

logger = logging.getLogger(__name__)

try:
    import slskd_api
except ImportError:
    logger.warning("slskd_api not installed. Install with: pip install slskd-api")
    slskd_api = None

from .graphiti_memory import MusicMemory


class SoulseekClient:
    """Client for interacting with slskd API"""
    
    def __init__(self):
        self.host = os.getenv("SLSKD_HOST", "http://localhost:5030")
        self.api_key = os.getenv("SLSKD_API_KEY", "")
        self.url_base = os.getenv("SLSKD_URL_BASE", "/")  # Default to "/" for proper URL construction
        self.client = None
        self.memory = MusicMemory()
        
    async def initialize(self):
        """Initialize slskd API client"""
        if not slskd_api:
            raise ImportError("slskd_api library not available")
            
        # Initialize the slskd API client
        # With SLSKD_NO_AUTH=true, we pass a dummy API key to satisfy the library
        self.client = slskd_api.SlskdClient(
            self.host,
            "no-auth-required",  # Dummy key when SLSKD_NO_AUTH=true
            self.url_base
        )
        
        # Initialize memory (optional)
        try:
            await self.memory.initialize(session_id="soulseek_discovery")
            logger.info("Soulseek memory initialized")
        except Exception as e:
            logger.warning(f"Memory initialization failed: {e}")
    
    async def search(
        self,
        query: str,
        min_bitrate: int = 320,
        max_results: int = 50,
        timeout: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for music on Soulseek network
        
        Args:
            query: Search query (artist, track, album)
            min_bitrate: Minimum bitrate in kbps (default 320)
            max_results: Maximum number of results
            timeout: Search timeout in seconds
            
        Returns:
            List of search results with file information
        """
        if not self.client:
            raise Exception("Client not initialized. Call initialize() first.")
        
        try:
            # Initiate search using slskd_api
            search_result = self.client.searches.search_text(
                searchText=query,
                fileLimit=max_results * 2,  # Get extra to filter
                filterResponses=True,
                searchTimeout=timeout * 1000  # Convert to milliseconds
            )
            
            # Extract search ID
            search_id = search_result.get('id')
            if not search_id:
                logger.error("Failed to get search ID")
                return []
            
            # Wait for search results to populate
            await asyncio.sleep(min(timeout, 5))  # Wait up to 5 seconds
            
            # Get search state to check completion
            search_state = self.client.searches.state(search_id)
            
            # Get the actual search responses
            responses = self.client.searches.search_responses(search_id)
            
            # Process and filter results
            processed_results = self._process_search_results(
                responses,
                min_bitrate,
                max_results
            )
            
            # Clean up the search
            try:
                self.client.searches.stop(search_id)
            except Exception as e:
                logger.debug(f"Error stopping search: {e}")
            
            # Log to memory
            if self.memory.initialized and processed_results:
                await self.memory._add_episode_safe(
                    name=f"soulseek_search_{datetime.now().strftime('%H%M%S')}",
                    episode_body=f"Searched Soulseek for: {query}, found {len(processed_results)} results",
                    source_description="Soulseek P2P search",
                    reference_time=datetime.now()
                )
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    def _process_search_results(
        self,
        responses: List[Dict],
        min_bitrate: int,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Process and filter search results from slskd_api"""
        processed = []
        
        # Extract files from search responses
        all_files = []
        for response in responses:
            username = response.get("username", "")
            files = response.get("files", [])
            
            for file in files:
                # Add username to file info
                file_info = {
                    "filename": file.get("filename", ""),
                    "username": username,
                    "size": file.get("size", 0),
                    "bitrate": file.get("bitRate"),
                    "sample_rate": file.get("sampleRate"),
                    "length": file.get("length"),
                    "extension": Path(file.get("filename", "")).suffix,
                    "free_upload_slots": response.get("hasFreeUploadSlot", False),
                    "upload_speed": response.get("uploadSpeed"),
                    "queue_length": response.get("queueLength", 0)
                }
                
                # Filter by bitrate if specified
                if file_info["bitrate"] is not None:
                    if file_info["bitrate"] >= min_bitrate:
                        all_files.append(file_info)
                else:
                    # Include files without bitrate info (might be lossless)
                    all_files.append(file_info)
        
        # Sort by quality indicators
        all_files.sort(
            key=lambda x: (
                x.get("free_upload_slots", False),  # Prefer free slots
                x.get("bitrate") or 0,  # Higher bitrate (handle None)
                -(x.get("queue_length") or 999),  # Shorter queue (handle None)
                -(x.get("size") or 0)  # Larger files (usually better quality)
            ),
            reverse=True
        )
        
        # Return top results
        return all_files[:max_results]
    
    async def download(
        self,
        username: str,
        filename: str,
        file_size: Optional[int] = None,
        output_dir: Optional[str] = None
    ) -> Optional[str]:
        """
        Download a file from Soulseek
        
        Args:
            username: Username of the peer
            filename: Full path of the file to download
            file_size: Size of the file (optional but recommended)
            output_dir: Optional output directory
            
        Returns:
            Path to downloaded file or None if failed
        """
        if not self.client:
            raise Exception("Client not initialized. Call initialize() first.")
            
        if not output_dir:
            output_dir = os.getenv("MUSIC_DOWNLOADS_PATH", "./slskd/downloads")
        
        try:
            # Prepare file information for download
            files = [{
                "filename": filename,
                "size": file_size if file_size else 0
            }]
            
            # Enqueue download using slskd_api
            download_result = self.client.transfers.enqueue(
                username=username,
                files=files
            )
            
            # Get download ID from result
            download_id = None
            if download_result and isinstance(download_result, list):
                download_id = download_result[0].get("id") if download_result else None
            elif download_result and isinstance(download_result, dict):
                download_id = download_result.get("id")
            
            if not download_id:
                logger.error("Failed to get download ID")
                return None
            
            # Monitor download progress
            output_path = await self._monitor_download(download_id, filename, output_dir)
            
            # Log to memory
            if self.memory.initialized and output_path:
                await self.memory.add_track_discovery(
                    track={
                        "title": Path(filename).stem,
                        "file_path": output_path,
                        "source_user": username
                    },
                    source="soulseek",
                    action="downloaded"
                )
            
            return output_path
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    async def _monitor_download(
        self,
        download_id: str,
        filename: str,
        output_dir: str,
        max_wait: int = 300
    ) -> Optional[str]:
        """Monitor download progress using slskd_api"""
        if not self.client:
            return None
            
        start_time = time.time()
        
        while (time.time() - start_time) < max_wait:
            try:
                # Get download status using slskd_api
                downloads = self.client.transfers.get_downloads()
                
                # Find our download
                for download in downloads:
                    if download.get("id") == download_id:
                        state = download.get("state", "").lower()
                        
                        if state == "completed":
                            # Download completed
                            file_name = Path(filename).name
                            output_path = os.path.join(output_dir, file_name)
                            logger.info(f"Download completed: {output_path}")
                            return output_path
                        
                        elif state in ["failed", "cancelled", "rejected"]:
                            logger.error(f"Download failed with state: {state}")
                            return None
                        
                        else:
                            # Still downloading
                            progress = download.get("percentComplete", 0)
                            logger.debug(f"Download progress: {progress}%")
                            break
                
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error monitoring download: {e}")
                await asyncio.sleep(5)
        
        logger.error("Download timed out")
        return None
    
    async def get_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get information about a Soulseek user"""
        if not self.client:
            return None
            
        try:
            # Use slskd_api to get user info
            user_info = self.client.users.get_info(username)
            return user_info
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return None
    
    async def browse_user(self, username: str) -> List[Dict[str, Any]]:
        """Browse a user's shared files"""
        if not self.client:
            return []
            
        try:
            # Request browse using slskd_api
            browse_result = self.client.users.browse(username)
            
            # Wait for browse to complete
            await asyncio.sleep(3)
            
            # Get browse status
            browse_status = self.client.users.get_browse_status(username)
            
            if browse_status and browse_status.get("status") == "completed":
                # Get the actual browse data
                directories = browse_status.get("directories", [])
                return self._process_browse_results(directories)
            else:
                logger.warning(f"Browse not completed for user {username}")
                return []
                    
        except Exception as e:
            logger.error(f"Browse error: {e}")
            return []
    
    def _process_browse_results(self, directories: List[Dict]) -> List[Dict[str, Any]]:
        """Process user browse results"""
        files = []
        
        # Extract files from directory structure
        for directory in directories:
            dir_name = directory.get("name", "")
            for file in directory.get("files", []):
                files.append({
                    "path": f"{dir_name}/{file.get('filename', '')}",
                    "filename": file.get('filename', ''),
                    "size": file.get('size', 0),
                    "extension": Path(file.get('filename', '')).suffix
                })
        
        return files
    
    async def close(self):
        """Close connections"""
        if self.memory.initialized:
            await self.memory.close()


class SoulseekDiscovery:
    """High-level Soulseek music discovery interface"""
    
    def __init__(self):
        self.client = SoulseekClient()
        
    async def initialize(self):
        """Initialize Soulseek client"""
        await self.client.initialize()
    
    async def discover_tracks(
        self,
        artist: Optional[str] = None,
        genre: Optional[str] = None,
        bpm_range: Optional[tuple] = None,
        key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover tracks based on criteria
        
        Args:
            artist: Artist name to search for
            genre: Genre to filter by
            bpm_range: Tuple of (min_bpm, max_bpm)
            key: Musical key (Camelot notation)
            
        Returns:
            List of discovered tracks
        """
        # Build search query
        query_parts = []
        if artist:
            query_parts.append(artist)
        if genre:
            query_parts.append(genre)
        if bpm_range:
            query_parts.append(f"{bpm_range[0]}-{bpm_range[1]}bpm")
        if key:
            query_parts.append(key)
        
        if not query_parts:
            logger.error("No search criteria provided")
            return []
        
        query = " ".join(query_parts)
        
        # Search Soulseek
        results = await self.client.search(query, min_bitrate=320)
        
        # Filter results based on criteria
        filtered = []
        for result in results:
            # Apply additional filters if needed
            if self._matches_criteria(result, genre, bpm_range, key):
                filtered.append(result)
        
        return filtered
    
    def _matches_criteria(
        self,
        result: Dict,
        genre: Optional[str],
        bpm_range: Optional[tuple],
        key: Optional[str]
    ) -> bool:
        """Check if result matches discovery criteria"""
        # Since Soulseek doesn't provide metadata, we rely on filename parsing
        filename = result.get("filename", "").lower()
        
        # Genre check (basic filename matching)
        if genre and genre.lower() not in filename:
            return False
        
        # BPM check (look for BPM in filename)
        if bpm_range:
            import re
            bpm_match = re.search(r'(\d{2,3})[\s\-_]*bpm', filename)
            if bpm_match:
                bpm = int(bpm_match.group(1))
                if not (bpm_range[0] <= bpm <= bpm_range[1]):
                    return False
        
        # Key check
        if key and key.lower() not in filename:
            return False
        
        return True
    
    async def download_track(
        self,
        search_result: Dict,
        output_dir: Optional[str] = None
    ) -> Optional[str]:
        """Download a track from search results"""
        username = search_result.get("username")
        filename = search_result.get("filename")
        file_size = search_result.get("size")
        
        if not username or not filename:
            logger.error("Invalid search result for download")
            return None
        
        return await self.client.download(username, filename, file_size, output_dir)
    
    async def find_similar_tracks(
        self,
        reference_track: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Find tracks similar to a reference"""
        # Search for the reference track
        results = await self.client.search(reference_track, max_results=limit)
        
        similar = []
        for result in results:
            # Get user who has this track
            username = result.get("username")
            if username:
                # Browse their collection for more tracks
                user_files = await self.client.browse_user(username)
                
                # Add relevant files to similar tracks
                for file in user_files[:5]:  # Limit per user
                    if file not in similar:
                        similar.append(file)
        
        return similar[:limit]
    
    
    async def close(self):
        """Close discovery client"""
        await self.client.close()


async def main():
    """Test Soulseek integration"""
    
    logging.basicConfig(level=logging.INFO)
    
    discovery = SoulseekDiscovery()
    
    try:
        await discovery.initialize()
        
        # Test search
        logger.info("Testing Soulseek search...")
        results = await discovery.discover_tracks(
            genre="techno",
            bpm_range=(125, 135)
        )
        
        logger.info(f"Found {len(results)} tracks")
        for result in results[:5]:
            logger.info(f"  - {result['filename']} ({result['bitrate']}kbps)")
        
        # Test download (if results found)
        if results:
            logger.info("Testing download...")
            downloaded = await discovery.download_track(results[0])
            if downloaded:
                logger.info(f"Successfully downloaded to: {downloaded}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        await discovery.close()


if __name__ == "__main__":
    asyncio.run(main())
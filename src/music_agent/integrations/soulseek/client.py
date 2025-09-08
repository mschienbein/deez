"""
Main Soulseek client.

Provides high-level interface for interacting with Soulseek via slskd.
"""

import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

from .config import SoulseekConfig
from .auth import SlskdAuthManager
from .api import SearchAPI, TransferAPI, UserAPI
from .download import DownloadManager
from .models import (
    SearchResult, FileInfo, Transfer, User, 
    UserInfo, BrowseResult
)
from .exceptions import SoulseekError

logger = logging.getLogger(__name__)


class SoulseekClient:
    """Main client for interacting with Soulseek via slskd."""
    
    def __init__(self, config: Optional[SoulseekConfig] = None):
        """
        Initialize Soulseek client.
        
        Args:
            config: Optional configuration (uses defaults if not provided)
        """
        self.config = config or SoulseekConfig.from_env()
        
        # Initialize auth manager
        self.auth_manager = SlskdAuthManager(
            api_key=self.config.slskd.api_key,
            no_auth=self.config.slskd.no_auth
        )
        
        # Initialize API clients
        self.search_api = SearchAPI(self.config.slskd, self.auth_manager)
        self.transfer_api = TransferAPI(self.config.slskd, self.auth_manager)
        self.user_api = UserAPI(self.config.slskd, self.auth_manager)
        
        # Initialize download manager
        self.download_manager = DownloadManager(
            self.transfer_api,
            self.config.download
        )
        
        self._connected = False
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def connect(self):
        """Connect to slskd server."""
        try:
            # Connect base API
            self.search_api.connect()
            self._connected = True
            logger.info("Connected to Soulseek via slskd")
        except Exception as e:
            logger.error(f"Failed to connect to slskd: {e}")
            raise SoulseekError(f"Connection failed: {e}")
    
    async def close(self):
        """Close connections."""
        # Nothing specific to close for slskd_api
        self._connected = False
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to slskd."""
        return self._connected
    
    # Search methods
    
    async def search(
        self,
        query: str,
        min_bitrate: int = 320,
        max_results: int = 50,
        timeout: int = 10
    ) -> List[FileInfo]:
        """
        Search for files on Soulseek.
        
        Args:
            query: Search query
            min_bitrate: Minimum bitrate filter
            max_results: Maximum results to return
            timeout: Search timeout in seconds
            
        Returns:
            List of FileInfo objects
        """
        if not self._connected:
            await self.connect()
        
        # Perform search
        search_result = await self.search_api.search(
            query=query,
            min_bitrate=min_bitrate,
            max_results=max_results,
            timeout=timeout
        )
        
        # Get best files
        return search_result.get_best_files(max_results)
    
    async def search_advanced(
        self,
        query: str,
        **kwargs
    ) -> SearchResult:
        """
        Advanced search returning full SearchResult.
        
        Args:
            query: Search query
            **kwargs: Additional search parameters
            
        Returns:
            SearchResult object
        """
        if not self._connected:
            await self.connect()
        
        return await self.search_api.search(query, **kwargs)
    
    # User methods
    
    async def get_user_info(self, username: str) -> UserInfo:
        """
        Get information about a user.
        
        Args:
            username: Username
            
        Returns:
            UserInfo object
        """
        if not self._connected:
            await self.connect()
        
        return await self.user_api.get_user_info(username)
    
    async def browse_user(self, username: str) -> BrowseResult:
        """
        Browse a user's shared files.
        
        Args:
            username: Username to browse
            
        Returns:
            BrowseResult object
        """
        if not self._connected:
            await self.connect()
        
        return await self.user_api.browse_user(username)
    
    async def get_user(self, username: str) -> User:
        """
        Get complete user information.
        
        Args:
            username: Username
            
        Returns:
            User object with info and browse result
        """
        if not self._connected:
            await self.connect()
        
        return await self.user_api.get_user(username)
    
    # Download methods
    
    async def download(
        self,
        file_info: FileInfo,
        output_dir: Optional[str] = None
    ) -> Optional[str]:
        """
        Download a file.
        
        Args:
            file_info: FileInfo from search results
            output_dir: Optional output directory
            
        Returns:
            Path to downloaded file or None
        """
        if not self._connected:
            await self.connect()
        
        return await self.download_manager.download_file(file_info, output_dir)
    
    async def download_from_search(
        self,
        query: str,
        output_dir: Optional[str] = None,
        min_bitrate: int = 320
    ) -> Optional[str]:
        """
        Search and download the best result.
        
        Args:
            query: Search query
            output_dir: Optional output directory
            min_bitrate: Minimum bitrate
            
        Returns:
            Path to downloaded file or None
        """
        # Search for files
        results = await self.search(query, min_bitrate=min_bitrate, max_results=10)
        
        if not results:
            logger.warning(f"No results found for: {query}")
            return None
        
        # Download the best result
        best_result = results[0]
        logger.info(f"Downloading best result: {best_result.file.filename}")
        
        return await self.download(best_result, output_dir)
    
    async def download_multiple(
        self,
        file_infos: List[FileInfo],
        output_dir: Optional[str] = None,
        max_concurrent: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Download multiple files.
        
        Args:
            file_infos: List of FileInfo objects
            output_dir: Optional output directory
            max_concurrent: Maximum concurrent downloads
            
        Returns:
            List of download results
        """
        if not self._connected:
            await self.connect()
        
        return await self.download_manager.download_multiple(
            file_infos,
            output_dir,
            max_concurrent
        )
    
    # Transfer management
    
    def get_downloads(self) -> List[Transfer]:
        """Get all current downloads."""
        if not self._connected:
            raise SoulseekError("Not connected to slskd")
        
        return self.transfer_api.get_all_downloads()
    
    def get_active_downloads(self) -> List[Transfer]:
        """Get active downloads."""
        if not self._connected:
            raise SoulseekError("Not connected to slskd")
        
        return self.download_manager.get_active_downloads()
    
    def cancel_download(self, download_id: str) -> bool:
        """Cancel a download."""
        if not self._connected:
            raise SoulseekError("Not connected to slskd")
        
        return self.download_manager.cancel_download(download_id)
    
    def retry_download(self, download_id: str) -> bool:
        """Retry a failed download."""
        if not self._connected:
            raise SoulseekError("Not connected to slskd")
        
        return self.download_manager.retry_download(download_id)
    
    # Discovery methods (high-level)
    
    async def discover_by_genre(
        self,
        genre: str,
        limit: int = 20
    ) -> List[FileInfo]:
        """
        Discover music by genre.
        
        Args:
            genre: Genre to search for
            limit: Maximum results
            
        Returns:
            List of FileInfo objects
        """
        # Search for genre
        results = await self.search(
            query=genre,
            max_results=limit * 2  # Get extra for filtering
        )
        
        # Filter by likely genre matches (basic filename matching)
        filtered = []
        genre_lower = genre.lower()
        
        for result in results:
            filename_lower = result.file.filename.lower()
            if genre_lower in filename_lower:
                filtered.append(result)
        
        return filtered[:limit] if filtered else results[:limit]
    
    async def discover_similar(
        self,
        reference_track: str,
        limit: int = 20
    ) -> List[FileInfo]:
        """
        Find tracks similar to a reference.
        
        Args:
            reference_track: Reference track name
            limit: Maximum results
            
        Returns:
            List of similar tracks
        """
        # Search for the reference track
        results = await self.search(reference_track, max_results=5)
        
        if not results:
            return []
        
        similar = []
        
        # Browse users who have the reference track
        for result in results[:3]:  # Check top 3 users
            try:
                browse_result = await self.browse_user(result.username)
                
                # Add some of their files as similar
                for file in browse_result.get_all_files()[:5]:
                    file_info = FileInfo(
                        file=file,
                        username=result.username,
                        free_upload_slots=result.free_upload_slots,
                        upload_speed=result.upload_speed,
                        queue_length=result.queue_length
                    )
                    
                    if file_info not in similar:
                        similar.append(file_info)
                        
            except Exception as e:
                logger.debug(f"Failed to browse {result.username}: {e}")
        
        return similar[:limit]
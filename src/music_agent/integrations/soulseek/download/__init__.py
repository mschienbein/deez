"""
Soulseek download manager.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..config import DownloadConfig
from ..api.transfers import TransferAPI
from ..models import FileInfo, Transfer
from ..exceptions import DownloadError

logger = logging.getLogger(__name__)


class DownloadManager:
    """Manages Soulseek downloads."""
    
    def __init__(self, transfer_api: TransferAPI, config: DownloadConfig):
        """
        Initialize download manager.
        
        Args:
            transfer_api: Transfer API instance
            config: Download configuration
        """
        self.transfer_api = transfer_api
        self.config = config
    
    async def download_file(
        self,
        file_info: FileInfo,
        output_dir: Optional[str] = None
    ) -> Optional[str]:
        """
        Download a file from search results.
        
        Args:
            file_info: FileInfo object from search
            output_dir: Optional output directory
            
        Returns:
            Path to downloaded file or None
        """
        if not output_dir:
            output_dir = self.config.output_dir
        
        # Check if file already exists
        output_path = self._get_output_path(file_info.file.filename, output_dir)
        if output_path.exists() and not self.config.overwrite:
            logger.info(f"File already exists: {output_path}")
            return str(output_path)
        
        try:
            # Download the file
            downloaded_path = await self.transfer_api.download(
                username=file_info.username,
                filename=file_info.file.filename,
                file_size=file_info.file.size,
                output_dir=output_dir
            )
            
            return downloaded_path
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise DownloadError(f"Failed to download {file_info.file.filename}: {e}")
    
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
        import asyncio
        
        if not output_dir:
            output_dir = self.config.output_dir
        
        results = []
        
        # Create download tasks in batches
        for i in range(0, len(file_infos), max_concurrent):
            batch = file_infos[i:i + max_concurrent]
            
            # Create tasks for batch
            tasks = []
            for file_info in batch:
                task = self.download_file(file_info, output_dir)
                tasks.append(task)
            
            # Wait for batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for file_info, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    results.append({
                        "file": file_info.file.filename,
                        "status": "failed",
                        "error": str(result)
                    })
                elif result:
                    results.append({
                        "file": file_info.file.filename,
                        "status": "success",
                        "path": result
                    })
                else:
                    results.append({
                        "file": file_info.file.filename,
                        "status": "failed",
                        "error": "Unknown error"
                    })
        
        return results
    
    def _get_output_path(self, filename: str, output_dir: str) -> Path:
        """
        Get output path for a file.
        
        Args:
            filename: Original filename
            output_dir: Output directory
            
        Returns:
            Path object
        """
        # Extract just the filename
        file_name = Path(filename).name
        
        # Create output directory if needed
        output_path = Path(output_dir)
        if self.config.create_folders:
            output_path.mkdir(parents=True, exist_ok=True)
        
        return output_path / file_name
    
    def get_active_downloads(self) -> List[Transfer]:
        """
        Get list of active downloads.
        
        Returns:
            List of active Transfer objects
        """
        all_downloads = self.transfer_api.get_all_downloads()
        return [d for d in all_downloads if d.is_active]
    
    def get_completed_downloads(self) -> List[Transfer]:
        """
        Get list of completed downloads.
        
        Returns:
            List of completed Transfer objects
        """
        all_downloads = self.transfer_api.get_all_downloads()
        return [d for d in all_downloads if d.is_complete]
    
    def cancel_download(self, download_id: str) -> bool:
        """
        Cancel a download.
        
        Args:
            download_id: Download ID
            
        Returns:
            True if cancelled successfully
        """
        return self.transfer_api.cancel_download(download_id)
    
    def retry_download(self, download_id: str) -> bool:
        """
        Retry a failed download.
        
        Args:
            download_id: Download ID
            
        Returns:
            True if retry initiated
        """
        return self.transfer_api.retry_download(download_id)
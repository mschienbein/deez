"""
Transfer API for Soulseek downloads and uploads.
"""

import asyncio
import logging
import time
from typing import List, Optional
from pathlib import Path

from .base import BaseAPI
from ..models import Transfer, TransferState, TransferDirection, FileInfo
from ..exceptions import DownloadError, TransferError, TimeoutError

logger = logging.getLogger(__name__)


class TransferAPI(BaseAPI):
    """API for file transfer operations."""
    
    async def download(
        self,
        username: str,
        filename: str,
        file_size: Optional[int] = None,
        output_dir: Optional[str] = None
    ) -> Optional[str]:
        """
        Download a file from Soulseek.
        
        Args:
            username: Username of the peer
            filename: Full path of the file
            file_size: Size of the file (optional)
            output_dir: Output directory
            
        Returns:
            Path to downloaded file or None if failed
        """
        self.ensure_connected()
        
        if not output_dir:
            output_dir = self.config.download.output_dir
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        try:
            # Prepare file information
            files = [{
                "filename": filename,
                "size": file_size if file_size else 0
            }]
            
            # Enqueue download
            enqueue_result = self.client.transfers.enqueue(
                username=username,
                files=files
            )
            
            # Extract download ID
            download_id = self._extract_download_id(enqueue_result)
            if not download_id:
                raise DownloadError("Failed to get download ID")
            
            logger.info(f"Enqueued download {download_id}: {filename} from {username}")
            
            # Monitor download
            output_path = await self._monitor_download(
                download_id, 
                filename, 
                output_dir
            )
            
            return output_path
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            raise DownloadError(f"Download failed: {e}")
    
    def _extract_download_id(self, enqueue_result) -> Optional[str]:
        """Extract download ID from enqueue result."""
        if not enqueue_result:
            return None
        
        if isinstance(enqueue_result, list) and enqueue_result:
            return enqueue_result[0].get("id")
        elif isinstance(enqueue_result, dict):
            return enqueue_result.get("id")
        
        return None
    
    async def _monitor_download(
        self,
        download_id: str,
        filename: str,
        output_dir: str
    ) -> Optional[str]:
        """
        Monitor download progress.
        
        Args:
            download_id: Download ID
            filename: Original filename
            output_dir: Output directory
            
        Returns:
            Path to downloaded file or None
        """
        start_time = time.time()
        max_wait = self.config.download.max_wait_time
        interval = self.config.download.monitor_interval
        
        last_progress = 0.0
        stall_counter = 0
        max_stalls = 30  # Max stalls before considering it failed
        
        while (time.time() - start_time) < max_wait:
            try:
                # Get current transfer status
                transfer = await self.get_download_status(download_id)
                
                if not transfer:
                    await asyncio.sleep(interval)
                    continue
                
                # Check if completed
                if transfer.is_complete:
                    file_name = Path(filename).name
                    output_path = str(Path(output_dir) / file_name)
                    logger.info(f"Download completed: {output_path}")
                    return output_path
                
                # Check if failed
                if transfer.is_failed:
                    error_msg = transfer.error_message or transfer.state.value
                    logger.error(f"Download failed: {error_msg}")
                    return None
                
                # Check progress
                if transfer.is_active:
                    if transfer.percent_complete > last_progress:
                        # Progress is being made
                        stall_counter = 0
                        last_progress = transfer.percent_complete
                        
                        # Log progress
                        if int(transfer.percent_complete) % 10 == 0:
                            logger.info(
                                f"Download progress: {transfer.percent_complete:.1f}% "
                                f"({transfer.transferred_mb:.1f}/{transfer.size_mb:.1f} MB) "
                                f"@ {transfer.speed_mbps:.2f} MB/s"
                            )
                    else:
                        # No progress
                        stall_counter += 1
                        if stall_counter > max_stalls:
                            logger.error("Download stalled for too long")
                            return None
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error monitoring download: {e}")
                await asyncio.sleep(interval * 2)
        
        raise TimeoutError(f"Download timed out after {max_wait} seconds")
    
    async def get_download_status(self, download_id: str) -> Optional[Transfer]:
        """
        Get status of a specific download.
        
        Args:
            download_id: Download ID
            
        Returns:
            Transfer object or None
        """
        self.ensure_connected()
        
        try:
            downloads = self.client.transfers.get_downloads()
            
            for download_data in downloads:
                if download_data.get("id") == download_id:
                    return Transfer.from_api(download_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get download status: {e}")
            return None
    
    def get_all_downloads(self) -> List[Transfer]:
        """
        Get all current downloads.
        
        Returns:
            List of Transfer objects
        """
        self.ensure_connected()
        
        try:
            downloads = self.client.transfers.get_downloads()
            return [Transfer.from_api(d) for d in downloads]
        except Exception as e:
            logger.error(f"Failed to get downloads: {e}")
            return []
    
    def get_all_uploads(self) -> List[Transfer]:
        """
        Get all current uploads.
        
        Returns:
            List of Transfer objects
        """
        self.ensure_connected()
        
        try:
            uploads = self.client.transfers.get_uploads()
            return [Transfer.from_api(u) for u in uploads]
        except Exception as e:
            logger.error(f"Failed to get uploads: {e}")
            return []
    
    def cancel_download(self, download_id: str) -> bool:
        """
        Cancel a download.
        
        Args:
            download_id: Download ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        self.ensure_connected()
        
        try:
            self.client.transfers.cancel_download(download_id)
            logger.info(f"Cancelled download {download_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel download {download_id}: {e}")
            return False
    
    def retry_download(self, download_id: str) -> bool:
        """
        Retry a failed download.
        
        Args:
            download_id: Download ID to retry
            
        Returns:
            True if retry initiated
        """
        self.ensure_connected()
        
        try:
            self.client.transfers.retry_download(download_id)
            logger.info(f"Retrying download {download_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to retry download {download_id}: {e}")
            return False
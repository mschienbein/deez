"""
Download manager for Mixcloud.

Coordinates the download process for cloudcasts.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime

import aiohttp
from aiohttp import ClientSession

from ..config import DownloadConfig
from ..models import Cloudcast
from ..types import DownloadOptions, StreamInfo
from ..exceptions import (
    DownloadError,
    StreamNotAvailableError,
    ExclusiveContentError,
)
from .stream_extractor import StreamExtractor
from .metadata import MetadataWriter
from .m3u8 import M3U8Downloader

logger = logging.getLogger(__name__)


class DownloadManager:
    """Manages cloudcast downloads."""
    
    def __init__(
        self,
        session: ClientSession,
        config: DownloadConfig,
        stream_extractor: Optional[StreamExtractor] = None
    ):
        """
        Initialize download manager.
        
        Args:
            session: aiohttp client session
            config: Download configuration
            stream_extractor: Optional stream extractor
        """
        self.session = session
        self.config = config
        self.stream_extractor = stream_extractor or StreamExtractor(session, config)
        self.metadata_writer = MetadataWriter(config)
        self.m3u8_downloader = M3U8Downloader(session, config)
        
        # Download queue
        self._download_queue = asyncio.Queue()
        self._active_downloads = {}
        self._download_lock = asyncio.Lock()
    
    async def download_cloudcast(
        self,
        cloudcast: Cloudcast,
        output_dir: Optional[str] = None,
        options: Optional[DownloadOptions] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """
        Download a cloudcast.
        
        Args:
            cloudcast: Cloudcast to download
            output_dir: Output directory (overrides config)
            options: Download options
            progress_callback: Progress callback function
            
        Returns:
            Path to downloaded file
        """
        # Check if cloudcast is exclusive
        if cloudcast.is_exclusive:
            if not options or not options.get("force_exclusive", False):
                raise ExclusiveContentError(
                    f"Cloudcast '{cloudcast.name}' is exclusive content"
                )
        
        # Get stream info
        stream_info = await self.stream_extractor.extract(cloudcast)
        
        if not stream_info:
            raise StreamNotAvailableError(f"No stream available for '{cloudcast.name}'")
        
        # Determine output path
        output_path = self._get_output_path(cloudcast, output_dir, options)
        
        # Check if file exists
        if os.path.exists(output_path) and not self.config.overwrite:
            logger.info(f"File already exists: {output_path}")
            return output_path
        
        # Download based on stream type
        if stream_info.get("hls_url"):
            # Download HLS stream
            await self._download_hls(
                stream_info["hls_url"],
                output_path,
                cloudcast,
                progress_callback
            )
        elif stream_info.get("stream_url"):
            # Download direct stream
            await self._download_direct(
                stream_info["stream_url"],
                output_path,
                cloudcast,
                progress_callback
            )
        elif stream_info.get("download_url"):
            # Download from download URL
            await self._download_direct(
                stream_info["download_url"],
                output_path,
                cloudcast,
                progress_callback
            )
        else:
            raise DownloadError("No downloadable stream found")
        
        # Write metadata if enabled
        if self.config.write_metadata:
            await self._write_metadata(output_path, cloudcast)
        
        logger.info(f"Downloaded: {cloudcast.name} -> {output_path}")
        return output_path
    
    async def download_playlist(
        self,
        cloudcasts: List[Cloudcast],
        output_dir: Optional[str] = None,
        options: Optional[DownloadOptions] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[str]:
        """
        Download multiple cloudcasts.
        
        Args:
            cloudcasts: List of cloudcasts to download
            output_dir: Output directory
            options: Download options
            progress_callback: Progress callback (current, total, status)
            
        Returns:
            List of downloaded file paths
        """
        downloaded = []
        total = len(cloudcasts)
        
        # Create semaphore for parallel downloads
        semaphore = asyncio.Semaphore(self.config.parallel_downloads)
        
        async def download_with_semaphore(index: int, cloudcast: Cloudcast):
            async with semaphore:
                try:
                    if progress_callback:
                        progress_callback(index + 1, total, f"Downloading: {cloudcast.name}")
                    
                    path = await self.download_cloudcast(
                        cloudcast,
                        output_dir,
                        options
                    )
                    return path
                except Exception as e:
                    logger.error(f"Failed to download '{cloudcast.name}': {e}")
                    return None
        
        # Download all cloudcasts
        tasks = [
            download_with_semaphore(i, cc)
            for i, cc in enumerate(cloudcasts)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=False)
        
        # Filter out failed downloads
        downloaded = [path for path in results if path]
        
        logger.info(f"Downloaded {len(downloaded)}/{total} cloudcasts")
        return downloaded
    
    async def _download_direct(
        self,
        url: str,
        output_path: str,
        cloudcast: Cloudcast,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ):
        """Download from direct URL."""
        try:
            # Get file size
            async with self.session.head(url) as response:
                total_size = int(response.headers.get("Content-Length", 0))
            
            # Download file
            downloaded = 0
            
            async with self.session.get(url) as response:
                response.raise_for_status()
                
                # Create output directory
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(self.config.chunk_size):
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress, f"Downloading: {cloudcast.name}")
            
        except Exception as e:
            logger.error(f"Download failed: {e}")
            # Clean up partial file
            if os.path.exists(output_path):
                os.remove(output_path)
            raise DownloadError(f"Failed to download: {e}")
    
    async def _download_hls(
        self,
        hls_url: str,
        output_path: str,
        cloudcast: Cloudcast,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ):
        """Download HLS stream."""
        try:
            await self.m3u8_downloader.download(
                hls_url,
                output_path,
                progress_callback
            )
        except Exception as e:
            logger.error(f"HLS download failed: {e}")
            # Clean up partial file
            if os.path.exists(output_path):
                os.remove(output_path)
            raise DownloadError(f"Failed to download HLS stream: {e}")
    
    async def _write_metadata(self, file_path: str, cloudcast: Cloudcast):
        """Write metadata to file."""
        try:
            # Download artwork if enabled
            artwork_path = None
            if self.config.embed_artwork and cloudcast.artwork_url:
                artwork_path = await self._download_artwork(cloudcast)
            
            # Write metadata
            await self.metadata_writer.write(
                file_path,
                cloudcast.get_metadata(),
                artwork_path
            )
            
            # Clean up artwork file
            if artwork_path and os.path.exists(artwork_path):
                os.remove(artwork_path)
            
        except Exception as e:
            logger.warning(f"Failed to write metadata: {e}")
    
    async def _download_artwork(self, cloudcast: Cloudcast) -> Optional[str]:
        """Download cloudcast artwork."""
        if not cloudcast.artwork_url:
            return None
        
        try:
            # Create temp file
            import tempfile
            fd, temp_path = tempfile.mkstemp(suffix=".jpg")
            os.close(fd)
            
            # Download artwork
            async with self.session.get(cloudcast.artwork_url) as response:
                response.raise_for_status()
                with open(temp_path, "wb") as f:
                    f.write(await response.read())
            
            return temp_path
            
        except Exception as e:
            logger.warning(f"Failed to download artwork: {e}")
            return None
    
    def _get_output_path(
        self,
        cloudcast: Cloudcast,
        output_dir: Optional[str] = None,
        options: Optional[DownloadOptions] = None
    ) -> str:
        """Generate output file path."""
        # Use provided dir or config default
        base_dir = output_dir or self.config.download_dir
        
        # Create user/show folders if enabled
        if self.config.create_folders:
            base_dir = os.path.join(base_dir, cloudcast.username)
        
        # Generate filename from template
        filename = self.config.filename_template.format(
            user=cloudcast.username,
            name=self._sanitize_filename(cloudcast.name),
            date=cloudcast.created_time.strftime("%Y%m%d") if cloudcast.created_time else "",
            id=cloudcast.id
        )
        
        # Add extension
        format = options.get("format", self.config.format) if options else self.config.format
        if not filename.endswith(f".{format}"):
            filename += f".{format}"
        
        # Build full path
        output_path = os.path.join(base_dir, filename)
        
        # Create directory
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        return output_path
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize filename for filesystem."""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "_")
        
        # Limit length
        max_length = 200
        if len(name) > max_length:
            name = name[:max_length]
        
        return name.strip()


__all__ = ["DownloadManager"]
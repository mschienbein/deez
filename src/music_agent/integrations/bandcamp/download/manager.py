"""
Download manager for Bandcamp.
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, List, Callable, Union
import aiohttp
from aiohttp import ClientSession

from ..config import DownloadConfig
from ..models import Track, Album
from ..types import DownloadOptions
from ..exceptions import DownloadError, StreamNotAvailableError
from .metadata import MetadataWriter

logger = logging.getLogger(__name__)


class DownloadManager:
    """Manages Bandcamp downloads."""
    
    def __init__(self, session: ClientSession, config: DownloadConfig):
        """
        Initialize download manager.
        
        Args:
            session: aiohttp session
            config: Download configuration
        """
        self.session = session
        self.config = config
        self.metadata_writer = MetadataWriter(config)
    
    async def download_track(
        self,
        track: Track,
        output_dir: Optional[str] = None,
        options: Optional[DownloadOptions] = None,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> str:
        """
        Download a track.
        
        Args:
            track: Track to download
            output_dir: Output directory
            options: Download options
            progress_callback: Progress callback
            
        Returns:
            Path to downloaded file
        """
        # Check if track can be downloaded
        if not track.is_downloadable:
            raise StreamNotAvailableError(f"Track '{track.title}' is not downloadable")
        
        # Get stream URL
        stream_url = track.download_url or track.stream_url
        if not stream_url:
            raise StreamNotAvailableError(f"No stream URL for track '{track.title}'")
        
        # Determine output path
        output_path = self._get_output_path(track, output_dir, options)
        
        # Check if file exists
        if os.path.exists(output_path) and not self.config.overwrite:
            logger.info(f"File already exists: {output_path}")
            return output_path
        
        # Download file
        await self._download_file(stream_url, output_path, track.title, progress_callback)
        
        # Write metadata
        if self.config.write_metadata:
            await self._write_metadata(output_path, track)
        
        logger.info(f"Downloaded: {track.title} -> {output_path}")
        return output_path
    
    async def download_album(
        self,
        album: Album,
        output_dir: Optional[str] = None,
        options: Optional[DownloadOptions] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> List[str]:
        """
        Download an entire album.
        
        Args:
            album: Album to download
            output_dir: Output directory
            options: Download options
            progress_callback: Progress callback (current, total, status)
            
        Returns:
            List of downloaded file paths
        """
        downloaded = []
        downloadable_tracks = album.get_downloadable_tracks()
        
        if not downloadable_tracks:
            raise DownloadError(f"No downloadable tracks in album '{album.title}'")
        
        total = len(downloadable_tracks)
        
        # Create album directory
        if self.config.create_album_folders:
            album_dir = self._get_album_dir(album, output_dir)
            output_dir = album_dir
        
        # Download tracks
        semaphore = asyncio.Semaphore(self.config.parallel_downloads)
        
        async def download_with_semaphore(index: int, track: Track):
            async with semaphore:
                try:
                    if progress_callback:
                        progress_callback(index + 1, total, f"Downloading: {track.title}")
                    
                    # Inherit album metadata
                    track.album = album.title
                    track.artist = track.artist or album.artist
                    
                    path = await self.download_track(track, output_dir, options)
                    return path
                except Exception as e:
                    logger.error(f"Failed to download '{track.title}': {e}")
                    return None
        
        tasks = [
            download_with_semaphore(i, track)
            for i, track in enumerate(downloadable_tracks)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=False)
        downloaded = [path for path in results if path]
        
        # Download artwork if available
        if album.artwork_url and self.config.embed_artwork:
            artwork_path = await self._download_artwork(album.artwork_url, output_dir)
            if artwork_path:
                logger.debug(f"Downloaded artwork to {artwork_path}")
        
        logger.info(f"Downloaded {len(downloaded)}/{total} tracks from '{album.title}'")
        return downloaded
    
    async def _download_file(
        self,
        url: str,
        output_path: str,
        name: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ):
        """Download a file from URL."""
        try:
            # Create output directory
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            async with self.session.get(url) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                
                with open(output_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(self.config.chunk_size):
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress, f"Downloading: {name}")
        
        except aiohttp.ClientError as e:
            # Clean up partial file
            if os.path.exists(output_path):
                os.remove(output_path)
            raise DownloadError(f"Download failed: {e}")
    
    async def _download_artwork(self, url: str, output_dir: str) -> Optional[str]:
        """Download album artwork."""
        try:
            output_path = os.path.join(output_dir, "cover.jpg")
            
            async with self.session.get(url) as response:
                response.raise_for_status()
                
                with open(output_path, "wb") as f:
                    f.write(await response.read())
            
            return output_path
            
        except Exception as e:
            logger.warning(f"Failed to download artwork: {e}")
            return None
    
    async def _write_metadata(self, file_path: str, track: Track):
        """Write metadata to file."""
        try:
            # Get artwork path if it exists
            artwork_path = None
            if self.config.embed_artwork:
                # Look for cover.jpg in same directory
                dir_path = os.path.dirname(file_path)
                cover_path = os.path.join(dir_path, "cover.jpg")
                if os.path.exists(cover_path):
                    artwork_path = cover_path
            
            # Write metadata
            metadata = track.get_metadata()
            
            # Add lyrics if enabled
            if self.config.embed_lyrics and track.lyrics:
                metadata["lyrics"] = track.lyrics
            
            await self.metadata_writer.write(file_path, metadata, artwork_path)
            
        except Exception as e:
            logger.warning(f"Failed to write metadata: {e}")
    
    def _get_output_path(
        self,
        track: Track,
        output_dir: Optional[str] = None,
        options: Optional[DownloadOptions] = None
    ) -> str:
        """Generate output file path."""
        # Use provided dir or config default
        base_dir = output_dir or self.config.download_dir
        
        # Create artist folder if enabled
        if self.config.create_artist_folders and track.artist:
            base_dir = os.path.join(base_dir, self._sanitize_filename(track.artist))
        
        # Generate filename from template
        filename = self.config.filename_template.format(
            artist=self._sanitize_filename(track.artist or "Unknown"),
            title=self._sanitize_filename(track.title),
            album=self._sanitize_filename(track.album or ""),
            track=track.track_num or "",
        )
        
        # Add extension
        ext = options.get("format", self.config.format) if options else self.config.format
        if not filename.endswith(f".{ext}"):
            filename += f".{ext}"
        
        return os.path.join(base_dir, filename)
    
    def _get_album_dir(self, album: Album, output_dir: Optional[str] = None) -> str:
        """Get album directory path."""
        base_dir = output_dir or self.config.download_dir
        
        # Create artist folder
        if self.config.create_artist_folders and album.artist:
            base_dir = os.path.join(base_dir, self._sanitize_filename(album.artist))
        
        # Create album folder
        album_dir = os.path.join(base_dir, self._sanitize_filename(album.title))
        Path(album_dir).mkdir(parents=True, exist_ok=True)
        
        return album_dir
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize filename for filesystem."""
        if not name:
            return ""
        
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "_")
        
        # Limit length
        if len(name) > 200:
            name = name[:200]
        
        return name.strip()


__all__ = ["DownloadManager"]
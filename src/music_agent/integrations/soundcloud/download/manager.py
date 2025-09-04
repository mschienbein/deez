"""
Download manager for SoundCloud tracks.

Coordinates downloads, handles different stream types, and manages metadata.
"""

import logging
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import aiofiles

from ..config import DownloadConfig
from ..types import DownloadOptions
from ..models import Track, Playlist
from ..exceptions import (
    DownloadError,
    TrackNotDownloadableError,
    StreamNotAvailableError,
)
from .stream_handler import StreamHandler
from .metadata import MetadataWriter
from .hls import HLSDownloader

logger = logging.getLogger(__name__)


class DownloadManager:
    """Manages track downloads from SoundCloud."""
    
    def __init__(self, client, config: Optional[DownloadConfig] = None):
        """
        Initialize download manager.
        
        Args:
            client: SoundCloud client instance
            config: Download configuration
        """
        self.client = client
        self.config = config or DownloadConfig()
        self.stream_handler = StreamHandler(client)
        self.metadata_writer = MetadataWriter()
        self.hls_downloader = HLSDownloader(config)
        
        # Thread pool for parallel downloads
        self._executor = ThreadPoolExecutor(max_workers=config.parallel_downloads)
    
    async def download_track(
        self,
        track: Track,
        options: Optional[DownloadOptions] = None
    ) -> Path:
        """
        Download a single track.
        
        Args:
            track: Track to download
            options: Download options
            
        Returns:
            Path to downloaded file
            
        Raises:
            DownloadError: If download fails
        """
        opts = options or {}
        
        # Determine output path
        output_path = self._get_output_path(track, opts)
        
        # Check if file already exists
        if output_path.exists() and not opts.get("overwrite", False):
            logger.info(f"File already exists: {output_path}")
            return output_path
        
        try:
            # Get stream URL
            stream_info = await self.stream_handler.get_stream_info(track)
            
            if not stream_info:
                raise StreamNotAvailableError(f"No stream available for track {track.id}")
            
            # Download based on stream type
            if stream_info["protocol"] == "hls":
                if not self.config.enable_hls:
                    raise TrackNotDownloadableError(
                        "Track requires HLS download which is disabled"
                    )
                
                await self.hls_downloader.download(
                    stream_info["url"],
                    output_path,
                    opts.get("progress_callback")
                )
            else:
                # Progressive download
                await self._download_progressive(
                    stream_info["url"],
                    output_path,
                    opts
                )
            
            # Write metadata if enabled
            if opts.get("write_metadata", self.config.write_metadata):
                artwork_data = None
                
                if opts.get("embed_artwork", self.config.embed_artwork):
                    artwork_data = await self._download_artwork(track, opts)
                
                await self.metadata_writer.write_metadata(
                    output_path,
                    track,
                    artwork_data
                )
            
            logger.info(f"Downloaded: {track.title} -> {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to download track {track.id}: {e}")
            
            # Clean up partial file
            if output_path.exists():
                output_path.unlink()
            
            raise DownloadError(f"Download failed: {e}")
    
    async def download_playlist(
        self,
        playlist: Playlist,
        output_dir: Optional[str] = None,
        options: Optional[DownloadOptions] = None
    ) -> List[Path]:
        """
        Download all tracks in a playlist.
        
        Args:
            playlist: Playlist to download
            output_dir: Output directory
            options: Download options
            
        Returns:
            List of downloaded file paths
        """
        opts = options or {}
        
        # Determine output directory
        if output_dir:
            base_dir = Path(output_dir)
        else:
            base_dir = self.config.download_dir / self._sanitize_filename(playlist.title)
        
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Download tracks
        downloaded = []
        failed = []
        
        # Use semaphore to limit concurrent downloads
        semaphore = asyncio.Semaphore(self.config.parallel_downloads)
        
        async def download_with_semaphore(track: Track, index: int):
            async with semaphore:
                try:
                    # Add track number to options
                    track_opts = dict(opts)
                    track_opts["track_number"] = index + 1
                    track_opts["album"] = playlist.title
                    
                    path = await self.download_track(track, track_opts)
                    return path, None
                except Exception as e:
                    logger.error(f"Failed to download {track.title}: {e}")
                    return None, (track, e)
        
        # Create tasks
        tasks = [
            download_with_semaphore(track, idx)
            for idx, track in enumerate(playlist.tracks)
        ]
        
        # Execute downloads
        results = await asyncio.gather(*tasks)
        
        for path, error in results:
            if path:
                downloaded.append(path)
            elif error:
                failed.append(error)
        
        # Create M3U playlist file
        if opts.get("create_m3u", True):
            m3u_path = base_dir / f"{self._sanitize_filename(playlist.title)}.m3u"
            await self._create_m3u(m3u_path, downloaded)
        
        # Report failures
        if failed:
            logger.warning(f"Failed to download {len(failed)} tracks:")
            for track, error in failed:
                logger.warning(f"  - {track.title}: {error}")
        
        logger.info(f"Downloaded {len(downloaded)}/{len(playlist.tracks)} tracks")
        return downloaded
    
    async def _download_progressive(
        self,
        url: str,
        output_path: Path,
        options: Dict[str, Any]
    ):
        """Download using progressive streaming."""
        chunk_size = options.get("chunk_size", self.config.chunk_size)
        progress_callback = options.get("progress_callback")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                
                async with aiofiles.open(output_path, "wb") as file:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        await file.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback:
                            progress_callback(downloaded, total_size)
    
    async def _download_artwork(
        self,
        track: Track,
        options: Dict[str, Any]
    ) -> Optional[bytes]:
        """Download track artwork."""
        if not track.artwork_url:
            return None
        
        # Get high quality artwork URL
        size = options.get("artwork_size", self.config.artwork_size)
        
        if size == "original":
            artwork_url = track.artwork_url.replace("-large", "-original")
        elif size in ["t500x500", "t300x300", "t67x67"]:
            artwork_url = track.artwork_url.replace("-large", f"-{size}")
        else:
            artwork_url = track.artwork_url_high
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(artwork_url) as response:
                    if response.status == 200:
                        return await response.read()
        except Exception as e:
            logger.warning(f"Failed to download artwork: {e}")
        
        return None
    
    def _get_output_path(self, track: Track, options: Dict[str, Any]) -> Path:
        """Determine output path for track."""
        if options.get("output_path"):
            return Path(options["output_path"])
        
        # Generate filename
        filename = self._generate_filename(track, options)
        
        # Add to download directory
        return self.config.download_dir / filename
    
    def _generate_filename(self, track: Track, options: Dict[str, Any]) -> str:
        """Generate filename for track."""
        # Get format from options
        template = options.get(
            "filename_template",
            "{artist} - {title}{album_part}.mp3"
        )
        
        # Prepare album part
        album_part = ""
        if track.album or options.get("album"):
            album = track.album or options["album"]
            track_no = track.track_number or options.get("track_number", "")
            
            if track_no:
                album_part = f" [{album} #{track_no}]"
            else:
                album_part = f" [{album}]"
        
        # Format filename
        filename = template.format(
            artist=self._sanitize_filename(track.artist),
            title=self._sanitize_filename(track.title),
            album=self._sanitize_filename(track.album or ""),
            track_number=track.track_number or "",
            album_part=album_part,
        )
        
        # Ensure .mp3 extension
        if not filename.endswith(".mp3"):
            filename += ".mp3"
        
        return filename
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize filename for filesystem."""
        if not name:
            return "Unknown"
        
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, "_")
        
        # Remove control characters
        name = "".join(c for c in name if ord(c) >= 32)
        
        # Limit length
        max_length = 200
        if len(name) > max_length:
            name = name[:max_length]
        
        return name.strip()
    
    async def _create_m3u(self, path: Path, files: List[Path]):
        """Create M3U playlist file."""
        content = "#EXTM3U\n"
        
        for file_path in files:
            # Use relative path if in same directory
            if file_path.parent == path.parent:
                content += f"{file_path.name}\n"
            else:
                content += f"{file_path}\n"
        
        async with aiofiles.open(path, "w") as f:
            await f.write(content)
    
    def __del__(self):
        """Clean up thread pool."""
        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=False)


__all__ = ["DownloadManager"]
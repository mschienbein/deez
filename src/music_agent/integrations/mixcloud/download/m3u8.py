"""
M3U8/HLS stream downloader for Mixcloud.

Handles downloading and assembling HLS streams.
"""

import asyncio
import logging
import os
import tempfile
from typing import Optional, List, Callable
from urllib.parse import urljoin, urlparse

import aiohttp
from aiohttp import ClientSession

from ..config import DownloadConfig
from ..exceptions import DownloadError

logger = logging.getLogger(__name__)


class M3U8Downloader:
    """Downloads and assembles M3U8/HLS streams."""
    
    def __init__(self, session: ClientSession, config: DownloadConfig):
        """
        Initialize M3U8 downloader.
        
        Args:
            session: aiohttp client session
            config: Download configuration
        """
        self.session = session
        self.config = config
        self._ffmpeg_available = self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available."""
        try:
            import subprocess
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.SubprocessError):
            logger.warning("ffmpeg not found - HLS download may fail")
            return False
    
    async def download(
        self,
        m3u8_url: str,
        output_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """
        Download M3U8 stream.
        
        Args:
            m3u8_url: URL to M3U8 playlist
            output_path: Output file path
            progress_callback: Progress callback
            
        Returns:
            True if successful
        """
        try:
            # If ffmpeg is available, use it for better compatibility
            if self._ffmpeg_available:
                return await self._download_with_ffmpeg(
                    m3u8_url, output_path, progress_callback
                )
            else:
                # Fall back to manual segment download
                return await self._download_segments(
                    m3u8_url, output_path, progress_callback
                )
            
        except Exception as e:
            logger.error(f"M3U8 download failed: {e}")
            raise DownloadError(f"Failed to download HLS stream: {e}")
    
    async def _download_with_ffmpeg(
        self,
        m3u8_url: str,
        output_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """Download using ffmpeg."""
        import subprocess
        
        try:
            # Build ffmpeg command
            cmd = [
                "ffmpeg",
                "-i", m3u8_url,
                "-c", "copy",  # Copy codec, don't re-encode
                "-bsf:a", "aac_adtstoasc",  # Fix for AAC audio
                "-y",  # Overwrite output
                output_path
            ]
            
            # Run ffmpeg
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Monitor progress if callback provided
            if progress_callback:
                asyncio.create_task(
                    self._monitor_ffmpeg_progress(
                        process, progress_callback, "Downloading HLS stream"
                    )
                )
            
            # Wait for completion
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                raise DownloadError(f"ffmpeg failed: {error_msg}")
            
            return True
            
        except Exception as e:
            logger.error(f"ffmpeg download failed: {e}")
            raise
    
    async def _monitor_ffmpeg_progress(
        self,
        process,
        progress_callback: Callable,
        status: str
    ):
        """Monitor ffmpeg progress."""
        # Simple progress simulation since ffmpeg progress parsing is complex
        progress = 0
        while process.returncode is None:
            await asyncio.sleep(1)
            progress = min(progress + 5, 95)
            progress_callback(progress, status)
        
        progress_callback(100, "Download complete")
    
    async def _download_segments(
        self,
        m3u8_url: str,
        output_path: str,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> bool:
        """Download M3U8 segments manually."""
        try:
            # Parse M3U8 playlist
            segments = await self._parse_m3u8(m3u8_url)
            
            if not segments:
                raise DownloadError("No segments found in M3U8 playlist")
            
            # Create temp directory for segments
            with tempfile.TemporaryDirectory() as temp_dir:
                # Download all segments
                segment_files = await self._download_all_segments(
                    segments, temp_dir, progress_callback
                )
                
                # Combine segments
                await self._combine_segments(segment_files, output_path)
            
            return True
            
        except Exception as e:
            logger.error(f"Segment download failed: {e}")
            raise
    
    async def _parse_m3u8(self, m3u8_url: str) -> List[str]:
        """Parse M3U8 playlist and extract segment URLs."""
        try:
            async with self.session.get(m3u8_url) as response:
                response.raise_for_status()
                content = await response.text()
            
            segments = []
            base_url = urljoin(m3u8_url, ".")
            
            for line in content.split("\n"):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith("#"):
                    continue
                
                # Build absolute URL
                if line.startswith("http"):
                    segment_url = line
                else:
                    segment_url = urljoin(base_url, line)
                
                segments.append(segment_url)
            
            # Check if this is a master playlist
            if "#EXT-X-STREAM-INF" in content:
                # Get the highest quality stream
                for segment_url in segments:
                    # Recursively parse the actual segment playlist
                    return await self._parse_m3u8(segment_url)
            
            return segments
            
        except Exception as e:
            logger.error(f"Failed to parse M3U8: {e}")
            raise DownloadError(f"Failed to parse M3U8 playlist: {e}")
    
    async def _download_all_segments(
        self,
        segments: List[str],
        temp_dir: str,
        progress_callback: Optional[Callable] = None
    ) -> List[str]:
        """Download all segments."""
        segment_files = []
        total = len(segments)
        
        # Create semaphore for concurrent downloads
        semaphore = asyncio.Semaphore(5)  # Limit concurrent downloads
        
        async def download_segment(index: int, url: str):
            async with semaphore:
                file_path = os.path.join(temp_dir, f"segment_{index:05d}.ts")
                
                try:
                    async with self.session.get(url) as response:
                        response.raise_for_status()
                        with open(file_path, "wb") as f:
                            f.write(await response.read())
                    
                    if progress_callback:
                        progress = ((index + 1) / total) * 100
                        progress_callback(
                            progress,
                            f"Downloading segments: {index + 1}/{total}"
                        )
                    
                    return file_path
                    
                except Exception as e:
                    logger.error(f"Failed to download segment {index}: {e}")
                    return None
        
        # Download all segments
        tasks = [
            download_segment(i, url)
            for i, url in enumerate(segments)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Filter out failed downloads
        segment_files = [f for f in results if f]
        
        if len(segment_files) < len(segments):
            logger.warning(
                f"Downloaded {len(segment_files)}/{len(segments)} segments"
            )
        
        return segment_files
    
    async def _combine_segments(
        self,
        segment_files: List[str],
        output_path: str
    ):
        """Combine segment files into single output file."""
        try:
            # Create output directory
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Combine segments
            with open(output_path, "wb") as output:
                for segment_file in sorted(segment_files):
                    if os.path.exists(segment_file):
                        with open(segment_file, "rb") as segment:
                            output.write(segment.read())
            
            logger.debug(f"Combined {len(segment_files)} segments into {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to combine segments: {e}")
            raise DownloadError(f"Failed to combine segments: {e}")


__all__ = ["M3U8Downloader"]
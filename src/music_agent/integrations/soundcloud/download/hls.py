"""
HLS stream downloader for SoundCloud.

Handles M3U8 playlist parsing and segment assembly.
"""

import logging
import asyncio
import re
from pathlib import Path
from typing import Optional, Callable, List, Dict, Any
from urllib.parse import urljoin, urlparse
import aiohttp
import aiofiles
from io import BytesIO

logger = logging.getLogger(__name__)


class HLSDownloader:
    """Downloads and assembles HLS streams."""
    
    def __init__(self, config=None):
        """
        Initialize HLS downloader.
        
        Args:
            config: Optional download configuration
        """
        self.config = config
        self.chunk_size = getattr(config, "chunk_size", 8192)
        self.max_retries = getattr(config, "max_retries", 3)
        self.parallel_segments = getattr(config, "parallel_downloads", 4)
    
    async def download(
        self,
        manifest_url: str,
        output_path: Path,
        progress_callback: Optional[Callable] = None
    ) -> bool:
        """
        Download HLS stream to file.
        
        Args:
            manifest_url: M3U8 manifest URL
            output_path: Output file path
            progress_callback: Optional progress callback(downloaded, total)
            
        Returns:
            True if successful
        """
        try:
            # Parse manifest
            segments = await self._parse_manifest(manifest_url)
            
            if not segments:
                logger.error("No segments found in manifest")
                return False
            
            # Calculate total size (if available)
            total_size = sum(s.get("size", 0) for s in segments)
            if total_size == 0:
                # Estimate based on duration and bitrate
                total_duration = sum(s.get("duration", 0) for s in segments)
                estimated_bitrate = 128000  # 128 kbps estimate
                total_size = int(total_duration * estimated_bitrate / 8)
            
            # Download segments
            downloaded = 0
            
            # Use temporary file for assembly
            temp_path = output_path.with_suffix(".tmp")
            
            async with aiofiles.open(temp_path, "wb") as output_file:
                # Download segments with concurrency limit
                semaphore = asyncio.Semaphore(self.parallel_segments)
                
                async def download_segment(segment: Dict[str, Any], index: int):
                    async with semaphore:
                        for attempt in range(self.max_retries):
                            try:
                                data = await self._download_segment(segment["url"])
                                return index, data
                            except Exception as e:
                                if attempt == self.max_retries - 1:
                                    logger.error(f"Failed to download segment {index}: {e}")
                                    raise
                                await asyncio.sleep(2 ** attempt)
                
                # Create download tasks
                tasks = [
                    download_segment(segment, idx)
                    for idx, segment in enumerate(segments)
                ]
                
                # Download and write in order
                results = await asyncio.gather(*tasks)
                results.sort(key=lambda x: x[0])  # Sort by index
                
                for idx, data in results:
                    await output_file.write(data)
                    downloaded += len(data)
                    
                    if progress_callback:
                        progress_callback(downloaded, total_size)
            
            # Move temp file to final location
            temp_path.rename(output_path)
            
            logger.info(f"HLS download complete: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"HLS download failed: {e}")
            
            # Clean up temp file
            temp_path = output_path.with_suffix(".tmp")
            if temp_path.exists():
                temp_path.unlink()
            
            return False
    
    async def _parse_manifest(self, manifest_url: str) -> List[Dict[str, Any]]:
        """
        Parse M3U8 manifest file.
        
        Args:
            manifest_url: URL to M3U8 manifest
            
        Returns:
            List of segment dictionaries
        """
        segments = []
        
        async with aiohttp.ClientSession() as session:
            async with session.get(manifest_url) as response:
                response.raise_for_status()
                content = await response.text()
        
        # Parse base URL
        base_url = urljoin(manifest_url, ".")
        
        # Parse manifest
        lines = content.strip().split("\n")
        current_duration = 0
        current_size = 0
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Duration tag
            if line.startswith("#EXTINF:"):
                match = re.match(r"#EXTINF:([\d.]+)", line)
                if match:
                    current_duration = float(match.group(1))
            
            # Byterange tag
            elif line.startswith("#EXT-X-BYTERANGE:"):
                match = re.match(r"#EXT-X-BYTERANGE:(\d+)(?:@(\d+))?", line)
                if match:
                    current_size = int(match.group(1))
            
            # Segment URL
            elif line and not line.startswith("#"):
                # Make absolute URL
                if line.startswith("http"):
                    url = line
                else:
                    url = urljoin(base_url, line)
                
                segments.append({
                    "url": url,
                    "duration": current_duration,
                    "size": current_size,
                })
                
                # Reset for next segment
                current_duration = 0
                current_size = 0
        
        return segments
    
    async def _download_segment(self, url: str) -> bytes:
        """
        Download a single segment.
        
        Args:
            url: Segment URL
            
        Returns:
            Segment data
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.read()
    
    async def download_to_memory(
        self,
        manifest_url: str,
        progress_callback: Optional[Callable] = None
    ) -> Optional[bytes]:
        """
        Download HLS stream to memory.
        
        Args:
            manifest_url: M3U8 manifest URL
            progress_callback: Optional progress callback
            
        Returns:
            Complete stream data or None
        """
        try:
            # Parse manifest
            segments = await self._parse_manifest(manifest_url)
            
            if not segments:
                return None
            
            # Calculate total size
            total_size = sum(s.get("size", 0) for s in segments)
            downloaded = 0
            
            # Download segments
            buffer = BytesIO()
            
            for segment in segments:
                data = await self._download_segment(segment["url"])
                buffer.write(data)
                downloaded += len(data)
                
                if progress_callback:
                    progress_callback(downloaded, total_size)
            
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to download to memory: {e}")
            return None
    
    def extract_info(self, manifest_content: str) -> Dict[str, Any]:
        """
        Extract information from M3U8 manifest.
        
        Args:
            manifest_content: M3U8 manifest content
            
        Returns:
            Dictionary with stream info
        """
        info = {
            "version": None,
            "target_duration": None,
            "media_sequence": 0,
            "segments": 0,
            "total_duration": 0,
            "has_encryption": False,
            "playlist_type": None,
        }
        
        lines = manifest_content.strip().split("\n")
        segment_count = 0
        total_duration = 0
        
        for line in lines:
            line = line.strip()
            
            # Version
            if line.startswith("#EXT-X-VERSION:"):
                info["version"] = int(line.split(":")[1])
            
            # Target duration
            elif line.startswith("#EXT-X-TARGETDURATION:"):
                info["target_duration"] = int(line.split(":")[1])
            
            # Media sequence
            elif line.startswith("#EXT-X-MEDIA-SEQUENCE:"):
                info["media_sequence"] = int(line.split(":")[1])
            
            # Playlist type
            elif line.startswith("#EXT-X-PLAYLIST-TYPE:"):
                info["playlist_type"] = line.split(":")[1]
            
            # Encryption
            elif line.startswith("#EXT-X-KEY:"):
                info["has_encryption"] = True
            
            # Duration
            elif line.startswith("#EXTINF:"):
                match = re.match(r"#EXTINF:([\d.]+)", line)
                if match:
                    total_duration += float(match.group(1))
            
            # Segment URL
            elif line and not line.startswith("#"):
                segment_count += 1
        
        info["segments"] = segment_count
        info["total_duration"] = total_duration
        
        return info


class HLSParser:
    """Utility class for parsing HLS manifests."""
    
    @staticmethod
    def is_master_playlist(content: str) -> bool:
        """Check if manifest is a master playlist."""
        return "#EXT-X-STREAM-INF:" in content
    
    @staticmethod
    def parse_master_playlist(content: str, base_url: str) -> List[Dict[str, Any]]:
        """
        Parse master playlist for variant streams.
        
        Args:
            content: M3U8 content
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of variant stream info
        """
        variants = []
        lines = content.strip().split("\n")
        
        current_info = {}
        
        for line in lines:
            line = line.strip()
            
            if line.startswith("#EXT-X-STREAM-INF:"):
                # Parse stream info
                current_info = HLSParser._parse_stream_info(line)
            
            elif line and not line.startswith("#") and current_info:
                # This is the URL
                if line.startswith("http"):
                    url = line
                else:
                    url = urljoin(base_url, line)
                
                current_info["url"] = url
                variants.append(current_info)
                current_info = {}
        
        return variants
    
    @staticmethod
    def _parse_stream_info(line: str) -> Dict[str, Any]:
        """Parse EXT-X-STREAM-INF tag."""
        info = {}
        
        # Remove tag prefix
        attrs = line.replace("#EXT-X-STREAM-INF:", "")
        
        # Parse attributes
        for attr in attrs.split(","):
            if "=" in attr:
                key, value = attr.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"')
                
                if key == "BANDWIDTH":
                    info["bandwidth"] = int(value)
                elif key == "CODECS":
                    info["codecs"] = value
                elif key == "RESOLUTION":
                    width, height = value.split("x")
                    info["resolution"] = {
                        "width": int(width),
                        "height": int(height),
                    }
                elif key == "FRAME-RATE":
                    info["frame_rate"] = float(value)
        
        return info
    
    @staticmethod
    def select_best_variant(variants: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Select best variant from list."""
        if not variants:
            return None
        
        # Sort by bandwidth (highest first)
        sorted_variants = sorted(
            variants,
            key=lambda v: v.get("bandwidth", 0),
            reverse=True
        )
        
        return sorted_variants[0]


__all__ = ["HLSDownloader", "HLSParser"]
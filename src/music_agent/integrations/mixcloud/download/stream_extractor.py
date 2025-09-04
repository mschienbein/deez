"""
Stream URL extractor for Mixcloud.

Extracts downloadable stream URLs from cloudcasts.
"""

import logging
import re
import json
from typing import Optional, Dict, Any
from urllib.parse import urljoin

import aiohttp
from aiohttp import ClientSession

from ..config import DownloadConfig, StreamConfig
from ..models import Cloudcast
from ..types import StreamInfo
from ..exceptions import StreamNotAvailableError, ExclusiveContentError

logger = logging.getLogger(__name__)


class StreamExtractor:
    """Extracts stream URLs from Mixcloud cloudcasts."""
    
    def __init__(self, session: ClientSession, config: DownloadConfig):
        """
        Initialize stream extractor.
        
        Args:
            session: aiohttp client session
            config: Download configuration
        """
        self.session = session
        self.config = config
        self.stream_config = StreamConfig()
    
    async def extract(self, cloudcast: Cloudcast) -> Optional[StreamInfo]:
        """
        Extract stream information from cloudcast.
        
        Args:
            cloudcast: Cloudcast to extract from
            
        Returns:
            Stream information or None
        """
        # Check if exclusive content
        if cloudcast.is_exclusive:
            logger.warning(f"Cloudcast '{cloudcast.name}' is exclusive content")
            if not self.stream_config.fallback_to_preview:
                raise ExclusiveContentError("Exclusive content cannot be downloaded")
        
        # Try different extraction methods
        stream_info = None
        
        if self.stream_config.extract_method in ["api", "hybrid"]:
            stream_info = await self._extract_from_api(cloudcast)
        
        if not stream_info and self.stream_config.extract_method in ["scrape", "hybrid"]:
            stream_info = await self._extract_from_page(cloudcast)
        
        if not stream_info and cloudcast.preview_url and self.stream_config.fallback_to_preview:
            stream_info = {
                "preview_url": cloudcast.preview_url,
                "quality": "preview",
                "duration": cloudcast.duration_seconds,
            }
        
        return stream_info
    
    async def _extract_from_api(self, cloudcast: Cloudcast) -> Optional[StreamInfo]:
        """Extract stream from API."""
        try:
            # Try embed API endpoint
            embed_url = f"https://api.mixcloud.com{cloudcast.key}embed-json/"
            
            async with self.session.get(embed_url) as response:
                if response.status != 200:
                    return None
                
                data = await response.json()
                
                stream_info = {}
                
                # Extract stream URLs
                if "stream_url" in data:
                    stream_info["stream_url"] = data["stream_url"]
                
                if "preview_url" in data:
                    stream_info["preview_url"] = data["preview_url"]
                
                # Check for HLS URL
                if "hls_url" in data:
                    stream_info["hls_url"] = data["hls_url"]
                
                # Check for download URL
                if cloudcast.download_url:
                    stream_info["download_url"] = cloudcast.download_url
                
                if stream_info:
                    stream_info.update({
                        "quality": "high" if "stream_url" in stream_info else "preview",
                        "duration": cloudcast.duration_seconds,
                        "format": "m4a" if "hls_url" in stream_info else "mp3",
                    })
                    return stream_info
                
        except Exception as e:
            logger.debug(f"API extraction failed: {e}")
        
        return None
    
    async def _extract_from_page(self, cloudcast: Cloudcast) -> Optional[StreamInfo]:
        """Extract stream by scraping page."""
        try:
            # Get cloudcast page
            page_url = cloudcast.mixcloud_url
            
            async with self.session.get(page_url) as response:
                if response.status != 200:
                    return None
                
                html = await response.text()
                
                # Look for stream data in page
                stream_info = self._parse_page_for_stream(html)
                
                if stream_info:
                    stream_info["duration"] = cloudcast.duration_seconds
                    return stream_info
                
        except Exception as e:
            logger.debug(f"Page extraction failed: {e}")
        
        return None
    
    def _parse_page_for_stream(self, html: str) -> Optional[StreamInfo]:
        """Parse HTML page for stream URLs."""
        stream_info = {}
        
        # Look for HLS stream URL
        hls_pattern = r'"hls_url"\s*:\s*"([^"]+)"'
        hls_match = re.search(hls_pattern, html)
        if hls_match:
            stream_info["hls_url"] = hls_match.group(1).replace("\\", "")
        
        # Look for preview URL
        preview_pattern = r'"preview_url"\s*:\s*"([^"]+)"'
        preview_match = re.search(preview_pattern, html)
        if preview_match:
            stream_info["preview_url"] = preview_match.group(1).replace("\\", "")
        
        # Look for stream URL
        stream_pattern = r'"stream_url"\s*:\s*"([^"]+)"'
        stream_match = re.search(stream_pattern, html)
        if stream_match:
            stream_info["stream_url"] = stream_match.group(1).replace("\\", "")
        
        # Look for encrypted streams (needs decryption)
        encrypted_pattern = r'"encrypted_play_info"\s*:\s*"([^"]+)"'
        encrypted_match = re.search(encrypted_pattern, html)
        if encrypted_match:
            encrypted_data = encrypted_match.group(1)
            # Try to decrypt (simplified - actual implementation would be more complex)
            decrypted = self._decrypt_stream_data(encrypted_data)
            if decrypted:
                stream_info.update(decrypted)
        
        # Look for React props data
        props_pattern = r'window\.__NUXT__\s*=\s*({.*?});'
        props_match = re.search(props_pattern, html, re.DOTALL)
        if props_match:
            try:
                props_data = json.loads(props_match.group(1))
                stream_data = self._extract_from_props(props_data)
                if stream_data:
                    stream_info.update(stream_data)
            except json.JSONDecodeError:
                pass
        
        if stream_info:
            stream_info["quality"] = "high" if "stream_url" in stream_info else "preview"
            stream_info["format"] = "m4a" if "hls_url" in stream_info else "mp3"
            return stream_info
        
        return None
    
    def _decrypt_stream_data(self, encrypted_data: str) -> Optional[Dict[str, str]]:
        """
        Decrypt stream data (simplified).
        
        Actual implementation would need proper decryption logic.
        """
        # This is a placeholder - actual Mixcloud decryption is more complex
        # and may involve XOR operations or other encryption methods
        logger.debug("Stream decryption not fully implemented")
        return None
    
    def _extract_from_props(self, props_data: Dict) -> Optional[Dict[str, str]]:
        """Extract stream URLs from React props data."""
        stream_info = {}
        
        # Navigate through nested structure
        try:
            # Different possible paths in the data structure
            paths = [
                ["data", "cloudcast", "streamInfo"],
                ["state", "cloudcast", "data", "streamInfo"],
                ["cloudcastData", "streamInfo"],
            ]
            
            for path in paths:
                data = props_data
                for key in path:
                    if isinstance(data, dict) and key in data:
                        data = data[key]
                    else:
                        break
                else:
                    # Found stream info
                    if isinstance(data, dict):
                        if "hlsUrl" in data:
                            stream_info["hls_url"] = data["hlsUrl"]
                        if "streamUrl" in data:
                            stream_info["stream_url"] = data["streamUrl"]
                        if "previewUrl" in data:
                            stream_info["preview_url"] = data["previewUrl"]
                        break
        except Exception:
            pass
        
        return stream_info if stream_info else None
    
    async def get_direct_url(self, cloudcast: Cloudcast) -> Optional[str]:
        """
        Get direct download URL if available.
        
        Args:
            cloudcast: Cloudcast object
            
        Returns:
            Direct download URL or None
        """
        stream_info = await self.extract(cloudcast)
        
        if not stream_info:
            return None
        
        # Prefer direct download URL
        if stream_info.get("download_url"):
            return stream_info["download_url"]
        
        # Then stream URL
        if stream_info.get("stream_url"):
            return stream_info["stream_url"]
        
        # HLS needs special handling
        if stream_info.get("hls_url"):
            return stream_info["hls_url"]
        
        # Fallback to preview
        return stream_info.get("preview_url")


__all__ = ["StreamExtractor"]
"""
Stream handler for SoundCloud tracks.

Handles stream URL resolution and format selection.
"""

import logging
from typing import Optional, Dict, Any
from urllib.parse import urljoin

from ..exceptions import (
    StreamNotAvailableError,
    AuthenticationError,
    TrackNotDownloadableError,
)

logger = logging.getLogger(__name__)


class StreamHandler:
    """Handles stream URL resolution for SoundCloud tracks."""
    
    def __init__(self, client):
        """
        Initialize stream handler.
        
        Args:
            client: SoundCloud client instance
        """
        self.client = client
    
    async def get_stream_info(self, track) -> Optional[Dict[str, Any]]:
        """
        Get stream information for a track.
        
        Args:
            track: Track model instance
            
        Returns:
            Dictionary with stream info or None if not available
            {
                "url": str,
                "protocol": "progressive" | "hls",
                "format": "mp3" | "opus" | "m4a",
                "quality": "128" | "256" | "original",
                "size": int (optional),
            }
        """
        if not track.streamable:
            raise TrackNotDownloadableError(f"Track {track.id} is not streamable")
        
        # Try to get direct stream URL first (for Go+ tracks)
        if track.download_url and track.downloadable:
            stream_url = await self._resolve_download_url(track)
            if stream_url:
                return {
                    "url": stream_url,
                    "protocol": "progressive",
                    "format": "original",
                    "quality": "original",
                }
        
        # Try progressive stream
        if track.stream_url:
            stream_url = await self._resolve_stream_url(track.stream_url)
            if stream_url:
                return {
                    "url": stream_url,
                    "protocol": "progressive",
                    "format": "mp3",
                    "quality": "128",
                }
        
        # Try HLS stream
        if hasattr(track, "media") and track.media:
            for transocoding in track.media.get("transcodings", []):
                if transocoding.get("format", {}).get("protocol") == "hls":
                    hls_url = await self._resolve_hls_url(transocoding["url"])
                    if hls_url:
                        return {
                            "url": hls_url,
                            "protocol": "hls",
                            "format": transocoding.get("format", {}).get("mime_type", "mp3"),
                            "quality": transocoding.get("quality", "128"),
                        }
        
        # Fallback: Try to get stream from API
        stream_info = await self._get_stream_from_api(track)
        if stream_info:
            return stream_info
        
        return None
    
    async def _resolve_download_url(self, track) -> Optional[str]:
        """Resolve download URL for Go+ tracks."""
        try:
            # Make request to download URL endpoint
            response = await self.client.session.get(
                track.download_url,
                params={"client_id": self.client.client_id}
            )
            
            if response.status == 200:
                data = await response.json()
                return data.get("redirectUri") or data.get("url")
        except Exception as e:
            logger.warning(f"Failed to resolve download URL: {e}")
        
        return None
    
    async def _resolve_stream_url(self, stream_url: str) -> Optional[str]:
        """Resolve progressive stream URL."""
        try:
            # Add client_id to stream URL
            if "?" in stream_url:
                url = f"{stream_url}&client_id={self.client.client_id}"
            else:
                url = f"{stream_url}?client_id={self.client.client_id}"
            
            # Make HEAD request to verify
            response = await self.client.session.head(url)
            if response.status == 200:
                return url
        except Exception as e:
            logger.warning(f"Failed to resolve stream URL: {e}")
        
        return None
    
    async def _resolve_hls_url(self, hls_url: str) -> Optional[str]:
        """Resolve HLS manifest URL."""
        try:
            # Request HLS manifest URL
            response = await self.client.session.get(
                hls_url,
                params={"client_id": self.client.client_id}
            )
            
            if response.status == 200:
                data = await response.json()
                return data.get("url")
        except Exception as e:
            logger.warning(f"Failed to resolve HLS URL: {e}")
        
        return None
    
    async def _get_stream_from_api(self, track) -> Optional[Dict[str, Any]]:
        """Get stream info directly from API."""
        try:
            # Try tracks/{id}/streams endpoint
            response = await self.client.session.get(
                f"{self.client.base_url}/tracks/{track.id}/streams",
                params={"client_id": self.client.client_id}
            )
            
            if response.status == 200:
                data = await response.json()
                
                # Check for progressive stream
                if "http_mp3_128_url" in data:
                    return {
                        "url": data["http_mp3_128_url"],
                        "protocol": "progressive",
                        "format": "mp3",
                        "quality": "128",
                    }
                
                # Check for HLS stream
                if "hls_mp3_128_url" in data:
                    return {
                        "url": data["hls_mp3_128_url"],
                        "protocol": "hls",
                        "format": "mp3",
                        "quality": "128",
                    }
                
                # Check for opus stream
                if "hls_opus_64_url" in data:
                    return {
                        "url": data["hls_opus_64_url"],
                        "protocol": "hls",
                        "format": "opus",
                        "quality": "64",
                    }
        except Exception as e:
            logger.error(f"Failed to get stream from API: {e}")
        
        return None
    
    def select_best_format(self, formats: list) -> Optional[Dict[str, Any]]:
        """
        Select best format from available options.
        
        Args:
            formats: List of format dictionaries
            
        Returns:
            Best format or None
        """
        if not formats:
            return None
        
        # Prefer progressive over HLS
        progressive = [f for f in formats if f["protocol"] == "progressive"]
        if progressive:
            # Prefer higher quality
            return max(progressive, key=lambda f: int(f.get("quality", "0")))
        
        # Fall back to HLS
        hls = [f for f in formats if f["protocol"] == "hls"]
        if hls:
            # Prefer MP3 over Opus
            mp3 = [f for f in hls if "mp3" in f.get("format", "")]
            if mp3:
                return max(mp3, key=lambda f: int(f.get("quality", "0")))
            return hls[0]
        
        return formats[0] if formats else None
    
    async def get_all_formats(self, track) -> list:
        """
        Get all available stream formats for a track.
        
        Args:
            track: Track model instance
            
        Returns:
            List of format dictionaries
        """
        formats = []
        
        # Check download URL
        if track.download_url and track.downloadable:
            stream_url = await self._resolve_download_url(track)
            if stream_url:
                formats.append({
                    "url": stream_url,
                    "protocol": "progressive",
                    "format": "original",
                    "quality": "original",
                })
        
        # Check stream URL
        if track.stream_url:
            stream_url = await self._resolve_stream_url(track.stream_url)
            if stream_url:
                formats.append({
                    "url": stream_url,
                    "protocol": "progressive",
                    "format": "mp3",
                    "quality": "128",
                })
        
        # Check media transcodings
        if hasattr(track, "media") and track.media:
            for transocoding in track.media.get("transcodings", []):
                protocol = transocoding.get("format", {}).get("protocol")
                if protocol in ["progressive", "hls"]:
                    if protocol == "hls":
                        url = await self._resolve_hls_url(transocoding["url"])
                    else:
                        url = await self._resolve_stream_url(transocoding["url"])
                    
                    if url:
                        formats.append({
                            "url": url,
                            "protocol": protocol,
                            "format": transocoding.get("format", {}).get("mime_type", "mp3"),
                            "quality": transocoding.get("quality", "128"),
                        })
        
        # Try API endpoint
        api_formats = await self._get_all_formats_from_api(track)
        formats.extend(api_formats)
        
        # Remove duplicates
        seen = set()
        unique_formats = []
        for fmt in formats:
            key = (fmt["protocol"], fmt["format"], fmt["quality"])
            if key not in seen:
                seen.add(key)
                unique_formats.append(fmt)
        
        return unique_formats
    
    async def _get_all_formats_from_api(self, track) -> list:
        """Get all formats from API streams endpoint."""
        formats = []
        
        try:
            response = await self.client.session.get(
                f"{self.client.base_url}/tracks/{track.id}/streams",
                params={"client_id": self.client.client_id}
            )
            
            if response.status == 200:
                data = await response.json()
                
                # Progressive formats
                if "http_mp3_128_url" in data:
                    formats.append({
                        "url": data["http_mp3_128_url"],
                        "protocol": "progressive",
                        "format": "mp3",
                        "quality": "128",
                    })
                
                # HLS formats
                if "hls_mp3_128_url" in data:
                    formats.append({
                        "url": data["hls_mp3_128_url"],
                        "protocol": "hls",
                        "format": "mp3",
                        "quality": "128",
                    })
                
                if "hls_opus_64_url" in data:
                    formats.append({
                        "url": data["hls_opus_64_url"],
                        "protocol": "hls",
                        "format": "opus",
                        "quality": "64",
                    })
        except Exception as e:
            logger.error(f"Failed to get formats from API: {e}")
        
        return formats


__all__ = ["StreamHandler"]
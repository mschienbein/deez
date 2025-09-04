"""
Album scraper for Bandcamp.
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from .base import BaseScraper
from ..types import AlbumInfo, TrackInfo
from ..exceptions import ParseError

logger = logging.getLogger(__name__)


class AlbumScraper(BaseScraper):
    """Scraper for Bandcamp album pages."""
    
    async def scrape_album(self, url: str) -> AlbumInfo:
        """
        Scrape an album page.
        
        Args:
            url: Album URL
            
        Returns:
            Album information
        """
        page_data = await self.scrape_page(url)
        
        if page_data["type"] != "album":
            raise ParseError(f"URL is not an album page: {url}")
        
        return self._parse_album_data(page_data, url)
    
    def _parse_album_data(self, page_data: Dict[str, Any], url: str) -> AlbumInfo:
        """Parse album data into AlbumInfo."""
        data = page_data["data"]
        metadata = page_data.get("metadata", {})
        stream_data = page_data.get("stream_data")
        
        # Extract tracks with stream data
        tracks = self._extract_tracks(data, stream_data)
        
        # Build album info
        album_info = AlbumInfo(
            id=str(data.get("album_id", "")),
            title=data.get("title", data.get("album_title", "")),
            artist=data.get("artist", ""),
            artist_id=str(data.get("artist_id", "")),
            url=url,
            release_date=data.get("release_date"),
            description=data.get("description"),
            tracks=tracks,
            artwork_url=data.get("artwork_url") or metadata.get("og_image"),
            tags=self._extract_tags(data),
            price=stream_data.get("price") if stream_data else data.get("price"),
            currency=stream_data.get("currency") if stream_data else data.get("currency"),
            label=data.get("label"),
            format=data.get("format", "Digital"),
            about=data.get("about")
        )
        
        return album_info
    
    def _extract_tracks(self, data: Dict[str, Any], stream_data: Optional[Dict[str, Any]] = None) -> List[TrackInfo]:
        """Extract track information from album data."""
        tracks = []
        
        # Get stream URLs from stream_data if available
        stream_urls = []
        if stream_data and "formats" in stream_data:
            stream_urls = [fmt["url"] for fmt in stream_data["formats"] if fmt.get("url")]
        elif stream_data and "mp3_url" in stream_data:
            # Single track case
            stream_urls = [stream_data["mp3_url"]]
        
        # Look for trackinfo in data
        if "trackinfo" in data:
            for idx, track_data in enumerate(data["trackinfo"], 1):
                # Get stream URL for this track
                stream_url = None
                if idx <= len(stream_urls):
                    stream_url = stream_urls[idx - 1]
                elif track_data.get("file") and isinstance(track_data["file"], dict):
                    stream_url = track_data["file"].get("mp3-128")
                    if stream_url and stream_url.startswith("//"):
                        stream_url = "https:" + stream_url
                
                track = TrackInfo(
                    id=str(track_data.get("id", "")),
                    title=track_data.get("title", ""),
                    artist=data.get("artist", ""),
                    album=data.get("title", ""),
                    duration=track_data.get("duration"),
                    track_num=track_data.get("track_num", idx),
                    url=track_data.get("url", ""),
                    stream_url=stream_url,
                    download_url=None,
                    price=track_data.get("price"),
                    currency=data.get("currency"),
                    release_date=data.get("release_date"),
                    lyrics=track_data.get("lyrics"),
                    tags=[],
                    file_format="mp3",
                    free=stream_data.get("free", False) if stream_data else False
                )
                tracks.append(track)
        
        return tracks
    
    def _extract_tags(self, data: Dict[str, Any]) -> List[str]:
        """Extract tags/genres from data."""
        tags = []
        
        if "tags" in data:
            if isinstance(data["tags"], list):
                tags = data["tags"]
            elif isinstance(data["tags"], str):
                tags = [data["tags"]]
        
        if "genre" in data:
            tags.append(data["genre"])
        
        return list(set(tags))  # Remove duplicates


__all__ = ["AlbumScraper"]
"""
Base scraper for Bandcamp.
"""

import asyncio
import logging
import json
import re
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin, urlparse

import aiohttp
from aiohttp import ClientSession, ClientTimeout
from bs4 import BeautifulSoup

from ..config import ScraperConfig
from ..exceptions import ScrapingError, ParseError, NetworkError
from ..types import PageData, StreamData

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base scraper for Bandcamp pages."""
    
    def __init__(self, session: ClientSession, config: ScraperConfig):
        """
        Initialize scraper.
        
        Args:
            session: aiohttp session
            config: Scraper configuration
        """
        self.session = session
        self.config = config
        self._last_request_time = 0
    
    async def scrape_page(self, url: str) -> PageData:
        """
        Scrape a Bandcamp page.
        
        Args:
            url: URL to scrape
            
        Returns:
            Extracted page data
        """
        html = await self._fetch_page(url)
        soup = BeautifulSoup(html, 'html.parser')
        
        # Determine page type
        page_type = self._determine_page_type(soup, url)
        
        # Extract data based on type
        if page_type == "album":
            data = self._extract_album_data(soup)
        elif page_type == "track":
            data = self._extract_track_data(soup)
        elif page_type == "artist":
            data = self._extract_artist_data(soup)
        else:
            raise ParseError(f"Unknown page type for URL: {url}")
        
        # Extract stream data
        stream_data = self._extract_stream_data(soup, html)
        
        # Extract additional metadata
        metadata = self._extract_metadata(soup)
        
        return PageData(
            type=page_type,
            data=data,
            stream_data=stream_data,
            metadata=metadata
        )
    
    async def _fetch_page(self, url: str) -> str:
        """
        Fetch HTML content from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content
        """
        # Apply rate limiting
        await self._apply_rate_limit()
        
        headers = {
            "User-Agent": self.config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        for attempt in range(self.config.max_retries):
            try:
                timeout = ClientTimeout(total=self.config.timeout)
                async with self.session.get(url, headers=headers, timeout=timeout) as response:
                    response.raise_for_status()
                    return await response.text()
                    
            except aiohttp.ClientError as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.config.max_retries}): {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    raise NetworkError(f"Failed to fetch page: {e}")
            except Exception as e:
                raise ScrapingError(f"Unexpected error fetching page: {e}")
    
    async def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        import time
        
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.config.rate_limit:
            await asyncio.sleep(self.config.rate_limit - time_since_last)
        
        self._last_request_time = time.time()
    
    def _determine_page_type(self, soup: BeautifulSoup, url: str) -> str:
        """
        Determine the type of Bandcamp page.
        
        Args:
            soup: BeautifulSoup object
            url: Page URL
            
        Returns:
            Page type ("album", "track", "artist")
        """
        # Check meta tags
        og_type = soup.find("meta", {"property": "og:type"})
        if og_type:
            content = og_type.get("content", "")
            if "album" in content:
                return "album"
            elif "song" in content:
                return "track"
            elif "band" in content or "artist" in content:
                return "artist"
        
        # Check URL patterns
        parsed = urlparse(url)
        path = parsed.path
        
        if "/album/" in path:
            return "album"
        elif "/track/" in path:
            return "track"
        elif path.count("/") <= 1:  # Root or single path segment
            return "artist"
        
        # Check page structure
        if soup.find("div", {"id": "tralbumData"}):
            if soup.find("table", {"id": "track_table"}):
                return "album"
            else:
                return "track"
        
        return "artist"
    
    def _extract_album_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract album data from page."""
        data = {}
        
        # Title
        title_elem = soup.find("h2", {"class": "trackTitle"})
        if title_elem:
            data["title"] = title_elem.get_text(strip=True)
        
        # Artist
        artist_elem = soup.find("span", {"itemprop": "byArtist"})
        if artist_elem:
            data["artist"] = artist_elem.get_text(strip=True)
        
        # Release date
        release_elem = soup.find("meta", {"itemprop": "datePublished"})
        if release_elem:
            data["release_date"] = release_elem.get("content")
        
        # Description
        desc_elem = soup.find("div", {"class": "tralbumData"})
        if desc_elem:
            data["description"] = desc_elem.get_text(strip=True)
        
        # Artwork
        art_elem = soup.find("a", {"class": "popupImage"})
        if art_elem:
            data["artwork_url"] = art_elem.get("href")
        
        # Extract embedded data
        embedded = self._extract_embedded_data(soup)
        if embedded:
            data.update(embedded)
        
        return data
    
    def _extract_track_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract track data from page."""
        data = {}
        
        # Similar to album but for single track
        title_elem = soup.find("h2", {"class": "trackTitle"})
        if title_elem:
            data["title"] = title_elem.get_text(strip=True)
        
        # Artist
        artist_elem = soup.find("span", {"itemprop": "byArtist"})
        if artist_elem:
            data["artist"] = artist_elem.get_text(strip=True)
        
        # Duration
        duration_elem = soup.find("meta", {"itemprop": "duration"})
        if duration_elem:
            data["duration"] = duration_elem.get("content")
        
        # Lyrics
        lyrics_elem = soup.find("div", {"class": "lyricsText"})
        if lyrics_elem:
            data["lyrics"] = lyrics_elem.get_text(strip=True)
        
        # Extract embedded data
        embedded = self._extract_embedded_data(soup)
        if embedded:
            data.update(embedded)
        
        return data
    
    def _extract_artist_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract artist/band data from page."""
        data = {}
        
        # Artist name
        name_elem = soup.find("p", {"id": "band-name-location"})
        if name_elem:
            name = name_elem.find("span", {"class": "title"})
            if name:
                data["name"] = name.get_text(strip=True)
        
        # Location
        location_elem = soup.find("span", {"class": "location"})
        if location_elem:
            data["location"] = location_elem.get_text(strip=True)
        
        # Bio
        bio_elem = soup.find("div", {"class": "bio-text"})
        if bio_elem:
            data["bio"] = bio_elem.get_text(strip=True)
        
        # Discography
        music_grid = soup.find("ol", {"id": "music-grid"})
        if music_grid:
            albums = []
            for item in music_grid.find_all("li"):
                album_data = self._extract_grid_item(item)
                if album_data:
                    albums.append(album_data)
            data["albums"] = albums
        
        return data
    
    def _extract_grid_item(self, item) -> Optional[Dict[str, Any]]:
        """Extract data from a music grid item."""
        data = {}
        
        # Title
        title_elem = item.find("p", {"class": "title"})
        if title_elem:
            data["title"] = title_elem.get_text(strip=True)
        
        # URL
        link = item.find("a")
        if link:
            data["url"] = link.get("href")
        
        # Artwork
        img = item.find("img")
        if img:
            data["artwork_url"] = img.get("src")
        
        return data if data else None
    
    def _extract_stream_data(self, soup: BeautifulSoup, html: str) -> Optional[StreamData]:
        """Extract stream URLs and data."""
        stream_data = StreamData(
            mp3_url=None,
            download_url=None,
            free=False,
            price=None,
            currency=None,
            formats=[]
        )
        
        # Look for TralbumData in JavaScript
        tralbum_pattern = r'var\s+TralbumData\s*=\s*({.*?});'
        match = re.search(tralbum_pattern, html, re.DOTALL)
        
        if match:
            js_data = match.group(1)
            
            # Extract trackinfo array using regex
            trackinfo_match = re.search(r'trackinfo\s*:\s*(\[.*?\])', js_data, re.DOTALL)
            if trackinfo_match:
                tracks_str = trackinfo_match.group(1)
                
                # Find MP3 stream URLs
                mp3_pattern = r'"mp3-128"\s*:\s*"([^"]+)"'
                mp3_matches = re.findall(mp3_pattern, tracks_str)
                
                if mp3_matches:
                    # Get the first available MP3 URL
                    mp3_url = mp3_matches[0]
                    
                    # Add https: prefix if needed
                    if mp3_url.startswith("//"):
                        mp3_url = "https:" + mp3_url
                    elif not mp3_url.startswith("http"):
                        # Relative URL, need to construct full URL
                        mp3_url = f"https://bandcamp.com{mp3_url}"
                    
                    stream_data["mp3_url"] = mp3_url
                    
                    # Store all URLs in formats
                    for url in mp3_matches:
                        if url.startswith("//"):
                            url = "https:" + url
                        elif not url.startswith("http"):
                            url = f"https://bandcamp.com{url}"
                        stream_data["formats"].append({"format": "mp3-128", "url": url})
            
            # Check if content is free
            free_match = re.search(r'freeDownloadPage\s*:\s*(true|false|null)', js_data)
            if free_match:
                stream_data["free"] = free_match.group(1) == "true"
            
            # Extract current track/album data
            current_match = re.search(r'current\s*:\s*({[^}]*})', js_data)
            if current_match:
                current_str = current_match.group(1)
                
                # Extract minimum price
                price_match = re.search(r'minimum_price\s*:\s*(\d+\.?\d*)', current_str)
                if price_match:
                    try:
                        stream_data["price"] = float(price_match.group(1))
                    except ValueError:
                        pass
                
                # Extract currency
                currency_match = re.search(r'currency\s*:\s*"([^"]+)"', current_str)
                if currency_match:
                    stream_data["currency"] = currency_match.group(1)
            
            # Alternative: Check for item_type to determine if it's purchasable
            item_type_match = re.search(r'item_type\s*:\s*"([^"]+)"', js_data)
            if item_type_match:
                item_type = item_type_match.group(1)
                # Track or album can potentially have streams
                if item_type in ["track", "album"]:
                    # Check if has a null file (means purchase required)
                    if not stream_data["mp3_url"]:
                        null_file_match = re.search(r'"file"\s*:\s*null', tracks_str)
                        if null_file_match:
                            logger.debug("Track requires purchase (file is null)")
        
        # Alternative: Look for data-tralbum attribute
        if not stream_data["mp3_url"]:
            player = soup.find(attrs={"data-tralbum": True})
            if player:
                data_attr = player.get("data-tralbum")
                if data_attr:
                    try:
                        data = json.loads(data_attr)
                        # Check for trackinfo
                        if "trackinfo" in data and data["trackinfo"]:
                            track = data["trackinfo"][0] if isinstance(data["trackinfo"], list) else data["trackinfo"]
                            if "file" in track and track["file"]:
                                if "mp3-128" in track["file"]:
                                    mp3_url = track["file"]["mp3-128"]
                                    if mp3_url.startswith("//"):
                                        mp3_url = "https:" + mp3_url
                                    stream_data["mp3_url"] = mp3_url
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.debug(f"Could not parse data-tralbum: {e}")
        
        return stream_data if stream_data["mp3_url"] else None
    
    def _extract_embedded_data(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract data from embedded JavaScript."""
        data = {}
        
        # Look for embedded data script
        scripts = soup.find_all("script")
        for script in scripts:
            text = script.string
            if text and "TralbumData" in text:
                # Extract trackinfo array
                trackinfo_match = re.search(r'trackinfo\s*:\s*(\[.*?\])', text, re.DOTALL)
                if trackinfo_match:
                    tracks_str = trackinfo_match.group(1)
                    # Parse track data
                    tracks = []
                    track_pattern = r'\{[^}]*?"title"\s*:\s*"([^"]+)"[^}]*?\}'
                    for match in re.finditer(track_pattern, tracks_str):
                        track_obj = match.group(0)
                        track_data = {}
                        
                        # Extract track fields
                        title_match = re.search(r'"title"\s*:\s*"([^"]+)"', track_obj)
                        if title_match:
                            track_data["title"] = title_match.group(1)
                        
                        id_match = re.search(r'"id"\s*:\s*(\d+)', track_obj)
                        if id_match:
                            track_data["id"] = id_match.group(1)
                        
                        duration_match = re.search(r'"duration"\s*:\s*(\d+\.?\d*)', track_obj)
                        if duration_match:
                            track_data["duration"] = float(duration_match.group(1))
                        
                        track_num_match = re.search(r'"track_num"\s*:\s*(\d+)', track_obj)
                        if track_num_match:
                            track_data["track_num"] = int(track_num_match.group(1))
                        
                        # Check for file/stream info
                        file_match = re.search(r'"file"\s*:\s*({[^}]+}|null)', track_obj)
                        if file_match and file_match.group(1) != "null":
                            file_data = file_match.group(1)
                            mp3_match = re.search(r'"mp3-128"\s*:\s*"([^"]+)"', file_data)
                            if mp3_match:
                                track_data["file"] = {"mp3-128": mp3_match.group(1)}
                        
                        if track_data:
                            tracks.append(track_data)
                    
                    if tracks:
                        data["trackinfo"] = tracks
                
                # Extract other fields with regex
                patterns = {
                    "album_id": r'album_id\s*:\s*(\d+)',
                    "artist": r'artist\s*:\s*"([^"]+)"',
                    "album_title": r'album_title\s*:\s*"([^"]+)"',
                    "title": r'current\s*:\s*\{[^}]*"title"\s*:\s*"([^"]+)"',
                    "item_type": r'item_type\s*:\s*"([^"]+)"',
                }
                
                for key, pattern in patterns.items():
                    match = re.search(pattern, text)
                    if match:
                        data[key] = match.group(1)
                
                # If we didn't get title from current, try alternatives
                if not data.get("title") and data.get("album_title"):
                    data["title"] = data["album_title"]
        
        return data
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract additional metadata from page."""
        metadata = {}
        
        # Open Graph tags
        og_tags = soup.find_all("meta", {"property": re.compile("^og:")})
        for tag in og_tags:
            key = tag.get("property", "").replace("og:", "")
            value = tag.get("content")
            if key and value:
                metadata[f"og_{key}"] = value
        
        # Twitter Card tags  
        twitter_tags = soup.find_all("meta", {"name": re.compile("^twitter:")})
        for tag in twitter_tags:
            key = tag.get("name", "").replace("twitter:", "")
            value = tag.get("content")
            if key and value:
                metadata[f"twitter_{key}"] = value
        
        # Schema.org data
        schema = soup.find("script", {"type": "application/ld+json"})
        if schema and schema.string:
            try:
                metadata["schema"] = json.loads(schema.string)
            except json.JSONDecodeError:
                pass
        
        return metadata


__all__ = ["BaseScraper"]
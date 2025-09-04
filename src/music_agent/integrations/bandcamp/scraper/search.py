"""
Search functionality for Bandcamp.
"""

import logging
import json
import re
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus, urlencode

from .base import BaseScraper
from ..types import SearchResult
from ..exceptions import ScrapingError

logger = logging.getLogger(__name__)


class SearchScraper(BaseScraper):
    """Scraper for Bandcamp search."""
    
    SEARCH_URL = "https://bandcamp.com/search"
    
    async def search(
        self,
        query: str,
        search_type: str = "all",
        page: int = 1
    ) -> List[SearchResult]:
        """
        Search Bandcamp.
        
        Args:
            query: Search query
            search_type: Type to search ("all", "artists", "albums", "tracks", "labels")
            page: Page number (1-indexed)
            
        Returns:
            List of search results
        """
        # Build search URL
        params = {
            "q": query,
            "page": page
        }
        
        if search_type != "all":
            # Map to Bandcamp's item_type parameter
            type_map = {
                "artists": "b",  # bands
                "albums": "a",
                "tracks": "t",
                "labels": "b"
            }
            if search_type in type_map:
                params["item_type"] = type_map[search_type]
        
        url = f"{self.SEARCH_URL}?{urlencode(params)}"
        
        # Fetch and parse
        html = await self._fetch_page(url)
        return self._parse_search_results(html)
    
    def _parse_search_results(self, html: str) -> List[SearchResult]:
        """Parse search results from HTML."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Find search results container
        results_list = soup.find("ul", {"class": "result-items"})
        if not results_list:
            return results
        
        # Parse each result item
        for item in results_list.find_all("li", {"class": "searchresult"}):
            result = self._parse_search_item(item)
            if result:
                results.append(result)
        
        return results
    
    def _parse_search_item(self, item) -> Optional[SearchResult]:
        """Parse a single search result item."""
        try:
            result = SearchResult(
                type="unknown",
                name="",
                artist=None,
                url="",
                image_url=None,
                genre=None,
                location=None,
                tags=[],
                released=None,
                num_tracks=None
            )
            
            # Type
            type_elem = item.find("div", {"class": "itemtype"})
            if type_elem:
                item_type = type_elem.get_text(strip=True).lower()
                if "artist" in item_type or "band" in item_type:
                    result["type"] = "artist"
                elif "album" in item_type:
                    result["type"] = "album"
                elif "track" in item_type:
                    result["type"] = "track"
                elif "label" in item_type:
                    result["type"] = "label"
            
            # Name/Title
            heading = item.find("div", {"class": "heading"})
            if heading:
                link = heading.find("a")
                if link:
                    result["name"] = link.get_text(strip=True)
                    result["url"] = link.get("href", "")
            
            # Artist (for albums/tracks)
            subhead = item.find("div", {"class": "subhead"})
            if subhead:
                result["artist"] = subhead.get_text(strip=True).replace("by ", "")
            
            # Image
            img = item.find("img", {"class": "art"})
            if img:
                result["image_url"] = img.get("src")
            
            # Genre
            genre_elem = item.find("div", {"class": "genre"})
            if genre_elem:
                result["genre"] = genre_elem.get_text(strip=True)
            
            # Location
            location_elem = item.find("div", {"class": "location"})
            if location_elem:
                result["location"] = location_elem.get_text(strip=True)
            
            # Tags
            tags_elem = item.find("div", {"class": "tags"})
            if tags_elem:
                tag_links = tags_elem.find_all("a")
                result["tags"] = [tag.get_text(strip=True) for tag in tag_links]
            
            # Release info
            released_elem = item.find("div", {"class": "released"})
            if released_elem:
                result["released"] = released_elem.get_text(strip=True).replace("released ", "")
            
            # Track count (for albums)
            length_elem = item.find("div", {"class": "length"})
            if length_elem:
                text = length_elem.get_text(strip=True)
                if "tracks" in text:
                    num = re.search(r'(\d+)', text)
                    if num:
                        result["num_tracks"] = int(num.group(1))
            
            return result if result["name"] and result["url"] else None
            
        except Exception as e:
            logger.debug(f"Error parsing search item: {e}")
            return None
    
    async def search_albums(self, query: str, page: int = 1) -> List[SearchResult]:
        """Search for albums."""
        return await self.search(query, "albums", page)
    
    async def search_artists(self, query: str, page: int = 1) -> List[SearchResult]:
        """Search for artists."""
        return await self.search(query, "artists", page)
    
    async def search_tracks(self, query: str, page: int = 1) -> List[SearchResult]:
        """Search for tracks."""
        return await self.search(query, "tracks", page)


__all__ = ["SearchScraper"]
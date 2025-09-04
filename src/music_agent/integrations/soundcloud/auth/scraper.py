"""
Client ID scraper for public SoundCloud access.

Extracts client IDs from public SoundCloud pages for
unauthenticated API access.
"""

import re
import logging
import random
from typing import List, Optional
import aiohttp
from bs4 import BeautifulSoup

from ..exceptions import ScrapingError, ClientIDError

logger = logging.getLogger(__name__)


class ClientIDScraper:
    """Scrapes client IDs from public SoundCloud pages."""
    
    # URLs to scrape for client IDs
    SCRAPE_URLS = [
        "https://soundcloud.com/",
        "https://soundcloud.com/discover",
        "https://soundcloud.com/charts/top",
        "https://soundcloud.com/charts/new",
        "https://soundcloud.com/explore",
    ]
    
    # Patterns to find client IDs in JavaScript
    CLIENT_ID_PATTERNS = [
        r'client_id["\']?\s*:\s*["\']([a-zA-Z0-9]+)["\']',
        r'clientId["\']?\s*:\s*["\']([a-zA-Z0-9]+)["\']',
        r'["\']client_id["\']\s*:\s*["\']([a-zA-Z0-9]+)["\']',
        r'api\.soundcloud\.com.*?client_id=([a-zA-Z0-9]+)',
    ]
    
    # User agents for requests
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    def __init__(self):
        """Initialize the scraper."""
        self._client_id_cache: List[str] = []
    
    async def scrape_client_id(self, url: Optional[str] = None) -> Optional[str]:
        """
        Scrape a client ID from a SoundCloud page.
        
        Args:
            url: Optional specific URL to scrape
            
        Returns:
            Client ID if found, None otherwise
        """
        target_url = url or random.choice(self.SCRAPE_URLS)
        
        try:
            # Fetch the page
            html = await self._fetch_page(target_url)
            
            # Extract scripts
            scripts = await self._extract_scripts(html, target_url)
            
            # Search for client ID
            for script_content in scripts:
                client_id = self._find_client_id(script_content)
                if client_id:
                    logger.info(f"Found client ID: {client_id[:8]}...")
                    return client_id
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to scrape client ID from {target_url}: {e}")
            return None
    
    async def scrape_multiple(self, count: int = 5) -> List[str]:
        """
        Scrape multiple client IDs.
        
        Args:
            count: Number of IDs to scrape
            
        Returns:
            List of unique client IDs
        """
        client_ids = set()
        
        for url in self.SCRAPE_URLS:
            if len(client_ids) >= count:
                break
            
            client_id = await self.scrape_client_id(url)
            if client_id:
                client_ids.add(client_id)
        
        # If we still need more, try with random URLs
        attempts = 0
        while len(client_ids) < count and attempts < 10:
            client_id = await self.scrape_client_id()
            if client_id:
                client_ids.add(client_id)
            attempts += 1
        
        result = list(client_ids)[:count]
        self._client_id_cache = result
        
        logger.info(f"Scraped {len(result)} client IDs")
        return result
    
    async def validate_client_id(self, client_id: str) -> bool:
        """
        Validate if a client ID works.
        
        Args:
            client_id: Client ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        test_url = f"https://api-v2.soundcloud.com/search?q=test&client_id={client_id}&limit=1"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    test_url,
                    headers={"User-Agent": random.choice(self.USER_AGENTS)},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    # Valid if we get 200 OK
                    is_valid = response.status == 200
                    
                    if is_valid:
                        logger.debug(f"Client ID {client_id[:8]}... is valid")
                    else:
                        logger.debug(f"Client ID {client_id[:8]}... is invalid (status: {response.status})")
                    
                    return is_valid
                    
            except Exception as e:
                logger.debug(f"Failed to validate client ID: {e}")
                return False
    
    async def get_working_client_id(self) -> str:
        """
        Get a working client ID, scraping if necessary.
        
        Returns:
            Valid client ID
            
        Raises:
            ClientIDError: If no valid ID can be found
        """
        # Try cached IDs first
        for client_id in self._client_id_cache:
            if await self.validate_client_id(client_id):
                return client_id
        
        # Scrape new ones
        client_ids = await self.scrape_multiple(5)
        
        for client_id in client_ids:
            if await self.validate_client_id(client_id):
                return client_id
        
        raise ClientIDError("Could not find a working client ID")
    
    async def _fetch_page(self, url: str) -> str:
        """
        Fetch a web page.
        
        Args:
            url: URL to fetch
            
        Returns:
            Page HTML
            
        Raises:
            ScrapingError: If fetch fails
        """
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    if response.status != 200:
                        raise ScrapingError(f"Failed to fetch {url}: status {response.status}")
                    
                    return await response.text()
                    
            except aiohttp.ClientError as e:
                raise ScrapingError(f"Network error fetching {url}: {e}")
    
    async def _extract_scripts(self, html: str, base_url: str) -> List[str]:
        """
        Extract JavaScript content from HTML.
        
        Args:
            html: Page HTML
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of script contents
        """
        soup = BeautifulSoup(html, "html.parser")
        scripts = []
        
        # Inline scripts
        for script in soup.find_all("script"):
            if script.string:
                scripts.append(script.string)
        
        # External scripts
        for script in soup.find_all("script", src=True):
            src = script["src"]
            
            # Make absolute URL
            if not src.startswith("http"):
                if src.startswith("//"):
                    src = "https:" + src
                elif src.startswith("/"):
                    src = base_url.rstrip("/") + src
                else:
                    src = base_url.rstrip("/") + "/" + src
            
            # Only fetch SoundCloud scripts
            if "soundcloud" in src.lower():
                try:
                    script_content = await self._fetch_page(src)
                    scripts.append(script_content)
                except Exception as e:
                    logger.debug(f"Failed to fetch script {src}: {e}")
        
        return scripts
    
    def _find_client_id(self, text: str) -> Optional[str]:
        """
        Find client ID in text using patterns.
        
        Args:
            text: Text to search
            
        Returns:
            Client ID if found
        """
        for pattern in self.CLIENT_ID_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                client_id = match.group(1)
                
                # Validate format (should be 32 chars, alphanumeric)
                if len(client_id) >= 20 and client_id.isalnum():
                    return client_id
        
        return None


__all__ = ["ClientIDScraper"]
"""
Simple and efficient 1001 Tracklists integration.

Returns raw structured data for the agent to process, avoiding LLM overhead
in the data extraction pipeline.
"""

import re
import time
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import hashlib

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import Playwright for JavaScript rendering
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available - JavaScript rendering disabled")

logger = logging.getLogger(__name__)


class TracklistsScraper:
    """
    Efficient scraper for 1001 Tracklists.
    
    Features:
    - Pattern-based extraction
    - Automatic retries
    - Rate limiting
    - Simple caching
    """
    
    BASE_URL = "https://www.1001tracklists.com"
    
    def __init__(self):
        """Initialize the scraper with session management."""
        # Create session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set headers to appear as a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Simple cache
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour
        
        # Rate limiting
        self._last_request_time = 0
        self._min_delay = 2.0  # 2 seconds between requests
        
        # Playwright browser (initialized on first use)
        self._playwright = None
        self._browser = None
    
    def _rate_limit(self):
        """Enforce rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_delay:
            time.sleep(self._min_delay - time_since_last)
        
        self._last_request_time = time.time()
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key for URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_cached(self, url: str) -> Optional[str]:
        """Get cached HTML if available and not expired."""
        cache_key = self._get_cache_key(url)
        if cache_key in self._cache:
            cached_time, html = self._cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                logger.debug(f"Using cached data for {url}")
                return html
        return None
    
    def _cache_html(self, url: str, html: str):
        """Cache HTML content."""
        cache_key = self._get_cache_key(url)
        self._cache[cache_key] = (time.time(), html)
    
    def _init_playwright(self):
        """Initialize Playwright browser on first use."""
        if not PLAYWRIGHT_AVAILABLE:
            return False
        
        if self._playwright is None:
            try:
                self._playwright = sync_playwright().start()
                self._browser = self._playwright.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                logger.info("Playwright browser initialized")
                return True
            except Exception as e:
                logger.error(f"Failed to initialize Playwright: {e}")
                return False
        return True
    
    def _fetch_with_playwright(self, url: str) -> Optional[str]:
        """
        Fetch a page using Playwright for JavaScript rendering.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if failed
        """
        if not self._init_playwright():
            return None
        
        try:
            # Create a new page with custom settings
            page = self._browser.new_page(
                # Set viewport to avoid mobile versions
                viewport={'width': 1920, 'height': 1080},
                # Set user agent to avoid bot detection
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Navigate to the URL with relaxed waiting
            # 'domcontentloaded' is faster than 'networkidle' and usually sufficient
            page.goto(url, wait_until='domcontentloaded', timeout=20000)
            
            # Wait for content to load
            # Try to wait for specific elements that indicate content is loaded
            try:
                # Wait for any of these selectors (more flexible)
                page.wait_for_selector('[data-trackid], .tlpTog, .tlpItem, .search-result, a[href*="/tracklist/"]', 
                                      timeout=5000)
            except:
                # If specific elements not found, just wait a bit for JS to execute
                page.wait_for_timeout(3000)
            
            # Get the full page HTML
            html = page.content()
            
            # Close the page
            page.close()
            
            return html
            
        except Exception as e:
            logger.error(f"Playwright failed to fetch {url}: {e}")
            return None
    
    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch a page with rate limiting and caching.
        Uses Playwright for 1001 Tracklists pages that require JavaScript.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if failed
        """
        # Check cache first
        cached = self._get_cached(url)
        if cached:
            return cached
        
        # Rate limit
        self._rate_limit()
        
        # Use Playwright for 1001 Tracklists pages
        if '1001tracklists.com' in url and PLAYWRIGHT_AVAILABLE:
            html = self._fetch_with_playwright(url)
            if html:
                # Cache successful response
                self._cache_html(url, html)
                return html
            else:
                logger.warning("Playwright fetch failed, falling back to requests")
        
        # Fallback to regular requests (or for non-1001TL sites)
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            html = response.text
            
            # Cache successful response
            self._cache_html(url, html)
            
            return html
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
    
    def __del__(self):
        """Clean up Playwright resources."""
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
    
    def extract_tracklist(self, url: str) -> Dict[str, Any]:
        """
        Extract tracklist data from a 1001 Tracklists URL.
        
        Args:
            url: Tracklist URL
            
        Returns:
            Structured tracklist data
        """
        html = self.fetch_page(url)
        if not html:
            return {'error': 'Failed to fetch page', 'url': url}
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract basic metadata
        data = {
            'url': url,
            'title': self._extract_title(soup),
            'dj': self._extract_dj(soup),
            'event': self._extract_event(soup),
            'date': self._extract_date(soup),
            'genres': self._extract_genres(soup),
            'tracks': self._extract_tracks(soup),
            'recording_links': self._extract_recording_links(soup),
            'stats': self._extract_stats(soup),
            'extracted_at': datetime.utcnow().isoformat()
        }
        
        return data
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract tracklist title."""
        # Try meta property first
        meta = soup.find('meta', {'property': 'og:title'})
        if meta and meta.get('content'):
            return meta['content']
        
        # Try h1 title
        h1 = soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        # Fallback to page title
        title = soup.find('title')
        if title:
            return title.get_text(strip=True)
        
        return "Unknown Tracklist"
    
    def _extract_dj(self, soup: BeautifulSoup) -> str:
        """Extract DJ/artist name."""
        # Look for DJ name in various places
        dj_elem = soup.find('span', {'class': 'djName'})
        if dj_elem:
            return dj_elem.get_text(strip=True)
        
        # Try to extract from title
        title = self._extract_title(soup)
        if ' @ ' in title:
            return title.split(' @ ')[0].strip()
        
        return "Unknown DJ"
    
    def _extract_event(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract event/venue name."""
        # Look for event info
        event_elem = soup.find('span', {'class': 'eventName'})
        if event_elem:
            return event_elem.get_text(strip=True)
        
        # Try meta description
        meta = soup.find('meta', {'name': 'description'})
        if meta and meta.get('content'):
            content = meta['content']
            if ' at ' in content:
                parts = content.split(' at ')
                if len(parts) > 1:
                    return parts[1].split(',')[0].strip()
        
        return None
    
    def _extract_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract date of the set."""
        # Look for date element
        date_elem = soup.find('time')
        if date_elem:
            return date_elem.get('datetime', date_elem.get_text(strip=True))
        
        # Look in various date classes
        for class_name in ['date', 'eventDate', 'tlDate']:
            elem = soup.find(class_=class_name)
            if elem:
                date_text = elem.get_text(strip=True)
                # Basic date parsing
                return date_text
        
        return None
    
    def _extract_genres(self, soup: BeautifulSoup) -> List[str]:
        """Extract music genres."""
        genres = []
        
        # Look for genre tags
        genre_elems = soup.find_all('a', {'class': re.compile('tag|genre')})
        for elem in genre_elems:
            genre = elem.get_text(strip=True)
            if genre and genre not in genres:
                genres.append(genre)
        
        return genres
    
    def _extract_tracks(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract track information."""
        tracks = []
        
        # Find track container (varies by page type)
        track_containers = (
            soup.find_all('div', {'class': re.compile('tlpItem|trackItem|track')}) or
            soup.find_all('tr', {'class': re.compile('tlpItem|track')}) or
            soup.find_all('li', {'class': re.compile('track')})
        )
        
        for idx, container in enumerate(track_containers, 1):
            track = self._parse_track(container, idx)
            if track:
                tracks.append(track)
        
        # If no tracks found with class, try alternative parsing
        if not tracks:
            tracks = self._extract_tracks_fallback(soup)
        
        return tracks
    
    def _parse_track(self, container, position: int) -> Optional[Dict[str, Any]]:
        """Parse individual track from container."""
        track = {
            'position': position,
            'cue': None,
            'artist': None,
            'title': None,
            'remix': None,
            'label': None,
            'mix_type': None,
            'is_id': False
        }
        
        # Extract cue time
        cue_elem = container.find(class_=re.compile('cue|time|timestamp'))
        if cue_elem:
            track['cue'] = cue_elem.get_text(strip=True)
        
        # Extract track info
        track_text = container.get_text(' ', strip=True)
        
        # Check if it's an ID track
        if 'ID - ID' in track_text or 'Unknown' in track_text:
            track['is_id'] = True
            track['artist'] = 'ID'
            track['title'] = 'ID'
        else:
            # Parse artist - title pattern
            parts = self._parse_track_text(track_text)
            track.update(parts)
        
        # Extract mix type (w/, into, etc.)
        if ' w/ ' in track_text:
            track['mix_type'] = 'w/'
        elif ' into ' in track_text.lower():
            track['mix_type'] = 'into'
        
        # Extract label if present
        label_elem = container.find(class_=re.compile('label'))
        if label_elem:
            track['label'] = label_elem.get_text(strip=True)
        
        return track if (track['artist'] or track['is_id']) else None
    
    def _parse_track_text(self, text: str) -> Dict[str, str]:
        """Parse track text into components."""
        result = {
            'artist': None,
            'title': None,
            'remix': None
        }
        
        # Clean up text
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'^\d+\.?\s*', '', text)  # Remove leading number
        text = re.sub(r'^\[?[\d:]+\]?\s*', '', text)  # Remove timestamp
        
        # Common patterns
        patterns = [
            # Artist - Title (Remix)
            r'^([^-]+?)\s*-\s*([^(]+?)(?:\s*\(([^)]+)\))?$',
            # Artist - Title [Label]
            r'^([^-]+?)\s*-\s*([^[]+?)(?:\s*\[[^\]]+\])?$',
            # Artist: Title
            r'^([^:]+?):\s*(.+)$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, text)
            if match:
                groups = match.groups()
                result['artist'] = groups[0].strip() if groups[0] else None
                result['title'] = groups[1].strip() if len(groups) > 1 and groups[1] else None
                if len(groups) > 2 and groups[2]:
                    result['remix'] = groups[2].strip()
                break
        
        # Fallback: assume entire text is title
        if not result['artist'] and not result['title']:
            result['title'] = text.strip()
        
        return result
    
    def _extract_tracks_fallback(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Fallback track extraction method."""
        tracks = []
        
        # Look for any text that looks like tracks
        # This is a simple pattern matching approach
        text = soup.get_text()
        lines = text.split('\n')
        
        track_pattern = re.compile(r'(?:^\d+\.?\s*)?(?:\[?[\d:]+\]?\s*)?([^-]+?)\s*-\s*(.+)')
        
        position = 1
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            match = track_pattern.match(line)
            if match:
                tracks.append({
                    'position': position,
                    'cue': None,
                    'artist': match.group(1).strip(),
                    'title': match.group(2).strip(),
                    'remix': None,
                    'label': None,
                    'mix_type': None,
                    'is_id': 'ID' in line
                })
                position += 1
            
            if position > 200:  # Sanity limit
                break
        
        return tracks
    
    def _extract_recording_links(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract links to recordings (SoundCloud, Mixcloud, etc.)."""
        links = {}
        
        # Look for player embeds and links
        for platform, patterns in {
            'soundcloud': ['soundcloud.com'],
            'mixcloud': ['mixcloud.com'],
            'youtube': ['youtube.com', 'youtu.be'],
            'spotify': ['spotify.com']
        }.items():
            for pattern in patterns:
                link = soup.find('a', href=re.compile(pattern))
                if link:
                    links[platform] = link['href']
                # Also check iframes
                iframe = soup.find('iframe', src=re.compile(pattern))
                if iframe:
                    links[platform] = iframe['src']
        
        return links
    
    def _extract_stats(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract view counts, favorites, etc."""
        stats = {
            'views': None,
            'favorites': None,
            'comments': None
        }
        
        # Look for stat elements
        for stat_type in ['views', 'plays', 'likes', 'favorites']:
            elem = soup.find(text=re.compile(stat_type, re.I))
            if elem:
                # Try to extract number
                parent = elem.parent
                if parent:
                    text = parent.get_text()
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        if 'view' in stat_type.lower() or 'play' in stat_type.lower():
                            stats['views'] = int(numbers[0])
                        elif 'fav' in stat_type.lower() or 'like' in stat_type.lower():
                            stats['favorites'] = int(numbers[0])
        
        return stats
    
    def search_tracks(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for tracks on 1001 Tracklists.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of track results
        """
        from urllib.parse import quote_plus
        
        # Build search URL with proper encoding
        encoded_query = quote_plus(query)
        search_url = f"{self.BASE_URL}/search?q={encoded_query}"
        
        html = self.fetch_page(search_url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # Parse search results - multiple strategies
        # Strategy 1: Look for search result containers
        result_containers = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'(search|result|track|item)', re.I))
        
        for container in result_containers[:limit * 2]:  # Get extra in case some fail
            result = self._parse_search_result(container)
            if result:
                results.append(result)
                if len(results) >= limit:
                    break
        
        # Strategy 2: If no results yet, look for links that appear to be tracklists
        if not results:
            tracklist_links = soup.find_all('a', href=re.compile(r'/tracklist/[a-z0-9]+/', re.I))
            
            for link in tracklist_links[:limit]:
                result = {
                    'type': 'tracklist',
                    'url': self.BASE_URL + link.get('href', ''),
                    'title': link.get_text(strip=True),
                    'dj': None,
                    'event': None,
                    'date': None
                }
                
                # Try to extract DJ name from title or nearby text
                title_text = link.get_text(strip=True)
                if ' @ ' in title_text:
                    parts = title_text.split(' @ ')
                    result['dj'] = parts[0].strip()
                    result['event'] = parts[1].strip() if len(parts) > 1 else None
                elif ' at ' in title_text.lower():
                    parts = title_text.split(' at ', 1)
                    result['dj'] = parts[0].strip()
                    result['event'] = parts[1].strip() if len(parts) > 1 else None
                
                # Look for date near the link
                parent = link.find_parent(['div', 'article', 'li'])
                if parent:
                    date_text = parent.get_text()
                    date_match = re.search(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}', date_text, re.I)
                    if date_match:
                        result['date'] = date_match.group(0)
                
                results.append(result)
        
        return results[:limit]
    
    def _parse_search_result(self, container) -> Optional[Dict[str, Any]]:
        """Parse a single search result container."""
        if not container:
            return None
        
        result = {
            'type': 'unknown',
            'url': None,
            'title': None,
            'dj': None,
            'event': None,
            'date': None,
            'description': None
        }
        
        # Find the main link
        link = container.find('a', href=re.compile(r'/tracklist/'))
        if link:
            result['url'] = self.BASE_URL + link.get('href', '')
            result['title'] = link.get_text(strip=True)
            result['type'] = 'tracklist'
        
        # Extract text content
        text = container.get_text(' ', strip=True)
        
        # Try to identify DJ name
        dj_patterns = [
            r'(?:by|dj|artist|performer)[:\s]+([^@\n]+?)(?:\s+@|\s+at|\n|$)',
            r'^([^@]+?)\s+@\s+',
            r'^([^-]+?)\s+-\s+'
        ]
        
        for pattern in dj_patterns:
            match = re.search(pattern, text, re.I)
            if match:
                result['dj'] = match.group(1).strip()
                break
        
        # Try to find event/venue
        if ' @ ' in text:
            parts = text.split(' @ ')
            if len(parts) > 1:
                result['event'] = parts[1].split('\n')[0].strip()
        elif ' at ' in text.lower():
            parts = re.split(r'\s+at\s+', text, flags=re.I)
            if len(parts) > 1:
                result['event'] = parts[1].split('\n')[0].strip()
        
        # Extract date
        date_match = re.search(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}', text)
        if date_match:
            result['date'] = date_match.group(0)
        
        return result if result['url'] else None
    
    def get_dj_sets(self, dj_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent sets by a DJ.
        
        Args:
            dj_name: DJ name
            limit: Maximum results
            
        Returns:
            List of tracklist URLs and metadata
        """
        from urllib.parse import quote_plus
        
        # Try multiple approaches to find DJ sets
        sets = []
        
        # Approach 1: Search for the DJ name
        search_results = self.search_tracks(dj_name, limit * 2)
        
        for result in search_results:
            # Filter results that likely belong to this DJ
            if result.get('dj'):
                # Normalize names for comparison
                result_dj = result['dj'].lower().replace('-', ' ').replace('_', ' ')
                search_dj = dj_name.lower().replace('-', ' ').replace('_', ' ')
                
                # Check if DJ name matches (partial match acceptable)
                if search_dj in result_dj or result_dj in search_dj:
                    sets.append({
                        'url': result.get('url'),
                        'title': result.get('title'),
                        'dj': result.get('dj'),
                        'event': result.get('event'),
                        'date': result.get('date'),
                        'type': 'tracklist'
                    })
            elif result.get('title'):
                # Check if DJ name is in the title
                if dj_name.lower() in result['title'].lower():
                    sets.append({
                        'url': result.get('url'),
                        'title': result.get('title'),
                        'dj': dj_name,
                        'event': result.get('event'),
                        'date': result.get('date'),
                        'type': 'tracklist'
                    })
        
        # Approach 2: Try constructing a DJ profile URL (common pattern)
        if len(sets) < limit:
            # Clean DJ name for URL
            dj_slug = dj_name.lower().replace(' ', '-').replace('_', '-')
            dj_slug = re.sub(r'[^a-z0-9-]', '', dj_slug)
            
            # Try common DJ profile URL patterns
            profile_urls = [
                f"{self.BASE_URL}/dj/{dj_slug}",
                f"{self.BASE_URL}/artist/{dj_slug}",
                f"{self.BASE_URL}/djs/{dj_slug}"
            ]
            
            for profile_url in profile_urls:
                html = self.fetch_page(profile_url)
                if html and '404' not in html[:1000]:  # Quick 404 check
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for tracklist links on the profile page
                    tracklist_links = soup.find_all('a', href=re.compile(r'/tracklist/[a-z0-9]+/', re.I))
                    
                    for link in tracklist_links:
                        if len(sets) >= limit:
                            break
                        
                        # Extract set information
                        set_info = {
                            'url': self.BASE_URL + link.get('href', ''),
                            'title': link.get_text(strip=True),
                            'dj': dj_name,
                            'event': None,
                            'date': None,
                            'type': 'tracklist'
                        }
                        
                        # Try to extract event and date from surrounding text
                        parent = link.find_parent(['div', 'article', 'li', 'tr'])
                        if parent:
                            parent_text = parent.get_text()
                            
                            # Extract event (common patterns: "@ Event" or "at Venue")
                            event_match = re.search(r'@\s+([^,\n]+)|at\s+([^,\n]+)', parent_text, re.I)
                            if event_match:
                                set_info['event'] = (event_match.group(1) or event_match.group(2)).strip()
                            
                            # Extract date
                            date_match = re.search(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}', parent_text)
                            if date_match:
                                set_info['date'] = date_match.group(0)
                        
                        # Avoid duplicates
                        if not any(s['url'] == set_info['url'] for s in sets):
                            sets.append(set_info)
                    
                    if sets:
                        break  # Found sets, don't try other URL patterns
        
        # Sort by date if available (most recent first)
        sets_with_dates = [s for s in sets if s.get('date')]
        sets_without_dates = [s for s in sets if not s.get('date')]
        
        try:
            sets_with_dates.sort(key=lambda x: x['date'], reverse=True)
        except:
            pass  # If date parsing fails, keep original order
        
        return (sets_with_dates + sets_without_dates)[:limit]
    
    def get_festival_sets(self, festival_url: str) -> List[Dict[str, Any]]:
        """
        Get all sets from a festival.
        
        Args:
            festival_url: Festival page URL
            
        Returns:
            List of sets with metadata
        """
        html = self.fetch_page(festival_url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        sets = []
        
        # Extract festival name from page
        festival_name = None
        title_elem = soup.find(['h1', 'h2', 'title'])
        if title_elem:
            festival_name = title_elem.get_text(strip=True)
        
        # Find all set links on festival page
        # Strategy 1: Look for tracklist links
        tracklist_links = soup.find_all('a', href=re.compile(r'/tracklist/[a-z0-9]+/', re.I))
        
        for link in tracklist_links:
            set_info = {
                'url': self.BASE_URL + link.get('href', ''),
                'title': link.get_text(strip=True),
                'festival': festival_name,
                'dj': None,
                'stage': None,
                'date': None,
                'time': None,
                'type': 'tracklist'
            }
            
            # Extract DJ name from link text or surrounding context
            link_text = link.get_text(strip=True)
            
            # Common patterns: "DJ Name @ Stage" or "DJ Name - Time"
            if ' @ ' in link_text:
                parts = link_text.split(' @ ')
                set_info['dj'] = parts[0].strip()
                if len(parts) > 1:
                    set_info['stage'] = parts[1].strip()
            elif ' - ' in link_text:
                parts = link_text.split(' - ')
                set_info['dj'] = parts[0].strip()
            else:
                # Try to extract DJ from the URL or title
                url_match = re.search(r'/([^/]+)-at-', link.get('href', ''), re.I)
                if url_match:
                    set_info['dj'] = url_match.group(1).replace('-', ' ').title()
                else:
                    set_info['dj'] = link_text
            
            # Look for additional metadata in parent container
            parent = link.find_parent(['div', 'article', 'li', 'tr', 'section'])
            if parent:
                parent_text = parent.get_text(' ', strip=True)
                
                # Extract stage information
                stage_patterns = [
                    r'(?:stage|room|arena|floor)[:\s]+([^,\n]+)',
                    r'@\s+([^,\n]+(?:stage|room|arena|tent))',
                ]
                for pattern in stage_patterns:
                    stage_match = re.search(pattern, parent_text, re.I)
                    if stage_match:
                        set_info['stage'] = stage_match.group(1).strip()
                        break
                
                # Extract date
                date_match = re.search(
                    r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',
                    parent_text, re.I
                )
                if date_match:
                    set_info['date'] = date_match.group(0)
                
                # Extract time
                time_match = re.search(r'\b(\d{1,2}:\d{2})\s*(?:AM|PM|am|pm)?\b', parent_text)
                if time_match:
                    set_info['time'] = time_match.group(0)
            
            # Avoid duplicates
            if not any(s['url'] == set_info['url'] for s in sets):
                sets.append(set_info)
        
        # Strategy 2: If no tracklist links found, look for any festival lineup structure
        if not sets:
            # Look for common lineup containers
            lineup_containers = soup.find_all(['div', 'section', 'article'], 
                                             class_=re.compile(r'(lineup|artist|performer|dj|set)', re.I))
            
            for container in lineup_containers:
                # Find links within the container
                links = container.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if '/tracklist/' in href or '/dj/' in href or '/artist/' in href:
                        set_info = {
                            'url': self.BASE_URL + href if not href.startswith('http') else href,
                            'title': link.get_text(strip=True),
                            'festival': festival_name,
                            'dj': link.get_text(strip=True),
                            'stage': None,
                            'date': None,
                            'time': None,
                            'type': 'tracklist' if '/tracklist/' in href else 'dj_profile'
                        }
                        
                        # Extract additional info from container
                        container_text = container.get_text()
                        
                        # Date extraction
                        date_match = re.search(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}', container_text)
                        if date_match:
                            set_info['date'] = date_match.group(0)
                        
                        # Avoid duplicates
                        if not any(s['url'] == set_info['url'] for s in sets):
                            sets.append(set_info)
        
        # Sort by date and time if available
        for set_info in sets:
            if set_info.get('date') and set_info.get('time'):
                try:
                    # Create a sortable datetime string
                    set_info['_sort_key'] = f"{set_info['date']} {set_info['time']}"
                except:
                    set_info['_sort_key'] = set_info.get('date', '')
            else:
                set_info['_sort_key'] = set_info.get('date', '')
        
        # Sort and remove sort key
        sets.sort(key=lambda x: x.get('_sort_key', ''))
        for set_info in sets:
            set_info.pop('_sort_key', None)
        
        return sets


# Main integration class
class OneThousandOneTracklists:
    """
    Simple 1001 Tracklists integration.
    
    Returns raw data for agent processing.
    """
    
    def __init__(self):
        """Initialize the integration."""
        self.scraper = TracklistsScraper()
    
    def get_tracklist(self, url: str) -> Dict[str, Any]:
        """
        Get a tracklist from URL.
        
        Returns raw structured data for agent to process.
        """
        return self.scraper.extract_tracklist(url)
    
    def search(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for tracks."""
        return self.scraper.search_tracks(query, limit)
    
    def get_dj_sets(self, dj_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get DJ's recent sets."""
        return self.scraper.get_dj_sets(dj_name, limit)
    
    def get_festival(self, festival_url: str) -> List[Dict[str, Any]]:
        """Get all sets from a festival."""
        return self.scraper.get_festival_sets(festival_url)
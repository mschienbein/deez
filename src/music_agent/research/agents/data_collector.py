"""
Data Collector - Platform Search Specialist Agent

Handles searching specific music platforms for track metadata.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, List
import hashlib
import json
from datetime import datetime, timedelta

from .base import ResearchAgent, AgentRole
from ..core.research_context import PlatformResult

logger = logging.getLogger(__name__)


class DataCollector(ResearchAgent):
    """
    Specialist agent for collecting data from a specific platform.
    
    Each instance handles one platform and knows how to:
    - Search for tracks on that platform
    - Parse platform-specific responses
    - Handle rate limiting and retries
    - Cache results
    """
    
    # Platform-specific search configurations
    PLATFORM_CONFIGS = {
        'spotify': {
            'tool': 'search_spotify',
            'fields': ['title', 'artist', 'album', 'duration_ms', 'isrc', 'popularity'],
            'rate_limit': 10,  # requests per second
            'cache_ttl': 86400  # 24 hours
        },
        'beatport': {
            'tool': 'search_beatport',
            'fields': ['title', 'artist', 'bpm', 'key', 'genre', 'label', 'release_date'],
            'rate_limit': 5,
            'cache_ttl': 86400
        },
        'discogs': {
            'tool': 'search_discogs',
            'fields': ['title', 'artist', 'label', 'catalog_number', 'year', 'genre', 'style'],
            'rate_limit': 3,
            'cache_ttl': 172800  # 48 hours
        },
        'deezer': {
            'tool': 'search_deezer',
            'fields': ['title', 'artist', 'album', 'duration', 'isrc', 'bpm'],
            'rate_limit': 10,
            'cache_ttl': 86400
        },
        'soundcloud': {
            'tool': 'search_soundcloud',
            'fields': ['title', 'artist', 'duration', 'genre', 'tags', 'waveform_url'],
            'rate_limit': 5,
            'cache_ttl': 43200  # 12 hours
        },
        'youtube': {
            'tool': 'search_youtube',
            'fields': ['title', 'artist', 'duration', 'views', 'description'],
            'rate_limit': 10,
            'cache_ttl': 43200
        },
        'musicbrainz': {
            'tool': 'search_musicbrainz',
            'fields': ['title', 'artist', 'album', 'isrc', 'recording_id', 'release_id'],
            'rate_limit': 1,  # Very strict rate limit
            'cache_ttl': 604800  # 7 days
        },
        'genius': {
            'tool': 'search_genius',
            'fields': ['title', 'artist', 'lyrics', 'writers', 'producers'],
            'rate_limit': 5,
            'cache_ttl': 172800
        },
        'lastfm': {
            'tool': 'search_lastfm',
            'fields': ['title', 'artist', 'tags', 'playcount', 'listeners'],
            'rate_limit': 5,
            'cache_ttl': 86400
        }
    }
    
    # Simple in-memory cache (would use Redis in production)
    _cache: Dict[str, Dict[str, Any]] = {}
    
    def __init__(
        self,
        platform: str,
        context: 'ResearchContext',
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize data collector for a specific platform.
        
        Args:
            platform: Platform name to search
            context: Shared research context
            config: Optional configuration
        """
        super().__init__(
            name=f"DataCollector_{platform}",
            role=AgentRole.DATA_COLLECTOR,
            context=context,
            config=config or {}
        )
        
        self.platform = platform
        self.platform_config = self.PLATFORM_CONFIGS.get(platform, {})
        
        # Search parameters
        self.max_retries = self.config.get('max_retries', 3)
        self.cache_enabled = self.config.get('cache_enabled', True)
        
        # Rate limiting
        self.last_request_time = None
        self.rate_limit_delay = 1.0 / self.platform_config.get('rate_limit', 10)
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute platform search.
        
        Returns:
            Search results
        """
        self.start()
        
        try:
            # Build search query
            query = self._build_search_query()
            
            # Check cache first
            if self.cache_enabled:
                cached_result = self._check_cache(query)
                if cached_result:
                    self.log(f"Cache hit for {self.platform}")
                    self.cache_hits += 1
                    self._process_result(cached_result, from_cache=True)
                    self.complete(success=True)
                    return cached_result
            
            # Perform search with retries
            result = None
            for attempt in range(self.max_retries):
                try:
                    # Rate limiting
                    await self._enforce_rate_limit()
                    
                    # Execute search
                    self.log(f"Searching {self.platform} (attempt {attempt + 1})")
                    result = await self._search_platform(query)
                    self.api_calls += 1
                    
                    if result:
                        break
                        
                except Exception as e:
                    self.log_error(f"Search attempt {attempt + 1} failed: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
            
            if result:
                # Cache successful result
                if self.cache_enabled:
                    self._cache_result(query, result)
                
                # Process and store result
                self._process_result(result)
                self.complete(success=True)
                
                return result
            else:
                self.log_error(f"Failed to search {self.platform} after {self.max_retries} attempts")
                self._store_failure()
                self.complete(success=False)
                return {}
                
        except Exception as e:
            self.log_error(f"Unexpected error: {e}")
            self._store_failure()
            self.complete(success=False)
            return {}
    
    def _build_search_query(self) -> str:
        """Build platform-specific search query."""
        parsed = self.context.parsed_query
        
        # Start with basic artist - title format
        if parsed.get('artist') and parsed.get('title'):
            query = f"{parsed['artist']} {parsed['title']}"
        elif parsed.get('title'):
            query = parsed['title']
        else:
            query = self.context.query
        
        # Platform-specific adjustments
        if self.platform == 'beatport':
            # Beatport prefers clean titles without remix in parentheses
            query = query.split('(')[0].strip()
        
        elif self.platform == 'discogs':
            # Discogs works better with quotes for exact matching
            if parsed.get('artist') and parsed.get('title'):
                query = f'"{parsed["artist"]}" "{parsed["title"]}"'
        
        elif self.platform == 'musicbrainz':
            # MusicBrainz has specific query syntax
            if parsed.get('artist') and parsed.get('title'):
                query = f'artist:"{parsed["artist"]}" AND recording:"{parsed["title"]}"'
        
        return query
    
    async def _search_platform(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Execute platform search using appropriate tool.
        
        This is where we would integrate with the actual tool registry.
        For now, returning mock data structure.
        """
        # In real implementation, would use:
        # from ...tools.registry import get_tool_registry
        # registry = get_tool_registry()
        # tool = registry.get_tool(self.platform_config['tool'])
        # results = await tool.search(query)
        
        # Mock implementation
        self.log(f"Would search {self.platform} with query: {query}")
        
        # Simulate platform response
        mock_data = self._generate_mock_data(query)
        
        # Simulate network delay
        await asyncio.sleep(0.5)
        
        return mock_data
    
    def _generate_mock_data(self, query: str) -> Dict[str, Any]:
        """Generate mock data for testing."""
        # Generate realistic mock data based on platform
        if self.platform == 'spotify':
            return {
                'tracks': [{
                    'title': 'Strobe',
                    'artist': 'deadmau5',
                    'album': 'For Lack of a Better Name',
                    'duration_ms': 634000,
                    'isrc': 'USUS11000356',
                    'spotify_id': '3Oa0j5wSr3Z3BmP8Qzqjyj',
                    'popularity': 65,
                    'preview_url': 'https://p.scdn.co/preview/...',
                    'external_urls': {'spotify': 'https://open.spotify.com/track/...'}
                }]
            }
        
        elif self.platform == 'beatport':
            return {
                'tracks': [{
                    'title': 'Strobe',
                    'artist': 'deadmau5',
                    'mix': 'Original Mix',
                    'bpm': 128,
                    'key': 'C# min',
                    'genre': 'Progressive House',
                    'label': 'mau5trap',
                    'release_date': '2009-10-06',
                    'beatport_id': 1234567,
                    'price': 2.49,
                    'length': '10:34',
                    'preview': 'https://geo-samples.beatport.com/...'
                }]
            }
        
        elif self.platform == 'discogs':
            return {
                'results': [{
                    'title': 'For Lack Of A Better Name',
                    'artist': 'Deadmau5',
                    'type': 'release',
                    'year': 2009,
                    'label': ['Ultra Records', 'mau5trap'],
                    'catalog_number': 'UL 2339',
                    'format': ['CD', 'Album'],
                    'genre': ['Electronic'],
                    'style': ['Progressive House', 'Electro House'],
                    'tracklist': [
                        {'position': '10', 'title': 'Strobe', 'duration': '10:37'}
                    ]
                }]
            }
        
        return {'results': [], 'error': 'No results found'}
    
    async def _enforce_rate_limit(self) -> None:
        """Enforce platform rate limiting."""
        if self.last_request_time:
            elapsed = (datetime.utcnow() - self.last_request_time).total_seconds()
            if elapsed < self.rate_limit_delay:
                wait_time = self.rate_limit_delay - elapsed
                self.log(f"Rate limiting: waiting {wait_time:.2f}s")
                await asyncio.sleep(wait_time)
        
        self.last_request_time = datetime.utcnow()
    
    def _check_cache(self, query: str) -> Optional[Dict[str, Any]]:
        """Check if result is in cache."""
        cache_key = self._get_cache_key(query)
        
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            
            # Check if cache is still valid
            if datetime.utcnow() < cached['expires']:
                return cached['data']
            else:
                # Remove expired entry
                del self._cache[cache_key]
        
        return None
    
    def _cache_result(self, query: str, result: Dict[str, Any]) -> None:
        """Cache search result."""
        cache_key = self._get_cache_key(query)
        ttl_seconds = self.platform_config.get('cache_ttl', 86400)
        
        self._cache[cache_key] = {
            'data': result,
            'expires': datetime.utcnow() + timedelta(seconds=ttl_seconds),
            'platform': self.platform
        }
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for query."""
        key_data = f"{self.platform}:{query}".encode('utf-8')
        return hashlib.md5(key_data).hexdigest()
    
    def _process_result(self, result: Dict[str, Any], from_cache: bool = False) -> None:
        """Process and store search result."""
        # Parse platform-specific response
        parsed = self._parse_platform_response(result)
        
        # Calculate confidence based on result quality
        confidence = self._calculate_confidence(parsed)
        
        # Create platform result
        platform_result = PlatformResult(
            platform=self.platform,
            success=bool(parsed),
            data=parsed,
            confidence=confidence,
            search_query=self._build_search_query(),
            num_results=len(parsed.get('tracks', []))
        )
        
        # Store in context
        self.context.add_platform_result(self.platform, platform_result)
        
        self.log(f"Found {platform_result.num_results} results with {confidence:.0%} confidence")
    
    def _parse_platform_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse platform-specific response into standard format."""
        parsed = {
            'platform': self.platform,
            'raw_response': response,
            'tracks': []
        }
        
        # Platform-specific parsing
        if self.platform == 'spotify' and 'tracks' in response:
            for track in response['tracks']:
                parsed['tracks'].append({
                    'title': track.get('title'),
                    'artist': track.get('artist'),
                    'album': track.get('album'),
                    'duration_ms': track.get('duration_ms'),
                    'isrc': track.get('isrc'),
                    'platform_id': track.get('spotify_id'),
                    'url': track.get('external_urls', {}).get('spotify'),
                    'preview_url': track.get('preview_url'),
                    'popularity': track.get('popularity')
                })
        
        elif self.platform == 'beatport' and 'tracks' in response:
            for track in response['tracks']:
                # Convert length string to ms
                duration_ms = None
                if track.get('length'):
                    parts = track['length'].split(':')
                    if len(parts) == 2:
                        duration_ms = (int(parts[0]) * 60 + int(parts[1])) * 1000
                
                parsed['tracks'].append({
                    'title': track.get('title'),
                    'artist': track.get('artist'),
                    'mix': track.get('mix'),
                    'bpm': track.get('bpm'),
                    'key': track.get('key'),
                    'genre': track.get('genre'),
                    'label': track.get('label'),
                    'release_date': track.get('release_date'),
                    'duration_ms': duration_ms,
                    'platform_id': track.get('beatport_id'),
                    'price': track.get('price'),
                    'preview_url': track.get('preview')
                })
        
        elif self.platform == 'discogs' and 'results' in response:
            for result in response['results']:
                # Find the specific track in tracklist if available
                if 'tracklist' in result:
                    for track in result['tracklist']:
                        if 'strobe' in track.get('title', '').lower():
                            parsed['tracks'].append({
                                'title': track.get('title'),
                                'artist': result.get('artist'),
                                'album': result.get('title'),
                                'position': track.get('position'),
                                'duration': track.get('duration'),
                                'year': result.get('year'),
                                'label': result.get('label', [None])[0],
                                'catalog_number': result.get('catalog_number'),
                                'genre': result.get('genre', [None])[0],
                                'style': result.get('style', [])
                            })
                            break
        
        return parsed
    
    def _calculate_confidence(self, parsed: Dict[str, Any]) -> float:
        """Calculate confidence score for search results."""
        if not parsed.get('tracks'):
            return 0.0
        
        confidence = 0.5  # Base confidence for having results
        
        # Platform-specific confidence adjustments
        platform_weights = {
            'beatport': 0.95,  # Very reliable for electronic music
            'spotify': 0.90,   # Generally reliable
            'discogs': 0.90,   # Reliable for detailed info
            'musicbrainz': 0.85,
            'deezer': 0.85,
            'genius': 0.80,
            'soundcloud': 0.70,
            'youtube': 0.60,
            'lastfm': 0.75
        }
        
        confidence *= platform_weights.get(self.platform, 0.75)
        
        # Adjust based on number of results
        num_results = len(parsed['tracks'])
        if num_results == 1:
            confidence *= 1.0  # Single exact match is good
        elif num_results <= 3:
            confidence *= 0.95  # Few results, likely accurate
        else:
            confidence *= 0.85  # Many results, might be ambiguous
        
        # Check if query matches results (simple check)
        if parsed['tracks']:
            first_track = parsed['tracks'][0]
            query_lower = self.context.query.lower()
            
            title_match = first_track.get('title', '').lower() in query_lower or query_lower in first_track.get('title', '').lower()
            artist_match = first_track.get('artist', '').lower() in query_lower or query_lower in first_track.get('artist', '').lower()
            
            if title_match or artist_match:
                confidence *= 1.1  # Boost for matching
            else:
                confidence *= 0.8  # Reduce for mismatch
        
        return min(confidence, 1.0)
    
    def _store_failure(self) -> None:
        """Store failure result in context."""
        platform_result = PlatformResult(
            platform=self.platform,
            success=False,
            error=f"Failed after {self.max_retries} attempts",
            confidence=0.0,
            search_query=self._build_search_query()
        )
        
        self.context.add_platform_result(self.platform, platform_result)
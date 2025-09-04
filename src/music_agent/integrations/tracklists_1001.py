"""
1001 Tracklists integration for DJ set and track data extraction.

This module provides scraping and analysis of DJ sets, festivals, and track data
from 1001tracklists.com with:
- Efficient HTML parsing with BeautifulSoup
- Structured data extraction
- Caching and rate limiting
- Raw data output for agent processing
"""

import re
import json
import asyncio
import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib

import httpx
from bs4 import BeautifulSoup
import openai
from pydantic import BaseModel, Field

from ..utils.config import get_config
from ..integrations.discogs import DiscogsIntegration

logger = logging.getLogger(__name__)


class MixType(Enum):
    """Types of track transitions in DJ sets."""
    STANDARD = "standard"
    WITH = "w/"  # Playing simultaneously
    INTO = "into"  # Direct transition
    OVER = "over"  # Layered mixing
    MASHUP = "mashup"
    ACAPELLA = "acapella"


@dataclass
class TrackMetadata:
    """Enhanced track metadata from multiple sources."""
    bpm: Optional[float] = None
    key: Optional[str] = None
    energy: Optional[float] = None
    genre: Optional[str] = None
    subgenre: Optional[str] = None
    release_date: Optional[datetime] = None
    spotify_uri: Optional[str] = None
    beatport_url: Optional[str] = None
    discogs_id: Optional[int] = None
    soundcloud_url: Optional[str] = None


@dataclass 
class DJSetTrack:
    """Represents a track in a DJ set with timing and mixing info."""
    position: int
    timestamp: Optional[str] = None
    artist: str = ""
    title: str = ""
    remix: Optional[str] = None
    label: Optional[str] = None
    mix_type: MixType = MixType.STANDARD
    mix_notes: Optional[str] = None  # e.g., "double drop", "key clash"
    is_id: bool = False  # Unknown/unreleased track
    confidence: float = 1.0  # LLM extraction confidence
    metadata: TrackMetadata = field(default_factory=TrackMetadata)
    
    @property
    def full_title(self) -> str:
        """Get full track title including remix."""
        base = f"{self.artist} - {self.title}"
        if self.remix:
            base += f" ({self.remix})"
        return base
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'position': self.position,
            'timestamp': self.timestamp,
            'artist': self.artist,
            'title': self.title,
            'remix': self.remix,
            'label': self.label,
            'mix_type': self.mix_type.value,
            'mix_notes': self.mix_notes,
            'is_id': self.is_id,
            'confidence': self.confidence,
            'bpm': self.metadata.bpm,
            'key': self.metadata.key,
            'genre': self.metadata.genre
        }


@dataclass
class DJSetInfo:
    """Complete DJ set/tracklist information."""
    id: str
    url: str
    dj_name: str
    event_name: Optional[str] = None
    date: Optional[datetime] = None
    venue: Optional[str] = None
    location: Optional[str] = None
    duration_minutes: Optional[int] = None
    genres: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    play_count: int = 0
    favorite_count: int = 0
    tracks: List[DJSetTrack] = field(default_factory=list)
    recording_url: Optional[str] = None  # SoundCloud/Mixcloud
    download_url: Optional[str] = None
    
    @property
    def track_count(self) -> int:
        """Number of tracks in the set."""
        return len(self.tracks)
    
    @property
    def avg_bpm(self) -> Optional[float]:
        """Calculate average BPM of the set."""
        bpms = [t.metadata.bpm for t in self.tracks if t.metadata.bpm]
        return sum(bpms) / len(bpms) if bpms else None
    
    @property
    def key_progression(self) -> List[str]:
        """Get key progression through the set."""
        return [t.metadata.key for t in self.tracks if t.metadata.key]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'url': self.url,
            'dj_name': self.dj_name,
            'event_name': self.event_name,
            'date': self.date.isoformat() if self.date else None,
            'venue': self.venue,
            'location': self.location,
            'duration_minutes': self.duration_minutes,
            'genres': self.genres,
            'tags': self.tags,
            'play_count': self.play_count,
            'favorite_count': self.favorite_count,
            'track_count': self.track_count,
            'avg_bpm': self.avg_bpm,
            'tracks': [t.to_dict() for t in self.tracks],
            'recording_url': self.recording_url
        }


class TracklistsLLMExtractor:
    """LLM-based extraction for 1001 Tracklists data."""
    
    def __init__(self, openai_client):
        self.client = openai_client
        
    async def extract_tracklist(self, html: str) -> Dict[str, Any]:
        """Extract tracklist data from HTML using LLM."""
        # Prepare a focused prompt for structured extraction
        prompt = """
        Extract DJ set/tracklist information from this HTML content.
        
        Return a JSON object with:
        - dj_name: Name of the DJ/artist
        - event_name: Event or show name
        - date: Date in ISO format if available
        - venue: Venue name
        - location: City/country
        - genres: Array of music genres
        - tracks: Array of track objects, each containing:
          - position: Track number
          - timestamp: Time in set (if shown)
          - artist: Track artist
          - title: Track title
          - remix: Remix name if applicable
          - label: Record label
          - mix_type: Type of transition (standard/w/into/over)
          - is_id: true if track is marked as "ID" (unknown)
        
        Focus on the main tracklist content. Extract as much as possible.
        """
        
        # Clean HTML to reduce token usage
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove scripts, styles, and unnecessary elements
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        
        # Get text content with structure preserved
        content = soup.get_text(separator='\n', strip=True)
        
        # Limit content length
        if len(content) > 15000:
            content = content[:15000]
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a music data extraction expert."},
                    {"role": "user", "content": f"{prompt}\n\nHTML Content:\n{content}"}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            # Fallback to basic extraction
            return self._fallback_extraction(soup)
    
    def _fallback_extraction(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Basic extraction as fallback when LLM fails."""
        data = {
            'dj_name': '',
            'event_name': '',
            'tracks': []
        }
        
        # Try to find DJ name
        dj_elem = soup.find('h1', class_='djName') or soup.find('meta', {'property': 'og:title'})
        if dj_elem:
            data['dj_name'] = dj_elem.get_text() if hasattr(dj_elem, 'get_text') else dj_elem.get('content', '')
        
        # Try to extract tracks (basic approach)
        track_divs = soup.find_all('div', class_=re.compile('track|tlpItem'))
        for i, div in enumerate(track_divs[:100]):  # Limit to 100 tracks
            track_text = div.get_text(separator=' ', strip=True)
            if track_text:
                data['tracks'].append({
                    'position': i + 1,
                    'artist': '',
                    'title': track_text,
                    'is_id': 'ID - ID' in track_text or 'Unknown' in track_text
                })
        
        return data


class OneThousandOneTracklistsIntegration:
    """
    Modern 1001 Tracklists integration with LLM enhancement.
    
    Features:
    - Intelligent HTML parsing with LLMs
    - Automatic track metadata enhancement
    - Festival and DJ analysis tools
    - Caching and rate limiting
    """
    
    def __init__(self):
        """Initialize the integration."""
        config = get_config()
        
        # HTTP client with retry logic
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; MusicAgent/1.0)',
                'Accept': 'text/html,application/json',
                'Accept-Language': 'en-US,en;q=0.9'
            }
        )
        
        # Initialize LLM extractor if OpenAI is configured
        self.llm_extractor = None
        if config.openai.api_key:
            openai.api_key = config.openai.api_key
            self.llm_extractor = TracklistsLLMExtractor(openai)
        
        # Cache for processed tracklists
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour
        
        # Rate limiting
        self._last_request = datetime.min
        self._min_request_interval = timedelta(seconds=2)  # 30 requests/minute
        
        # Initialize other integrations for enrichment
        self.discogs = DiscogsIntegration()
    
    async def _rate_limit(self):
        """Enforce rate limiting."""
        now = datetime.now()
        time_since_last = now - self._last_request
        
        if time_since_last < self._min_request_interval:
            wait_time = (self._min_request_interval - time_since_last).total_seconds()
            await asyncio.sleep(wait_time)
        
        self._last_request = datetime.now()
    
    def _get_cache_key(self, url: str) -> str:
        """Generate cache key for URL."""
        return hashlib.md5(url.encode()).hexdigest()
    
    async def get_tracklist(self, url: str, enhance: bool = True) -> DJSetInfo:
        """
        Fetch and parse a DJ set tracklist.
        
        Args:
            url: 1001 Tracklists URL
            enhance: Whether to enhance tracks with external data
        
        Returns:
            Complete DJ set information
        """
        # Check cache
        cache_key = self._get_cache_key(url)
        if cache_key in self._cache:
            cached_time, cached_data = self._cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self._cache_ttl):
                logger.info(f"Returning cached tracklist for {url}")
                return cached_data
        
        # Rate limit
        await self._rate_limit()
        
        try:
            # Fetch HTML
            response = await self.client.get(url)
            response.raise_for_status()
            html = response.text
            
            # Extract with LLM or fallback
            if self.llm_extractor:
                extracted = await self.llm_extractor.extract_tracklist(html)
            else:
                # Basic extraction without LLM
                soup = BeautifulSoup(html, 'html.parser')
                extracted = self._basic_extraction(soup)
            
            # Create DJSetInfo object
            dj_set = self._create_djset_from_extraction(url, extracted)
            
            # Enhance with external data if requested
            if enhance:
                dj_set = await self._enhance_tracklist(dj_set)
            
            # Cache the result
            self._cache[cache_key] = (datetime.now(), dj_set)
            
            return dj_set
            
        except Exception as e:
            logger.error(f"Error fetching tracklist from {url}: {e}")
            raise
    
    def _basic_extraction(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Basic HTML extraction without LLM."""
        data = {
            'dj_name': '',
            'event_name': '',
            'date': None,
            'venue': '',
            'location': '',
            'genres': [],
            'tracks': []
        }
        
        # Extract basic metadata
        title_elem = soup.find('title')
        if title_elem:
            title_text = title_elem.get_text()
            # Parse title format: "DJ Name @ Event - Date"
            parts = title_text.split('@')
            if parts:
                data['dj_name'] = parts[0].strip()
                if len(parts) > 1:
                    event_parts = parts[1].split('-')
                    if event_parts:
                        data['event_name'] = event_parts[0].strip()
        
        # Extract tracks
        track_number = 1
        for track_elem in soup.find_all(['div', 'tr'], class_=re.compile('track|tlpItem')):
            track_text = track_elem.get_text(separator=' ', strip=True)
            
            # Basic parsing of track format: "Artist - Title (Remix)"
            if ' - ' in track_text:
                parts = track_text.split(' - ', 1)
                artist = parts[0].strip()
                title_part = parts[1].strip()
                
                # Extract remix
                remix = None
                if '(' in title_part and ')' in title_part:
                    title, remix_part = title_part.split('(', 1)
                    remix = remix_part.rstrip(')')
                else:
                    title = title_part
                
                data['tracks'].append({
                    'position': track_number,
                    'artist': artist,
                    'title': title,
                    'remix': remix,
                    'is_id': 'ID' in track_text
                })
                track_number += 1
        
        return data
    
    def _create_djset_from_extraction(self, url: str, data: Dict[str, Any]) -> DJSetInfo:
        """Create DJSetInfo from extracted data."""
        # Generate ID from URL
        set_id = self._get_cache_key(url)
        
        # Parse date if available
        date = None
        if data.get('date'):
            try:
                date = datetime.fromisoformat(data['date'])
            except:
                pass
        
        # Create track objects
        tracks = []
        for track_data in data.get('tracks', []):
            track = DJSetTrack(
                position=track_data.get('position', 0),
                timestamp=track_data.get('timestamp'),
                artist=track_data.get('artist', ''),
                title=track_data.get('title', ''),
                remix=track_data.get('remix'),
                label=track_data.get('label'),
                is_id=track_data.get('is_id', False),
                confidence=track_data.get('confidence', 0.8)
            )
            
            # Parse mix type
            if track_data.get('mix_type'):
                try:
                    track.mix_type = MixType(track_data['mix_type'])
                except:
                    pass
            
            tracks.append(track)
        
        return DJSetInfo(
            id=set_id,
            url=url,
            dj_name=data.get('dj_name', ''),
            event_name=data.get('event_name'),
            date=date,
            venue=data.get('venue'),
            location=data.get('location'),
            genres=data.get('genres', []),
            tags=data.get('tags', []),
            tracks=tracks
        )
    
    async def _enhance_tracklist(self, dj_set: DJSetInfo) -> DJSetInfo:
        """
        Enhance tracklist with external data sources.
        
        Adds BPM, key, genre, and streaming links from:
        - Spotify (if configured)
        - Beatport (if configured)
        - Discogs
        """
        for track in dj_set.tracks:
            if track.is_id or not track.artist:
                continue
            
            # Try Discogs for additional metadata
            try:
                search_query = f"{track.artist} {track.title}"
                if track.remix:
                    search_query += f" {track.remix}"
                
                discogs_results = self.discogs.search(
                    query=search_query,
                    page=1,
                    per_page=1
                )
                
                if discogs_results.get('results'):
                    result = discogs_results['results'][0]
                    track.metadata.genre = result.get('genre', [None])[0] if result.get('genre') else None
                    track.metadata.discogs_id = result.get('id')
            except Exception as e:
                logger.debug(f"Discogs enhancement failed for {track.full_title}: {e}")
            
            # Add a small delay between lookups
            await asyncio.sleep(0.1)
        
        return dj_set
    
    async def analyze_dj_style(self, dj_name: str, num_sets: int = 10) -> Dict[str, Any]:
        """
        Analyze a DJ's mixing style and track preferences.
        
        Args:
            dj_name: Name of the DJ
            num_sets: Number of recent sets to analyze
        
        Returns:
            Analysis including BPM ranges, key preferences, genre distribution
        """
        # This would require searching for the DJ's sets
        # For now, return a placeholder structure
        return {
            'dj_name': dj_name,
            'sets_analyzed': 0,
            'avg_bpm': None,
            'bpm_range': None,
            'preferred_keys': [],
            'genre_distribution': {},
            'signature_tracks': [],
            'avg_set_length': None,
            'mixing_style': 'unknown'
        }
    
    async def find_track_appearances(
        self,
        artist: str,
        title: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Find all DJ sets that include a specific track.
        
        Args:
            artist: Track artist
            title: Track title
            limit: Maximum results
        
        Returns:
            List of appearances with DJ name, event, and date
        """
        # This would require search functionality on 1001 Tracklists
        # For now, return empty list
        return []
    
    async def get_festival_lineup(self, festival_url: str) -> List[DJSetInfo]:
        """
        Get all DJ sets from a festival.
        
        Args:
            festival_url: 1001 Tracklists festival page URL
        
        Returns:
            List of all DJ sets from the festival
        """
        # This would require parsing festival pages
        # For now, return empty list
        return []
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
"""
MusicBrainz API client implementation.
"""

import time
import logging
from typing import Optional, List, Dict, Any

import musicbrainzngs as mb

from .config import MusicBrainzConfig
from .models import (
    Artist,
    Recording,
    Release,
    ReleaseGroup,
    Label,
    EntityType,
    SearchResults,
)
from .exceptions import (
    AuthenticationError,
    APIError,
    RateLimitError,
    NotFoundError,
    NetworkError,
)
from .api import SearchAPI, DatabaseAPI

logger = logging.getLogger(__name__)


class MusicBrainzClient:
    """Main MusicBrainz API client."""
    
    def __init__(self, config: Optional[MusicBrainzConfig] = None):
        """
        Initialize MusicBrainz client.
        
        Args:
            config: Optional configuration. If not provided, will load from environment.
        """
        self.config = config or MusicBrainzConfig.from_env()
        self.config.validate()
        
        # Initialize musicbrainzngs
        self._init_mb_client()
        
        # Initialize API modules
        self.search = SearchAPI(self)
        self.database = DatabaseAPI(self)
        
        # Rate limiting
        self._last_request_time = 0
    
    def _init_mb_client(self):
        """Initialize the underlying musicbrainzngs client."""
        # Set user agent (required by MusicBrainz)
        mb.set_useragent(
            self.config.app_name,
            self.config.app_version,
            self.config.contact_email or "https://github.com/user/project"
        )
        
        # Set authentication if available
        if self.config.username and self.config.password:
            mb.auth(self.config.username, self.config.password)
        
        # Set rate limit
        mb.set_rate_limit(
            limit_or_interval=1.0 / self.config.requests_per_second,
            new_requests=1
        )
        
        logger.info(f"MusicBrainz client initialized with user agent: {self.config.user_agent}")
    
    def _handle_rate_limit(self):
        """Handle rate limiting (1 request per second for MusicBrainz)."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < (1.0 / self.config.requests_per_second):
            sleep_time = (1.0 / self.config.requests_per_second) - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    # Convenience methods for common operations
    
    def search_artists(
        self,
        query: str,
        limit: int = 25,
        offset: int = 0,
        **filters
    ) -> SearchResults:
        """
        Search for artists.
        
        Args:
            query: Search query
            limit: Number of results
            offset: Pagination offset
            **filters: Additional filters
            
        Returns:
            SearchResults object
        """
        return self.search.search_artist(query, limit, offset, **filters)
    
    def search_releases(
        self,
        query: str,
        artist: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
        **filters
    ) -> SearchResults:
        """
        Search for releases.
        
        Args:
            query: Search query
            artist: Filter by artist name
            limit: Number of results
            offset: Pagination offset
            **filters: Additional filters
            
        Returns:
            SearchResults object
        """
        return self.search.search_release(query, artist, limit, offset, **filters)
    
    def search_recordings(
        self,
        query: str,
        artist: Optional[str] = None,
        release: Optional[str] = None,
        limit: int = 25,
        offset: int = 0,
        **filters
    ) -> SearchResults:
        """
        Search for recordings.
        
        Args:
            query: Search query
            artist: Filter by artist name
            release: Filter by release name
            limit: Number of results
            offset: Pagination offset
            **filters: Additional filters
            
        Returns:
            SearchResults object
        """
        return self.search.search_recording(query, artist, release, limit, offset, **filters)
    
    def get_artist(self, artist_id: str) -> Artist:
        """
        Get artist information.
        
        Args:
            artist_id: MusicBrainz ID
            
        Returns:
            Artist object
        """
        return self.database.get_artist(artist_id, includes=['aliases', 'tags', 'ratings'])
    
    def get_recording(self, recording_id: str) -> Recording:
        """
        Get recording information.
        
        Args:
            recording_id: MusicBrainz ID
            
        Returns:
            Recording object
        """
        return self.database.get_recording(recording_id, includes=['artists', 'releases', 'isrcs'])
    
    def get_release(self, release_id: str) -> Release:
        """
        Get release information.
        
        Args:
            release_id: MusicBrainz ID
            
        Returns:
            Release object
        """
        return self.database.get_release(
            release_id,
            includes=['artists', 'labels', 'recordings', 'release-groups', 'media']
        )
    
    def get_release_group(self, release_group_id: str) -> ReleaseGroup:
        """
        Get release group information.
        
        Args:
            release_group_id: MusicBrainz ID
            
        Returns:
            ReleaseGroup object
        """
        return self.database.get_release_group(
            release_group_id,
            includes=['artists', 'releases', 'tags']
        )
    
    def get_label(self, label_id: str) -> Label:
        """
        Get label information.
        
        Args:
            label_id: MusicBrainz ID
            
        Returns:
            Label object
        """
        return self.database.get_label(label_id, includes=['aliases', 'tags', 'ratings'])
    
    def get_recording_by_isrc(self, isrc: str) -> List[Recording]:
        """
        Get recordings by ISRC.
        
        Args:
            isrc: International Standard Recording Code
            
        Returns:
            List of Recording objects
        """
        try:
            result = mb.get_recordings_by_isrc(isrc, includes=['artists', 'releases'])
            
            recordings = []
            if 'isrc' in result and 'recording-list' in result['isrc']:
                parser = self.database.parser
                for rec_data in result['isrc']['recording-list']:
                    recordings.append(parser.parse_recording(rec_data))
            
            return recordings
            
        except Exception as e:
            raise APIError(f"Failed to get recordings by ISRC: {e}")
    
    def get_cover_art(self, release_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cover art URLs for a release.
        
        Args:
            release_id: MusicBrainz release ID
            
        Returns:
            Dictionary with cover art URLs or None
        """
        try:
            # Check if release has cover art
            release = self.get_release(release_id)
            if not release.has_cover_art:
                return None
            
            # Get cover art from Cover Art Archive
            import requests
            response = requests.get(
                f"https://coverartarchive.org/release/{release_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get cover art: {e}")
            return None
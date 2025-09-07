"""
Discogs API client implementation.
"""

import time
import logging
from typing import Optional, List, Dict, Any, Union
from urllib.parse import urlencode

import discogs_client
from discogs_client.exceptions import HTTPError

from .config import DiscogsConfig
from .models import (
    SearchType,
    Artist,
    Release,
    Master,
    Label,
    Track,
    SearchResult,
    MarketplaceListing,
    CollectionItem,
    Image,
)
from .exceptions import (
    AuthenticationError,
    APIError,
    RateLimitError,
    NotFoundError,
    NetworkError,
)
from .api import SearchAPI, DatabaseAPI, MarketplaceAPI, CollectionAPI

logger = logging.getLogger(__name__)


class DiscogsClient:
    """Main Discogs API client."""
    
    def __init__(self, config: Optional[DiscogsConfig] = None):
        """
        Initialize Discogs client.
        
        Args:
            config: Optional configuration. If not provided, will load from environment.
        """
        self.config = config or DiscogsConfig.from_env()
        self.config.validate()
        
        # Initialize the official client
        self._client = self._init_client()
        
        # Initialize API modules
        self.search = SearchAPI(self)
        self.database = DatabaseAPI(self)
        self.marketplace = MarketplaceAPI(self)
        self.collection = CollectionAPI(self)
        
        # Rate limiting
        self._last_request_time = 0
        self._request_count = 0
        
    def _init_client(self) -> discogs_client.Client:
        """Initialize the underlying Discogs client."""
        if self.config.user_token:
            return discogs_client.Client(
                self.config.user_agent,
                user_token=self.config.user_token
            )
        elif self.config.consumer_key and self.config.consumer_secret:
            return discogs_client.Client(
                self.config.user_agent,
                consumer_key=self.config.consumer_key,
                consumer_secret=self.config.consumer_secret
            )
        else:
            # Create unauthenticated client (limited rate limits)
            return discogs_client.Client(self.config.user_agent)
    
    def _handle_rate_limit(self):
        """Handle rate limiting."""
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self._last_request_time > 60:
            self._request_count = 0
            self._last_request_time = current_time
        
        # Check if we need to wait
        if self._request_count >= self.config.requests_per_minute:
            sleep_time = 60 - (current_time - self._last_request_time)
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.1f} seconds")
                time.sleep(sleep_time)
                self._request_count = 0
                self._last_request_time = time.time()
        
        self._request_count += 1
    
    def _make_request(self, method: str, *args, **kwargs) -> Any:
        """
        Make a request with error handling and rate limiting.
        
        Args:
            method: Method name to call on the client
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method
            
        Returns:
            API response
            
        Raises:
            Various API exceptions
        """
        self._handle_rate_limit()
        
        retries = 0
        while retries < self.config.max_retries:
            try:
                result = getattr(self._client, method)(*args, **kwargs)
                return result
            except HTTPError as e:
                if e.status_code == 401:
                    raise AuthenticationError("Authentication failed")
                elif e.status_code == 404:
                    raise NotFoundError(f"Resource not found: {e}")
                elif e.status_code == 429:
                    retry_after = int(e.headers.get('Retry-After', 60))
                    if retries < self.config.max_retries - 1:
                        logger.warning(f"Rate limited, retrying after {retry_after} seconds")
                        time.sleep(retry_after)
                        retries += 1
                        continue
                    raise RateLimitError("Rate limit exceeded", retry_after=retry_after)
                else:
                    raise APIError(f"API error: {e}", status_code=e.status_code)
            except Exception as e:
                if retries < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (2 ** retries))
                    retries += 1
                    continue
                raise NetworkError(f"Network error: {e}")
        
        raise APIError("Max retries exceeded")
    
    # Convenience methods for common operations
    
    def search_releases(
        self,
        query: str,
        artist: Optional[str] = None,
        label: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[Union[int, str]] = None,
        country: Optional[str] = None,
        format: Optional[str] = None,
        per_page: int = 50,
        page: int = 1
    ) -> List[SearchResult]:
        """
        Search for releases.
        
        Args:
            query: Search query
            artist: Filter by artist name
            label: Filter by label
            genre: Filter by genre
            year: Filter by year or year range
            country: Filter by country
            format: Filter by format (Vinyl, CD, etc.)
            per_page: Results per page
            page: Page number
            
        Returns:
            List of search results
        """
        return self.search.search(
            query=query,
            type=SearchType.RELEASE,
            artist=artist,
            label=label,
            genre=genre,
            year=year,
            country=country,
            format=format,
            per_page=per_page,
            page=page
        )
    
    def get_release(self, release_id: int) -> Release:
        """
        Get detailed release information.
        
        Args:
            release_id: Discogs release ID
            
        Returns:
            Release object
        """
        return self.database.get_release(release_id)
    
    def get_master(self, master_id: int) -> Master:
        """
        Get master release information.
        
        Args:
            master_id: Discogs master ID
            
        Returns:
            Master object
        """
        return self.database.get_master(master_id)
    
    def get_artist(self, artist_id: int) -> Artist:
        """
        Get artist information.
        
        Args:
            artist_id: Discogs artist ID
            
        Returns:
            Artist object
        """
        return self.database.get_artist(artist_id)
    
    def get_label(self, label_id: int) -> Label:
        """
        Get label information.
        
        Args:
            label_id: Discogs label ID
            
        Returns:
            Label object
        """
        return self.database.get_label(label_id)
    
    def get_marketplace_listings(
        self,
        release_id: int,
        condition: Optional[str] = None,
        currency: str = "USD"
    ) -> List[MarketplaceListing]:
        """
        Get marketplace listings for a release.
        
        Args:
            release_id: Discogs release ID
            condition: Filter by condition
            currency: Currency for prices
            
        Returns:
            List of marketplace listings
        """
        return self.marketplace.get_listings(
            release_id,
            condition=condition,
            currency=currency
        )
    
    def get_collection(
        self,
        username: Optional[str] = None,
        folder_id: int = 0
    ) -> List[CollectionItem]:
        """
        Get user's collection.
        
        Args:
            username: Username (defaults to authenticated user)
            folder_id: Collection folder ID (0 for all)
            
        Returns:
            List of collection items
        """
        return self.collection.get_collection(username, folder_id)
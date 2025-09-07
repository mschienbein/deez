"""
Main Beatport API client.
"""

from typing import Optional, List, Dict, Any

from .config import BeatportConfig
from .auth import BeatportAuth
from .api import SearchAPI, TracksAPI, ChartsAPI
from .models import (
    Track, Release, Artist, Label,
    SearchQuery, SearchResult, Chart,
    ChartType, SearchType
)


class BeatportClient:
    """
    Main Beatport API client.
    
    Example:
        >>> from beatport import BeatportClient
        >>> client = BeatportClient()
        >>> 
        >>> # Search for tracks
        >>> tracks = client.search_tracks("deadmau5")
        >>> 
        >>> # Get track details
        >>> track = client.get_track(12345)
        >>> 
        >>> # Get charts
        >>> top_100 = client.get_top_100()
    """
    
    def __init__(self, config: Optional[BeatportConfig] = None):
        """
        Initialize Beatport client.
        
        Args:
            config: Configuration object (uses env if not provided)
        """
        self.config = config or BeatportConfig.from_env()
        self.config.validate()
        
        # Initialize auth handler
        self.auth = BeatportAuth(self.config)
        
        # Initialize API modules
        self.search_api = SearchAPI(self.auth, self.config)
        self.tracks_api = TracksAPI(self.auth, self.config)
        self.charts_api = ChartsAPI(self.auth, self.config)
    
    # Authentication methods
    
    def authenticate(self) -> str:
        """
        Authenticate and get access token.
        
        Returns:
            Access token
        """
        return self.auth.authenticate()
    
    def login(self, username: str, password: str) -> str:
        """
        Login with credentials.
        
        Args:
            username: Beatport username
            password: Beatport password
            
        Returns:
            Access token
        """
        return self.auth.login(username, password)
    
    # Search methods
    
    def search(self, query: SearchQuery) -> SearchResult:
        """
        Perform advanced search.
        
        Args:
            query: Search query parameters
            
        Returns:
            Search results
        """
        return self.search_api.search(query)
    
    def search_tracks(
        self,
        query: str,
        genre_id: Optional[int] = None,
        bpm_low: Optional[int] = None,
        bpm_high: Optional[int] = None,
        key_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 25
    ) -> List[Track]:
        """
        Search for tracks.
        
        Args:
            query: Search query
            genre_id: Filter by genre
            bpm_low: Minimum BPM
            bpm_high: Maximum BPM
            key_id: Filter by key
            page: Page number
            per_page: Results per page
            
        Returns:
            List of tracks
        """
        return self.search_api.search_tracks(
            query,
            genre_id=genre_id,
            bpm_low=bpm_low,
            bpm_high=bpm_high,
            key_id=key_id,
            page=page,
            per_page=per_page
        )
    
    def search_releases(
        self,
        query: str,
        label_id: Optional[int] = None,
        page: int = 1,
        per_page: int = 25
    ) -> List[Release]:
        """
        Search for releases.
        
        Args:
            query: Search query
            label_id: Filter by label
            page: Page number
            per_page: Results per page
            
        Returns:
            List of releases
        """
        return self.search_api.search_releases(
            query,
            label_id=label_id,
            page=page,
            per_page=per_page
        )
    
    def search_artists(
        self,
        query: str,
        page: int = 1,
        per_page: int = 25
    ) -> List[Artist]:
        """
        Search for artists.
        
        Args:
            query: Search query
            page: Page number
            per_page: Results per page
            
        Returns:
            List of artists
        """
        return self.search_api.search_artists(
            query,
            page=page,
            per_page=per_page
        )
    
    def search_labels(
        self,
        query: str,
        page: int = 1,
        per_page: int = 25
    ) -> List[Label]:
        """
        Search for labels.
        
        Args:
            query: Search query
            page: Page number
            per_page: Results per page
            
        Returns:
            List of labels
        """
        return self.search_api.search_labels(
            query,
            page=page,
            per_page=per_page
        )
    
    def autocomplete(
        self,
        query: str,
        search_type: Optional[SearchType] = None
    ) -> Dict[str, List[str]]:
        """
        Get autocomplete suggestions.
        
        Args:
            query: Partial query
            search_type: Type to search
            
        Returns:
            Suggestions by type
        """
        return self.search_api.autocomplete(query, search_type)
    
    # Track methods
    
    def get_track(self, track_id: int) -> Track:
        """
        Get track by ID.
        
        Args:
            track_id: Track ID
            
        Returns:
            Track object
        """
        return self.tracks_api.get_track(track_id)
    
    def get_track_by_slug(self, slug: str) -> Track:
        """
        Get track by slug.
        
        Args:
            slug: Track slug
            
        Returns:
            Track object
        """
        return self.tracks_api.get_track_by_slug(slug)
    
    def get_related_tracks(
        self,
        track_id: int,
        limit: int = 10
    ) -> List[Track]:
        """
        Get related tracks.
        
        Args:
            track_id: Track ID
            limit: Maximum results
            
        Returns:
            List of related tracks
        """
        return self.tracks_api.get_related_tracks(track_id, limit)
    
    def get_track_stream_url(self, track_id: int) -> Optional[str]:
        """
        Get track preview stream URL.
        
        Args:
            track_id: Track ID
            
        Returns:
            Stream URL or None
        """
        return self.tracks_api.get_track_stream_url(track_id)
    
    # Chart methods
    
    def get_chart(
        self,
        chart_type: ChartType = ChartType.TOP_100,
        genre_id: Optional[int] = None
    ) -> Chart:
        """
        Get chart.
        
        Args:
            chart_type: Type of chart
            genre_id: Genre filter
            
        Returns:
            Chart object
        """
        return self.charts_api.get_chart(chart_type, genre_id)
    
    def get_top_100(
        self,
        genre_id: Optional[int] = None
    ) -> List[Track]:
        """
        Get Beatport Top 100.
        
        Args:
            genre_id: Genre filter
            
        Returns:
            List of tracks
        """
        chart_tracks = self.charts_api.get_top_100(genre_id)
        return [ct.track for ct in chart_tracks]
    
    def get_hype_chart(
        self,
        genre_id: Optional[int] = None
    ) -> List[Track]:
        """
        Get Hype chart.
        
        Args:
            genre_id: Genre filter
            
        Returns:
            List of tracks
        """
        chart_tracks = self.charts_api.get_hype_chart(genre_id)
        return [ct.track for ct in chart_tracks]
    
    def get_essential_chart(
        self,
        genre_id: Optional[int] = None
    ) -> List[Track]:
        """
        Get Essential chart.
        
        Args:
            genre_id: Genre filter
            
        Returns:
            List of tracks
        """
        chart_tracks = self.charts_api.get_essential_chart(genre_id)
        return [ct.track for ct in chart_tracks]
    
    # Utility methods
    
    def close(self) -> None:
        """Close client and cleanup resources."""
        if hasattr(self.auth, 'session'):
            self.auth.session.close()
        if hasattr(self.search_api, 'session'):
            self.search_api.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
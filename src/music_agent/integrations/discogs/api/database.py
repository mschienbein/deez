"""
Database API functionality for Discogs.
"""

import logging
from typing import Optional, List, Dict, Any

from ..models import Artist, Release, Master, Label
from ..exceptions import NotFoundError, APIError
from .parsers import DataParser

logger = logging.getLogger(__name__)


class DatabaseAPI:
    """Handles database queries for artists, releases, masters, and labels."""
    
    def __init__(self, client):
        """
        Initialize database API.
        
        Args:
            client: Parent DiscogsClient instance
        """
        self.client = client
        self.parser = DataParser()
    
    def get_release(self, release_id: int) -> Release:
        """
        Get detailed release information.
        
        Args:
            release_id: Discogs release ID
            
        Returns:
            Release object with full details
            
        Raises:
            NotFoundError: If release not found
        """
        try:
            release_data = self.client._client.release(release_id)
            return self.parser.parse_release(release_data)
        except Exception as e:
            if "404" in str(e):
                raise NotFoundError(f"Release {release_id} not found")
            raise APIError(f"Failed to get release {release_id}: {e}")
    
    def get_master(self, master_id: int) -> Master:
        """
        Get master release information.
        
        Args:
            master_id: Discogs master ID
            
        Returns:
            Master object with full details
            
        Raises:
            NotFoundError: If master not found
        """
        try:
            master_data = self.client._client.master(master_id)
            return self.parser.parse_master(master_data)
        except Exception as e:
            if "404" in str(e):
                raise NotFoundError(f"Master {master_id} not found")
            raise APIError(f"Failed to get master {master_id}: {e}")
    
    def get_artist(self, artist_id: int) -> Artist:
        """
        Get artist information.
        
        Args:
            artist_id: Discogs artist ID
            
        Returns:
            Artist object with full details
            
        Raises:
            NotFoundError: If artist not found
        """
        try:
            artist_data = self.client._client.artist(artist_id)
            return self.parser.parse_artist(artist_data)
        except Exception as e:
            if "404" in str(e):
                raise NotFoundError(f"Artist {artist_id} not found")
            raise APIError(f"Failed to get artist {artist_id}: {e}")
    
    def get_label(self, label_id: int) -> Label:
        """
        Get label information.
        
        Args:
            label_id: Discogs label ID
            
        Returns:
            Label object with full details
            
        Raises:
            NotFoundError: If label not found
        """
        try:
            label_data = self.client._client.label(label_id)
            return self.parser.parse_label(label_data)
        except Exception as e:
            if "404" in str(e):
                raise NotFoundError(f"Label {label_id} not found")
            raise APIError(f"Failed to get label {label_id}: {e}")
    
    def get_artist_releases(
        self,
        artist_id: int,
        sort: str = "year",
        sort_order: str = "asc",
        per_page: int = 50,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get releases by an artist.
        
        Args:
            artist_id: Discogs artist ID
            sort: Sort by (year, title, format)
            sort_order: Sort order (asc, desc)
            per_page: Results per page
            page: Page number
            
        Returns:
            List of release dictionaries
        """
        try:
            artist = self.client._client.artist(artist_id)
            releases = artist.releases.page(page)
            return [self.parser.parse_basic_release(r) for r in releases]
        except Exception as e:
            raise APIError(f"Failed to get artist releases: {e}")
    
    def get_label_releases(
        self,
        label_id: int,
        per_page: int = 50,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get releases on a label.
        
        Args:
            label_id: Discogs label ID
            per_page: Results per page
            page: Page number
            
        Returns:
            List of release dictionaries
        """
        try:
            label = self.client._client.label(label_id)
            releases = label.releases.page(page)
            return [self.parser.parse_basic_release(r) for r in releases]
        except Exception as e:
            raise APIError(f"Failed to get label releases: {e}")
    
    def get_master_versions(
        self,
        master_id: int,
        per_page: int = 50,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get all versions of a master release.
        
        Args:
            master_id: Discogs master ID
            per_page: Results per page
            page: Page number
            
        Returns:
            List of version dictionaries
        """
        try:
            master = self.client._client.master(master_id)
            versions = master.versions.page(page)
            return [self.parser.parse_basic_release(v) for v in versions]
        except Exception as e:
            raise APIError(f"Failed to get master versions: {e}")
"""
Database API functionality for MusicBrainz.
"""

import logging
from typing import Optional, List, Dict, Any

from ..models import (
    Artist,
    Recording,
    Release,
    ReleaseGroup,
    Label,
)
from ..exceptions import APIError, NotFoundError
from .parsers import DataParser

logger = logging.getLogger(__name__)


class DatabaseAPI:
    """Handles database lookup operations."""
    
    def __init__(self, client):
        """
        Initialize database API.
        
        Args:
            client: Parent MusicBrainzClient instance
        """
        self.client = client
        self.parser = DataParser()
    
    def get_artist(
        self,
        artist_id: str,
        includes: Optional[List[str]] = None
    ) -> Artist:
        """
        Get artist by MBID.
        
        Args:
            artist_id: MusicBrainz ID
            includes: Additional data to include (aliases, tags, ratings, etc.)
            
        Returns:
            Artist object
        """
        try:
            import musicbrainzngs as mb
            
            includes = includes or []
            result = mb.get_artist_by_id(artist_id, includes=includes)
            
            if 'artist' in result:
                return self.parser.parse_artist(result['artist'])
            else:
                raise NotFoundError(f"Artist {artist_id} not found")
                
        except mb.ResponseError as e:
            if e.cause and '404' in str(e.cause):
                raise NotFoundError(f"Artist {artist_id} not found")
            raise APIError(f"Failed to get artist: {e}")
        except Exception as e:
            raise APIError(f"Failed to get artist: {e}")
    
    def get_recording(
        self,
        recording_id: str,
        includes: Optional[List[str]] = None
    ) -> Recording:
        """
        Get recording by MBID.
        
        Args:
            recording_id: MusicBrainz ID
            includes: Additional data to include (artists, releases, isrcs, etc.)
            
        Returns:
            Recording object
        """
        try:
            import musicbrainzngs as mb
            
            includes = includes or ['artists', 'releases']
            result = mb.get_recording_by_id(recording_id, includes=includes)
            
            if 'recording' in result:
                return self.parser.parse_recording(result['recording'])
            else:
                raise NotFoundError(f"Recording {recording_id} not found")
                
        except mb.ResponseError as e:
            if e.cause and '404' in str(e.cause):
                raise NotFoundError(f"Recording {recording_id} not found")
            raise APIError(f"Failed to get recording: {e}")
        except Exception as e:
            raise APIError(f"Failed to get recording: {e}")
    
    def get_release(
        self,
        release_id: str,
        includes: Optional[List[str]] = None
    ) -> Release:
        """
        Get release by MBID.
        
        Args:
            release_id: MusicBrainz ID
            includes: Additional data to include (artists, labels, recordings, etc.)
            
        Returns:
            Release object
        """
        try:
            import musicbrainzngs as mb
            
            includes = includes or ['artists', 'labels', 'recordings', 'release-groups']
            result = mb.get_release_by_id(release_id, includes=includes)
            
            if 'release' in result:
                return self.parser.parse_release(result['release'])
            else:
                raise NotFoundError(f"Release {release_id} not found")
                
        except mb.ResponseError as e:
            if e.cause and '404' in str(e.cause):
                raise NotFoundError(f"Release {release_id} not found")
            raise APIError(f"Failed to get release: {e}")
        except Exception as e:
            raise APIError(f"Failed to get release: {e}")
    
    def get_release_group(
        self,
        release_group_id: str,
        includes: Optional[List[str]] = None
    ) -> ReleaseGroup:
        """
        Get release group by MBID.
        
        Args:
            release_group_id: MusicBrainz ID
            includes: Additional data to include (artists, releases, tags, etc.)
            
        Returns:
            ReleaseGroup object
        """
        try:
            import musicbrainzngs as mb
            
            includes = includes or ['artists', 'releases']
            result = mb.get_release_group_by_id(release_group_id, includes=includes)
            
            if 'release-group' in result:
                return self.parser.parse_release_group(result['release-group'])
            else:
                raise NotFoundError(f"Release group {release_group_id} not found")
                
        except mb.ResponseError as e:
            if e.cause and '404' in str(e.cause):
                raise NotFoundError(f"Release group {release_group_id} not found")
            raise APIError(f"Failed to get release group: {e}")
        except Exception as e:
            raise APIError(f"Failed to get release group: {e}")
    
    def get_label(
        self,
        label_id: str,
        includes: Optional[List[str]] = None
    ) -> Label:
        """
        Get label by MBID.
        
        Args:
            label_id: MusicBrainz ID
            includes: Additional data to include (aliases, tags, ratings, etc.)
            
        Returns:
            Label object
        """
        try:
            import musicbrainzngs as mb
            
            includes = includes or []
            result = mb.get_label_by_id(label_id, includes=includes)
            
            if 'label' in result:
                return self.parser.parse_label(result['label'])
            else:
                raise NotFoundError(f"Label {label_id} not found")
                
        except mb.ResponseError as e:
            if e.cause and '404' in str(e.cause):
                raise NotFoundError(f"Label {label_id} not found")
            raise APIError(f"Failed to get label: {e}")
        except Exception as e:
            raise APIError(f"Failed to get label: {e}")
    
    def get_artist_releases(
        self,
        artist_id: str,
        release_type: Optional[List[str]] = None,
        limit: int = 25,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get releases by an artist.
        
        Args:
            artist_id: MusicBrainz artist ID
            release_type: Filter by release type
            limit: Number of results
            offset: Pagination offset
            
        Returns:
            List of release dictionaries
        """
        try:
            import musicbrainzngs as mb
            
            kwargs = {
                'limit': limit,
                'offset': offset,
            }
            if release_type:
                kwargs['release_type'] = release_type
            
            result = mb.browse_releases(artist=artist_id, **kwargs)
            return result.get('release-list', [])
            
        except Exception as e:
            raise APIError(f"Failed to get artist releases: {e}")
    
    def get_label_releases(
        self,
        label_id: str,
        limit: int = 25,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get releases on a label.
        
        Args:
            label_id: MusicBrainz label ID
            limit: Number of results
            offset: Pagination offset
            
        Returns:
            List of release dictionaries
        """
        try:
            import musicbrainzngs as mb
            
            result = mb.browse_releases(label=label_id, limit=limit, offset=offset)
            return result.get('release-list', [])
            
        except Exception as e:
            raise APIError(f"Failed to get label releases: {e}")
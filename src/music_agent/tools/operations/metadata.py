"""
Base metadata operation template for all integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class MetadataOperation(ABC):
    """Base class for all metadata operations."""
    
    platform_name: str = "unknown"
    
    @abstractmethod
    async def get_track_metadata(self, track_id: str, **kwargs) -> Dict[str, Any]:
        """Get detailed track metadata."""
        pass
    
    async def get_album_metadata(self, album_id: str, **kwargs) -> Dict[str, Any]:
        """Get detailed album metadata. Optional - some platforms may not support this."""
        return {'error': f'{self.platform_name} does not support album metadata'}
    
    async def get_artist_metadata(self, artist_id: str, **kwargs) -> Dict[str, Any]:
        """Get detailed artist metadata. Optional - some platforms may not support this."""
        return {'error': f'{self.platform_name} does not support artist metadata'}
    
    async def get_audio_features(self, track_id: str, **kwargs) -> Dict[str, Any]:
        """Get audio features (BPM, key, energy, etc.). Optional - some platforms may not support this."""
        return {'error': f'{self.platform_name} does not support audio features'}
    
    def standardize_track_metadata(self, raw_result: Dict) -> Dict[str, Any]:
        """Convert platform-specific track metadata to standard format."""
        return {
            'id': raw_result.get('id'),
            'title': raw_result.get('title') or raw_result.get('name'),
            'artist': self._extract_artist_info(raw_result),
            'album': self._extract_album_info(raw_result),
            'duration': self._extract_duration_ms(raw_result),
            'release_date': self._extract_release_date(raw_result),
            'genre': self._extract_genre(raw_result),
            'bpm': self._extract_bpm(raw_result),
            'key': self._extract_key(raw_result),
            'isrc': self._extract_isrc(raw_result),
            'explicit': self._extract_explicit_flag(raw_result),
            'popularity': self._extract_popularity(raw_result),
            'platform': self.platform_name,
            'url': raw_result.get('url') or raw_result.get('external_urls', {}).get('spotify'),
            'preview_url': raw_result.get('preview_url'),
            'artwork_url': self._extract_artwork_url(raw_result),
            'metadata': self._extract_raw_metadata(raw_result)
        }
    
    def standardize_album_metadata(self, raw_result: Dict) -> Dict[str, Any]:
        """Convert platform-specific album metadata to standard format."""
        return {
            'id': raw_result.get('id'),
            'title': raw_result.get('name') or raw_result.get('title'),
            'artist': self._extract_artist_info(raw_result),
            'release_date': self._extract_release_date(raw_result),
            'total_tracks': raw_result.get('total_tracks') or raw_result.get('track_count'),
            'genre': self._extract_genre(raw_result),
            'label': self._extract_label(raw_result),
            'upc': self._extract_upc(raw_result),
            'platform': self.platform_name,
            'url': raw_result.get('url') or raw_result.get('external_urls', {}).get('spotify'),
            'artwork_url': self._extract_artwork_url(raw_result),
            'tracks': self._extract_album_tracks(raw_result),
            'metadata': self._extract_raw_metadata(raw_result)
        }
    
    def standardize_artist_metadata(self, raw_result: Dict) -> Dict[str, Any]:
        """Convert platform-specific artist metadata to standard format."""
        return {
            'id': raw_result.get('id'),
            'name': raw_result.get('name'),
            'genres': self._extract_artist_genres(raw_result),
            'popularity': self._extract_popularity(raw_result),
            'followers': self._extract_follower_count(raw_result),
            'platform': self.platform_name,
            'url': raw_result.get('url') or raw_result.get('external_urls', {}).get('spotify'),
            'image_url': self._extract_artist_image(raw_result),
            'metadata': self._extract_raw_metadata(raw_result)
        }
    
    def _extract_artist_info(self, raw_result: Dict) -> Dict[str, Any]:
        """Extract artist information. Override in subclasses."""
        artists = raw_result.get('artists', [])
        if artists and isinstance(artists, list):
            primary_artist = artists[0]
            return {
                'id': primary_artist.get('id'),
                'name': primary_artist.get('name'),
                'all_artists': [{'id': a.get('id'), 'name': a.get('name')} for a in artists]
            }
        return {
            'id': None,
            'name': raw_result.get('artist') or 'Unknown',
            'all_artists': []
        }
    
    def _extract_album_info(self, raw_result: Dict) -> Dict[str, Any]:
        """Extract album information. Override in subclasses."""
        album = raw_result.get('album', {})
        return {
            'id': album.get('id'),
            'name': album.get('name') or album.get('title'),
            'release_date': album.get('release_date'),
            'total_tracks': album.get('total_tracks')
        }
    
    def _extract_duration_ms(self, raw_result: Dict) -> Optional[int]:
        """Extract duration in milliseconds. Override in subclasses."""
        return raw_result.get('duration_ms')
    
    def _extract_release_date(self, raw_result: Dict) -> Optional[str]:
        """Extract release date. Override in subclasses."""
        return raw_result.get('release_date')
    
    def _extract_genre(self, raw_result: Dict) -> Optional[str]:
        """Extract primary genre. Override in subclasses."""
        genres = raw_result.get('genres', [])
        if genres and isinstance(genres, list):
            return genres[0]
        return raw_result.get('genre')
    
    def _extract_bpm(self, raw_result: Dict) -> Optional[float]:
        """Extract BPM. Override in subclasses."""
        return raw_result.get('bpm') or raw_result.get('tempo')
    
    def _extract_key(self, raw_result: Dict) -> Optional[str]:
        """Extract musical key. Override in subclasses."""
        return raw_result.get('key')
    
    def _extract_isrc(self, raw_result: Dict) -> Optional[str]:
        """Extract ISRC code. Override in subclasses."""
        external_ids = raw_result.get('external_ids', {})
        return external_ids.get('isrc') or raw_result.get('isrc')
    
    def _extract_explicit_flag(self, raw_result: Dict) -> bool:
        """Extract explicit content flag. Override in subclasses."""
        return raw_result.get('explicit', False)
    
    def _extract_popularity(self, raw_result: Dict) -> Optional[int]:
        """Extract popularity score. Override in subclasses."""
        return raw_result.get('popularity')
    
    def _extract_artwork_url(self, raw_result: Dict) -> Optional[str]:
        """Extract artwork URL. Override in subclasses."""
        images = raw_result.get('images', [])
        if images and isinstance(images, list):
            return images[0].get('url')
        return raw_result.get('artwork_url')
    
    def _extract_label(self, raw_result: Dict) -> Optional[str]:
        """Extract record label. Override in subclasses."""
        return raw_result.get('label')
    
    def _extract_upc(self, raw_result: Dict) -> Optional[str]:
        """Extract UPC code. Override in subclasses."""
        external_ids = raw_result.get('external_ids', {})
        return external_ids.get('upc') or raw_result.get('upc')
    
    def _extract_album_tracks(self, raw_result: Dict) -> List[Dict[str, Any]]:
        """Extract album track list. Override in subclasses."""
        tracks = raw_result.get('tracks', {})
        if isinstance(tracks, dict):
            return tracks.get('items', [])
        elif isinstance(tracks, list):
            return tracks
        return []
    
    def _extract_artist_genres(self, raw_result: Dict) -> List[str]:
        """Extract artist genres. Override in subclasses."""
        return raw_result.get('genres', [])
    
    def _extract_follower_count(self, raw_result: Dict) -> Optional[int]:
        """Extract follower count. Override in subclasses."""
        followers = raw_result.get('followers', {})
        return followers.get('total') if isinstance(followers, dict) else followers
    
    def _extract_artist_image(self, raw_result: Dict) -> Optional[str]:
        """Extract artist image URL. Override in subclasses."""
        return self._extract_artwork_url(raw_result)
    
    def _extract_raw_metadata(self, raw_result: Dict) -> Dict[str, Any]:
        """Extract platform-specific raw metadata. Override in subclasses."""
        return {'raw': raw_result}
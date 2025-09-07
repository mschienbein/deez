"""
Data parsers for MusicBrainz API responses.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from ..models import (
    Artist,
    Recording,
    Release,
    ReleaseGroup,
    Label,
    Track,
    Medium,
    SearchResult,
    EntityType,
    ReleaseStatus,
    ReleaseType,
)


class DataParser:
    """Parse MusicBrainz API responses into model objects."""
    
    def parse_artist(self, data: Dict[str, Any]) -> Artist:
        """Parse artist data."""
        return Artist(
            id=data.get('id', ''),
            name=data.get('name', ''),
            sort_name=data.get('sort-name'),
            disambiguation=data.get('disambiguation'),
            type=data.get('type'),
            gender=data.get('gender'),
            country=data.get('country'),
            area=data.get('area'),
            begin_date=self._parse_date(data.get('life-span', {}).get('begin')),
            end_date=self._parse_date(data.get('life-span', {}).get('end')),
            life_span=data.get('life-span'),
            aliases=data.get('aliases', []),
            tags=data.get('tags', []),
            rating=data.get('rating', {}).get('value') if data.get('rating') else None,
            isnis=data.get('isnis', []),
            ipis=data.get('ipis', []),
        )
    
    def parse_recording(self, data: Dict[str, Any]) -> Recording:
        """Parse recording data."""
        return Recording(
            id=data.get('id', ''),
            title=data.get('title', ''),
            length=data.get('length'),
            disambiguation=data.get('disambiguation'),
            artist_credit=data.get('artist-credit', []),
            releases=data.get('releases', []),
            isrcs=data.get('isrcs', []),
            tags=data.get('tags', []),
            rating=data.get('rating', {}).get('value') if data.get('rating') else None,
        )
    
    def parse_release(self, data: Dict[str, Any]) -> Release:
        """Parse release data."""
        status = None
        if data.get('status'):
            try:
                status = ReleaseStatus(data['status'].lower())
            except ValueError:
                pass
        
        return Release(
            id=data.get('id', ''),
            title=data.get('title', ''),
            status=status,
            quality=data.get('quality'),
            disambiguation=data.get('disambiguation'),
            packaging=data.get('packaging'),
            barcode=data.get('barcode'),
            release_date=self._parse_date(data.get('date')),
            country=data.get('country'),
            artist_credit=data.get('artist-credit', []),
            label_info=data.get('label-info', []),
            media=self._parse_media(data.get('media', [])),
            release_group=data.get('release-group'),
            tags=data.get('tags', []),
            rating=data.get('rating', {}).get('value') if data.get('rating') else None,
            cover_art_archive=data.get('cover-art-archive'),
            text_representation=data.get('text-representation'),
        )
    
    def parse_release_group(self, data: Dict[str, Any]) -> ReleaseGroup:
        """Parse release group data."""
        release_type = None
        if data.get('primary-type'):
            try:
                release_type = ReleaseType(data['primary-type'].lower())
            except ValueError:
                pass
        
        return ReleaseGroup(
            id=data.get('id', ''),
            title=data.get('title', ''),
            type=release_type,
            primary_type=data.get('primary-type'),
            secondary_types=data.get('secondary-types', []),
            disambiguation=data.get('disambiguation'),
            artist_credit=data.get('artist-credit', []),
            releases=data.get('releases', []),
            tags=data.get('tags', []),
            rating=data.get('rating', {}).get('value') if data.get('rating') else None,
            first_release_date=self._parse_date(data.get('first-release-date')),
        )
    
    def parse_label(self, data: Dict[str, Any]) -> Label:
        """Parse label data."""
        return Label(
            id=data.get('id', ''),
            name=data.get('name', ''),
            sort_name=data.get('sort-name'),
            disambiguation=data.get('disambiguation'),
            type=data.get('type'),
            country=data.get('country'),
            area=data.get('area'),
            life_span=data.get('life-span'),
            aliases=data.get('aliases', []),
            tags=data.get('tags', []),
            label_code=data.get('label-code'),
            ipis=data.get('ipis', []),
            isnis=data.get('isnis', []),
        )
    
    def parse_search_result(self, data: Dict[str, Any], entity_type: EntityType) -> SearchResult:
        """Parse search result."""
        # Extract common fields
        result = SearchResult(
            type=entity_type,
            id=data.get('id', ''),
            score=data.get('score', 0),
            disambiguation=data.get('disambiguation'),
            tags=[tag['name'] for tag in data.get('tags', []) if 'name' in tag],
        )
        
        # Entity-specific fields
        if entity_type == EntityType.ARTIST:
            result.name = data.get('name')
            result.country = data.get('country')
        
        elif entity_type == EntityType.RELEASE:
            result.title = data.get('title')
            result.status = data.get('status')
            result.date = data.get('date')
            result.country = data.get('country')
            result.barcode = data.get('barcode')
            result.track_count = data.get('track-count')
            
            # Get artist from artist-credit
            if data.get('artist-credit'):
                artists = []
                for credit in data['artist-credit']:
                    if 'name' in credit:
                        artists.append(credit['name'])
                result.artist = ' '.join(artists)
            
            # Get label info
            if data.get('label-info'):
                labels = []
                for info in data['label-info']:
                    if 'label' in info and 'name' in info['label']:
                        labels.append(info['label']['name'])
                    if 'catalog-number' in info:
                        result.catalog_number = info['catalog-number']
                if labels:
                    result.label = ', '.join(labels)
        
        elif entity_type == EntityType.RECORDING:
            result.title = data.get('title')
            
            # Get artist from artist-credit
            if data.get('artist-credit'):
                artists = []
                for credit in data['artist-credit']:
                    if 'name' in credit:
                        artists.append(credit['name'])
                result.artist = ' '.join(artists)
        
        elif entity_type == EntityType.LABEL:
            result.name = data.get('name')
            result.country = data.get('country')
        
        return result
    
    def _parse_media(self, media_list: List[Dict[str, Any]]) -> List[Medium]:
        """Parse media list."""
        media = []
        for medium_data in media_list:
            medium = Medium(
                position=medium_data.get('position', 0),
                format=medium_data.get('format'),
                title=medium_data.get('title'),
                track_count=medium_data.get('track-count', 0),
                tracks=self._parse_tracks(medium_data.get('tracks', [])),
            )
            media.append(medium)
        return media
    
    def _parse_tracks(self, track_list: List[Dict[str, Any]]) -> List[Track]:
        """Parse track list."""
        tracks = []
        for track_data in track_list:
            track = Track(
                id=track_data.get('id'),
                position=track_data.get('position'),
                number=track_data.get('number'),
                title=track_data.get('title', ''),
                length=track_data.get('length'),
                recording_id=track_data.get('recording', {}).get('id') if track_data.get('recording') else None,
                artist_credit=track_data.get('artist-credit', []),
            )
            tracks.append(track)
        return tracks
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        
        # Try different date formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m',
            '%Y',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
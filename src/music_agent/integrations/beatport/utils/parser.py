"""
Response parser for Beatport API.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from ..models import (
    Track, Release, Artist, Label, Genre, Key,
    Remixer, Waveform, Stream, Price,
    Chart, ChartTrack
)


class ResponseParser:
    """Parse API responses into model objects."""
    
    def parse_artist(self, data: Dict[str, Any]) -> Artist:
        """
        Parse artist data.
        
        Args:
            data: Raw artist data
            
        Returns:
            Artist object
        """
        return Artist(
            id=data['id'],
            name=data['name'],
            slug=data.get('slug'),
            url=data.get('url'),
            image=data.get('image'),
            biography=data.get('biography'),
            facebook=data.get('facebook'),
            twitter=data.get('twitter'),
            soundcloud=data.get('soundcloud'),
            instagram=data.get('instagram')
        )
    
    def parse_label(self, data: Dict[str, Any]) -> Label:
        """
        Parse label data.
        
        Args:
            data: Raw label data
            
        Returns:
            Label object
        """
        return Label(
            id=data['id'],
            name=data['name'],
            slug=data.get('slug'),
            url=data.get('url'),
            image=data.get('image'),
            biography=data.get('biography')
        )
    
    def parse_genre(self, data: Dict[str, Any]) -> Genre:
        """
        Parse genre data.
        
        Args:
            data: Raw genre data
            
        Returns:
            Genre object
        """
        return Genre(
            id=data['id'],
            name=data['name'],
            slug=data.get('slug'),
            url=data.get('url')
        )
    
    def parse_key(self, data: Dict[str, Any]) -> Key:
        """
        Parse key data.
        
        Args:
            data: Raw key data
            
        Returns:
            Key object
        """
        return Key(
            id=data['id'],
            name=data['name'],
            short_name=data.get('short_name'),
            camelot=data.get('camelot')
        )
    
    def parse_remixer(self, data: Dict[str, Any]) -> Remixer:
        """
        Parse remixer data.
        
        Args:
            data: Raw remixer data
            
        Returns:
            Remixer object
        """
        return Remixer(
            id=data['id'],
            name=data['name'],
            slug=data.get('slug'),
            url=data.get('url')
        )
    
    def parse_waveform(self, data: Dict[str, Any]) -> Waveform:
        """
        Parse waveform data.
        
        Args:
            data: Raw waveform data
            
        Returns:
            Waveform object
        """
        return Waveform(
            url=data.get('url'),
            width=data.get('width'),
            height=data.get('height')
        )
    
    def parse_stream(self, data: Dict[str, Any]) -> Stream:
        """
        Parse stream data.
        
        Args:
            data: Raw stream data
            
        Returns:
            Stream object
        """
        return Stream(
            url=data['url'],
            format=data.get('format', 'mp3'),
            quality=data.get('quality', '128')
        )
    
    def parse_price(self, data: Dict[str, Any]) -> Price:
        """
        Parse price data.
        
        Args:
            data: Raw price data
            
        Returns:
            Price object
        """
        return Price(
            currency=data.get('currency', 'USD'),
            value=float(data.get('value', 0)),
            formatted=data.get('formatted')
        )
    
    def parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse datetime string.
        
        Args:
            date_str: Date string
            
        Returns:
            datetime object or None
        """
        if not date_str:
            return None
        
        # Try different formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def parse_track(self, data: Dict[str, Any]) -> Track:
        """
        Parse track data.
        
        Args:
            data: Raw track data
            
        Returns:
            Track object
        """
        track = Track(
            id=data['id'],
            name=data['name'],
            mix=data.get('mix_name'),
            slug=data.get('slug'),
            url=data.get('url')
        )
        
        # Parse artists
        if 'artists' in data:
            track.artists = [self.parse_artist(a) for a in data['artists']]
        
        # Parse remixers
        if 'remixers' in data:
            track.remixers = [self.parse_remixer(r) for r in data['remixers']]
        
        # Parse label
        if 'label' in data and data['label']:
            track.label = self.parse_label(data['label'])
        
        # Parse dates
        track.release_date = self.parse_datetime(data.get('release_date'))
        track.publish_date = self.parse_datetime(data.get('publish_date'))
        
        # Parse genres
        if 'genre' in data and data['genre']:
            track.genre = self.parse_genre(data['genre'])
        if 'sub_genre' in data and data['sub_genre']:
            track.sub_genre = self.parse_genre(data['sub_genre'])
        
        # Parse key
        if 'key' in data and data['key']:
            track.key = self.parse_key(data['key'])
        
        # Music metadata
        track.bpm = data.get('bpm')
        track.length_ms = data.get('length_ms') or data.get('duration_ms')
        
        # Media
        track.image = data.get('image')
        
        if 'waveform' in data and data['waveform']:
            track.waveform = self.parse_waveform(data['waveform'])
        
        if 'preview' in data and data['preview']:
            track.preview = self.parse_stream(data['preview'])
        
        # Purchase info
        if 'price' in data and data['price']:
            track.price = self.parse_price(data['price'])
        
        track.exclusive = data.get('exclusive', False)
        track.available = data.get('available', True)
        
        # Additional metadata
        track.isrc = data.get('isrc')
        track.catalog_number = data.get('catalog_number')
        
        return track
    
    def parse_release(self, data: Dict[str, Any]) -> Release:
        """
        Parse release data.
        
        Args:
            data: Raw release data
            
        Returns:
            Release object
        """
        release = Release(
            id=data['id'],
            name=data['name'],
            slug=data.get('slug'),
            url=data.get('url')
        )
        
        # Parse artists
        if 'artists' in data:
            release.artists = [self.parse_artist(a) for a in data['artists']]
        
        # Parse label
        if 'label' in data and data['label']:
            release.label = self.parse_label(data['label'])
        
        # Parse dates
        release.release_date = self.parse_datetime(data.get('release_date'))
        release.publish_date = self.parse_datetime(data.get('publish_date'))
        
        # Metadata
        release.catalog_number = data.get('catalog_number')
        release.upc = data.get('upc')
        
        # Media
        release.image = data.get('image')
        
        # Tracks
        if 'tracks' in data:
            release.tracks = [self.parse_track(t) for t in data['tracks']]
        release.track_count = data.get('track_count', len(release.tracks))
        
        # Purchase info
        if 'price' in data and data['price']:
            release.price = self.parse_price(data['price'])
        
        release.exclusive = data.get('exclusive', False)
        
        return release
    
    def parse_chart_track(self, data: Dict[str, Any]) -> ChartTrack:
        """
        Parse chart track data.
        
        Args:
            data: Raw chart track data
            
        Returns:
            ChartTrack object
        """
        return ChartTrack(
            position=data['position'],
            track=self.parse_track(data['track']),
            change=data.get('change'),
            peak_position=data.get('peak_position'),
            weeks_on_chart=data.get('weeks_on_chart')
        )
    
    def parse_chart(self, data: Dict[str, Any]) -> Chart:
        """
        Parse chart data.
        
        Args:
            data: Raw chart data
            
        Returns:
            Chart object
        """
        chart = Chart(
            id=data.get('id'),
            name=data.get('name', ''),
            description=data.get('description'),
            slug=data.get('slug'),
            url=data.get('url')
        )
        
        # Parse genre
        if 'genre' in data and data['genre']:
            chart.genre = self.parse_genre(data['genre'])
        
        # Parse date
        chart.published_date = self.parse_datetime(data.get('published_date'))
        
        # Parse tracks
        if 'tracks' in data:
            chart.tracks = [self.parse_chart_track(t) for t in data['tracks']]
        elif 'results' in data:
            # Some endpoints return results instead of tracks
            chart.tracks = [self.parse_chart_track(t) for t in data['results']]
        
        return chart
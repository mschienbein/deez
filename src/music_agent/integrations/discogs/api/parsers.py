"""
Data parsing utilities for Discogs API responses.
"""

from typing import Any, Dict, List

from ..models import (
    Artist, Release, Master, Label, Track, Image
)


class DataParser:
    """Handles parsing of raw Discogs API data into model objects."""
    
    def parse_release(self, data: Any) -> Release:
        """Parse raw release data into Release model."""
        release = Release(
            id=data.id,
            title=data.title,
            resource_url=data.data.get('resource_url', ''),
            uri=data.data.get('uri'),
            status=data.data.get('status'),
            year=data.year,
            country=data.country,
            released=data.data.get('released'),
            released_formatted=data.data.get('released_formatted'),
            notes=data.data.get('notes'),
            data_quality=data.data.get('data_quality'),
            master_id=data.master and data.master.id,
            master_url=data.master and data.data.get('master_url'),
            thumb=data.data.get('thumb'),
            estimated_weight=data.data.get('estimated_weight'),
            community=data.data.get('community'),
            marketplace_stats=data.data.get('marketplace_stats')
        )
        
        # Parse formats
        if hasattr(data, 'formats'):
            release.formats = data.formats
        
        # Parse genres and styles
        if hasattr(data, 'genres'):
            release.genres = data.genres or []
        if hasattr(data, 'styles'):
            release.styles = data.styles or []
        
        # Parse artists
        if hasattr(data, 'artists'):
            release.artists = [self.parse_artist_simple(a) for a in data.artists]
        
        # Parse labels
        if hasattr(data, 'labels'):
            release.labels = [self.parse_label_simple(l) for l in data.labels]
        
        # Parse tracklist
        if hasattr(data, 'tracklist'):
            release.tracklist = [self.parse_track(t) for t in data.tracklist]
        
        # Parse images
        if hasattr(data, 'images'):
            release.images = [self.parse_image(i) for i in data.images]
        
        return release
    
    def parse_master(self, data: Any) -> Master:
        """Parse raw master data into Master model."""
        master = Master(
            id=data.id,
            title=data.title,
            resource_url=data.data.get('resource_url', ''),
            uri=data.data.get('uri'),
            versions_url=data.data.get('versions_url'),
            main_release=data.main_release,
            main_release_url=data.data.get('main_release_url'),
            year=data.year,
            data_quality=data.data.get('data_quality'),
            num_for_sale=data.data.get('num_for_sale'),
            lowest_price=data.data.get('lowest_price')
        )
        
        # Parse genres and styles
        if hasattr(data, 'genres'):
            master.genres = data.genres or []
        if hasattr(data, 'styles'):
            master.styles = data.styles or []
        
        # Parse artists
        if hasattr(data, 'artists'):
            master.artists = [self.parse_artist_simple(a) for a in data.artists]
        
        # Parse tracklist
        if hasattr(data, 'tracklist'):
            master.tracklist = [self.parse_track(t) for t in data.tracklist]
        
        # Parse images
        if hasattr(data, 'images'):
            master.images = [self.parse_image(i) for i in data.images]
        
        return master
    
    def parse_artist(self, data: Any) -> Artist:
        """Parse raw artist data into Artist model."""
        artist = Artist(
            id=data.id,
            name=data.name,
            resource_url=data.data.get('resource_url', ''),
            uri=data.data.get('uri'),
            releases_url=data.data.get('releases_url'),
            profile=data.data.get('profile'),
            data_quality=data.data.get('data_quality')
        )
        
        # Parse additional fields
        if hasattr(data, 'namevariations'):
            artist.namevariations = data.namevariations or []
        if hasattr(data, 'aliases'):
            artist.aliases = [a.data for a in data.aliases] if data.aliases else []
        if hasattr(data, 'urls'):
            artist.urls = data.urls or []
        if hasattr(data, 'images'):
            artist.images = [self.parse_image(i) for i in data.images]
        if hasattr(data, 'members'):
            artist.members = [m.data for m in data.members] if data.members else []
        if hasattr(data, 'groups'):
            artist.groups = [g.data for g in data.groups] if data.groups else []
        
        return artist
    
    def parse_label(self, data: Any) -> Label:
        """Parse raw label data into Label model."""
        label = Label(
            id=data.id,
            name=data.name,
            resource_url=data.data.get('resource_url', ''),
            uri=data.data.get('uri'),
            releases_url=data.data.get('releases_url'),
            profile=data.data.get('profile'),
            data_quality=data.data.get('data_quality'),
            contact_info=data.data.get('contact_info')
        )
        
        # Parse additional fields
        if hasattr(data, 'sublabels'):
            label.sublabels = [s.data for s in data.sublabels] if data.sublabels else []
        if hasattr(data, 'urls'):
            label.urls = data.urls or []
        if hasattr(data, 'images'):
            label.images = [self.parse_image(i) for i in data.images]
        
        return label
    
    def parse_artist_simple(self, data: Any) -> Artist:
        """Parse simple artist reference."""
        return Artist(
            id=data.id if hasattr(data, 'id') else 0,
            name=data.name if hasattr(data, 'name') else '',
            resource_url=data.data.get('resource_url', '') if hasattr(data, 'data') else '',
            anv=data.data.get('anv') if hasattr(data, 'data') else None,
            join=data.data.get('join') if hasattr(data, 'data') else None,
            role=data.data.get('role') if hasattr(data, 'data') else None,
            tracks=data.data.get('tracks') if hasattr(data, 'data') else None
        )
    
    def parse_label_simple(self, data: Any) -> Label:
        """Parse simple label reference."""
        return Label(
            id=data.id if hasattr(data, 'id') else 0,
            name=data.name if hasattr(data, 'name') else '',
            resource_url=data.data.get('resource_url', '') if hasattr(data, 'data') else '',
            catno=data.data.get('catno') if hasattr(data, 'data') else None,
            entity_type=data.data.get('entity_type') if hasattr(data, 'data') else None,
            entity_type_name=data.data.get('entity_type_name') if hasattr(data, 'data') else None
        )
    
    def parse_track(self, data: Any) -> Track:
        """Parse track data."""
        track = Track(
            position=data.get('position', '') if isinstance(data, dict) else getattr(data, 'position', ''),
            title=data.get('title', '') if isinstance(data, dict) else getattr(data, 'title', ''),
            duration=data.get('duration') if isinstance(data, dict) else getattr(data, 'duration', None),
            type_=data.get('type_') if isinstance(data, dict) else getattr(data, 'type_', None)
        )
        
        # Parse artists if present
        if isinstance(data, dict):
            if 'artists' in data:
                track.artists = [self.parse_artist_simple(a) for a in data['artists']]
            if 'extraartists' in data:
                track.extraartists = [self.parse_artist_simple(a) for a in data['extraartists']]
        else:
            if hasattr(data, 'artists'):
                track.artists = [self.parse_artist_simple(a) for a in data.artists]
            if hasattr(data, 'extraartists'):
                track.extraartists = [self.parse_artist_simple(a) for a in data.extraartists]
        
        return track
    
    def parse_image(self, data: Any) -> Image:
        """Parse image data."""
        if isinstance(data, dict):
            return Image(
                type=data.get('type', ''),
                uri=data.get('uri', ''),
                resource_url=data.get('resource_url', ''),
                uri150=data.get('uri150'),
                width=data.get('width'),
                height=data.get('height')
            )
        else:
            return Image(
                type=getattr(data, 'type', ''),
                uri=getattr(data, 'uri', ''),
                resource_url=getattr(data, 'resource_url', ''),
                uri150=getattr(data, 'uri150', None),
                width=getattr(data, 'width', None),
                height=getattr(data, 'height', None)
            )
    
    def parse_basic_release(self, data: Any) -> Dict[str, Any]:
        """Parse basic release info for lists."""
        # Handle both dict-like objects and discogs_client objects
        result = {}
        
        # Get attributes either from object properties or dict keys
        if hasattr(data, 'id'):
            result['id'] = data.id
        elif hasattr(data, 'get'):
            result['id'] = data.get('id')
            
        if hasattr(data, 'title'):
            result['title'] = data.title
        elif hasattr(data, 'get'):
            result['title'] = data.get('title')
            
        if hasattr(data, 'year'):
            result['year'] = data.year
        elif hasattr(data, 'get'):
            result['year'] = data.get('year')
            
        if hasattr(data, 'format'):
            result['format'] = data.format
        elif hasattr(data, 'get'):
            result['format'] = data.get('format')
            
        if hasattr(data, 'label'):
            result['label'] = data.label
        elif hasattr(data, 'get'):
            result['label'] = data.get('label')
            
        if hasattr(data, 'catno'):
            result['catno'] = data.catno
        elif hasattr(data, 'get'):
            result['catno'] = data.get('catno')
            
        if hasattr(data, 'data') and hasattr(data.data, 'get'):
            result['resource_url'] = data.data.get('resource_url')
        elif hasattr(data, 'get'):
            result['resource_url'] = data.get('resource_url')
            
        return result
"""
Beatport data models.
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Artist:
    """Represents a Beatport artist."""
    
    id: int
    name: str
    slug: Optional[str] = None
    url: Optional[str] = None
    image: Optional[str] = None
    biography: Optional[str] = None
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Artist":
        """Create from API response."""
        return cls(
            id=data["id"],
            name=data["name"],
            slug=data.get("slug"),
            url=data.get("url"),
            image=data.get("image", {}).get("uri") if data.get("image") else None,
            biography=data.get("biography"),
        )


@dataclass
class Label:
    """Represents a Beatport label."""
    
    id: int
    name: str
    slug: Optional[str] = None
    url: Optional[str] = None
    image: Optional[str] = None
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Label":
        """Create from API response."""
        return cls(
            id=data["id"],
            name=data["name"],
            slug=data.get("slug"),
            url=data.get("url"),
            image=data.get("image", {}).get("uri") if data.get("image") else None,
        )


@dataclass
class Genre:
    """Represents a Beatport genre."""
    
    id: int
    name: str
    slug: Optional[str] = None
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Genre":
        """Create from API response."""
        return cls(
            id=data["id"],
            name=data["name"],
            slug=data.get("slug"),
        )


@dataclass
class Track:
    """Represents a Beatport track."""
    
    id: int
    name: str
    mix_name: Optional[str] = None
    artists: List[Artist] = field(default_factory=list)
    remixers: List[Artist] = field(default_factory=list)
    label: Optional[Label] = None
    genre: Optional[Genre] = None
    sub_genre: Optional[Genre] = None
    
    # Track details
    bpm: Optional[int] = None
    key: Optional[str] = None
    length: Optional[str] = None
    length_ms: Optional[int] = None
    released: Optional[str] = None
    
    # URLs and IDs
    slug: Optional[str] = None
    url: Optional[str] = None
    preview_url: Optional[str] = None
    waveform_url: Optional[str] = None
    image: Optional[str] = None
    catalog_number: Optional[str] = None
    isrc: Optional[str] = None
    
    # Pricing
    price: Optional[float] = None
    price_currency: Optional[str] = None
    
    # Release info
    release_id: Optional[int] = None
    release_name: Optional[str] = None
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Track":
        """Create from API response."""
        # Parse artists
        artists = [Artist.from_api(a) for a in data.get("artists", [])]
        remixers = [Artist.from_api(a) for a in data.get("remixers", [])]
        
        # Parse label
        label = None
        if data.get("label"):
            label = Label.from_api(data["label"])
        
        # Parse genre
        genre = None
        if data.get("genre"):
            genre = Genre.from_api(data["genre"])
        
        sub_genre = None
        if data.get("sub_genre"):
            sub_genre = Genre.from_api(data["sub_genre"])
        
        # Get preview URL
        preview_url = None
        if data.get("sample_url"):
            preview_url = data["sample_url"]
        elif data.get("preview"):
            preview_url = data["preview"].get("url")
        
        # Get image
        image = None
        if data.get("image"):
            image = data["image"].get("uri")
        elif data.get("release", {}).get("image"):
            image = data["release"]["image"].get("uri")
        
        return cls(
            id=data["id"],
            name=data["name"],
            mix_name=data.get("mix_name"),
            artists=artists,
            remixers=remixers,
            label=label,
            genre=genre,
            sub_genre=sub_genre,
            bpm=data.get("bpm"),
            key=data.get("key"),
            length=data.get("length"),
            length_ms=data.get("length_ms"),
            released=data.get("publish_date") or data.get("release_date"),
            slug=data.get("slug"),
            url=data.get("url"),
            preview_url=preview_url,
            waveform_url=data.get("waveform_url"),
            image=image,
            catalog_number=data.get("catalog_number"),
            isrc=data.get("isrc"),
            price=data.get("price", {}).get("value") if data.get("price") else None,
            price_currency=data.get("price", {}).get("currency") if data.get("price") else None,
            release_id=data.get("release", {}).get("id") if data.get("release") else None,
            release_name=data.get("release", {}).get("name") if data.get("release") else None,
        )
    
    @property
    def full_title(self) -> str:
        """Get full track title with mix name."""
        if self.mix_name and self.mix_name != "Original Mix":
            return f"{self.name} ({self.mix_name})"
        return self.name
    
    @property
    def artist_names(self) -> str:
        """Get comma-separated artist names."""
        return ", ".join(a.name for a in self.artists)
    
    @property
    def remixer_names(self) -> str:
        """Get comma-separated remixer names."""
        return ", ".join(r.name for r in self.remixers)


@dataclass
class Release:
    """Represents a Beatport release (album/EP)."""
    
    id: int
    name: str
    artists: List[Artist] = field(default_factory=list)
    label: Optional[Label] = None
    
    # Release details
    catalog_number: Optional[str] = None
    release_date: Optional[str] = None
    track_count: Optional[int] = None
    
    # URLs and images
    slug: Optional[str] = None
    url: Optional[str] = None
    image: Optional[str] = None
    
    # Tracks
    tracks: List[Track] = field(default_factory=list)
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Release":
        """Create from API response."""
        # Parse artists
        artists = [Artist.from_api(a) for a in data.get("artists", [])]
        
        # Parse label
        label = None
        if data.get("label"):
            label = Label.from_api(data["label"])
        
        # Parse tracks if included
        tracks = []
        if data.get("tracks"):
            tracks = [Track.from_api(t) for t in data["tracks"]]
        
        # Get image
        image = None
        if data.get("image"):
            image = data["image"].get("uri")
        
        return cls(
            id=data["id"],
            name=data["name"],
            artists=artists,
            label=label,
            catalog_number=data.get("catalog_number"),
            release_date=data.get("publish_date") or data.get("release_date"),
            track_count=data.get("track_count") or len(tracks),
            slug=data.get("slug"),
            url=data.get("url"),
            image=image,
            tracks=tracks,
        )
    
    @property
    def artist_names(self) -> str:
        """Get comma-separated artist names."""
        return ", ".join(a.name for a in self.artists)


@dataclass
class Chart:
    """Represents a Beatport chart."""
    
    id: int
    name: str
    description: Optional[str] = None
    genre: Optional[Genre] = None
    tracks: List[Track] = field(default_factory=list)
    
    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "Chart":
        """Create from API response."""
        # Parse genre
        genre = None
        if data.get("genre"):
            genre = Genre.from_api(data["genre"])
        
        # Parse tracks
        tracks = []
        if data.get("tracks"):
            tracks = [Track.from_api(t) for t in data["tracks"]]
        
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description"),
            genre=genre,
            tracks=tracks,
        )
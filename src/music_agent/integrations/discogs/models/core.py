"""
Core data models for Discogs.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Image:
    """Image information."""
    type: str  # primary or secondary
    uri: str
    resource_url: str
    uri150: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass
class Artist:
    """Artist information."""
    id: int
    name: str
    resource_url: str
    uri: Optional[str] = None
    releases_url: Optional[str] = None
    anv: Optional[str] = None  # Artist name variation
    join: Optional[str] = None
    role: Optional[str] = None
    tracks: Optional[str] = None
    profile: Optional[str] = None
    data_quality: Optional[str] = None
    namevariations: List[str] = field(default_factory=list)
    aliases: List[Dict[str, Any]] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    images: List[Image] = field(default_factory=list)
    members: List[Dict[str, Any]] = field(default_factory=list)
    groups: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Label:
    """Label information."""
    id: int
    name: str
    resource_url: str
    uri: Optional[str] = None
    releases_url: Optional[str] = None
    catno: Optional[str] = None
    entity_type: Optional[str] = None
    entity_type_name: Optional[str] = None
    profile: Optional[str] = None
    data_quality: Optional[str] = None
    contact_info: Optional[str] = None
    sublabels: List[Dict[str, Any]] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    images: List[Image] = field(default_factory=list)


@dataclass
class Track:
    """Track information."""
    position: str
    title: str
    duration: Optional[str] = None
    type_: Optional[str] = None  # track or heading
    artists: List[Artist] = field(default_factory=list)
    extraartists: List[Artist] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> Optional[int]:
        """Convert duration string to seconds."""
        if not self.duration:
            return None
        try:
            parts = self.duration.split(":")
            if len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        except (ValueError, AttributeError):
            return None
        return None
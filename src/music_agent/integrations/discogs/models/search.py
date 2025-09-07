"""
Search result models for Discogs.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from .enums import SearchType


@dataclass
class SearchResult:
    """Search result container."""
    type: SearchType
    id: int
    title: str
    artist: Optional[str] = None  # Primary artist name
    thumb: Optional[str] = None
    cover_image: Optional[str] = None
    resource_url: Optional[str] = None
    uri: Optional[str] = None
    country: Optional[str] = None
    year: Optional[int] = None
    format: List[str] = field(default_factory=list)
    label: List[str] = field(default_factory=list)
    genre: List[str] = field(default_factory=list)
    style: List[str] = field(default_factory=list)
    barcode: List[str] = field(default_factory=list)
    catno: Optional[str] = None
    community: Optional[Dict[str, Any]] = None
    format_quantity: Optional[int] = None
    formats: List[Dict[str, Any]] = field(default_factory=list)
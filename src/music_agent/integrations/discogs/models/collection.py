"""
Collection models for Discogs.
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class CollectionItem:
    """Item in user's collection."""
    id: int
    instance_id: int
    folder_id: int
    rating: int
    basic_information: Dict[str, Any]
    notes: Optional[str] = None
    date_added: Optional[str] = None
    
    @property
    def release_id(self) -> int:
        """Get release ID from basic information."""
        return self.basic_information.get("id", self.id)
    
    @property
    def title(self) -> str:
        """Get release title."""
        return self.basic_information.get("title", "Unknown")
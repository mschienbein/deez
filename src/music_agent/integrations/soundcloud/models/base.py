"""
Base model class for SoundCloud resources.

Provides common functionality for all models.
"""

from typing import Dict, Any, Optional, TypeVar, Type
from datetime import datetime
from abc import ABC, abstractmethod
import json

T = TypeVar("T", bound="BaseModel")


class BaseModel(ABC):
    """Base class for all SoundCloud models."""
    
    def __init__(self, data: Dict[str, Any], client=None):
        """
        Initialize model from API response data.
        
        Args:
            data: Raw API response data
            client: Optional SoundCloud client for API calls
        """
        self._raw_data = data
        self._client = client
        self._parse_data(data)
    
    @abstractmethod
    def _parse_data(self, data: Dict[str, Any]):
        """
        Parse raw API data into model attributes.
        
        Args:
            data: Raw API response data
        """
        pass
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any], client=None) -> T:
        """
        Create model instance from dictionary.
        
        Args:
            data: Dictionary data
            client: Optional SoundCloud client
            
        Returns:
            Model instance
        """
        return cls(data, client)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dictionary representation
        """
        result = {}
        
        for key, value in self.__dict__.items():
            if key.startswith("_"):
                continue
            
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, BaseModel):
                result[key] = value.to_dict()
            elif isinstance(value, list):
                result[key] = [
                    item.to_dict() if isinstance(item, BaseModel) else item
                    for item in value
                ]
            else:
                result[key] = value
        
        return result
    
    def to_json(self, **kwargs) -> str:
        """
        Convert model to JSON string.
        
        Args:
            **kwargs: Additional arguments for json.dumps
            
        Returns:
            JSON string
        """
        return json.dumps(self.to_dict(), **kwargs)
    
    @staticmethod
    def _parse_datetime(date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse datetime string from API.
        
        Args:
            date_str: Date string in ISO format
            
        Returns:
            Parsed datetime or None
        """
        if not date_str:
            return None
        
        try:
            # SoundCloud uses ISO format with timezone
            if "+" in date_str:
                # Remove timezone for simplicity
                date_str = date_str.split("+")[0]
            
            if date_str.endswith("Z"):
                date_str = date_str[:-1]
            
            return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def _safe_get(data: Dict[str, Any], key: str, default=None):
        """
        Safely get value from dictionary.
        
        Args:
            data: Dictionary
            key: Key to get
            default: Default value if key not found
            
        Returns:
            Value or default
        """
        return data.get(key, default)
    
    def refresh(self):
        """
        Refresh model data from API.
        
        Requires client to be set.
        """
        if not self._client:
            raise RuntimeError("Client not available for refresh")
        
        # Subclasses should implement specific refresh logic
        raise NotImplementedError("Refresh not implemented for this model")
    
    def __repr__(self) -> str:
        """String representation of model."""
        class_name = self.__class__.__name__
        
        # Try to use common attributes for representation
        if hasattr(self, "title"):
            return f"<{class_name}: {self.title}>"
        elif hasattr(self, "username"):
            return f"<{class_name}: {self.username}>"
        elif hasattr(self, "id"):
            return f"<{class_name}: {self.id}>"
        else:
            return f"<{class_name}>"
    
    def __eq__(self, other) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, self.__class__):
            return False
        
        if hasattr(self, "id") and hasattr(other, "id"):
            return self.id == other.id
        
        return False
    
    def __hash__(self) -> int:
        """Hash based on ID."""
        if hasattr(self, "id"):
            return hash(self.id)
        
        return hash(id(self))


__all__ = ["BaseModel"]
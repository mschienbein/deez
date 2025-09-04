"""
Base model for Bandcamp entities.
"""

from typing import Dict, Any, Optional, List, TypeVar, Type

T = TypeVar('T', bound='BaseModel')


class BaseModel:
    """Base class for Bandcamp models."""
    
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize model with data.
        
        Args:
            data: Data dictionary
        """
        self._data = data or {}
        self._parse_data()
    
    def _parse_data(self):
        """Parse data into model attributes."""
        # Override in subclasses
        pass
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create model from dictionary.
        
        Args:
            data: Data dictionary
            
        Returns:
            Model instance
        """
        return cls(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dictionary representation
        """
        return self._data.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from data.
        
        Args:
            key: Key to get
            default: Default value
            
        Returns:
            Value or default
        """
        return self._data.get(key, default)
    
    def __repr__(self) -> str:
        """String representation."""
        class_name = self.__class__.__name__
        return f"<{class_name}({self._get_repr_fields()})>"
    
    def _get_repr_fields(self) -> str:
        """Get fields for representation."""
        return ""


__all__ = ["BaseModel"]
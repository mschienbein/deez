"""
Base model class for Mixcloud entities.

Provides common functionality for all models.
"""

from typing import Dict, Any, Optional, List, TypeVar, Type
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T', bound='BaseModel')


class BaseModel:
    """Base class for all Mixcloud models."""
    
    def __init__(self, data: Dict[str, Any]):
        """
        Initialize model with raw data.
        
        Args:
            data: Raw data from API
        """
        self._raw_data = data or {}
        self._parse_data()
    
    def _parse_data(self):
        """Parse raw data into model attributes."""
        # Override in subclasses
        pass
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create model instance from dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            Model instance
        """
        return cls(data)
    
    @classmethod
    def from_list(cls: Type[T], data_list: List[Dict[str, Any]]) -> List[T]:
        """
        Create list of model instances from list of dictionaries.
        
        Args:
            data_list: List of dictionary data
            
        Returns:
            List of model instances
        """
        return [cls(data) for data in data_list]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary.
        
        Returns:
            Dictionary representation
        """
        return self._raw_data.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from raw data.
        
        Args:
            key: Key to get
            default: Default value if key not found
            
        Returns:
            Value or default
        """
        return self._raw_data.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        """Get item from raw data."""
        return self._raw_data[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists in raw data."""
        return key in self._raw_data
    
    def __repr__(self) -> str:
        """String representation."""
        class_name = self.__class__.__name__
        return f"<{class_name}({self._get_repr_fields()})>"
    
    def _get_repr_fields(self) -> str:
        """Get fields for string representation."""
        # Override in subclasses
        return ""
    
    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        """
        Parse datetime string.
        
        Args:
            value: Datetime string
            
        Returns:
            Datetime object or None
        """
        if not value:
            return None
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            try:
                # Try common format
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except (ValueError, AttributeError):
                logger.debug(f"Could not parse datetime: {value}")
                return None
    
    def _parse_int(self, value: Any) -> Optional[int]:
        """
        Parse integer value.
        
        Args:
            value: Value to parse
            
        Returns:
            Integer or None
        """
        if value is None:
            return None
        
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_float(self, value: Any) -> Optional[float]:
        """
        Parse float value.
        
        Args:
            value: Value to parse
            
        Returns:
            Float or None
        """
        if value is None:
            return None
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def _parse_bool(self, value: Any) -> bool:
        """
        Parse boolean value.
        
        Args:
            value: Value to parse
            
        Returns:
            Boolean
        """
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            return value.lower() in ('true', 'yes', '1')
        
        return bool(value)


class PaginatedResult:
    """Represents a paginated result from the API."""
    
    def __init__(
        self,
        items: List[BaseModel],
        total: Optional[int] = None,
        next_url: Optional[str] = None,
        previous_url: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None
    ):
        """
        Initialize paginated result.
        
        Args:
            items: List of model instances
            total: Total number of items
            next_url: URL for next page
            previous_url: URL for previous page
            page: Current page number
            per_page: Items per page
        """
        self.items = items
        self.total = total
        self.next_url = next_url
        self.previous_url = previous_url
        self.page = page
        self.per_page = per_page
    
    @property
    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.next_url is not None
    
    @property
    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.previous_url is not None
    
    def __iter__(self):
        """Iterate over items."""
        return iter(self.items)
    
    def __len__(self):
        """Get number of items in current page."""
        return len(self.items)
    
    def __getitem__(self, index):
        """Get item by index."""
        return self.items[index]


__all__ = ["BaseModel", "PaginatedResult"]
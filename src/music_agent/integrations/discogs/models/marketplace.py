"""
Marketplace models for Discogs.
"""

from typing import Optional, Dict, Any, Union
from dataclasses import dataclass


@dataclass
class MarketplaceListing:
    """Marketplace listing information."""
    id: int
    resource_url: str
    uri: str
    status: str
    condition: str
    sleeve_condition: str
    price: Dict[str, Union[float, str]]  # value and currency
    shipping_price: Optional[Dict[str, Union[float, str]]] = None
    posted: Optional[str] = None
    ships_from: Optional[str] = None
    comments: Optional[str] = None
    seller: Optional[Dict[str, Any]] = None
    release: Optional[Dict[str, Any]] = None
    audio: Optional[bool] = None
    allow_offers: Optional[bool] = None
    
    @property
    def total_price(self) -> float:
        """Calculate total price including shipping."""
        base = self.price.get("value", 0) if isinstance(self.price, dict) else 0
        shipping = 0
        if self.shipping_price and isinstance(self.shipping_price, dict):
            shipping = self.shipping_price.get("value", 0)
        return base + shipping
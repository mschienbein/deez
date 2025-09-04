"""
Scraping modules for Bandcamp.
"""

from .base import BaseScraper
from .album import AlbumScraper
from .search import SearchScraper

__all__ = [
    "BaseScraper",
    "AlbumScraper", 
    "SearchScraper",
]
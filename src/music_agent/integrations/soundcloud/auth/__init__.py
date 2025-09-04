"""
Authentication module for SoundCloud integration.

Handles multiple authentication strategies including OAuth2,
client ID scraping, and token management.
"""

from .manager import AuthManager
from .oauth import OAuth2Handler
from .scraper import ClientIDScraper
from .token_store import TokenStore

__all__ = [
    "AuthManager",
    "OAuth2Handler",
    "ClientIDScraper",
    "TokenStore",
]
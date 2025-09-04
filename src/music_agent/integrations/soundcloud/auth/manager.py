"""
Authentication manager for SoundCloud.

Coordinates between different authentication strategies and
manages credentials lifecycle.
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ..config import APIConfig
from ..types import AuthCredentials, TokenResponse
from ..exceptions import (
    AuthenticationError,
    ClientIDError,
    TokenExpiredError,
)
from .oauth import OAuth2Handler
from .scraper import ClientIDScraper
from .token_store import TokenStore

logger = logging.getLogger(__name__)


class AuthManager:
    """
    Manages authentication for SoundCloud API access.
    
    Supports multiple authentication methods:
    - OAuth2 with client credentials
    - OAuth2 with user credentials
    - Public access with scraped client IDs
    """
    
    def __init__(self, config: Optional[APIConfig] = None):
        """
        Initialize authentication manager.
        
        Args:
            config: API configuration with credentials
        """
        self.config = config or APIConfig()
        self.oauth = OAuth2Handler(config)
        self.scraper = ClientIDScraper()
        self.token_store = TokenStore()
        
        # Current authentication state
        self._access_token: Optional[str] = None
        self._client_id: Optional[str] = None
        self._token_expires: Optional[datetime] = None
        
        # Client ID pool for rotation
        self._client_id_pool: list[str] = []
        self._current_client_index: int = 0
        
        # Initialize from config
        self._init_from_config()
    
    def _init_from_config(self):
        """Initialize authentication from configuration."""
        if self.config.access_token:
            self._access_token = self.config.access_token
            logger.info("Using access token from configuration")
        
        if self.config.client_id:
            self._client_id = self.config.client_id
            logger.info("Using client ID from configuration")
    
    @property
    def is_authenticated(self) -> bool:
        """Check if we have valid authentication."""
        return bool(self._access_token or self._client_id)
    
    @property
    def needs_refresh(self) -> bool:
        """Check if token needs refreshing."""
        if not self._token_expires:
            return False
        
        # Refresh 5 minutes before expiry
        buffer = timedelta(minutes=5)
        return datetime.now() >= (self._token_expires - buffer)
    
    async def authenticate(self, credentials: Optional[AuthCredentials] = None) -> bool:
        """
        Authenticate with SoundCloud.
        
        Tries multiple strategies:
        1. Use provided credentials
        2. Use stored tokens
        3. OAuth2 flow if credentials available
        4. Fall back to client ID scraping
        
        Args:
            credentials: Optional authentication credentials
            
        Returns:
            True if authentication successful
            
        Raises:
            AuthenticationError: If all authentication methods fail
        """
        # Try provided credentials first
        if credentials:
            if credentials.get("access_token"):
                self._access_token = credentials["access_token"]
                return True
            
            if credentials.get("client_id"):
                self._client_id = credentials["client_id"]
                return True
        
        # Try stored tokens
        stored_token = await self.token_store.get_token()
        if stored_token:
            self._access_token = stored_token["access_token"]
            self._token_expires = datetime.fromisoformat(stored_token["expires_at"])
            
            if self.needs_refresh and stored_token.get("refresh_token"):
                await self.refresh_token(stored_token["refresh_token"])
            
            return True
        
        # Try OAuth2 flow
        if self.config.client_secret:
            try:
                token = await self.oauth.authenticate(credentials)
                await self._handle_token_response(token)
                return True
            except AuthenticationError as e:
                logger.warning(f"OAuth2 authentication failed: {e}")
        
        # Fall back to client ID scraping
        try:
            await self._scrape_client_ids()
            return bool(self._client_id)
        except Exception as e:
            logger.error(f"Client ID scraping failed: {e}")
            raise AuthenticationError("All authentication methods failed")
    
    async def refresh_token(self, refresh_token: Optional[str] = None) -> TokenResponse:
        """
        Refresh the access token.
        
        Args:
            refresh_token: Refresh token to use
            
        Returns:
            New token response
            
        Raises:
            TokenExpiredError: If refresh fails
        """
        if not refresh_token:
            stored = await self.token_store.get_token()
            if stored and stored.get("refresh_token"):
                refresh_token = stored["refresh_token"]
            else:
                raise TokenExpiredError("No refresh token available")
        
        try:
            token = await self.oauth.refresh_token(refresh_token)
            await self._handle_token_response(token)
            return token
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise TokenExpiredError(f"Failed to refresh token: {e}")
    
    async def _handle_token_response(self, token: TokenResponse):
        """Handle and store token response."""
        self._access_token = token["access_token"]
        
        # Calculate expiry time
        expires_in = token.get("expires_in", 3600)
        self._token_expires = datetime.now() + timedelta(seconds=expires_in)
        
        # Store token
        await self.token_store.store_token(
            access_token=token["access_token"],
            refresh_token=token.get("refresh_token"),
            expires_at=self._token_expires.isoformat(),
            scope=token.get("scope", ""),
        )
    
    async def _scrape_client_ids(self):
        """Scrape and validate client IDs."""
        logger.info("Scraping client IDs from public pages")
        
        # Scrape multiple IDs for pool
        ids = await self.scraper.scrape_multiple(count=5)
        
        # Validate each ID
        valid_ids = []
        for client_id in ids:
            if await self.scraper.validate_client_id(client_id):
                valid_ids.append(client_id)
        
        if not valid_ids:
            raise ClientIDError("No valid client IDs found")
        
        self._client_id_pool = valid_ids
        self._client_id = valid_ids[0]
        self._current_client_index = 0
        
        logger.info(f"Found {len(valid_ids)} valid client IDs")
    
    def rotate_client_id(self) -> bool:
        """
        Rotate to next client ID in pool.
        
        Returns:
            True if rotation successful, False if no more IDs
        """
        if not self._client_id_pool:
            return False
        
        self._current_client_index = (self._current_client_index + 1) % len(self._client_id_pool)
        self._client_id = self._client_id_pool[self._current_client_index]
        
        logger.info(f"Rotated to client ID {self._current_client_index + 1}/{len(self._client_id_pool)}")
        return True
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Dictionary of headers
            
        Raises:
            AuthenticationError: If not authenticated
        """
        if self._access_token:
            return {"Authorization": f"OAuth {self._access_token}"}
        
        if self._client_id:
            return {}  # Client ID goes in query params, not headers
        
        raise AuthenticationError("Not authenticated")
    
    def get_auth_params(self) -> Dict[str, str]:
        """
        Get authentication parameters for API requests.
        
        Returns:
            Dictionary of query parameters
        """
        params = {}
        
        if self._access_token:
            params["oauth_token"] = self._access_token
        elif self._client_id:
            params["client_id"] = self._client_id
        
        return params
    
    async def revoke_token(self):
        """Revoke the current access token."""
        if self._access_token:
            try:
                await self.oauth.revoke_token(self._access_token)
                await self.token_store.delete_token()
                self._access_token = None
                self._token_expires = None
                logger.info("Token revoked successfully")
            except Exception as e:
                logger.error(f"Failed to revoke token: {e}")
    
    def clear_credentials(self):
        """Clear all stored credentials."""
        self._access_token = None
        self._client_id = None
        self._token_expires = None
        self._client_id_pool.clear()
        self._current_client_index = 0


__all__ = ["AuthManager"]
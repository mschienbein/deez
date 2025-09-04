"""
Authentication manager for Mixcloud.

Coordinates authentication strategies and token management.
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from ..config import AuthConfig
from ..types import TokenResponse, AuthCredentials
from ..exceptions import (
    AuthenticationError,
    TokenExpiredError,
    InvalidCredentialsError,
)
from .oauth import OAuth2Handler
from .token_store import TokenStore

logger = logging.getLogger(__name__)


class AuthenticationManager:
    """Manages authentication for Mixcloud API."""
    
    def __init__(self, config: AuthConfig):
        """
        Initialize authentication manager.
        
        Args:
            config: Authentication configuration
        """
        self.config = config
        self.oauth_handler = OAuth2Handler(config)
        self.token_store = TokenStore(config.token_file)
        self._access_token = None
        self._refresh_token = None
        self._token_expires_at = None
        self._lock = asyncio.Lock()
        
    async def initialize(self):
        """Initialize authentication, loading stored tokens if available."""
        # Try to load stored tokens
        stored_token = await self.token_store.load()
        
        if stored_token:
            self._access_token = stored_token.get("access_token")
            self._refresh_token = stored_token.get("refresh_token")
            
            # Calculate expiration time if provided
            if "expires_at" in stored_token:
                self._token_expires_at = datetime.fromisoformat(stored_token["expires_at"])
            elif "expires_in" in stored_token:
                self._token_expires_at = datetime.now() + timedelta(seconds=stored_token["expires_in"])
            
            logger.info("Loaded stored authentication tokens")
        
        # Use config tokens if no stored tokens
        elif self.config.access_token:
            self._access_token = self.config.access_token
            self._refresh_token = self.config.refresh_token
            logger.info("Using tokens from configuration")
    
    async def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get valid access token, refreshing if necessary.
        
        Args:
            force_refresh: Force token refresh even if not expired
            
        Returns:
            Valid access token
        """
        async with self._lock:
            # Check if we need to refresh
            if force_refresh or self._is_token_expired():
                await self._refresh_token_internal()
            
            # If still no token, need to authenticate
            if not self._access_token:
                await self.authenticate_interactive()
            
            if not self._access_token:
                raise AuthenticationError("Failed to obtain access token")
            
            return self._access_token
    
    async def authenticate_interactive(self) -> str:
        """
        Perform interactive authentication.
        
        Returns:
            Access token
        """
        logger.info("Starting interactive authentication flow...")
        
        try:
            # Get authorization URL
            auth_url = await self.oauth_handler.get_authorization_url()
            
            # Start callback server and handle auth
            token_response = await self._handle_interactive_auth(auth_url)
            
            # Store tokens
            await self._store_tokens(token_response)
            
            return self._access_token
            
        except Exception as e:
            logger.error(f"Interactive authentication failed: {e}")
            raise AuthenticationError(f"Authentication failed: {e}")
    
    async def authenticate_with_code(self, authorization_code: str) -> str:
        """
        Authenticate with authorization code.
        
        Args:
            authorization_code: OAuth2 authorization code
            
        Returns:
            Access token
        """
        try:
            # Exchange code for token
            token_response = await self.oauth_handler.exchange_code_for_token(
                authorization_code
            )
            
            # Store tokens
            await self._store_tokens(token_response)
            
            return self._access_token
            
        except Exception as e:
            logger.error(f"Code exchange failed: {e}")
            raise AuthenticationError(f"Failed to exchange code: {e}")
    
    async def refresh_token(self) -> str:
        """
        Refresh the access token.
        
        Returns:
            New access token
        """
        async with self._lock:
            await self._refresh_token_internal()
            return self._access_token
    
    async def revoke_token(self):
        """Revoke current tokens and clear storage."""
        async with self._lock:
            # Clear tokens
            self._access_token = None
            self._refresh_token = None
            self._token_expires_at = None
            
            # Clear stored tokens
            await self.token_store.clear()
            
            logger.info("Tokens revoked and cleared")
    
    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated.
        
        Returns:
            True if authenticated
        """
        return self._access_token is not None
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Headers dictionary with Authorization header
        """
        if not self._access_token:
            return {}
        
        return {
            "Authorization": f"Bearer {self._access_token}"
        }
    
    async def _handle_interactive_auth(self, auth_url: str) -> TokenResponse:
        """
        Handle interactive authentication flow.
        
        Args:
            auth_url: Authorization URL
            
        Returns:
            Token response
        """
        import webbrowser
        from .oauth import CallbackServer
        
        # Start callback server
        callback_server = CallbackServer(self.oauth_handler)
        server_task = asyncio.create_task(callback_server.start())
        
        try:
            # Open browser
            logger.info(f"Opening browser for authorization...")
            print(f"\nPlease authorize the application in your browser.")
            print(f"If the browser doesn't open, visit: {auth_url}\n")
            
            webbrowser.open(auth_url)
            
            # Wait for callback
            await asyncio.wait_for(
                self.oauth_handler.callback_received.wait(),
                timeout=300  # 5 minutes timeout
            )
            
            if not self.oauth_handler.authorization_code:
                raise AuthenticationError("No authorization code received")
            
            # Exchange code for token
            token_response = await self.oauth_handler.exchange_code_for_token(
                self.oauth_handler.authorization_code
            )
            
            return token_response
            
        except asyncio.TimeoutError:
            raise AuthenticationError("Authentication timeout - no response received")
        finally:
            # Stop callback server
            await callback_server.stop()
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
    
    async def _refresh_token_internal(self):
        """Internal method to refresh token."""
        if not self._refresh_token:
            logger.warning("No refresh token available, need to re-authenticate")
            await self.authenticate_interactive()
            return
        
        try:
            # Refresh token
            token_response = await self.oauth_handler.refresh_access_token(
                self._refresh_token
            )
            
            # Store new tokens
            await self._store_tokens(token_response)
            
            logger.info("Successfully refreshed access token")
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            # If refresh fails, try interactive auth
            await self.authenticate_interactive()
    
    async def _store_tokens(self, token_response: TokenResponse):
        """Store tokens from response."""
        self._access_token = token_response["access_token"]
        self._refresh_token = token_response.get("refresh_token", self._refresh_token)
        
        # Calculate expiration
        if token_response.get("expires_in"):
            self._token_expires_at = datetime.now() + timedelta(
                seconds=token_response["expires_in"]
            )
        
        # Store to disk
        token_data = {
            "access_token": self._access_token,
            "refresh_token": self._refresh_token,
            "token_type": token_response.get("token_type", "Bearer"),
        }
        
        if self._token_expires_at:
            token_data["expires_at"] = self._token_expires_at.isoformat()
        
        await self.token_store.save(token_data)
        
        logger.debug("Tokens stored successfully")
    
    def _is_token_expired(self) -> bool:
        """Check if token is expired."""
        if not self._token_expires_at:
            return False
        
        # Refresh 5 minutes before expiry
        buffer = timedelta(minutes=5)
        return datetime.now() >= (self._token_expires_at - buffer)


__all__ = ["AuthenticationManager"]
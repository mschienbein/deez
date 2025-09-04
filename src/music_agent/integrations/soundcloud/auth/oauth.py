"""
OAuth2 handler for SoundCloud authentication.

Implements various OAuth2 flows for different authentication scenarios.
"""

import logging
from typing import Optional, Dict, Any
from urllib.parse import urlencode
import aiohttp

from ..config import APIConfig
from ..types import AuthCredentials, TokenResponse
from ..exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
)

logger = logging.getLogger(__name__)


class OAuth2Handler:
    """Handles OAuth2 authentication flows for SoundCloud."""
    
    TOKEN_URL = "https://api.soundcloud.com/oauth2/token"
    AUTHORIZE_URL = "https://soundcloud.com/connect"
    
    def __init__(self, config: Optional[APIConfig] = None):
        """
        Initialize OAuth2 handler.
        
        Args:
            config: API configuration
        """
        self.config = config or APIConfig()
    
    async def authenticate(self, credentials: Optional[AuthCredentials] = None) -> TokenResponse:
        """
        Authenticate using appropriate OAuth2 flow.
        
        Args:
            credentials: Authentication credentials
            
        Returns:
            Token response
            
        Raises:
            AuthenticationError: If authentication fails
        """
        creds = credentials or {}
        
        # Merge with config
        creds.setdefault("client_id", self.config.client_id)
        creds.setdefault("client_secret", self.config.client_secret)
        
        # Determine flow based on available credentials
        if creds.get("code"):
            return await self.authorization_code_flow(creds)
        elif creds.get("username") and creds.get("password"):
            return await self.user_credentials_flow(creds)
        elif creds.get("refresh_token"):
            return await self.refresh_token(creds["refresh_token"])
        elif creds.get("client_id") and creds.get("client_secret"):
            return await self.client_credentials_flow(creds)
        else:
            raise InvalidCredentialsError(
                "Insufficient credentials for OAuth2 authentication"
            )
    
    async def authorization_code_flow(self, credentials: AuthCredentials) -> TokenResponse:
        """
        Exchange authorization code for access token.
        
        Args:
            credentials: Must contain code, client_id, client_secret, redirect_uri
            
        Returns:
            Token response
        """
        if not all(k in credentials for k in ["code", "client_id", "client_secret", "redirect_uri"]):
            raise InvalidCredentialsError(
                "Authorization code flow requires: code, client_id, client_secret, redirect_uri"
            )
        
        data = {
            "grant_type": "authorization_code",
            "client_id": credentials["client_id"],
            "client_secret": credentials["client_secret"],
            "redirect_uri": credentials["redirect_uri"],
            "code": credentials["code"],
        }
        
        return await self._request_token(data)
    
    async def user_credentials_flow(self, credentials: AuthCredentials) -> TokenResponse:
        """
        Authenticate with username and password.
        
        Args:
            credentials: Must contain username, password, client_id, client_secret
            
        Returns:
            Token response
        """
        if not all(k in credentials for k in ["username", "password", "client_id", "client_secret"]):
            raise InvalidCredentialsError(
                "User credentials flow requires: username, password, client_id, client_secret"
            )
        
        data = {
            "grant_type": "password",
            "client_id": credentials["client_id"],
            "client_secret": credentials["client_secret"],
            "username": credentials["username"],
            "password": credentials["password"],
            "scope": credentials.get("scope", "non-expiring"),
        }
        
        return await self._request_token(data)
    
    async def client_credentials_flow(self, credentials: AuthCredentials) -> TokenResponse:
        """
        Authenticate with client credentials only.
        
        Args:
            credentials: Must contain client_id, client_secret
            
        Returns:
            Token response
        """
        if not all(k in credentials for k in ["client_id", "client_secret"]):
            raise InvalidCredentialsError(
                "Client credentials flow requires: client_id, client_secret"
            )
        
        data = {
            "grant_type": "client_credentials",
            "client_id": credentials["client_id"],
            "client_secret": credentials["client_secret"],
            "scope": credentials.get("scope", ""),
        }
        
        return await self._request_token(data)
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh an access token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New token response
        """
        if not self.config.client_id or not self.config.client_secret:
            raise InvalidCredentialsError(
                "Token refresh requires client_id and client_secret"
            )
        
        data = {
            "grant_type": "refresh_token",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": refresh_token,
        }
        
        return await self._request_token(data)
    
    def get_authorization_url(
        self,
        redirect_uri: str,
        scope: str = "non-expiring",
        state: Optional[str] = None,
    ) -> str:
        """
        Generate authorization URL for OAuth2 code flow.
        
        Args:
            redirect_uri: Callback URL
            scope: Permission scope
            state: Optional state parameter
            
        Returns:
            Authorization URL
        """
        if not self.config.client_id:
            raise InvalidCredentialsError("Client ID required for authorization URL")
        
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
        }
        
        if state:
            params["state"] = state
        
        return f"{self.AUTHORIZE_URL}?{urlencode(params)}"
    
    async def _request_token(self, data: Dict[str, Any]) -> TokenResponse:
        """
        Make token request to SoundCloud.
        
        Args:
            data: Request payload
            
        Returns:
            Token response
            
        Raises:
            AuthenticationError: If request fails
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.TOKEN_URL,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                    ssl=self.config.verify_ssl,
                ) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        return TokenResponse(
                            access_token=token_data["access_token"],
                            expires_in=token_data.get("expires_in", 3600),
                            scope=token_data.get("scope", ""),
                            refresh_token=token_data.get("refresh_token"),
                            token_type=token_data.get("token_type", "Bearer"),
                        )
                    else:
                        error_text = await response.text()
                        raise AuthenticationError(
                            f"Token request failed: {response.status} - {error_text}"
                        )
            except aiohttp.ClientError as e:
                raise AuthenticationError(f"Network error during authentication: {e}")
    
    async def revoke_token(self, access_token: str):
        """
        Revoke an access token.
        
        Note: SoundCloud may not support token revocation.
        This is a best-effort attempt.
        
        Args:
            access_token: Token to revoke
        """
        # SoundCloud doesn't have a standard revoke endpoint
        # This is a placeholder for future implementation
        logger.warning("Token revocation not implemented for SoundCloud")


__all__ = ["OAuth2Handler"]
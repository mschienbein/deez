"""
Beatport authentication handler.
"""

import re
import time
import json
import asyncio
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlencode, parse_qs, urlparse

import aiohttp
from bs4 import BeautifulSoup

from .config import BeatportConfig
from .exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    TokenExpiredError,
)

logger = logging.getLogger(__name__)


class BeatportAuth:
    """Handles Beatport API authentication."""
    
    def __init__(self, config: BeatportConfig, session: aiohttp.ClientSession):
        """
        Initialize authentication handler.
        
        Args:
            config: Beatport configuration
            session: aiohttp session
        """
        self.config = config
        self.session = session
        self._client_id = config.client_id
    
    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with Beatport API.
        
        Returns:
            Token data dictionary
        """
        # Try to load existing token
        token_data = self.config.load_token()
        if token_data and self._is_token_valid(token_data):
            logger.debug("Using existing valid token")
            return token_data
        
        # Get client_id if not provided
        if not self._client_id:
            self._client_id = await self._scrape_client_id()
            self.config.client_id = self._client_id
        
        # Authenticate with username/password
        if self.config.username and self.config.password:
            logger.info("Authenticating with username/password")
            token_data = await self._authenticate_with_credentials()
        else:
            raise AuthenticationError(
                "No valid authentication method available. "
                "Please provide username/password or a valid token."
            )
        
        # Save token
        self.config.save_token(token_data)
        return token_data
    
    async def _scrape_client_id(self) -> str:
        """
        Scrape client_id from Beatport API docs.
        
        Returns:
            Client ID string
        """
        logger.debug("Scraping client_id from API docs")
        
        try:
            async with self.session.get(self.config.docs_url) as response:
                html = await response.text()
            
            # Look for client_id in the HTML/JavaScript
            # The client_id is typically in the Swagger UI initialization
            patterns = [
                r'clientId["\s:]+["\']([\w-]+)["\']',
                r'client_id["\s:]+["\']([\w-]+)["\']',
                r'appName["\s:]+["\']([\w-]+)["\']',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    client_id = match.group(1)
                    logger.debug(f"Found client_id: {client_id}")
                    return client_id
            
            # Fallback: Look for it in inline scripts
            soup = BeautifulSoup(html, 'html.parser')
            scripts = soup.find_all('script')
            
            for script in scripts:
                if script.string:
                    for pattern in patterns:
                        match = re.search(pattern, script.string, re.IGNORECASE)
                        if match:
                            client_id = match.group(1)
                            logger.debug(f"Found client_id in script: {client_id}")
                            return client_id
            
            # Use known default if scraping fails
            # This is the client_id used by Beatport's own Swagger UI
            default_client_id = "2AwNUbQL0Y8xqaK5W8FzVYnZUXmC5PcvhDnU"
            logger.warning(f"Could not scrape client_id, using default: {default_client_id}")
            return default_client_id
            
        except Exception as e:
            logger.error(f"Error scraping client_id: {e}")
            # Return known default
            return "2AwNUbQL0Y8xqaK5W8FzVYnZUXmC5PcvhDnU"
    
    async def _authenticate_with_credentials(self) -> Dict[str, Any]:
        """
        Authenticate using username and password.
        
        Returns:
            Token data dictionary
        """
        if not self._client_id:
            raise AuthenticationError("Client ID is required for authentication")
        
        # Step 1: Get authorization code
        auth_code = await self._get_authorization_code()
        
        # Step 2: Exchange code for token
        token_data = await self._exchange_code_for_token(auth_code)
        
        return token_data
    
    async def _get_authorization_code(self) -> str:
        """
        Get authorization code using username/password.
        
        Returns:
            Authorization code
        """
        # Build authorization URL
        auth_params = {
            "client_id": self._client_id,
            "response_type": "code",
            "redirect_uri": "https://api.beatport.com/v4/auth/o/callback/",
            "scope": "account-read catalog-read",
        }
        
        auth_url = f"{self.config.auth_url}/o/authorize/?{urlencode(auth_params)}"
        
        # Step 1: Get login page
        async with self.session.get(auth_url) as response:
            if response.status != 200:
                raise AuthenticationError(f"Failed to get login page: {response.status}")
            
            html = await response.text()
            
            # Extract CSRF token
            csrf_token = await self._extract_csrf_token(html)
            
            # Get cookies
            cookies = response.cookies
        
        # Step 2: Submit login form
        login_url = f"{self.config.auth_url}/login/"
        login_data = {
            "username": self.config.username,
            "password": self.config.password,
            "csrfmiddlewaretoken": csrf_token,
            "next": f"/v4/auth/o/authorize/?{urlencode(auth_params)}",
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": auth_url,
        }
        
        async with self.session.post(
            login_url,
            data=login_data,
            headers=headers,
            cookies=cookies,
            allow_redirects=False
        ) as response:
            if response.status not in [302, 303]:
                raise InvalidCredentialsError("Invalid username or password")
            
            # Follow redirect to get authorization code
            redirect_url = response.headers.get("Location")
            
            if not redirect_url:
                raise AuthenticationError("No redirect URL after login")
        
        # Step 3: Follow redirects to get code
        async with self.session.get(
            redirect_url,
            cookies=cookies,
            allow_redirects=False
        ) as response:
            final_url = response.headers.get("Location", redirect_url)
        
        # Extract code from callback URL
        parsed = urlparse(final_url)
        params = parse_qs(parsed.query)
        
        if "code" not in params:
            raise AuthenticationError("No authorization code in callback")
        
        return params["code"][0]
    
    async def _exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code
            
        Returns:
            Token data dictionary
        """
        token_url = f"{self.config.auth_url}/o/token/"
        
        token_data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self._client_id,
            "redirect_uri": "https://api.beatport.com/v4/auth/o/callback/",
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        async with self.session.post(
            token_url,
            data=token_data,
            headers=headers
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise AuthenticationError(f"Failed to get token: {error_text}")
            
            token_response = await response.json()
        
        # Add expiration timestamp
        if "expires_in" in token_response:
            token_response["expires_at"] = int(time.time()) + token_response["expires_in"]
        
        return token_response
    
    async def refresh_token(self) -> Dict[str, Any]:
        """
        Refresh the access token.
        
        Returns:
            New token data dictionary
        """
        if not self.config.refresh_token:
            raise AuthenticationError("No refresh token available")
        
        token_url = f"{self.config.auth_url}/o/token/"
        
        token_data = {
            "grant_type": "refresh_token",
            "refresh_token": self.config.refresh_token,
            "client_id": self._client_id,
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
        }
        
        async with self.session.post(
            token_url,
            data=token_data,
            headers=headers
        ) as response:
            if response.status != 200:
                # If refresh fails, need to re-authenticate
                logger.warning("Token refresh failed, re-authenticating")
                return await self._authenticate_with_credentials()
            
            token_response = await response.json()
        
        # Add expiration timestamp
        if "expires_in" in token_response:
            token_response["expires_at"] = int(time.time()) + token_response["expires_in"]
        
        # Save new token
        self.config.save_token(token_response)
        
        return token_response
    
    async def _extract_csrf_token(self, html: str) -> str:
        """
        Extract CSRF token from HTML.
        
        Args:
            html: HTML content
            
        Returns:
            CSRF token
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Look for CSRF token in forms
        csrf_input = soup.find('input', {'name': 'csrfmiddlewaretoken'})
        if csrf_input:
            return csrf_input.get('value', '')
        
        # Look in meta tags
        csrf_meta = soup.find('meta', {'name': 'csrf-token'})
        if csrf_meta:
            return csrf_meta.get('content', '')
        
        # Look in cookies or JavaScript
        csrf_pattern = r'csrfmiddlewaretoken["\s:]+["\']([\w]+)["\']'
        match = re.search(csrf_pattern, html)
        if match:
            return match.group(1)
        
        logger.warning("Could not find CSRF token")
        return ""
    
    def _is_token_valid(self, token_data: Dict[str, Any]) -> bool:
        """
        Check if token is still valid.
        
        Args:
            token_data: Token data dictionary
            
        Returns:
            True if valid
        """
        if not token_data or "access_token" not in token_data:
            return False
        
        # Check expiration
        expires_at = token_data.get("expires_at")
        if expires_at:
            # Add buffer of 60 seconds
            return time.time() < (expires_at - 60)
        
        # If no expiration, assume valid
        return True
    
    async def ensure_authenticated(self) -> str:
        """
        Ensure we have a valid access token.
        
        Returns:
            Access token
        """
        # Check if current token is valid
        if self.config.access_token and self.config.token_expires_at:
            if time.time() < (self.config.token_expires_at - 60):
                return self.config.access_token
        
        # Try to refresh if we have refresh token
        if self.config.refresh_token and self.config.auto_refresh_token:
            try:
                token_data = await self.refresh_token()
                return token_data["access_token"]
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
        
        # Re-authenticate
        token_data = await self.authenticate()
        return token_data["access_token"]
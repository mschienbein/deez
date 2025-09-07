"""
Beatport OAuth authentication handler.
"""

import time
import json
import re
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

from .config import BeatportConfig
from .exceptions import (
    AuthenticationError, TokenExpiredError,
    InvalidCredentialsError, NetworkError
)


class BeatportAuth:
    """Handle Beatport OAuth authentication."""
    
    def __init__(self, config: BeatportConfig):
        """
        Initialize authentication handler.
        
        Args:
            config: Beatport configuration
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self._access_token = config.access_token
        self._refresh_token = config.refresh_token
        self._token_expires = None
        self._client_id = config.client_id
        
        # Try to load saved token
        if not self._access_token and config.token_file:
            self._load_saved_token()
    
    def _load_saved_token(self) -> None:
        """Load token from saved file."""
        token_data = self.config.load_token()
        if token_data:
            self._access_token = token_data.get('access_token')
            self._refresh_token = token_data.get('refresh_token')
            expires_at = token_data.get('expires_at')
            if expires_at:
                self._token_expires = datetime.fromisoformat(expires_at)
    
    def _save_token(self) -> None:
        """Save current token to file."""
        if self.config.token_file:
            token_data = {
                'access_token': self._access_token,
                'refresh_token': self._refresh_token,
                'expires_at': self._token_expires.isoformat() if self._token_expires else None,
                'client_id': self._client_id
            }
            self.config.save_token(token_data)
    
    def _scrape_client_id(self) -> str:
        """
        Scrape client ID from Beatport API docs.
        
        Returns:
            Client ID
            
        Raises:
            AuthenticationError: If client ID cannot be found
        """
        try:
            response = self.session.get(self.config.docs_url)
            response.raise_for_status()
            
            # Look for client_id in the page
            match = re.search(r'client_id["\']?\s*[:=]\s*["\']([^"\']+)["\']', response.text)
            if match:
                return match.group(1)
            
            # Try parsing as HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look in script tags
            for script in soup.find_all('script'):
                if script.string:
                    match = re.search(r'client_id["\']?\s*[:=]\s*["\']([^"\']+)["\']', script.string)
                    if match:
                        return match.group(1)
            
            raise AuthenticationError("Could not find client_id in API docs")
            
        except requests.RequestException as e:
            raise NetworkError(f"Failed to fetch API docs: {e}")
    
    def _get_client_id(self) -> str:
        """
        Get client ID, scraping if necessary.
        
        Returns:
            Client ID
        """
        if not self._client_id:
            self._client_id = self._scrape_client_id()
        return self._client_id
    
    def authenticate(self) -> str:
        """
        Authenticate and get access token.
        
        Returns:
            Access token
            
        Raises:
            AuthenticationError: If authentication fails
        """
        # If we have a valid token, return it
        if self._access_token and not self.is_token_expired():
            return self._access_token
        
        # Try to refresh if we have a refresh token
        if self._refresh_token:
            try:
                return self.refresh_token()
            except TokenExpiredError:
                pass  # Fall through to login
        
        # Need to login with credentials
        if not self.config.username or not self.config.password:
            raise InvalidCredentialsError(
                "Username and password required for authentication"
            )
        
        return self.login(self.config.username, self.config.password)
    
    def login(self, username: str, password: str) -> str:
        """
        Login with username and password.
        
        Args:
            username: Beatport username
            password: Beatport password
            
        Returns:
            Access token
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
            AuthenticationError: If login fails
        """
        client_id = self._get_client_id()
        
        # OAuth password grant
        token_url = f"{self.config.base_url}/auth/o/token/"
        
        data = {
            'grant_type': 'password',
            'username': username,
            'password': password,
            'client_id': client_id,
            'scope': 'account'
        }
        
        try:
            response = self.session.post(token_url, data=data)
            
            if response.status_code == 401:
                raise InvalidCredentialsError("Invalid username or password")
            
            response.raise_for_status()
            token_data = response.json()
            
            self._access_token = token_data['access_token']
            self._refresh_token = token_data.get('refresh_token')
            
            # Calculate expiry
            expires_in = token_data.get('expires_in', 3600)
            self._token_expires = datetime.now() + timedelta(seconds=expires_in)
            
            # Save token
            self._save_token()
            
            return self._access_token
            
        except requests.RequestException as e:
            raise AuthenticationError(f"Login failed: {e}")
    
    def refresh_token(self) -> str:
        """
        Refresh the access token using refresh token.
        
        Returns:
            New access token
            
        Raises:
            TokenExpiredError: If refresh token is invalid
            AuthenticationError: If refresh fails
        """
        if not self._refresh_token:
            raise TokenExpiredError("No refresh token available")
        
        client_id = self._get_client_id()
        token_url = f"{self.config.base_url}/auth/o/token/"
        
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self._refresh_token,
            'client_id': client_id
        }
        
        try:
            response = self.session.post(token_url, data=data)
            
            if response.status_code == 401:
                raise TokenExpiredError("Refresh token expired or invalid")
            
            response.raise_for_status()
            token_data = response.json()
            
            self._access_token = token_data['access_token']
            if 'refresh_token' in token_data:
                self._refresh_token = token_data['refresh_token']
            
            # Calculate expiry
            expires_in = token_data.get('expires_in', 3600)
            self._token_expires = datetime.now() + timedelta(seconds=expires_in)
            
            # Save token
            self._save_token()
            
            return self._access_token
            
        except requests.RequestException as e:
            raise AuthenticationError(f"Token refresh failed: {e}")
    
    def is_token_expired(self) -> bool:
        """
        Check if the current token is expired.
        
        Returns:
            True if token is expired or will expire soon
        """
        if not self._token_expires:
            return False  # Assume not expired if we don't know
        
        # Consider expired if less than 5 minutes remaining
        buffer = timedelta(minutes=5)
        return datetime.now() >= (self._token_expires - buffer)
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            Headers dict with authorization
            
        Raises:
            AuthenticationError: If authentication fails
        """
        token = self.authenticate()
        return {
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    
    def revoke_token(self) -> None:
        """Revoke the current access token."""
        if not self._access_token:
            return
        
        revoke_url = f"{self.config.base_url}/auth/o/revoke_token/"
        
        data = {
            'token': self._access_token,
            'client_id': self._get_client_id()
        }
        
        try:
            response = self.session.post(revoke_url, data=data)
            response.raise_for_status()
            
            self._access_token = None
            self._token_expires = None
            
            # Clear saved token
            if self.config.token_file:
                self.config.save_token({})
                
        except requests.RequestException:
            pass  # Ignore revocation errors
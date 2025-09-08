"""
Deezer authentication management.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any
import aiohttp
from aiohttp import ClientSession

from ..config import AuthConfig
from ..exceptions import AuthenticationError, InvalidARLError, SessionExpiredError

logger = logging.getLogger(__name__)


class AuthenticationManager:
    """Manages Deezer authentication using ARL token."""
    
    def __init__(self, config: AuthConfig):
        """
        Initialize authentication manager.
        
        Args:
            config: Authentication configuration
        """
        self.config = config
        self.csrf_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.license_token: Optional[str] = None
        self.user_data: Dict[str, Any] = {}
        self.is_authenticated = False
        self.session: Optional[ClientSession] = None
    
    async def authenticate(self, session: ClientSession) -> bool:
        """
        Authenticate using ARL token.
        
        Args:
            session: aiohttp session to use
            
        Returns:
            True if authentication successful
            
        Raises:
            InvalidARLError: If ARL token is invalid
        """
        self.session = session
        
        if not self.config.arl:
            logger.warning("No ARL token provided, running in unauthenticated mode")
            return False
        
        try:
            # Set ARL cookie
            from yarl import URL
            session.cookie_jar.update_cookies(
                {"arl": self.config.arl},
                response_url=URL("https://www.deezer.com")
            )
            
            # Get user data to validate authentication
            user_data = await self._get_user_data()
            
            if not user_data or not user_data.get("results"):
                raise InvalidARLError("Invalid or expired ARL token")
            
            results = user_data["results"]
            
            # Extract authentication info
            self.user_data = results
            self.csrf_token = results.get("checkForm")
            
            user_info = results.get("USER", {})
            self.user_id = user_info.get("USER_ID")
            
            # Get license token and capabilities
            options = user_info.get("OPTIONS", {})
            self.license_token = options.get("license_token")
            
            # Store user capabilities
            web_sound_quality = options.get("web_sound_quality", {})
            self.has_lossless = web_sound_quality.get("lossless", False)
            self.has_high_quality = web_sound_quality.get("high", False)
            
            self.is_authenticated = True
            
            logger.info(f"Authenticated as Deezer user {self.user_id}")
            logger.info(f"Available qualities: FLAC={self.has_lossless}, HQ={self.has_high_quality}")
            
            # Save session if configured
            if self.config.auto_refresh:
                await self._save_session()
            
            return True
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise AuthenticationError(f"Failed to authenticate: {e}")
    
    async def _get_user_data(self) -> Dict[str, Any]:
        """Get user data from Deezer API."""
        if not self.session:
            raise AuthenticationError("No session available")
        
        url = "https://www.deezer.com/ajax/gw-light.php"
        params = {
            "method": "deezer.getUserData",
            "input": "3",
            "api_version": "1.0",
            "api_token": "null",
        }
        
        async with self.session.post(url, params=params, json={}) as response:
            if response.status != 200:
                raise AuthenticationError(f"Failed to get user data: {response.status}")
            return await response.json()
    
    async def refresh_token(self) -> bool:
        """
        Refresh authentication token.
        
        Returns:
            True if refresh successful
        """
        if not self.session:
            return False
        
        try:
            # Re-authenticate with existing ARL
            return await self.authenticate(self.session)
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return False
    
    async def _save_session(self):
        """Save session data to file."""
        if not self.config.session_file:
            return
        
        session_data = {
            "arl": self.config.arl,
            "csrf_token": self.csrf_token,
            "user_id": self.user_id,
            "license_token": self.license_token,
            "user_data": self.user_data,
        }
        
        session_file = Path(self.config.session_file)
        session_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(session_file, "w") as f:
            json.dump(session_data, f, indent=2)
        
        logger.debug(f"Session saved to {session_file}")
    
    async def load_session(self) -> bool:
        """
        Load session from file.
        
        Returns:
            True if session loaded successfully
        """
        if not self.config.session_file:
            return False
        
        session_file = Path(self.config.session_file)
        if not session_file.exists():
            return False
        
        try:
            with open(session_file, "r") as f:
                session_data = json.load(f)
            
            self.config.arl = session_data.get("arl")
            self.csrf_token = session_data.get("csrf_token")
            self.user_id = session_data.get("user_id")
            self.license_token = session_data.get("license_token")
            self.user_data = session_data.get("user_data", {})
            
            if self.csrf_token and self.user_id:
                self.is_authenticated = True
                logger.info(f"Session loaded for user {self.user_id}")
                return True
            
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
        
        return False
    
    def get_api_token(self) -> str:
        """Get API token for requests."""
        return self.csrf_token or "null"
    
    @property
    def is_premium(self) -> bool:
        """Check if user has premium subscription."""
        if not self.is_authenticated:
            return False
        
        user_info = self.user_data.get("USER", {})
        offer_id = user_info.get("OFFER_ID", 0)
        
        # Deezer offer IDs for premium subscriptions
        premium_offers = [1, 2, 3, 4, 6, 7, 8, 9]
        return offer_id in premium_offers
    
    @property
    def available_qualities(self) -> list:
        """Get list of available audio qualities."""
        qualities = ["MP3_128"]
        
        if self.is_premium:
            qualities.append("MP3_320")
            
        if hasattr(self, "has_lossless") and self.has_lossless:
            qualities.append("FLAC")
        
        return qualities
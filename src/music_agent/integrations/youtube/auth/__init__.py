"""
YouTube authentication and authorization.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
import httpx

logger = logging.getLogger(__name__)


@dataclass
class YouTubeCredentials:
    """YouTube credentials container."""
    
    cookies_file: Optional[str] = None
    api_key: Optional[str] = None
    oauth_token: Optional[str] = None
    oauth_refresh_token: Optional[str] = None
    
    def is_authenticated(self) -> bool:
        """Check if we have valid authentication."""
        return bool(self.cookies_file or self.api_key or self.oauth_token)
    
    def to_ytdlp_opts(self) -> Dict[str, Any]:
        """Convert to yt-dlp options."""
        opts = {}
        if self.cookies_file and Path(self.cookies_file).exists():
            opts['cookiefile'] = self.cookies_file
        return opts


class YouTubeAuth:
    """Handle YouTube authentication."""
    
    def __init__(self, cookies_file: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize authentication."""
        self.cookies_file = cookies_file
        self.api_key = api_key
        self._oauth_token: Optional[str] = None
        self._oauth_refresh_token: Optional[str] = None
        
    @classmethod
    def from_env(cls) -> "YouTubeAuth":
        """Create from environment variables."""
        return cls(
            cookies_file=os.getenv("YOUTUBE_COOKIES_FILE"),
            api_key=os.getenv("YOUTUBE_API_KEY")
        )
    
    def get_credentials(self) -> YouTubeCredentials:
        """Get current credentials."""
        return YouTubeCredentials(
            cookies_file=self.cookies_file,
            api_key=self.api_key,
            oauth_token=self._oauth_token,
            oauth_refresh_token=self._oauth_refresh_token
        )
    
    def load_cookies_from_browser(self, browser: str = "chrome") -> bool:
        """
        Load cookies from browser.
        
        Args:
            browser: Browser name (chrome, firefox, safari, edge)
            
        Returns:
            True if cookies loaded successfully
        """
        try:
            # This would use browser_cookie3 or similar
            # For now, we'll just check if cookies file exists
            if self.cookies_file and Path(self.cookies_file).exists():
                logger.info(f"Loaded cookies from {self.cookies_file}")
                return True
            
            logger.warning("No cookies file found")
            return False
            
        except Exception as e:
            logger.error(f"Failed to load cookies: {e}")
            return False
    
    def export_cookies(self, filepath: str) -> bool:
        """
        Export cookies to Netscape format for yt-dlp.
        
        Args:
            filepath: Path to save cookies file
            
        Returns:
            True if exported successfully
        """
        try:
            if not self.cookies_file:
                logger.error("No cookies to export")
                return False
            
            # Copy cookies file to new location
            import shutil
            shutil.copy(self.cookies_file, filepath)
            logger.info(f"Exported cookies to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export cookies: {e}")
            return False
    
    async def oauth_flow(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://localhost:8080/callback"
    ) -> bool:
        """
        Perform OAuth2 flow for YouTube Data API.
        
        Args:
            client_id: OAuth client ID
            client_secret: OAuth client secret
            redirect_uri: Redirect URI for OAuth
            
        Returns:
            True if authentication successful
        """
        try:
            # This would implement full OAuth2 flow
            # For now, we'll just store the credentials
            logger.info("OAuth flow would be implemented here")
            return False
            
        except Exception as e:
            logger.error(f"OAuth flow failed: {e}")
            return False
    
    def validate_api_key(self) -> bool:
        """
        Validate YouTube Data API key.
        
        Returns:
            True if API key is valid
        """
        if not self.api_key:
            return False
        
        try:
            # Test API key with a simple request
            url = "https://www.googleapis.com/youtube/v3/videos"
            params = {
                "part": "snippet",
                "id": "dQw4w9WgXcQ",  # Rick Roll for testing
                "key": self.api_key
            }
            
            with httpx.Client() as client:
                response = client.get(url, params=params)
                
                if response.status_code == 200:
                    logger.info("API key validated successfully")
                    return True
                else:
                    logger.error(f"API key validation failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to validate API key: {e}")
            return False
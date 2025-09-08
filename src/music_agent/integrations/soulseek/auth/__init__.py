"""
Soulseek/slskd authentication manager.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SlskdAuthManager:
    """Manages authentication with slskd server."""
    
    def __init__(self, api_key: Optional[str] = None, no_auth: bool = False):
        """
        Initialize auth manager.
        
        Args:
            api_key: API key for slskd server
            no_auth: Whether authentication is disabled (SLSKD_NO_AUTH=true)
        """
        self.api_key = api_key
        self.no_auth = no_auth
        self._authenticated = False
    
    def get_auth_token(self) -> Optional[str]:
        """
        Get authentication token for API requests.
        
        Returns:
            API key or dummy token if no auth required
        """
        if self.no_auth:
            # When SLSKD_NO_AUTH=true, we still need to provide something
            # to satisfy the slskd_api library
            return "no-auth-required"
        
        if not self.api_key:
            logger.warning("No API key configured for slskd")
            return None
        
        return self.api_key
    
    def validate_connection(self, client) -> bool:
        """
        Validate connection to slskd server.
        
        Args:
            client: slskd_api client instance
            
        Returns:
            True if connection is valid
        """
        try:
            # Try to get server info to validate connection
            if hasattr(client, 'server'):
                info = client.server.state()
                if info:
                    self._authenticated = True
                    logger.info("Successfully connected to slskd server")
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to validate slskd connection: {e}")
            return False
    
    @property
    def is_authenticated(self) -> bool:
        """Check if authenticated with slskd."""
        return self._authenticated or self.no_auth
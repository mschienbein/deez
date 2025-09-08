"""
Base API client for slskd server.
"""

import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

try:
    import slskd_api
except ImportError:
    logger.error("slskd_api not installed. Install with: pip install slskd-api")
    slskd_api = None

from ..config import SlskdConfig
from ..auth import SlskdAuthManager
from ..exceptions import SlskdConnectionError, SlskdAuthenticationError


class BaseAPI:
    """Base API client for slskd server."""
    
    def __init__(self, config: SlskdConfig, auth_manager: SlskdAuthManager):
        """
        Initialize base API client.
        
        Args:
            config: slskd configuration
            auth_manager: Authentication manager
        """
        self.config = config
        self.auth_manager = auth_manager
        self.client: Optional[Any] = None
        self._connected = False
    
    def connect(self):
        """Connect to slskd server."""
        if not slskd_api:
            raise ImportError("slskd_api library not available")
        
        # Get auth token
        auth_token = self.auth_manager.get_auth_token()
        if not auth_token and not self.config.no_auth:
            raise SlskdAuthenticationError("No authentication token available")
        
        try:
            # Initialize slskd client
            self.client = slskd_api.SlskdClient(
                self.config.host,
                auth_token or "no-auth",
                self.config.url_base
            )
            
            # Validate connection
            if self.auth_manager.validate_connection(self.client):
                self._connected = True
                logger.info(f"Connected to slskd server at {self.config.host}")
            else:
                raise SlskdConnectionError("Failed to validate connection to slskd")
                
        except Exception as e:
            logger.error(f"Failed to connect to slskd: {e}")
            raise SlskdConnectionError(f"Connection failed: {e}")
    
    def ensure_connected(self):
        """Ensure client is connected."""
        if not self._connected or not self.client:
            self.connect()
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to slskd."""
        return self._connected and self.client is not None
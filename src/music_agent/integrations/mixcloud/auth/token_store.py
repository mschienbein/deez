"""
Token storage for Mixcloud authentication.

Handles secure storage and retrieval of OAuth tokens.
"""

import json
import logging
import os
from typing import Optional, Dict, Any
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class TokenStore:
    """Stores and manages OAuth tokens."""
    
    def __init__(self, token_file: str = "~/.mixcloud_token"):
        """
        Initialize token store.
        
        Args:
            token_file: Path to token file
        """
        self.token_file = Path(os.path.expanduser(token_file))
        self._lock = asyncio.Lock()
        
    async def save(self, token_data: Dict[str, Any]):
        """
        Save token data to file.
        
        Args:
            token_data: Token data to save
        """
        async with self._lock:
            try:
                # Ensure directory exists
                self.token_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Write token data
                with open(self.token_file, 'w') as f:
                    json.dump(token_data, f, indent=2)
                
                # Set restrictive permissions (user read/write only)
                os.chmod(self.token_file, 0o600)
                
                logger.debug(f"Tokens saved to {self.token_file}")
                
            except Exception as e:
                logger.error(f"Failed to save tokens: {e}")
                raise
    
    async def load(self) -> Optional[Dict[str, Any]]:
        """
        Load token data from file.
        
        Returns:
            Token data if available, None otherwise
        """
        async with self._lock:
            if not self.token_file.exists():
                logger.debug("Token file does not exist")
                return None
            
            try:
                with open(self.token_file, 'r') as f:
                    token_data = json.load(f)
                
                logger.debug(f"Tokens loaded from {self.token_file}")
                return token_data
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid token file format: {e}")
                return None
            except Exception as e:
                logger.error(f"Failed to load tokens: {e}")
                return None
    
    async def clear(self):
        """Clear stored tokens."""
        async with self._lock:
            if self.token_file.exists():
                try:
                    self.token_file.unlink()
                    logger.debug("Token file removed")
                except Exception as e:
                    logger.error(f"Failed to remove token file: {e}")
    
    async def update(self, updates: Dict[str, Any]):
        """
        Update specific fields in stored tokens.
        
        Args:
            updates: Fields to update
        """
        # Load existing tokens
        token_data = await self.load() or {}
        
        # Update fields
        token_data.update(updates)
        
        # Save updated tokens
        await self.save(token_data)
    
    def exists(self) -> bool:
        """
        Check if token file exists.
        
        Returns:
            True if token file exists
        """
        return self.token_file.exists()


class KeyringTokenStore(TokenStore):
    """
    Secure token storage using system keyring.
    
    This provides more secure storage than file-based storage
    by using the system's credential manager.
    """
    
    def __init__(self, service_name: str = "mixcloud", username: str = "default"):
        """
        Initialize keyring token store.
        
        Args:
            service_name: Service name for keyring
            username: Username for keyring entry
        """
        self.service_name = service_name
        self.username = username
        self._keyring_available = False
        
        try:
            import keyring
            self._keyring = keyring
            self._keyring_available = True
            logger.debug("Keyring available for secure token storage")
        except ImportError:
            logger.warning("Keyring not available, falling back to file storage")
            super().__init__()
    
    async def save(self, token_data: Dict[str, Any]):
        """Save token data to keyring."""
        if not self._keyring_available:
            return await super().save(token_data)
        
        try:
            # Convert to JSON string for storage
            token_json = json.dumps(token_data)
            
            # Store in keyring
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._keyring.set_password,
                self.service_name,
                self.username,
                token_json
            )
            
            logger.debug("Tokens saved to system keyring")
            
        except Exception as e:
            logger.error(f"Failed to save to keyring: {e}")
            # Fall back to file storage
            await super().save(token_data)
    
    async def load(self) -> Optional[Dict[str, Any]]:
        """Load token data from keyring."""
        if not self._keyring_available:
            return await super().load()
        
        try:
            # Get from keyring
            token_json = await asyncio.get_event_loop().run_in_executor(
                None,
                self._keyring.get_password,
                self.service_name,
                self.username
            )
            
            if not token_json:
                logger.debug("No tokens in keyring")
                return None
            
            # Parse JSON
            token_data = json.loads(token_json)
            
            logger.debug("Tokens loaded from system keyring")
            return token_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid token data in keyring: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load from keyring: {e}")
            # Fall back to file storage
            return await super().load()
    
    async def clear(self):
        """Clear tokens from keyring."""
        if not self._keyring_available:
            return await super().clear()
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._keyring.delete_password,
                self.service_name,
                self.username
            )
            
            logger.debug("Tokens cleared from keyring")
            
        except Exception as e:
            logger.error(f"Failed to clear from keyring: {e}")
            # Fall back to file storage
            await super().clear()
    
    def exists(self) -> bool:
        """Check if tokens exist in keyring."""
        if not self._keyring_available:
            return super().exists()
        
        try:
            password = self._keyring.get_password(self.service_name, self.username)
            return password is not None
        except Exception:
            return False


__all__ = ["TokenStore", "KeyringTokenStore"]
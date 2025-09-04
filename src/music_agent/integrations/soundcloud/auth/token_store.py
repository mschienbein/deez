"""
Token storage for SoundCloud authentication.

Securely stores and manages authentication tokens.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    logging.warning("keyring not available - tokens will be stored in plaintext file")

logger = logging.getLogger(__name__)


class TokenStore:
    """
    Stores and manages authentication tokens.
    
    Uses keyring for secure storage when available,
    falls back to file storage.
    """
    
    SERVICE_NAME = "soundcloud-music-agent"
    TOKEN_KEY = "auth_token"
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize token store.
        
        Args:
            storage_path: Optional path for file-based storage
        """
        self.storage_path = storage_path or Path.home() / ".soundcloud" / "tokens.json"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def store_token(
        self,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[str] = None,
        scope: Optional[str] = None,
        **extra_data
    ):
        """
        Store authentication token.
        
        Args:
            access_token: Access token
            refresh_token: Optional refresh token
            expires_at: Token expiry time (ISO format)
            scope: Token scope
            **extra_data: Additional data to store
        """
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "scope": scope,
            "stored_at": datetime.now().isoformat(),
            **extra_data,
        }
        
        if KEYRING_AVAILABLE:
            try:
                keyring.set_password(
                    self.SERVICE_NAME,
                    self.TOKEN_KEY,
                    json.dumps(token_data)
                )
                logger.debug("Token stored in keyring")
                return
            except Exception as e:
                logger.warning(f"Failed to store in keyring: {e}")
        
        # Fall back to file storage
        self._store_to_file(token_data)
    
    async def get_token(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve stored token.
        
        Returns:
            Token data if available, None otherwise
        """
        if KEYRING_AVAILABLE:
            try:
                token_json = keyring.get_password(self.SERVICE_NAME, self.TOKEN_KEY)
                if token_json:
                    return json.loads(token_json)
            except Exception as e:
                logger.warning(f"Failed to retrieve from keyring: {e}")
        
        # Fall back to file storage
        return self._get_from_file()
    
    async def delete_token(self):
        """Delete stored token."""
        if KEYRING_AVAILABLE:
            try:
                keyring.delete_password(self.SERVICE_NAME, self.TOKEN_KEY)
                logger.debug("Token deleted from keyring")
            except Exception:
                pass  # Token might not exist
        
        # Also delete file
        if self.storage_path.exists():
            self.storage_path.unlink()
            logger.debug("Token file deleted")
    
    async def is_token_valid(self) -> bool:
        """
        Check if stored token is still valid.
        
        Returns:
            True if token exists and hasn't expired
        """
        token = await self.get_token()
        
        if not token or not token.get("access_token"):
            return False
        
        # Check expiry
        if token.get("expires_at"):
            try:
                expires = datetime.fromisoformat(token["expires_at"])
                if datetime.now() >= expires:
                    logger.debug("Stored token has expired")
                    return False
            except (ValueError, TypeError):
                pass
        
        return True
    
    def _store_to_file(self, token_data: Dict[str, Any]):
        """Store token to file."""
        try:
            # Encrypt sensitive data if possible
            # For now, just store as JSON with restricted permissions
            self.storage_path.write_text(json.dumps(token_data, indent=2))
            
            # Set restrictive permissions (Unix-like systems)
            try:
                import os
                os.chmod(self.storage_path, 0o600)
            except (ImportError, OSError):
                pass
            
            logger.debug(f"Token stored to {self.storage_path}")
            
        except Exception as e:
            logger.error(f"Failed to store token to file: {e}")
    
    def _get_from_file(self) -> Optional[Dict[str, Any]]:
        """Get token from file."""
        if not self.storage_path.exists():
            return None
        
        try:
            token_data = json.loads(self.storage_path.read_text())
            return token_data
        except Exception as e:
            logger.error(f"Failed to read token from file: {e}")
            return None
    
    async def store_client_ids(self, client_ids: list[str]):
        """
        Store scraped client IDs.
        
        Args:
            client_ids: List of client IDs
        """
        data = {
            "client_ids": client_ids,
            "stored_at": datetime.now().isoformat(),
        }
        
        ids_path = self.storage_path.parent / "client_ids.json"
        
        try:
            ids_path.write_text(json.dumps(data, indent=2))
            logger.debug(f"Stored {len(client_ids)} client IDs")
        except Exception as e:
            logger.error(f"Failed to store client IDs: {e}")
    
    async def get_client_ids(self) -> Optional[list[str]]:
        """
        Retrieve stored client IDs.
        
        Returns:
            List of client IDs if available
        """
        ids_path = self.storage_path.parent / "client_ids.json"
        
        if not ids_path.exists():
            return None
        
        try:
            data = json.loads(ids_path.read_text())
            
            # Check age (refresh if older than 24 hours)
            stored_at = datetime.fromisoformat(data["stored_at"])
            age = datetime.now() - stored_at
            
            if age.days >= 1:
                logger.debug("Stored client IDs are stale")
                return None
            
            return data.get("client_ids")
            
        except Exception as e:
            logger.error(f"Failed to read client IDs: {e}")
            return None


__all__ = ["TokenStore"]
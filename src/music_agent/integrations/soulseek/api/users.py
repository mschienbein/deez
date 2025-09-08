"""
User API for Soulseek.
"""

import asyncio
import logging
from typing import Optional, List

from .base import BaseAPI
from ..models import UserInfo, BrowseResult, User
from ..exceptions import UserNotFoundError

logger = logging.getLogger(__name__)


class UserAPI(BaseAPI):
    """API for user-related operations."""
    
    async def get_user_info(self, username: str) -> UserInfo:
        """
        Get information about a user.
        
        Args:
            username: Username to get info for
            
        Returns:
            UserInfo object
        """
        self.ensure_connected()
        
        try:
            # The correct method is 'info' not 'get_info'
            info_data = self.client.users.info(username)
            # Pass username since API doesn't return it
            return UserInfo.from_api(info_data, username=username)
        except Exception as e:
            logger.error(f"Failed to get user info for {username}: {e}")
            raise UserNotFoundError(f"User {username} not found or error: {e}")
    
    async def browse_user(self, username: str, timeout: int = 10) -> BrowseResult:
        """
        Browse a user's shared files.
        
        Args:
            username: Username to browse
            timeout: Timeout in seconds
            
        Returns:
            BrowseResult object
        """
        self.ensure_connected()
        
        try:
            # Request browse
            self.client.users.browse(username)
            logger.info(f"Initiated browse for user {username}")
            
            # Wait for browse to complete
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                # Get browse status - the correct method is 'browsing_status'
                status = self.client.users.browsing_status(username)
                
                if status and status.get("status") == "completed":
                    # Browse completed, return result
                    return BrowseResult.from_api(username, status)
                
                await asyncio.sleep(1)
            
            # Timeout - return partial results if available
            status = self.client.users.browsing_status(username)
            if status:
                logger.warning(f"Browse timed out for {username}, returning partial results")
                return BrowseResult.from_api(username, status)
            else:
                raise UserNotFoundError(f"Browse failed for user {username}")
                
        except Exception as e:
            logger.error(f"Failed to browse user {username}: {e}")
            raise UserNotFoundError(f"Failed to browse user {username}: {e}")
    
    async def get_user(self, username: str) -> User:
        """
        Get complete user information including browse.
        
        Args:
            username: Username
            
        Returns:
            User object with info and browse result
        """
        user = User(username=username)
        
        # Get user info
        try:
            user.info = await self.get_user_info(username)
        except Exception as e:
            logger.warning(f"Failed to get info for {username}: {e}")
        
        # Browse user files (optional)
        try:
            user.browse_result = await self.browse_user(username)
        except Exception as e:
            logger.warning(f"Failed to browse {username}: {e}")
        
        return user
    
    def add_user_to_list(self, username: str) -> bool:
        """
        Add user to the user list.
        
        Args:
            username: Username to add
            
        Returns:
            True if added successfully
        """
        self.ensure_connected()
        
        try:
            self.client.users.add(username)
            logger.info(f"Added {username} to user list")
            return True
        except Exception as e:
            logger.error(f"Failed to add {username} to list: {e}")
            return False
    
    def remove_user_from_list(self, username: str) -> bool:
        """
        Remove user from the user list.
        
        Args:
            username: Username to remove
            
        Returns:
            True if removed successfully
        """
        self.ensure_connected()
        
        try:
            self.client.users.remove(username)
            logger.info(f"Removed {username} from user list")
            return True
        except Exception as e:
            logger.error(f"Failed to remove {username} from list: {e}")
            return False
    
    def get_user_list(self) -> List[str]:
        """
        Get list of users.
        
        Returns:
            List of usernames
        """
        self.ensure_connected()
        
        try:
            return self.client.users.get_all()
        except Exception as e:
            logger.error(f"Failed to get user list: {e}")
            return []
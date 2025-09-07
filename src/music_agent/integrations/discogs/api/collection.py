"""
Collection API functionality for Discogs.
"""

import logging
from typing import Optional, List, Dict, Any

from ..models import CollectionItem
from ..exceptions import APIError, AuthenticationError

logger = logging.getLogger(__name__)


class CollectionAPI:
    """Handles collection and wantlist operations."""
    
    def __init__(self, client):
        """
        Initialize collection API.
        
        Args:
            client: Parent DiscogsClient instance
        """
        self.client = client
    
    def get_collection(
        self,
        username: Optional[str] = None,
        folder_id: int = 0,
        sort: str = "artist",
        sort_order: str = "asc",
        per_page: int = 50,
        page: int = 1
    ) -> List[CollectionItem]:
        """
        Get user's collection.
        
        Args:
            username: Username (defaults to authenticated user)
            folder_id: Folder ID (0 for all folders)
            sort: Sort field (artist, title, catno, year, added)
            sort_order: Sort order (asc, desc)
            per_page: Results per page
            page: Page number
            
        Returns:
            List of CollectionItem objects
        """
        try:
            if username:
                user = self.client._client.user(username)
            else:
                # Get authenticated user
                user = self.client._client.identity()
            
            # Get collection
            if folder_id == 0:
                collection = user.collection_folders[0].releases
            else:
                folder = user.collection_folders.folder(folder_id)
                collection = folder.releases
            
            # Apply sorting and pagination
            collection_page = collection.page(page)
            
            # Convert to our model
            items = []
            for item in collection_page:
                items.append(self._parse_collection_item(item))
            
            return items
            
        except Exception as e:
            logger.error(f"Failed to get collection: {e}")
            if "401" in str(e):
                raise AuthenticationError("Authentication required for collection access")
            raise APIError(f"Failed to get collection: {e}")
    
    def get_collection_folders(
        self,
        username: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user's collection folders.
        
        Args:
            username: Username (defaults to authenticated user)
            
        Returns:
            List of folder dictionaries
        """
        try:
            if username:
                user = self.client._client.user(username)
            else:
                user = self.client._client.identity()
            
            folders = []
            for folder in user.collection_folders:
                folders.append({
                    'id': folder.id,
                    'name': folder.name,
                    'count': folder.count,
                    'resource_url': folder.data.get('resource_url')
                })
            
            return folders
            
        except Exception as e:
            logger.error(f"Failed to get collection folders: {e}")
            raise APIError(f"Failed to get collection folders: {e}")
    
    def add_to_collection(
        self,
        release_id: int,
        folder_id: int = 1
    ) -> bool:
        """
        Add a release to collection.
        
        Args:
            release_id: Discogs release ID
            folder_id: Target folder ID (1 is usually "Uncategorized")
            
        Returns:
            True if successful
        """
        try:
            user = self.client._client.identity()
            folder = user.collection_folders.folder(folder_id)
            folder.add_release(release_id)
            return True
            
        except Exception as e:
            logger.error(f"Failed to add to collection: {e}")
            raise APIError(f"Failed to add to collection: {e}")
    
    def remove_from_collection(
        self,
        release_id: int,
        folder_id: int = 1,
        instance_id: Optional[int] = None
    ) -> bool:
        """
        Remove a release from collection.
        
        Args:
            release_id: Discogs release ID
            folder_id: Folder ID
            instance_id: Specific instance ID (for multiple copies)
            
        Returns:
            True if successful
        """
        try:
            user = self.client._client.identity()
            folder = user.collection_folders.folder(folder_id)
            
            if instance_id:
                folder.remove_release(instance_id)
            else:
                # Find instance ID
                for item in folder.releases:
                    if item.release.id == release_id:
                        folder.remove_release(item.instance_id)
                        break
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove from collection: {e}")
            raise APIError(f"Failed to remove from collection: {e}")
    
    def get_wantlist(
        self,
        username: Optional[str] = None,
        per_page: int = 50,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get user's wantlist.
        
        Args:
            username: Username (defaults to authenticated user)
            per_page: Results per page
            page: Page number
            
        Returns:
            List of wantlist items
        """
        try:
            if username:
                user = self.client._client.user(username)
            else:
                user = self.client._client.identity()
            
            wantlist = user.wantlist.page(page)
            
            items = []
            for item in wantlist:
                items.append({
                    'id': item.id,
                    'rating': item.rating,
                    'notes': item.notes,
                    'basic_information': item.data.get('basic_information', {}),
                    'resource_url': item.data.get('resource_url')
                })
            
            return items
            
        except Exception as e:
            logger.error(f"Failed to get wantlist: {e}")
            raise APIError(f"Failed to get wantlist: {e}")
    
    def add_to_wantlist(
        self,
        release_id: int,
        notes: Optional[str] = None,
        rating: Optional[int] = None
    ) -> bool:
        """
        Add a release to wantlist.
        
        Args:
            release_id: Discogs release ID
            notes: Optional notes
            rating: Optional rating (0-5)
            
        Returns:
            True if successful
        """
        try:
            user = self.client._client.identity()
            release = self.client._client.release(release_id)
            user.wantlist.add(release)
            
            # Note: Setting notes and rating would require additional API calls
            return True
            
        except Exception as e:
            logger.error(f"Failed to add to wantlist: {e}")
            raise APIError(f"Failed to add to wantlist: {e}")
    
    def remove_from_wantlist(
        self,
        release_id: int
    ) -> bool:
        """
        Remove a release from wantlist.
        
        Args:
            release_id: Discogs release ID
            
        Returns:
            True if successful
        """
        try:
            user = self.client._client.identity()
            release = self.client._client.release(release_id)
            user.wantlist.remove(release)
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove from wantlist: {e}")
            raise APIError(f"Failed to remove from wantlist: {e}")
    
    def get_collection_value(
        self,
        username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get estimated collection value.
        
        Args:
            username: Username (defaults to authenticated user)
            
        Returns:
            Dictionary with value statistics
        """
        try:
            if username:
                user = self.client._client.user(username)
            else:
                user = self.client._client.identity()
            
            # Get collection value (if available)
            collection = user.collection_folders[0]
            
            return {
                'minimum': collection.data.get('value', {}).get('minimum'),
                'median': collection.data.get('value', {}).get('median'),
                'maximum': collection.data.get('value', {}).get('maximum'),
                'count': collection.count
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection value: {e}")
            raise APIError(f"Failed to get collection value: {e}")
    
    def _parse_collection_item(self, item: Any) -> CollectionItem:
        """Parse raw collection item into model."""
        return CollectionItem(
            id=item.id if hasattr(item, 'id') else 0,
            instance_id=item.instance_id if hasattr(item, 'instance_id') else 0,
            folder_id=item.folder_id if hasattr(item, 'folder_id') else 1,
            rating=item.rating if hasattr(item, 'rating') else 0,
            basic_information=item.data.get('basic_information', {}) if hasattr(item, 'data') else {},
            notes=item.notes if hasattr(item, 'notes') else None,
            date_added=item.date_added if hasattr(item, 'date_added') else None
        )
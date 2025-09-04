"""
Comprehensive Discogs API integration for the Music Agent.

This module provides complete access to all Discogs API features including:
- Database queries (artists, releases, labels, masters)
- User management (profile, submissions, contributions)
- Collection management (folders, fields, value)
- Wantlist management
- Marketplace operations (inventory, orders, listings)
- Community data (release stats)
- Advanced search with filters
"""

import os
import time
import logging
from typing import Optional, List, Dict, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

import discogs_client
from discogs_client.exceptions import HTTPError, AuthorizationError

from ..utils.config import get_config

logger = logging.getLogger(__name__)


class SearchType(Enum):
    """Discogs search types."""
    RELEASE = "release"
    MASTER = "master"
    ARTIST = "artist"
    LABEL = "label"


class ListingCondition(Enum):
    """Marketplace listing conditions."""
    MINT = "Mint (M)"
    NEAR_MINT = "Near Mint (NM or M-)"
    VERY_GOOD_PLUS = "Very Good Plus (VG+)"
    VERY_GOOD = "Very Good (VG)"
    GOOD_PLUS = "Good Plus (G+)"
    GOOD = "Good (G)"
    FAIR = "Fair (F)"
    POOR = "Poor (P)"


class ListingStatus(Enum):
    """Marketplace listing status."""
    FOR_SALE = "For Sale"
    DRAFT = "Draft"
    EXPIRED = "Expired"
    SOLD = "Sold"
    DELETED = "Deleted"


class Currency(Enum):
    """Supported currencies."""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    AUD = "AUD"
    CAD = "CAD"
    JPY = "JPY"


@dataclass
class SearchFilters:
    """Advanced search filters."""
    query: str
    type: Optional[SearchType] = None
    title: Optional[str] = None
    release_title: Optional[str] = None
    credit: Optional[str] = None
    artist: Optional[str] = None
    anv: Optional[str] = None  # Artist name variation
    label: Optional[str] = None
    genre: Optional[str] = None
    style: Optional[str] = None
    country: Optional[str] = None
    year: Optional[Union[int, str]] = None  # Can be year or range like "1990-2000"
    format: Optional[str] = None  # Vinyl, CD, etc.
    catno: Optional[str] = None  # Catalog number
    barcode: Optional[str] = None
    track: Optional[str] = None
    submitter: Optional[str] = None
    contributor: Optional[str] = None


class DiscogsIntegration:
    """Complete Discogs API integration."""

    def __init__(self):
        """Initialize Discogs client with configuration."""
        config = get_config()
        self.config = config.discogs
        
        # Initialize client with authentication
        if self.config.user_token:
            # Use personal access token for simpler auth
            self.client = discogs_client.Client(
                self.config.user_agent,
                user_token=self.config.user_token
            )
        elif self.config.consumer_key and self.config.consumer_secret:
            # Use OAuth for full access
            self.client = discogs_client.Client(
                self.config.user_agent,
                consumer_key=self.config.consumer_key,
                consumer_secret=self.config.consumer_secret
            )
        else:
            # No auth - limited access
            self.client = discogs_client.Client(self.config.user_agent)
        
        self.last_request_time = 0
        self.request_count = 0
        
    def _rate_limit(self):
        """Enforce rate limiting."""
        # Discogs allows 60 requests per minute for authenticated users
        # 25 requests per minute for unauthenticated
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < (60 / self.config.rate_limit):
            sleep_time = (60 / self.config.rate_limit) - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
        self.request_count += 1

    # ====================================
    # Database Methods
    # ====================================

    def search(
        self,
        query: Optional[str] = None,
        filters: Optional[SearchFilters] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """
        Advanced search with filters.
        
        Args:
            query: Basic search query
            filters: Advanced search filters
            page: Page number for pagination
            per_page: Results per page (max 100)
        
        Returns:
            Search results with pagination info
        """
        self._rate_limit()
        
        try:
            if filters:
                # Build search parameters from filters
                params = {}
                if filters.query:
                    params['q'] = filters.query
                if filters.type:
                    params['type'] = filters.type.value
                if filters.title:
                    params['title'] = filters.title
                if filters.release_title:
                    params['release_title'] = filters.release_title
                if filters.artist:
                    params['artist'] = filters.artist
                if filters.label:
                    params['label'] = filters.label
                if filters.genre:
                    params['genre'] = filters.genre
                if filters.style:
                    params['style'] = filters.style
                if filters.country:
                    params['country'] = filters.country
                if filters.year:
                    params['year'] = str(filters.year)
                if filters.format:
                    params['format'] = filters.format
                if filters.catno:
                    params['catno'] = filters.catno
                if filters.barcode:
                    params['barcode'] = filters.barcode
                if filters.track:
                    params['track'] = filters.track
                    
                results = self.client.search(**params, page=page, per_page=per_page)
            else:
                # Simple search
                results = self.client.search(query, page=page, per_page=per_page)
            
            # Limit iteration to avoid fetching all pages
            serialized_results = []
            for i, r in enumerate(results):
                if i >= per_page:  # Stop at requested page size
                    break
                serialized_results.append(self._serialize_result(r))
            
            return {
                'results': serialized_results,
                'pagination': {
                    'page': getattr(results, 'page', page),
                    'pages': getattr(results, 'pages', 1),
                    'per_page': getattr(results, 'per_page', per_page),
                    'items': getattr(results, 'count', len(serialized_results))
                }
            }
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {'results': [], 'pagination': {}, 'error': str(e)}

    def get_release(self, release_id: int) -> Dict[str, Any]:
        """Get detailed release information."""
        self._rate_limit()
        
        try:
            release = self.client.release(release_id)
            return self._serialize_release(release)
        except Exception as e:
            logger.error(f"Error fetching release {release_id}: {e}")
            return {'error': str(e)}

    def get_master(self, master_id: int) -> Dict[str, Any]:
        """Get master release information."""
        self._rate_limit()
        
        try:
            master = self.client.master(master_id)
            return self._serialize_master(master)
        except Exception as e:
            logger.error(f"Error fetching master {master_id}: {e}")
            return {'error': str(e)}

    def get_artist(self, artist_id: int) -> Dict[str, Any]:
        """Get detailed artist information."""
        self._rate_limit()
        
        try:
            artist = self.client.artist(artist_id)
            return self._serialize_artist(artist)
        except Exception as e:
            logger.error(f"Error fetching artist {artist_id}: {e}")
            return {'error': str(e)}

    def get_label(self, label_id: int) -> Dict[str, Any]:
        """Get detailed label information."""
        self._rate_limit()
        
        try:
            label = self.client.label(label_id)
            return self._serialize_label(label)
        except Exception as e:
            logger.error(f"Error fetching label {label_id}: {e}")
            return {'error': str(e)}

    def get_release_stats(self, release_id: int) -> Dict[str, Any]:
        """Get community statistics for a release (haves/wants)."""
        self._rate_limit()
        
        try:
            release = self.client.release(release_id)
            return {
                'release_id': release_id,
                'num_for_sale': release.num_for_sale,
                'lowest_price': release.lowest_price,
                'community': {
                    'have': release.community.have,
                    'want': release.community.want,
                    'rating': {
                        'average': release.community.rating.average,
                        'count': release.community.rating.count
                    }
                }
            }
        except Exception as e:
            logger.error(f"Error fetching release stats {release_id}: {e}")
            return {'error': str(e)}

    # ====================================
    # User Methods
    # ====================================

    def get_identity(self) -> Dict[str, Any]:
        """Get authenticated user identity."""
        self._rate_limit()
        
        try:
            identity = self.client.identity()
            return {
                'id': getattr(identity, 'id', None),
                'username': getattr(identity, 'username', None),
                'resource_url': getattr(identity, 'resource_url', None),
                'consumer_name': getattr(identity, 'consumer_name', None)
            }
        except Exception as e:
            logger.error(f"Error fetching identity: {e}")
            return {'error': str(e)}

    def get_user(self, username: str) -> Dict[str, Any]:
        """Get user profile information."""
        self._rate_limit()
        
        try:
            user = self.client.user(username)
            return self._serialize_user(user)
        except Exception as e:
            logger.error(f"Error fetching user {username}: {e}")
            return {'error': str(e)}

    def get_user_submissions(
        self,
        username: str,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """Get user's submissions (edits to existing database entries)."""
        self._rate_limit()
        
        try:
            user = self.client.user(username)
            submissions = user.submissions.page(page)
            
            return {
                'submissions': [self._serialize_result(s) for s in submissions],
                'pagination': {
                    'page': page,
                    'pages': submissions.pages,
                    'per_page': per_page,
                    'items': submissions.count
                }
            }
        except Exception as e:
            logger.error(f"Error fetching user submissions: {e}")
            return {'submissions': [], 'error': str(e)}

    def get_user_contributions(
        self,
        username: str,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """Get user's contributions (new releases added)."""
        self._rate_limit()
        
        try:
            user = self.client.user(username)
            contributions = user.contributions.page(page)
            
            return {
                'contributions': [self._serialize_result(c) for c in contributions],
                'pagination': {
                    'page': page,
                    'pages': contributions.pages,
                    'per_page': per_page,
                    'items': contributions.count
                }
            }
        except Exception as e:
            logger.error(f"Error fetching user contributions: {e}")
            return {'contributions': [], 'error': str(e)}

    # ====================================
    # Collection Methods
    # ====================================

    def get_collection_folders(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user's collection folders."""
        self._rate_limit()
        
        try:
            if username:
                user = self.client.user(username)
            else:
                user = self.client.identity()
            
            folders = user.collection_folders
            return [self._serialize_folder(f) for f in folders]
        except Exception as e:
            logger.error(f"Error fetching collection folders: {e}")
            return []

    def get_collection_folder(
        self,
        folder_id: int,
        username: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
        sort: str = 'added',
        sort_order: str = 'desc'
    ) -> Dict[str, Any]:
        """Get releases in a collection folder."""
        self._rate_limit()
        
        try:
            if username:
                user = self.client.user(username)
            else:
                user = self.client.identity()
            
            folder = None
            for f in user.collection_folders:
                if f.id == folder_id:
                    folder = f
                    break
            
            if not folder:
                return {'error': f'Folder {folder_id} not found'}
            
            releases = folder.releases.page(page).sort(sort, sort_order)
            
            return {
                'folder': self._serialize_folder(folder),
                'releases': [self._serialize_collection_item(r) for r in releases],
                'pagination': {
                    'page': page,
                    'pages': releases.pages,
                    'per_page': per_page,
                    'items': releases.count
                }
            }
        except Exception as e:
            logger.error(f"Error fetching collection folder: {e}")
            return {'error': str(e)}

    def add_to_collection(
        self,
        release_id: int,
        folder_id: int = 1,  # Default folder (All)
        notes: Optional[str] = None,
        rating: Optional[int] = None
    ) -> bool:
        """Add a release to collection."""
        self._rate_limit()
        
        try:
            user = self.client.identity()
            
            # Find the folder
            folder = None
            for f in user.collection_folders:
                if f.id == folder_id:
                    folder = f
                    break
            
            if not folder:
                logger.error(f"Folder {folder_id} not found")
                return False
            
            # Add release to folder
            folder.add_release(release_id, notes=notes, rating=rating)
            return True
            
        except Exception as e:
            logger.error(f"Error adding to collection: {e}")
            return False

    def remove_from_collection(
        self,
        release_id: int,
        instance_id: int,
        folder_id: int = 1
    ) -> bool:
        """Remove a release from collection."""
        self._rate_limit()
        
        try:
            user = self.client.identity()
            
            # Find the folder
            folder = None
            for f in user.collection_folders:
                if f.id == folder_id:
                    folder = f
                    break
            
            if not folder:
                logger.error(f"Folder {folder_id} not found")
                return False
            
            # Remove release from folder
            folder.remove_release(release_id, instance_id)
            return True
            
        except Exception as e:
            logger.error(f"Error removing from collection: {e}")
            return False

    def get_collection_value(self, username: Optional[str] = None) -> Dict[str, Any]:
        """Get collection value statistics."""
        self._rate_limit()
        
        try:
            if username:
                user = self.client.user(username)
            else:
                user = self.client.identity()
            
            value = user.collection_value
            return {
                'minimum': value.minimum,
                'median': value.median,
                'maximum': value.maximum,
                'currency': 'USD'  # Discogs uses USD for valuations
            }
        except Exception as e:
            logger.error(f"Error fetching collection value: {e}")
            return {'error': str(e)}

    def get_collection_fields(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user-defined collection fields."""
        self._rate_limit()
        
        try:
            if username:
                user = self.client.user(username)
            else:
                user = self.client.identity()
            
            fields = user.collection_fields
            return [
                {
                    'id': field.id,
                    'name': field.name,
                    'type': field.type,
                    'public': field.public,
                    'position': field.position,
                    'lines': getattr(field, 'lines', None)
                }
                for field in fields
            ]
        except Exception as e:
            logger.error(f"Error fetching collection fields: {e}")
            return []

    # ====================================
    # Wantlist Methods
    # ====================================

    def get_wantlist(
        self,
        username: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """Get user's wantlist."""
        self._rate_limit()
        
        try:
            if username:
                user = self.client.user(username)
            else:
                user = self.client.identity()
            
            wantlist = user.wantlist.page(page)
            
            return {
                'wants': [self._serialize_want(w) for w in wantlist],
                'pagination': {
                    'page': page,
                    'pages': wantlist.pages,
                    'per_page': per_page,
                    'items': wantlist.count
                }
            }
        except Exception as e:
            logger.error(f"Error fetching wantlist: {e}")
            return {'wants': [], 'error': str(e)}

    def add_to_wantlist(
        self,
        release_id: int,
        notes: Optional[str] = None,
        rating: Optional[int] = None
    ) -> bool:
        """Add a release to wantlist."""
        self._rate_limit()
        
        try:
            user = self.client.identity()
            user.wantlist.add(release_id, notes=notes, rating=rating)
            return True
        except Exception as e:
            logger.error(f"Error adding to wantlist: {e}")
            return False

    def remove_from_wantlist(self, release_id: int) -> bool:
        """Remove a release from wantlist."""
        self._rate_limit()
        
        try:
            user = self.client.identity()
            user.wantlist.remove(release_id)
            return True
        except Exception as e:
            logger.error(f"Error removing from wantlist: {e}")
            return False

    # ====================================
    # Marketplace Methods
    # ====================================

    def get_inventory(
        self,
        username: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
        status: Optional[ListingStatus] = None,
        sort: str = 'listed',
        sort_order: str = 'desc'
    ) -> Dict[str, Any]:
        """Get user's marketplace inventory."""
        self._rate_limit()
        
        try:
            if username:
                user = self.client.user(username)
            else:
                user = self.client.identity()
            
            inventory = user.inventory
            
            # Apply filters if specified
            if status:
                inventory = inventory.filter(status=status.value)
            
            listings = inventory.page(page).sort(sort, sort_order)
            
            return {
                'listings': [self._serialize_listing(l) for l in listings],
                'pagination': {
                    'page': page,
                    'pages': listings.pages,
                    'per_page': per_page,
                    'items': listings.count
                }
            }
        except Exception as e:
            logger.error(f"Error fetching inventory: {e}")
            return {'listings': [], 'error': str(e)}

    def create_listing(
        self,
        release_id: int,
        condition: ListingCondition,
        price: float,
        status: ListingStatus = ListingStatus.FOR_SALE,
        sleeve_condition: Optional[ListingCondition] = None,
        comments: Optional[str] = None,
        allow_offers: bool = False,
        external_id: Optional[str] = None,
        location: Optional[str] = None,
        weight: Optional[float] = None,
        format_quantity: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create a marketplace listing."""
        self._rate_limit()
        
        try:
            user = self.client.identity()
            
            listing_data = {
                'release_id': release_id,
                'condition': condition.value,
                'price': price,
                'status': status.value
            }
            
            if sleeve_condition:
                listing_data['sleeve_condition'] = sleeve_condition.value
            if comments:
                listing_data['comments'] = comments
            if allow_offers:
                listing_data['allow_offers'] = allow_offers
            if external_id:
                listing_data['external_id'] = external_id
            if location:
                listing_data['location'] = location
            if weight:
                listing_data['weight'] = weight
            if format_quantity:
                listing_data['format_quantity'] = format_quantity
            
            listing = user.inventory.add_listing(**listing_data)
            return self._serialize_listing(listing)
            
        except Exception as e:
            logger.error(f"Error creating listing: {e}")
            return {'error': str(e)}

    def update_listing(
        self,
        listing_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        """Update a marketplace listing."""
        self._rate_limit()
        
        try:
            user = self.client.identity()
            
            # Find the listing
            listing = None
            for l in user.inventory:
                if l.id == listing_id:
                    listing = l
                    break
            
            if not listing:
                return {'error': f'Listing {listing_id} not found'}
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(listing, key):
                    setattr(listing, key, value)
            
            listing.save()
            return self._serialize_listing(listing)
            
        except Exception as e:
            logger.error(f"Error updating listing: {e}")
            return {'error': str(e)}

    def delete_listing(self, listing_id: int) -> bool:
        """Delete a marketplace listing."""
        self._rate_limit()
        
        try:
            user = self.client.identity()
            
            # Find and delete the listing
            for listing in user.inventory:
                if listing.id == listing_id:
                    listing.delete()
                    return True
            
            logger.error(f"Listing {listing_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"Error deleting listing: {e}")
            return False

    def get_marketplace_price_suggestions(self, release_id: int) -> Dict[str, Any]:
        """Get price suggestions for a release."""
        self._rate_limit()
        
        try:
            release = self.client.release(release_id)
            
            # Get marketplace stats
            stats = {
                'release_id': release_id,
                'num_for_sale': release.num_for_sale,
                'lowest_price': release.lowest_price
            }
            
            # Get price statistics from current listings if available
            if hasattr(release, 'marketplace_stats'):
                stats.update({
                    'currency': 'USD',
                    'prices': {
                        'lowest': release.marketplace_stats.lowest_price,
                        'median': release.marketplace_stats.median_price,
                        'highest': release.marketplace_stats.highest_price
                    },
                    'conditions': release.marketplace_stats.conditions
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error fetching price suggestions: {e}")
            return {'error': str(e)}

    # ====================================
    # Order Management Methods
    # ====================================

    def get_orders(
        self,
        status: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
        sort: str = 'created',
        sort_order: str = 'desc'
    ) -> Dict[str, Any]:
        """Get marketplace orders."""
        self._rate_limit()
        
        try:
            user = self.client.identity()
            orders = user.orders
            
            if status:
                orders = orders.filter(status=status)
            
            orders_page = orders.page(page).sort(sort, sort_order)
            
            return {
                'orders': [self._serialize_order(o) for o in orders_page],
                'pagination': {
                    'page': page,
                    'pages': orders_page.pages,
                    'per_page': per_page,
                    'items': orders_page.count
                }
            }
        except Exception as e:
            logger.error(f"Error fetching orders: {e}")
            return {'orders': [], 'error': str(e)}

    def get_order(self, order_id: str) -> Dict[str, Any]:
        """Get specific order details."""
        self._rate_limit()
        
        try:
            user = self.client.identity()
            
            for order in user.orders:
                if order.id == order_id:
                    return self._serialize_order(order)
            
            return {'error': f'Order {order_id} not found'}
            
        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {e}")
            return {'error': str(e)}

    def get_order_messages(self, order_id: str) -> List[Dict[str, Any]]:
        """Get messages for an order."""
        self._rate_limit()
        
        try:
            user = self.client.identity()
            
            for order in user.orders:
                if order.id == order_id:
                    messages = order.messages
                    return [
                        {
                            'id': msg.id,
                            'subject': msg.subject,
                            'message': msg.message,
                            'from': msg.from_user,
                            'timestamp': msg.timestamp.isoformat() if hasattr(msg.timestamp, 'isoformat') else str(msg.timestamp),
                            'unread': getattr(msg, 'unread', False)
                        }
                        for msg in messages
                    ]
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching order messages: {e}")
            return []

    def send_order_message(
        self,
        order_id: str,
        message: str,
        subject: Optional[str] = None
    ) -> bool:
        """Send a message about an order."""
        self._rate_limit()
        
        try:
            user = self.client.identity()
            
            for order in user.orders:
                if order.id == order_id:
                    order.add_message(message, subject=subject)
                    return True
            
            logger.error(f"Order {order_id} not found")
            return False
            
        except Exception as e:
            logger.error(f"Error sending order message: {e}")
            return False

    # ====================================
    # Serialization Methods
    # ====================================

    def _serialize_result(self, result) -> Dict[str, Any]:
        """Serialize a search result."""
        # Determine type from class name
        result_type = result.__class__.__name__.lower()
        
        data = {
            'id': result.id,
            'type': getattr(result, 'type', result_type),
            'title': getattr(result, 'title', getattr(result, 'name', '')),
            'uri': getattr(result, 'uri', ''),
            'resource_url': getattr(result, 'resource_url', '')
        }
        
        # Add type-specific fields
        if hasattr(result, 'year'):
            data['year'] = result.year
        if hasattr(result, 'country'):
            data['country'] = result.country
        if hasattr(result, 'format'):
            data['format'] = result.format
        if hasattr(result, 'label'):
            data['label'] = result.label
        if hasattr(result, 'catno'):
            data['catno'] = result.catno
        if hasattr(result, 'thumb'):
            data['thumb'] = result.thumb
        if hasattr(result, 'cover_image'):
            data['cover_image'] = result.cover_image
        if hasattr(result, 'artists_sort'):
            data['artists_sort'] = result.artists_sort
        
        return data

    def _serialize_release(self, release) -> Dict[str, Any]:
        """Serialize a release object."""
        # Handle artists - can be list of objects or dicts
        artists = []
        for a in getattr(release, 'artists', []):
            if isinstance(a, dict):
                artists.append(a)
            else:
                artists.append({
                    'id': getattr(a, 'id', None),
                    'name': getattr(a, 'name', str(a))
                })
        
        # Handle labels
        labels = []
        for l in getattr(release, 'labels', []):
            if isinstance(l, dict):
                labels.append(l)
            else:
                labels.append({
                    'id': getattr(l, 'id', None),
                    'name': getattr(l, 'name', str(l)),
                    'catno': getattr(l, 'catno', None)
                })
        
        # Handle formats
        formats = []
        for f in getattr(release, 'formats', []):
            if isinstance(f, dict):
                formats.append(f)
            else:
                formats.append({
                    'name': getattr(f, 'name', None),
                    'qty': getattr(f, 'qty', None),
                    'descriptions': getattr(f, 'descriptions', [])
                })
        
        # Handle tracklist
        tracklist = []
        for t in getattr(release, 'tracklist', []):
            if isinstance(t, dict):
                tracklist.append(t)
            else:
                tracklist.append({
                    'position': getattr(t, 'position', ''),
                    'title': getattr(t, 'title', ''),
                    'duration': getattr(t, 'duration', ''),
                    'type': getattr(t, 'type_', '')
                })
        
        # Handle images
        images = []
        for i in getattr(release, 'images', []):
            if isinstance(i, dict):
                images.append(i)
            else:
                images.append({
                    'type': getattr(i, 'type', ''),
                    'uri': getattr(i, 'uri', ''),
                    'width': getattr(i, 'width', 0),
                    'height': getattr(i, 'height', 0)
                })
        
        return {
            'id': getattr(release, 'id', None),
            'title': getattr(release, 'title', ''),
            'artists': artists,
            'labels': labels,
            'formats': formats,
            'genres': getattr(release, 'genres', []),
            'styles': getattr(release, 'styles', []),
            'year': getattr(release, 'year', None),
            'country': getattr(release, 'country', None),
            'notes': getattr(release, 'notes', None),
            'tracklist': tracklist,
            'images': images,
            'videos': [],  # Videos often not present
            'uri': getattr(release, 'uri', ''),
            'resource_url': getattr(release, 'resource_url', ''),
            'master_id': getattr(release, 'master_id', None),
            'marketplace': {
                'num_for_sale': getattr(release, 'num_for_sale', 0),
                'lowest_price': getattr(release, 'lowest_price', None)
            },
            'community': {
                'have': getattr(getattr(release, 'community', {}), 'have', 0),
                'want': getattr(getattr(release, 'community', {}), 'want', 0),
                'rating': {
                    'average': 0,
                    'count': 0
                }
            }
        }

    def _serialize_master(self, master) -> Dict[str, Any]:
        """Serialize a master release."""
        return {
            'id': master.id,
            'title': master.title,
            'artists': [{'id': a.id, 'name': a.name} for a in master.artists],
            'genres': master.genres,
            'styles': master.styles,
            'year': master.year,
            'tracklist': [
                {
                    'position': t.position,
                    'title': t.title,
                    'duration': t.duration,
                    'type': t.type_
                }
                for t in master.tracklist
            ],
            'images': [{'type': i.type, 'uri': i.uri, 'width': i.width, 'height': i.height} for i in master.images],
            'uri': master.uri,
            'resource_url': master.resource_url,
            'versions_url': master.versions_url,
            'num_for_sale': master.num_for_sale,
            'lowest_price': master.lowest_price
        }

    def _serialize_artist(self, artist) -> Dict[str, Any]:
        """Serialize an artist."""
        # Handle images
        images = []
        for i in getattr(artist, 'images', []):
            if isinstance(i, dict):
                images.append(i)
            else:
                images.append({
                    'type': getattr(i, 'type', ''),
                    'uri': getattr(i, 'uri', ''),
                    'width': getattr(i, 'width', 0),
                    'height': getattr(i, 'height', 0)
                })
        
        return {
            'id': getattr(artist, 'id', None),
            'name': getattr(artist, 'name', ''),
            'real_name': getattr(artist, 'real_name', None),
            'profile': getattr(artist, 'profile', None),
            'images': images,
            'uri': getattr(artist, 'uri', ''),
            'resource_url': getattr(artist, 'resource_url', ''),
            'urls': getattr(artist, 'urls', []),
            'namevariations': getattr(artist, 'namevariations', []),
            'aliases': [],
            'members': [],
            'groups': []
        }

    def _serialize_label(self, label) -> Dict[str, Any]:
        """Serialize a label."""
        return {
            'id': label.id,
            'name': label.name,
            'profile': label.profile,
            'contact_info': label.contact_info,
            'parent_label': {'id': label.parent_label.id, 'name': label.parent_label.name} if hasattr(label, 'parent_label') and label.parent_label else None,
            'sublabels': [{'id': s.id, 'name': s.name} for s in label.sublabels] if hasattr(label, 'sublabels') else [],
            'images': [{'type': i.type, 'uri': i.uri, 'width': i.width, 'height': i.height} for i in label.images],
            'uri': label.uri,
            'resource_url': label.resource_url,
            'urls': label.urls
        }

    def _serialize_user(self, user) -> Dict[str, Any]:
        """Serialize a user."""
        return {
            'id': user.id,
            'username': user.username,
            'profile': user.profile,
            'location': user.location,
            'registered': user.registered.isoformat() if hasattr(user.registered, 'isoformat') else str(user.registered),
            'rating': user.rating,
            'num_collection': user.num_collection,
            'num_wantlist': user.num_wantlist,
            'num_for_sale': user.num_for_sale,
            'avatar_url': user.avatar_url,
            'uri': user.uri,
            'resource_url': user.resource_url
        }

    def _serialize_folder(self, folder) -> Dict[str, Any]:
        """Serialize a collection folder."""
        return {
            'id': folder.id,
            'name': folder.name,
            'count': folder.count,
            'resource_url': folder.resource_url
        }

    def _serialize_collection_item(self, item) -> Dict[str, Any]:
        """Serialize a collection item."""
        return {
            'id': item.id,
            'instance_id': item.instance_id,
            'release': {
                'id': item.release.id,
                'title': item.release.title,
                'artists': [{'name': a.name} for a in item.release.artists],
                'year': item.release.year,
                'thumb': item.release.thumb
            },
            'rating': item.rating,
            'notes': item.notes,
            'date_added': item.date_added.isoformat() if hasattr(item.date_added, 'isoformat') else str(item.date_added)
        }

    def _serialize_want(self, want) -> Dict[str, Any]:
        """Serialize a wantlist item."""
        return {
            'id': want.id,
            'release': {
                'id': want.release.id,
                'title': want.release.title,
                'artists': [{'name': a.name} for a in want.release.artists],
                'year': want.release.year,
                'thumb': want.release.thumb
            },
            'rating': want.rating,
            'notes': want.notes,
            'date_added': want.date_added.isoformat() if hasattr(want.date_added, 'isoformat') else str(want.date_added)
        }

    def _serialize_listing(self, listing) -> Dict[str, Any]:
        """Serialize a marketplace listing."""
        return {
            'id': listing.id,
            'release': {
                'id': listing.release.id,
                'title': listing.release.title,
                'thumb': listing.release.thumb
            },
            'price': listing.price,
            'condition': listing.condition,
            'sleeve_condition': listing.sleeve_condition,
            'comments': listing.comments,
            'ships_from': listing.ships_from,
            'allow_offers': listing.allow_offers,
            'status': listing.status,
            'posted': listing.posted.isoformat() if hasattr(listing.posted, 'isoformat') else str(listing.posted),
            'uri': listing.uri,
            'resource_url': listing.resource_url
        }

    def _serialize_order(self, order) -> Dict[str, Any]:
        """Serialize an order."""
        return {
            'id': order.id,
            'status': order.status,
            'items': [
                {
                    'id': item.id,
                    'release': {'id': item.release.id, 'title': item.release.title},
                    'price': item.price,
                    'media_condition': item.media_condition,
                    'sleeve_condition': item.sleeve_condition
                }
                for item in order.items
            ],
            'total': order.total,
            'shipping': order.shipping,
            'fee': order.fee,
            'currency': order.currency,
            'created': order.created.isoformat() if hasattr(order.created, 'isoformat') else str(order.created),
            'last_activity': order.last_activity.isoformat() if hasattr(order.last_activity, 'isoformat') else str(order.last_activity),
            'buyer': {'username': order.buyer.username} if hasattr(order, 'buyer') else None,
            'seller': {'username': order.seller.username} if hasattr(order, 'seller') else None,
            'messages_url': order.messages_url,
            'uri': order.uri,
            'resource_url': order.resource_url
        }
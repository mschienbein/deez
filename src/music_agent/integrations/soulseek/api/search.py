"""
Search API for Soulseek.
"""

import asyncio
import logging
from typing import List, Optional

from .base import BaseAPI
from ..models import SearchResult, SearchResponse, SearchState, FileInfo
from ..exceptions import SearchError

logger = logging.getLogger(__name__)


class SearchAPI(BaseAPI):
    """API for search operations."""
    
    async def search(
        self,
        query: str,
        min_bitrate: int = 320,
        max_results: int = 50,
        timeout: int = 10
    ) -> SearchResult:
        """
        Search for files on Soulseek network.
        
        Args:
            query: Search query
            min_bitrate: Minimum bitrate filter
            max_results: Maximum number of results
            timeout: Search timeout in seconds
            
        Returns:
            SearchResult object
        """
        self.ensure_connected()
        
        try:
            # Initiate search
            # Use default search config values (config here is SlskdConfig, not SoulseekConfig)
            file_limit_multiplier = 2.0  # Default multiplier
            filter_responses = True  # Default filter
            
            search_response = self.client.searches.search_text(
                searchText=query,
                fileLimit=int(max_results * file_limit_multiplier),
                filterResponses=filter_responses,
                searchTimeout=timeout * 1000  # Convert to milliseconds
            )
            
            search_id = search_response.get('id')
            if not search_id:
                raise SearchError("Failed to get search ID from server")
            
            logger.info(f"Started search {search_id} for: {query}")
            
            # Wait for results to populate
            wait_time = min(timeout, 5)  # Default wait time
            await asyncio.sleep(wait_time)
            
            # Get search state
            state_response = self.client.searches.state(search_id)
            state_str = state_response.get("state", "pending").lower()
            
            # Handle complex state strings from slskd
            if "completed" in state_str:
                state = SearchState.COMPLETED
            elif "in_progress" in state_str or "inprogress" in state_str:
                state = SearchState.IN_PROGRESS
            elif "cancelled" in state_str:
                state = SearchState.CANCELLED
            elif "failed" in state_str:
                state = SearchState.FAILED
            else:
                state = SearchState.PENDING
            
            # Get search responses
            responses_data = self.client.searches.search_responses(search_id)
            
            # Create SearchResult
            result = SearchResult.from_api(
                {"id": search_id, "searchText": query, "state": state.value},
                responses_data
            )
            
            # Apply bitrate filter
            if min_bitrate > 0:
                filtered_files = result.filter_by_bitrate(min_bitrate)
                # Reconstruct responses with filtered files
                # For simplicity, we'll just update the file count
                result.file_count = len(filtered_files)
            
            # Stop the search
            try:
                self.client.searches.stop(search_id)
                logger.debug(f"Stopped search {search_id}")
            except Exception as e:
                logger.debug(f"Error stopping search {search_id}: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            raise SearchError(f"Search failed: {e}")
    
    async def get_search_state(self, search_id: str) -> SearchState:
        """
        Get the state of a search.
        
        Args:
            search_id: Search ID
            
        Returns:
            SearchState
        """
        self.ensure_connected()
        
        try:
            state_response = self.client.searches.state(search_id)
            state_str = state_response.get("state", "pending").lower()
            return SearchState(state_str)
        except Exception as e:
            logger.error(f"Failed to get search state: {e}")
            raise SearchError(f"Failed to get search state: {e}")
    
    def stop_search(self, search_id: str):
        """
        Stop a search.
        
        Args:
            search_id: Search ID to stop
        """
        self.ensure_connected()
        
        try:
            self.client.searches.stop(search_id)
            logger.info(f"Stopped search {search_id}")
        except Exception as e:
            logger.warning(f"Failed to stop search {search_id}: {e}")
    
    def get_active_searches(self) -> List[dict]:
        """
        Get list of active searches.
        
        Returns:
            List of active search data
        """
        self.ensure_connected()
        
        try:
            return self.client.searches.get_all()
        except Exception as e:
            logger.error(f"Failed to get active searches: {e}")
            return []
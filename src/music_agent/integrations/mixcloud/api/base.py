"""
Base API client for Mixcloud.

Provides common functionality for all API endpoints.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, TypeVar, Type
from urllib.parse import urlencode, urljoin
import aiohttp
from aiohttp import ClientSession, ClientError, ClientTimeout

from ..config import APIConfig
from ..auth.manager import AuthenticationManager
from ..exceptions import (
    APIError,
    NotFoundError,
    RateLimitError,
    ServerError,
    NetworkError,
    InvalidResponseError,
)
from ..models.base import BaseModel, PaginatedResult

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class BaseAPI:
    """Base class for Mixcloud API endpoints."""
    
    def __init__(
        self,
        session: ClientSession,
        config: APIConfig,
        auth_manager: Optional[AuthenticationManager] = None
    ):
        """
        Initialize base API.
        
        Args:
            session: aiohttp client session
            config: API configuration
            auth_manager: Optional authentication manager
        """
        self.session = session
        self.config = config
        self.auth_manager = auth_manager
        self.base_url = config.base_url
        
        # Rate limiting
        self._rate_limiter = asyncio.Semaphore(config.rate_limit)
        self._last_request_time = 0
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        authenticated: bool = False
    ) -> Dict[str, Any]:
        """
        Make an API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint path
            params: Query parameters
            data: Form data
            json: JSON data
            headers: Additional headers
            authenticated: Whether to include authentication
            
        Returns:
            API response data
        """
        # Build URL
        url = self._build_url(endpoint)
        
        # Build headers
        request_headers = {
            "User-Agent": self.config.user_agent,
        }
        
        if headers:
            request_headers.update(headers)
        
        # Add authentication if needed
        if authenticated and self.auth_manager:
            token = await self.auth_manager.get_access_token()
            request_headers["Authorization"] = f"Bearer {token}"
        
        # Apply rate limiting
        async with self._rate_limiter:
            # Add delay if needed
            await self._apply_rate_limit()
            
            # Make request with retry logic
            return await self._make_request_with_retry(
                method, url, params, data, json, request_headers
            )
    
    async def _make_request_with_retry(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Make request with retry logic.
        
        Args:
            method: HTTP method
            url: Full URL
            params: Query parameters
            data: Form data
            json: JSON data
            headers: Headers
            
        Returns:
            Response data
        """
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                # Log request
                logger.debug(f"API request: {method} {url}")
                
                # Make request
                timeout = ClientTimeout(total=self.config.timeout)
                async with self.session.request(
                    method,
                    url,
                    params=params,
                    data=data,
                    json=json,
                    headers=headers,
                    timeout=timeout
                ) as response:
                    # Check status
                    if response.status == 404:
                        raise NotFoundError(f"Resource not found: {url}")
                    elif response.status == 429:
                        retry_after = response.headers.get("Retry-After", "60")
                        raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after}s")
                    elif response.status >= 500:
                        raise ServerError(f"Server error: {response.status}")
                    elif response.status >= 400:
                        error_text = await response.text()
                        raise APIError(f"API error {response.status}: {error_text}")
                    
                    # Parse response
                    content_type = response.headers.get("Content-Type", "")
                    
                    # Try to parse as JSON first
                    text = await response.text()
                    try:
                        import json
                        return json.loads(text)
                    except (json.JSONDecodeError, ValueError):
                        # If not JSON, check content type
                        if "application/json" in content_type:
                            # Expected JSON but couldn't parse
                            raise InvalidResponseError(f"Invalid JSON response: {text[:200]}")
                        else:
                            # Return as text wrapped in dict
                            return {"response": text, "_raw": True}
            
            except (ClientError, asyncio.TimeoutError) as e:
                last_error = NetworkError(f"Network error: {e}")
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.config.max_retries}): {e}")
                
                # Wait before retry
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
            
            except (RateLimitError, ServerError) as e:
                last_error = e
                logger.warning(f"API error (attempt {attempt + 1}/{self.config.max_retries}): {e}")
                
                # Wait longer for rate limit or server errors
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (3 ** attempt))
            
            except Exception as e:
                # Don't retry on other exceptions
                raise APIError(f"Unexpected error: {e}")
        
        # Raise last error after all retries
        if last_error:
            raise last_error
        else:
            raise APIError("Request failed after all retries")
    
    async def _get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        authenticated: bool = False
    ) -> Dict[str, Any]:
        """Make GET request."""
        return await self._request("GET", endpoint, params=params, authenticated=authenticated)
    
    async def _post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        authenticated: bool = True
    ) -> Dict[str, Any]:
        """Make POST request."""
        return await self._request("POST", endpoint, data=data, json=json, authenticated=authenticated)
    
    async def _delete(
        self,
        endpoint: str,
        authenticated: bool = True
    ) -> Dict[str, Any]:
        """Make DELETE request."""
        return await self._request("DELETE", endpoint, authenticated=authenticated)
    
    def _build_url(self, endpoint: str) -> str:
        """
        Build full URL from endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Full URL
        """
        # Remove leading slash if present
        endpoint = endpoint.lstrip("/")
        
        # Add trailing slash if not present (Mixcloud API requires it)
        if not endpoint.endswith("/"):
            endpoint += "/"
        
        return urljoin(self.base_url, endpoint)
    
    async def _apply_rate_limit(self):
        """Apply rate limiting between requests."""
        import time
        
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        min_interval = 1.0 / self.config.rate_limit
        
        if time_since_last < min_interval:
            await asyncio.sleep(min_interval - time_since_last)
        
        self._last_request_time = time.time()
    
    async def _get_paginated(
        self,
        endpoint: str,
        model_class: Type[T],
        params: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0,
        authenticated: bool = False
    ) -> PaginatedResult:
        """
        Get paginated results.
        
        Args:
            endpoint: API endpoint
            model_class: Model class to instantiate
            params: Query parameters
            limit: Results per page
            offset: Results offset
            authenticated: Whether to authenticate
            
        Returns:
            Paginated result
        """
        # Add pagination params
        if params is None:
            params = {}
        params["limit"] = limit
        params["offset"] = offset
        
        # Make request
        data = await self._get(endpoint, params, authenticated)
        
        # Parse results
        items = []
        results_key = "data" if "data" in data else "results"
        if results_key in data:
            for item_data in data[results_key]:
                items.append(model_class(item_data))
        
        # Get pagination info
        paging = data.get("paging", {})
        
        return PaginatedResult(
            items=items,
            total=data.get("total_results"),
            next_url=paging.get("next"),
            previous_url=paging.get("previous"),
            page=(offset // limit) + 1 if limit else 1,
            per_page=limit
        )


__all__ = ["BaseAPI"]
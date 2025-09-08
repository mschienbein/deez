"""
Base API class for Deezer.
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from ..config import APIConfig
from ..exceptions import APIError, RateLimitError, NotFoundError

logger = logging.getLogger(__name__)


class BaseAPI:
    """Base class for Deezer API endpoints."""
    
    def __init__(
        self,
        session: ClientSession,
        config: APIConfig,
        auth_manager: Optional[Any] = None
    ):
        """
        Initialize base API.
        
        Args:
            session: aiohttp session
            config: API configuration
            auth_manager: Optional authentication manager
        """
        self.session = session
        self.config = config
        self.auth_manager = auth_manager
        self._rate_limiter = asyncio.Semaphore(config.rate_limit)
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        use_gateway: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make an API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON data for POST requests
            use_gateway: Use gateway API instead of public API
            **kwargs: Additional request arguments
            
        Returns:
            API response
            
        Raises:
            APIError: If request fails
        """
        async with self._rate_limiter:
            # Determine base URL
            if use_gateway:
                base_url = self.config.gateway_url
                # Add authentication token if available
                if self.auth_manager and self.auth_manager.is_authenticated:
                    if params is None:
                        params = {}
                    params["api_token"] = self.auth_manager.get_api_token()
                    params["input"] = "3"
                    params["api_version"] = "1.0"
            else:
                base_url = self.config.api_base
            
            # Build full URL
            if use_gateway:
                url = base_url
                if params and "method" in params:
                    params_copy = params.copy()
                    method_name = params_copy.pop("method")
                    url = f"{base_url}?method={method_name}"
                    for key, value in params_copy.items():
                        url += f"&{key}={value}"
            else:
                url = urljoin(base_url + "/", endpoint.lstrip("/"))
            
            # Set timeout
            timeout = ClientTimeout(total=self.config.timeout)
            
            # Prepare headers
            headers = {
                "User-Agent": self.config.user_agent,
            }
            
            # Retry logic
            last_error = None
            for attempt in range(self.config.max_retries):
                try:
                    async with self.session.request(
                        method,
                        url,
                        params=params if not use_gateway else None,
                        json=json_data,
                        headers=headers,
                        timeout=timeout,
                        **kwargs
                    ) as response:
                        # Handle rate limiting
                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", 60))
                            raise RateLimitError(
                                f"Rate limit exceeded, retry after {retry_after}s",
                                status_code=429
                            )
                        
                        # Handle not found
                        if response.status == 404:
                            raise NotFoundError(
                                f"Resource not found: {url}",
                                status_code=404
                            )
                        
                        # Handle other errors
                        if response.status >= 400:
                            error_text = await response.text()
                            raise APIError(
                                f"API request failed: {response.status} - {error_text}",
                                status_code=response.status
                            )
                        
                        # Parse response
                        data = await response.json()
                        
                        # Check for API errors in response
                        if use_gateway and data.get("error"):
                            error = data["error"]
                            if isinstance(error, dict):
                                error_code = error.get("code")
                                error_msg = error.get("message", "Unknown error")
                                
                                # Handle specific error codes
                                if error_code == "INVALID_TOKEN":
                                    # Try to refresh authentication
                                    if self.auth_manager:
                                        await self.auth_manager.refresh_token()
                                        # Retry the request
                                        continue
                                
                                raise APIError(f"API error {error_code}: {error_msg}")
                        
                        return data
                
                except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                    last_error = e
                    if attempt < self.config.max_retries - 1:
                        await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                    else:
                        raise APIError(f"Request failed after {self.config.max_retries} attempts: {e}")
            
            if last_error:
                raise APIError(f"Request failed: {last_error}")
    
    async def get(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a GET request."""
        return await self._request("GET", endpoint, **kwargs)
    
    async def post(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a POST request."""
        return await self._request("POST", endpoint, **kwargs)
    
    async def gateway_call(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a gateway API call.
        
        Args:
            method: Gateway method name
            params: Method parameters
            
        Returns:
            API response
        """
        request_params = {"method": method}
        return await self._request(
            "POST",
            "",
            params=request_params,
            json_data=params or {},
            use_gateway=True
        )
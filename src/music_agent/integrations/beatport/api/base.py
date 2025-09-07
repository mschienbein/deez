"""
Base API client for Beatport.
"""

import time
from typing import Optional, Dict, Any, List
import requests
from urllib.parse import urljoin

from ..auth import BeatportAuth
from ..config import BeatportConfig
from ..exceptions import (
    APIError, RateLimitError, NotFoundError,
    NetworkError, TokenExpiredError
)


class BaseAPI:
    """Base API client with common functionality."""
    
    def __init__(self, auth: BeatportAuth, config: BeatportConfig):
        """
        Initialize base API client.
        
        Args:
            auth: Authentication handler
            config: API configuration
        """
        self.auth = auth
        self.config = config
        self.session = requests.Session()
        self._last_request_time = 0
    
    def _get_url(self, endpoint: str) -> str:
        """
        Build full URL for endpoint.
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Full URL
        """
        # Base URL should be https://api.beatport.com/v4
        base = f"{self.config.base_url}/{self.config.api_version}/"
        
        # Ensure endpoint doesn't start with /
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
        
        # Don't use urljoin as it can mess up the path
        return base + endpoint
    
    def _apply_rate_limit(self) -> None:
        """Apply rate limiting between requests."""
        if self.config.rate_limit_delay > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.config.rate_limit_delay:
                time.sleep(self.config.rate_limit_delay - elapsed)
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response.
        
        Args:
            response: HTTP response
            
        Returns:
            Response data
            
        Raises:
            Various API exceptions based on status
        """
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            raise TokenExpiredError("Authentication token expired")
        elif response.status_code == 404:
            raise NotFoundError("Resource not found")
        elif response.status_code == 429:
            retry_after = response.headers.get('Retry-After')
            raise RateLimitError(
                "Rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None
            )
        else:
            try:
                error_data = response.json()
                message = error_data.get('detail', 'API request failed')
            except:
                message = f"API request failed with status {response.status_code}"
            raise APIError(message, status_code=response.status_code)
    
    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        retry_on_401: bool = True
    ) -> Dict[str, Any]:
        """
        Make API request with retries.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            retry_on_401: Whether to retry on 401 with token refresh
            
        Returns:
            Response data
            
        Raises:
            Various API exceptions
        """
        url = self._get_url(endpoint)
        headers = self.auth.get_headers()
        
        # Apply rate limiting
        self._apply_rate_limit()
        
        retries = 0
        while retries <= self.config.max_retries:
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=data,
                    timeout=self.config.timeout
                )
                
                self._last_request_time = time.time()
                
                # Handle 401 with token refresh
                if response.status_code == 401 and retry_on_401:
                    try:
                        self.auth.refresh_token()
                        headers = self.auth.get_headers()
                        retry_on_401 = False  # Only try refresh once
                        continue
                    except:
                        pass  # Fall through to normal error handling
                
                return self._handle_response(response)
                
            except requests.Timeout:
                raise NetworkError("Request timed out")
            except requests.ConnectionError as e:
                if retries < self.config.max_retries:
                    time.sleep(self.config.retry_delay * (2 ** retries))
                    retries += 1
                else:
                    raise NetworkError(f"Connection failed: {e}")
            except TokenExpiredError:
                if retry_on_401:
                    try:
                        self.auth.refresh_token()
                        headers = self.auth.get_headers()
                        retry_on_401 = False
                        continue
                    except:
                        raise
                raise
            except RateLimitError as e:
                if e.retry_after and retries < self.config.max_retries:
                    time.sleep(e.retry_after)
                    retries += 1
                else:
                    raise
    
    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make GET request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data
        """
        return self._request('GET', endpoint, params=params)
    
    def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make POST request.
        
        Args:
            endpoint: API endpoint
            data: Request body
            params: Query parameters
            
        Returns:
            Response data
        """
        return self._request('POST', endpoint, data=data, params=params)
    
    def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make PUT request.
        
        Args:
            endpoint: API endpoint
            data: Request body
            params: Query parameters
            
        Returns:
            Response data
        """
        return self._request('PUT', endpoint, data=data, params=params)
    
    def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make DELETE request.
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            Response data
        """
        return self._request('DELETE', endpoint, params=params)
    
    def paginate(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        max_pages: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Paginate through API results.
        
        Args:
            endpoint: API endpoint
            params: Initial parameters
            max_pages: Maximum pages to fetch
            
        Returns:
            List of all results
        """
        if params is None:
            params = {}
        
        all_results = []
        page = 1
        
        while True:
            params['page'] = page
            params['per_page'] = params.get('per_page', self.config.default_per_page)
            
            response = self.get(endpoint, params)
            
            # Extract results (handle different response formats)
            if 'results' in response:
                results = response['results']
            elif 'data' in response:
                results = response['data']
            else:
                results = [response]
            
            all_results.extend(results)
            
            # Check for more pages
            if 'next' not in response or not response['next']:
                break
            
            if max_pages and page >= max_pages:
                break
            
            page += 1
        
        return all_results
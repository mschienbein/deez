"""
OAuth2 implementation for Mixcloud.

Handles the OAuth2 authorization code flow.
"""

import asyncio
import logging
import secrets
import webbrowser
from typing import Optional, Dict, Any
from urllib.parse import urlencode, parse_qs, urlparse
import aiohttp
from aiohttp import web

from ..config import AuthConfig
from ..types import TokenResponse, AuthCredentials
from ..exceptions import OAuthError, AuthenticationError

logger = logging.getLogger(__name__)


class OAuth2Handler:
    """Handles OAuth2 authentication flow for Mixcloud."""
    
    AUTHORIZE_URL = "https://www.mixcloud.com/oauth/authorize"
    TOKEN_URL = "https://www.mixcloud.com/oauth/access_token"
    
    def __init__(self, config: AuthConfig):
        """
        Initialize OAuth2 handler.
        
        Args:
            config: Authentication configuration
        """
        self.config = config
        self.state = None
        self.authorization_code = None
        self.callback_received = asyncio.Event()
        
    async def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        Get the authorization URL for user consent.
        
        Args:
            state: Optional state parameter for security
            
        Returns:
            Authorization URL
        """
        if not self.config.client_id:
            raise AuthenticationError("Client ID not configured")
        
        # Generate state if not provided
        self.state = state or secrets.token_urlsafe(32)
        
        # Build authorization URL
        params = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "state": self.state,
        }
        
        # Add scope if configured
        if self.config.scope:
            params["scope"] = self.config.scope
        
        url = f"{self.AUTHORIZE_URL}?{urlencode(params)}"
        logger.debug(f"Authorization URL: {url}")
        
        return url
    
    async def exchange_code_for_token(self, code: str) -> TokenResponse:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from callback
            
        Returns:
            Token response with access token
        """
        if not self.config.client_id or not self.config.client_secret:
            raise AuthenticationError("Client credentials not configured")
        
        # Prepare token request
        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.config.redirect_uri,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.TOKEN_URL, data=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise OAuthError(f"Token exchange failed: {error_text}")
                    
                    token_data = await response.json()
                    
                    # Validate token response
                    if "access_token" not in token_data:
                        raise OAuthError("No access token in response")
                    
                    return TokenResponse(
                        access_token=token_data["access_token"],
                        token_type=token_data.get("token_type", "Bearer"),
                        expires_in=token_data.get("expires_in"),
                        refresh_token=token_data.get("refresh_token"),
                        scope=token_data.get("scope")
                    )
                    
        except aiohttp.ClientError as e:
            raise OAuthError(f"Network error during token exchange: {e}")
    
    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """
        Refresh an expired access token.
        
        Args:
            refresh_token: Refresh token
            
        Returns:
            New token response
        """
        if not self.config.client_id or not self.config.client_secret:
            raise AuthenticationError("Client credentials not configured")
        
        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.TOKEN_URL, data=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise OAuthError(f"Token refresh failed: {error_text}")
                    
                    token_data = await response.json()
                    
                    return TokenResponse(
                        access_token=token_data["access_token"],
                        token_type=token_data.get("token_type", "Bearer"),
                        expires_in=token_data.get("expires_in"),
                        refresh_token=token_data.get("refresh_token", refresh_token),
                        scope=token_data.get("scope")
                    )
                    
        except aiohttp.ClientError as e:
            raise OAuthError(f"Network error during token refresh: {e}")
    
    async def authorize_interactive(self, open_browser: bool = True) -> str:
        """
        Perform interactive OAuth2 authorization.
        
        Args:
            open_browser: Whether to automatically open browser
            
        Returns:
            Access token
        """
        # Get authorization URL
        auth_url = await self.get_authorization_url()
        
        # Start local callback server
        callback_server = CallbackServer(self)
        server_task = asyncio.create_task(callback_server.start())
        
        try:
            # Open browser if requested
            if open_browser:
                logger.info(f"Opening browser for authorization...")
                webbrowser.open(auth_url)
            else:
                logger.info(f"Please visit this URL to authorize: {auth_url}")
            
            # Wait for callback
            await asyncio.wait_for(self.callback_received.wait(), timeout=300)
            
            if not self.authorization_code:
                raise OAuthError("No authorization code received")
            
            # Exchange code for token
            token_response = await self.exchange_code_for_token(self.authorization_code)
            
            return token_response["access_token"]
            
        finally:
            # Stop callback server
            await callback_server.stop()
            server_task.cancel()
            try:
                await server_task
            except asyncio.CancelledError:
                pass
    
    def handle_callback(self, url: str) -> Optional[str]:
        """
        Handle OAuth callback URL.
        
        Args:
            url: Callback URL with parameters
            
        Returns:
            Authorization code if successful
        """
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # Check state parameter
        if "state" in params:
            if params["state"][0] != self.state:
                raise OAuthError("State parameter mismatch - possible CSRF attack")
        
        # Check for error
        if "error" in params:
            error = params["error"][0]
            error_desc = params.get("error_description", ["Unknown error"])[0]
            raise OAuthError(f"Authorization failed: {error} - {error_desc}")
        
        # Get authorization code
        if "code" not in params:
            raise OAuthError("No authorization code in callback")
        
        self.authorization_code = params["code"][0]
        self.callback_received.set()
        
        return self.authorization_code


class CallbackServer:
    """Local HTTP server for OAuth callback."""
    
    def __init__(self, oauth_handler: OAuth2Handler):
        """
        Initialize callback server.
        
        Args:
            oauth_handler: OAuth2 handler instance
        """
        self.oauth_handler = oauth_handler
        self.app = web.Application()
        self.runner = None
        self.site = None
        
        # Setup routes
        self.app.router.add_get("/callback", self.handle_callback)
        self.app.router.add_get("/", self.handle_root)
    
    async def start(self):
        """Start the callback server."""
        # Parse redirect URI to get port
        parsed = urlparse(self.oauth_handler.config.redirect_uri)
        port = parsed.port or 8080
        
        # Start server
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "localhost", port)
        await self.site.start()
        
        logger.debug(f"Callback server started on port {port}")
    
    async def stop(self):
        """Stop the callback server."""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
        
        logger.debug("Callback server stopped")
    
    async def handle_callback(self, request: web.Request) -> web.Response:
        """Handle OAuth callback request."""
        try:
            # Build full URL with query parameters
            url = str(request.url)
            
            # Handle callback
            self.oauth_handler.handle_callback(url)
            
            # Return success page
            html = """
            <html>
            <head>
                <title>Authorization Successful</title>
                <style>
                    body { font-family: Arial; text-align: center; padding: 50px; }
                    .success { color: green; font-size: 24px; }
                </style>
            </head>
            <body>
                <div class="success">✓ Authorization successful!</div>
                <p>You can close this window and return to the application.</p>
            </body>
            </html>
            """
            return web.Response(text=html, content_type="text/html")
            
        except Exception as e:
            logger.error(f"Callback error: {e}")
            
            # Return error page
            html = f"""
            <html>
            <head>
                <title>Authorization Failed</title>
                <style>
                    body {{ font-family: Arial; text-align: center; padding: 50px; }}
                    .error {{ color: red; font-size: 24px; }}
                </style>
            </head>
            <body>
                <div class="error">✗ Authorization failed</div>
                <p>{str(e)}</p>
            </body>
            </html>
            """
            return web.Response(text=html, content_type="text/html", status=400)
    
    async def handle_root(self, request: web.Request) -> web.Response:
        """Handle root request."""
        html = """
        <html>
        <head>
            <title>Mixcloud OAuth</title>
        </head>
        <body>
            <h1>Mixcloud OAuth Callback Server</h1>
            <p>Waiting for authorization callback...</p>
        </body>
        </html>
        """
        return web.Response(text=html, content_type="text/html")


__all__ = ["OAuth2Handler", "CallbackServer"]
"""
Tool Registry - Centralized Tool Management

Provides intelligent discovery, registration, and management of all music agent tools.
Supports dynamic loading, categorization, and filtering of tools across all integrations.
"""

import logging
import inspect
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ToolCategory(Enum):
    """Tool categories for organization and filtering."""
    CORE = "core"
    SEARCH = "search"
    DOWNLOAD = "download"
    METADATA = "metadata"
    PLAYLIST = "playlist"
    STREAMING = "streaming"
    ANALYTICS = "analytics"
    DISCOVERY = "discovery"
    MARKETPLACE = "marketplace"
    SOCIAL = "social"
    UTILITY = "utility"


class IntegrationPlatform(Enum):
    """Supported integration platforms."""
    MULTI_PLATFORM = "multi_platform"
    DEEZER = "deezer"
    SPOTIFY = "spotify"
    YOUTUBE = "youtube"
    SOUNDCLOUD = "soundcloud"
    BANDCAMP = "bandcamp"
    SOULSEEK = "soulseek"
    DISCOGS = "discogs"
    TRACKLISTS_1001 = "tracklists_1001"
    BEATPORT = "beatport"
    MIXCLOUD = "mixcloud"
    REKORDBOX = "rekordbox"
    GRAPHITI_MEMORY = "graphiti_memory"


@dataclass
class ToolInfo:
    """Metadata about a registered tool."""
    name: str
    function: Callable
    category: ToolCategory
    platform: IntegrationPlatform
    description: str
    deprecated: bool = False
    requires_auth: bool = False
    requires_config: bool = False
    dependencies: List[str] = None
    version: str = "1.0.0"
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class ToolRegistry:
    """
    Centralized registry for all music agent tools.
    
    Provides intelligent tool discovery, registration, and management
    with support for categorization, filtering, and dependency tracking.
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolInfo] = {}
        self._categories: Dict[ToolCategory, List[str]] = {}
        self._platforms: Dict[IntegrationPlatform, List[str]] = {}
        self._failed_imports: Set[str] = set()
        
        # Initialize category and platform dictionaries
        for category in ToolCategory:
            self._categories[category] = []
        for platform in IntegrationPlatform:
            self._platforms[platform] = []
    
    def register_tool(
        self,
        name: str,
        function: Callable,
        category: ToolCategory,
        platform: IntegrationPlatform,
        description: str = None,
        **kwargs
    ) -> bool:
        """
        Register a tool with the registry.
        
        Args:
            name: Tool name (should be unique)
            function: Tool function
            category: Tool category
            platform: Integration platform
            description: Tool description
            **kwargs: Additional tool metadata
        
        Returns:
            True if registered successfully, False otherwise
        """
        try:
            if name in self._tools:
                logger.warning(f"Tool '{name}' already registered, overwriting")
            
            # Auto-generate description from docstring if not provided
            if description is None and function.__doc__:
                description = function.__doc__.strip().split('\n')[0]
            elif description is None:
                description = f"Tool function: {name}"
            
            tool_info = ToolInfo(
                name=name,
                function=function,
                category=category,
                platform=platform,
                description=description,
                **kwargs
            )
            
            self._tools[name] = tool_info
            self._categories[category].append(name)
            self._platforms[platform].append(name)
            
            logger.debug(f"Registered tool: {name} ({category.value}/{platform.value})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register tool '{name}': {e}")
            return False
    
    def auto_discover_tools(self) -> int:
        """
        Automatically discover and register all available tools.
        
        Returns:
            Number of tools successfully registered
        """
        registered_count = 0
        
        # Register core tools
        registered_count += self._register_core_tools()
        
        # Register integration-specific tools
        registered_count += self._register_integration_tools()
        
        # Register legacy tools for backward compatibility
        registered_count += self._register_legacy_tools()
        
        logger.info(f"Auto-discovered and registered {registered_count} tools")
        return registered_count
    
    def _register_core_tools(self) -> int:
        """Register core multi-platform tools."""
        count = 0
        
        try:
            from .core import (
                search_music,
                match_track_across_platforms,
                search_and_download,
                create_cross_platform_playlist,
                export_playlist,
                get_track_info,
                analyze_music_trends
            )
            
            core_tools = [
                (search_music, ToolCategory.SEARCH, "Search music across all platforms"),
                (match_track_across_platforms, ToolCategory.SEARCH, "Find same track across platforms"),
                (search_and_download, ToolCategory.DOWNLOAD, "Search and download with intelligent routing"),
                (create_cross_platform_playlist, ToolCategory.PLAYLIST, "Create playlists from multiple platforms"),
                (export_playlist, ToolCategory.PLAYLIST, "Export playlists in various formats"),
                (get_track_info, ToolCategory.METADATA, "Get track metadata from any platform"),
                (analyze_music_trends, ToolCategory.ANALYTICS, "Analyze listening patterns and trends")
            ]
            
            for func, category, desc in core_tools:
                if self.register_tool(
                    func.__name__, 
                    func, 
                    category, 
                    IntegrationPlatform.MULTI_PLATFORM,
                    desc
                ):
                    count += 1
                    
        except ImportError as e:
            logger.warning(f"Failed to import core tools: {e}")
            self._failed_imports.add("core")
        
        return count
    
    def _register_integration_tools(self) -> int:
        """Register integration-specific tools."""
        count = 0
        
        # Deezer tools
        count += self._register_deezer_tools()
        
        # Soulseek tools
        count += self._register_soulseek_tools()
        
        # Discogs tools
        count += self._register_discogs_tools()
        
        # 1001 Tracklists tools
        count += self._register_tracklists_tools()
        
        return count
    
    def _register_deezer_tools(self) -> int:
        """Register Deezer integration tools."""
        count = 0
        
        try:
            from .integrations.deezer import (
                search_deezer_tracks,
                search_deezer_albums,
                download_deezer_track,
                get_deezer_track_info
            )
            
            deezer_tools = [
                (search_deezer_tracks, ToolCategory.SEARCH, "Search tracks on Deezer"),
                (search_deezer_albums, ToolCategory.SEARCH, "Search albums on Deezer"),
                (download_deezer_track, ToolCategory.DOWNLOAD, "Download tracks from Deezer", {"requires_auth": True}),
                (get_deezer_track_info, ToolCategory.METADATA, "Get track metadata from Deezer")
            ]
            
            for item in deezer_tools:
                func, category, desc = item[:3]
                kwargs = item[3] if len(item) > 3 else {}
                
                if self.register_tool(
                    func.__name__, 
                    func, 
                    category, 
                    IntegrationPlatform.DEEZER,
                    desc,
                    **kwargs
                ):
                    count += 1
                    
        except ImportError as e:
            logger.warning(f"Failed to import Deezer tools: {e}")
            self._failed_imports.add("deezer")
        
        return count
    
    def _register_soulseek_tools(self) -> int:
        """Register Soulseek integration tools."""
        count = 0
        
        try:
            from .integrations.soulseek import (
                soulseek_search,
                soulseek_download,
                soulseek_discover,
                soulseek_user_info,
                soulseek_browse_user
            )
            
            soulseek_tools = [
                (soulseek_search, ToolCategory.SEARCH, "Search P2P network via Soulseek", {"requires_config": True}),
                (soulseek_download, ToolCategory.DOWNLOAD, "Download from Soulseek P2P", {"requires_config": True}),
                (soulseek_discover, ToolCategory.DISCOVERY, "Discover music via Soulseek", {"requires_config": True}),
                (soulseek_user_info, ToolCategory.SOCIAL, "Get Soulseek user information", {"requires_config": True}),
                (soulseek_browse_user, ToolCategory.SOCIAL, "Browse Soulseek user files", {"requires_config": True})
            ]
            
            for func, category, desc, kwargs in soulseek_tools:
                if self.register_tool(
                    func.__name__, 
                    func, 
                    category, 
                    IntegrationPlatform.SOULSEEK,
                    desc,
                    **kwargs
                ):
                    count += 1
                    
        except ImportError as e:
            logger.warning(f"Failed to import Soulseek tools: {e}")
            self._failed_imports.add("soulseek")
        
        return count
    
    def _register_discogs_tools(self) -> int:
        """Register Discogs integration tools."""
        count = 0
        
        try:
            from .integrations.discogs import (
                discogs_search,
                discogs_get_release,
                discogs_get_master,
                discogs_get_artist,
                discogs_get_label,
                discogs_search_marketplace,
                discogs_get_listing
            )
            
            discogs_tools = [
                (discogs_search, ToolCategory.SEARCH, "Search Discogs database"),
                (discogs_get_release, ToolCategory.METADATA, "Get release details from Discogs"),
                (discogs_get_master, ToolCategory.METADATA, "Get master release from Discogs"),
                (discogs_get_artist, ToolCategory.METADATA, "Get artist info from Discogs"),
                (discogs_get_label, ToolCategory.METADATA, "Get label info from Discogs"),
                (discogs_search_marketplace, ToolCategory.MARKETPLACE, "Search Discogs marketplace"),
                (discogs_get_listing, ToolCategory.MARKETPLACE, "Get marketplace listing details")
            ]
            
            for func, category, desc in discogs_tools:
                if self.register_tool(
                    func.__name__, 
                    func, 
                    category, 
                    IntegrationPlatform.DISCOGS,
                    desc
                ):
                    count += 1
                    
        except ImportError as e:
            logger.warning(f"Failed to import Discogs tools: {e}")
            self._failed_imports.add("discogs")
        
        return count
    
    def _register_tracklists_tools(self) -> int:
        """Register 1001 Tracklists integration tools."""
        count = 0
        
        try:
            from .integrations.tracklists_1001 import (
                get_1001_tracklist,
                analyze_dj_style,
                discover_festival_tracks,
                get_tracklist,
                search_tracklists,
                get_dj_recent_sets,
                extract_track_list,
                find_common_tracks,
                export_as_playlist
            )
            
            tracklist_tools = [
                (get_1001_tracklist, ToolCategory.METADATA, "Get advanced DJ set tracklist"),
                (analyze_dj_style, ToolCategory.ANALYTICS, "Analyze DJ mixing style"),
                (discover_festival_tracks, ToolCategory.DISCOVERY, "Discover trending festival tracks"),
                (get_tracklist, ToolCategory.METADATA, "Get simple DJ set tracklist"),
                (search_tracklists, ToolCategory.SEARCH, "Search 1001 Tracklists"),
                (get_dj_recent_sets, ToolCategory.SEARCH, "Get DJ's recent sets"),
                (extract_track_list, ToolCategory.UTILITY, "Extract clean track list"),
                (find_common_tracks, ToolCategory.ANALYTICS, "Find common tracks across sets"),
                (export_as_playlist, ToolCategory.PLAYLIST, "Export tracklist as playlist")
            ]
            
            for func, category, desc in tracklist_tools:
                if self.register_tool(
                    func.__name__, 
                    func, 
                    category, 
                    IntegrationPlatform.TRACKLISTS_1001,
                    desc
                ):
                    count += 1
                    
        except ImportError as e:
            logger.warning(f"Failed to import 1001 Tracklists tools: {e}")
            self._failed_imports.add("tracklists_1001")
        
        return count
    
    def _register_legacy_tools(self) -> int:
        """Register legacy tools for backward compatibility."""
        count = 0
        
        try:
            from .download_tool import download_track
            
            if self.register_tool(
                download_track.__name__,
                download_track,
                ToolCategory.DOWNLOAD,
                IntegrationPlatform.DEEZER,
                "Legacy download tool (Deezer only)",
                deprecated=True
            ):
                count += 1
                
        except ImportError as e:
            logger.debug(f"Legacy tools not available: {e}")
        
        return count
    
    def get_all_tools(self) -> List[Callable]:
        """Get all registered tool functions."""
        return [tool_info.function for tool_info in self._tools.values()]
    
    def get_tools_by_category(self, category: ToolCategory) -> List[Callable]:
        """Get tools filtered by category."""
        tool_names = self._categories.get(category, [])
        return [self._tools[name].function for name in tool_names if name in self._tools]
    
    def get_tools_by_platform(self, platform: IntegrationPlatform) -> List[Callable]:
        """Get tools filtered by platform."""
        tool_names = self._platforms.get(platform, [])
        return [self._tools[name].function for name in tool_names if name in self._tools]
    
    def get_tools_by_filter(
        self, 
        categories: Optional[List[ToolCategory]] = None,
        platforms: Optional[List[IntegrationPlatform]] = None,
        include_deprecated: bool = False,
        requires_auth: Optional[bool] = None,
        requires_config: Optional[bool] = None
    ) -> List[Callable]:
        """Get tools with advanced filtering."""
        filtered_tools = []
        
        for tool_info in self._tools.values():
            # Filter by category
            if categories and tool_info.category not in categories:
                continue
            
            # Filter by platform
            if platforms and tool_info.platform not in platforms:
                continue
            
            # Filter deprecated tools
            if not include_deprecated and tool_info.deprecated:
                continue
            
            # Filter by auth requirement
            if requires_auth is not None and tool_info.requires_auth != requires_auth:
                continue
            
            # Filter by config requirement
            if requires_config is not None and tool_info.requires_config != requires_config:
                continue
            
            filtered_tools.append(tool_info.function)
        
        return filtered_tools
    
    def get_tool_info(self, name: str) -> Optional[ToolInfo]:
        """Get detailed information about a tool."""
        return self._tools.get(name)
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about the tool registry."""
        stats = {
            "total_tools": len(self._tools),
            "by_category": {cat.value: len(tools) for cat, tools in self._categories.items() if tools},
            "by_platform": {plat.value: len(tools) for plat, tools in self._platforms.items() if tools},
            "deprecated_tools": sum(1 for tool in self._tools.values() if tool.deprecated),
            "auth_required_tools": sum(1 for tool in self._tools.values() if tool.requires_auth),
            "config_required_tools": sum(1 for tool in self._tools.values() if tool.requires_config),
            "failed_imports": list(self._failed_imports)
        }
        return stats
    
    def list_available_tools(self, detailed: bool = False) -> Dict[str, Any]:
        """List all available tools with optional details."""
        if detailed:
            return {
                name: {
                    "category": tool.category.value,
                    "platform": tool.platform.value,
                    "description": tool.description,
                    "deprecated": tool.deprecated,
                    "requires_auth": tool.requires_auth,
                    "requires_config": tool.requires_config,
                    "version": tool.version
                }
                for name, tool in self._tools.items()
            }
        else:
            return {
                name: tool.description 
                for name, tool in self._tools.items()
            }


# Global registry instance
_registry = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _registry.auto_discover_tools()
    return _registry


def get_all_tools() -> List[Callable]:
    """Convenience function to get all registered tools."""
    return get_tool_registry().get_all_tools()


def get_tools_by_category(category: ToolCategory) -> List[Callable]:
    """Convenience function to get tools by category."""
    return get_tool_registry().get_tools_by_category(category)


def get_tools_by_platform(platform: IntegrationPlatform) -> List[Callable]:
    """Convenience function to get tools by platform."""
    return get_tool_registry().get_tools_by_platform(platform)


def get_registry_stats() -> Dict[str, Any]:
    """Convenience function to get registry statistics."""
    return get_tool_registry().get_registry_stats()


def list_available_tools(detailed: bool = False) -> Dict[str, Any]:
    """Convenience function to list available tools."""
    return get_tool_registry().list_available_tools(detailed)
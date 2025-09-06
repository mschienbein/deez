"""
Comprehensive tools management for the music agent.
"""

import logging
from typing import List, Any, Dict, Optional
from enum import Enum

from .standard_tools import StandardToolsProvider
from ...tools.registry import (
    get_tool_registry,
    ToolCategory,
    IntegrationPlatform,
    get_registry_stats
)

logger = logging.getLogger(__name__)


class ToolsProfile(Enum):
    """Predefined tool profiles for different use cases."""
    MINIMAL = "minimal"          # Basic tools only
    STANDARD = "standard"        # Standard + core music tools
    FULL = "full"               # All available tools
    SEARCH_FOCUSED = "search"    # Search and metadata tools
    DOWNLOAD_FOCUSED = "download" # Download and file tools
    ANALYTICS_FOCUSED = "analytics" # Analytics and discovery tools


class ToolsManager:
    """
    Manages tool selection, filtering, and provisioning for the music agent.
    
    Provides intelligent tool management with support for profiles, filtering,
    and dynamic tool selection based on requirements.
    """
    
    def __init__(self):
        self.standard_tools_provider = StandardToolsProvider()
        self.tool_registry = get_tool_registry()
        self._cache = {}
    
    def get_tools_by_profile(self, profile: ToolsProfile) -> List[Any]:
        """
        Get tools based on a predefined profile.
        
        Args:
            profile: Tool profile to use
        
        Returns:
            List of tool functions for the profile
        """
        cache_key = f"profile_{profile.value}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        tools = []
        
        if profile == ToolsProfile.MINIMAL:
            tools = self.standard_tools_provider.get_basic_tools()
            
        elif profile == ToolsProfile.STANDARD:
            tools = self.standard_tools_provider.get_standard_tools()
            tools.extend(self.tool_registry.get_tools_by_platform(IntegrationPlatform.MULTI_PLATFORM))
            
        elif profile == ToolsProfile.FULL:
            tools = self.standard_tools_provider.get_standard_tools()
            tools.extend(self.tool_registry.get_all_tools())
            
        elif profile == ToolsProfile.SEARCH_FOCUSED:
            tools = self.standard_tools_provider.get_basic_tools()
            tools.extend(self.tool_registry.get_tools_by_category(ToolCategory.SEARCH))
            tools.extend(self.tool_registry.get_tools_by_category(ToolCategory.METADATA))
            
        elif profile == ToolsProfile.DOWNLOAD_FOCUSED:
            tools = self.standard_tools_provider.get_standard_tools()
            tools.extend(self.tool_registry.get_tools_by_category(ToolCategory.DOWNLOAD))
            tools.extend(self.tool_registry.get_tools_by_category(ToolCategory.SEARCH))
            
        elif profile == ToolsProfile.ANALYTICS_FOCUSED:
            tools = self.standard_tools_provider.get_basic_tools()
            tools.extend(self.tool_registry.get_tools_by_category(ToolCategory.ANALYTICS))
            tools.extend(self.tool_registry.get_tools_by_category(ToolCategory.DISCOVERY))
        
        # Remove duplicates while preserving order
        unique_tools = []
        seen = set()
        for tool in tools:
            if tool not in seen:
                unique_tools.append(tool)
                seen.add(tool)
        
        self._cache[cache_key] = unique_tools
        logger.info(f"Loaded {len(unique_tools)} tools for profile: {profile.value}")
        
        return unique_tools
    
    def get_custom_tools(
        self,
        include_standard: bool = True,
        categories: Optional[List[ToolCategory]] = None,
        platforms: Optional[List[IntegrationPlatform]] = None,
        exclude_deprecated: bool = True,
        exclude_auth_required: bool = False,
        exclude_config_required: bool = False
    ) -> List[Any]:
        """
        Get custom tool selection with advanced filtering.
        
        Args:
            include_standard: Whether to include standard Strands tools
            categories: Tool categories to include
            platforms: Integration platforms to include
            exclude_deprecated: Whether to exclude deprecated tools
            exclude_auth_required: Whether to exclude tools requiring authentication
            exclude_config_required: Whether to exclude tools requiring configuration
        
        Returns:
            Filtered list of tool functions
        """
        tools = []
        
        # Add standard tools if requested
        if include_standard:
            tools.extend(self.standard_tools_provider.get_standard_tools())
        
        # Add music tools with filtering
        music_tools = self.tool_registry.get_tools_by_filter(
            categories=categories,
            platforms=platforms,
            include_deprecated=not exclude_deprecated,
            requires_auth=False if exclude_auth_required else None,
            requires_config=False if exclude_config_required else None
        )
        tools.extend(music_tools)
        
        # Remove duplicates
        unique_tools = list(dict.fromkeys(tools))
        
        logger.info(f"Custom tool selection: {len(unique_tools)} tools")
        return unique_tools
    
    def get_tools_for_platform(
        self, 
        platform: IntegrationPlatform,
        include_core: bool = True
    ) -> List[Any]:
        """
        Get tools for a specific platform with optional core tools.
        
        Args:
            platform: Integration platform
            include_core: Whether to include core multi-platform tools
        
        Returns:
            Platform-specific tools
        """
        tools = self.standard_tools_provider.get_standard_tools()
        tools.extend(self.tool_registry.get_tools_by_platform(platform))
        
        if include_core and platform != IntegrationPlatform.MULTI_PLATFORM:
            tools.extend(self.tool_registry.get_tools_by_platform(IntegrationPlatform.MULTI_PLATFORM))
        
        unique_tools = list(dict.fromkeys(tools))
        logger.info(f"Platform tools ({platform.value}): {len(unique_tools)} tools")
        
        return unique_tools
    
    def get_recommended_tools(
        self,
        user_requirements: Optional[Dict[str, Any]] = None
    ) -> List[Any]:
        """
        Get recommended tools based on user requirements and usage patterns.
        
        Args:
            user_requirements: Dictionary of user requirements/preferences
        
        Returns:
            Recommended list of tools
        """
        if not user_requirements:
            # Default recommendation: standard profile
            return self.get_tools_by_profile(ToolsProfile.STANDARD)
        
        # Analyze requirements and recommend tools
        has_auth = user_requirements.get("has_authentication", False)
        needs_downloads = user_requirements.get("needs_downloads", False)
        focuses_on_search = user_requirements.get("focuses_on_search", False)
        needs_analytics = user_requirements.get("needs_analytics", False)
        
        # Determine appropriate profile
        if needs_downloads and has_auth:
            profile = ToolsProfile.DOWNLOAD_FOCUSED
        elif focuses_on_search:
            profile = ToolsProfile.SEARCH_FOCUSED
        elif needs_analytics:
            profile = ToolsProfile.ANALYTICS_FOCUSED
        else:
            profile = ToolsProfile.STANDARD
        
        tools = self.get_tools_by_profile(profile)
        
        # Additional filtering based on requirements
        if not has_auth:
            # Filter out tools that require authentication
            filtered_tools = []
            for tool in tools:
                # Check if tool requires auth (this would need tool metadata)
                # For now, include all tools
                filtered_tools.append(tool)
            tools = filtered_tools
        
        logger.info(f"Recommended {len(tools)} tools based on requirements")
        return tools
    
    def get_tools_summary(self) -> Dict[str, Any]:
        """
        Get a summary of available tools and registry status.
        
        Returns:
            Summary information about tools
        """
        registry_stats = get_registry_stats()
        
        summary = {
            "registry_stats": registry_stats,
            "standard_tools": {
                "total": len(self.standard_tools_provider.get_standard_tools()),
                "basic": len(self.standard_tools_provider.get_basic_tools()),
                "file": len(self.standard_tools_provider.get_file_tools()),
                "system": len(self.standard_tools_provider.get_system_tools())
            },
            "profiles": {
                profile.value: len(self.get_tools_by_profile(profile))
                for profile in ToolsProfile
            }
        }
        
        return summary
    
    def validate_tool_requirements(self, tools: List[Any]) -> Dict[str, Any]:
        """
        Validate that tool requirements can be met.
        
        Args:
            tools: List of tools to validate
        
        Returns:
            Validation results with warnings/errors
        """
        validation = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "tools_requiring_auth": [],
            "tools_requiring_config": [],
            "deprecated_tools": []
        }
        
        for tool in tools:
            tool_name = getattr(tool, '__name__', str(tool))
            tool_info = self.tool_registry.get_tool_info(tool_name)
            
            if tool_info:
                if tool_info.deprecated:
                    validation["deprecated_tools"].append(tool_name)
                    validation["warnings"].append(f"Tool '{tool_name}' is deprecated")
                
                if tool_info.requires_auth:
                    validation["tools_requiring_auth"].append(tool_name)
                
                if tool_info.requires_config:
                    validation["tools_requiring_config"].append(tool_name)
        
        if validation["deprecated_tools"]:
            validation["warnings"].append(
                f"Found {len(validation['deprecated_tools'])} deprecated tools"
            )
        
        return validation
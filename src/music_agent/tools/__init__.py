"""
Music Agent Tools - Refactored Architecture

This module provides a comprehensive set of tools for music discovery, management,
and analysis across multiple platforms. The tools are organized into several categories:

## Core Tools (Multi-platform)
- Cross-platform search and discovery
- Playlist creation and management
- Metadata retrieval and analysis
- Download orchestration

## Integration-Specific Tools
- Platform-specific implementations for each music service
- Specialized features unique to each platform

## Operations Templates
- Base classes and interfaces for consistent behavior
- Standardized data formats across platforms

## Database Tools
- Track and playlist management
- Listening history and analytics
- Cross-platform synchronization

## Utility Tools
- File operations and format conversion
- Text processing and normalization
- URL parsing and validation
"""

# Tools are imported lazily via the registry system to avoid dependency issues

# Export registry functions for public API
__all__ = [
    # Registry functions
    'get_all_tools',
    'get_tools_by_category',
    'get_tools_by_platform',
    'get_registry_stats',
    'list_available_tools',
    'ToolCategory',
    'IntegrationPlatform'
]


# Tool registry integration - use the new registry pattern
from .registry import (
    get_all_tools, 
    get_tools_by_category as get_tools_by_category_registry, 
    get_tools_by_platform,
    get_registry_stats,
    list_available_tools,
    ToolCategory,
    IntegrationPlatform
)

def get_all_tools():
    """
    Get all available tools for agent registration.
    
    Uses the new tool registry system for intelligent tool discovery.
    
    Returns:
        List of all tool functions that can be registered with the agent
    """
    from .registry import get_all_tools as registry_get_all_tools
    return registry_get_all_tools()


def get_tools_by_category():
    """
    Get tools organized by category (legacy format).
    
    Returns:
        Dictionary with tools organized by category
    """
    from .registry import get_tool_registry
    registry = get_tool_registry()
    
    return {
        'core': registry.get_tools_by_platform(IntegrationPlatform.MULTI_PLATFORM),
        'deezer': registry.get_tools_by_platform(IntegrationPlatform.DEEZER),
        'soulseek': registry.get_tools_by_platform(IntegrationPlatform.SOULSEEK),
        'discogs': registry.get_tools_by_platform(IntegrationPlatform.DISCOGS),
        'tracklists': registry.get_tools_by_platform(IntegrationPlatform.TRACKLISTS_1001)
    }
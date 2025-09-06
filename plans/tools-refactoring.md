# Tools Refactoring Plan

## Current State Analysis

### Existing Tool Files
1. **`music_tools.py`** - General music operations with Deezer/Spotify/YouTube
2. **`download_tool.py`** - Deezer-specific download functionality  
3. **`soulseek_tools.py`** - Soulseek P2P search and download
4. **`discogs_tools.py`** - Comprehensive Discogs database operations
5. **`tracklists_tools.py`** - Complex 1001 Tracklists analysis
6. **`tracklists_simple_tools.py`** - Simple 1001 Tracklists operations

### Problems Identified
1. **Mixed Integration Logic**: `music_tools.py` and `download_tool.py` hardcode Deezer but should be generic
2. **Inconsistent Organization**: Some files are integration-specific, others are generic
3. **Redundant Functionality**: Two tracklists tools with overlapping features
4. **Poor Scalability**: Adding 13+ integrations will create confusion
5. **Unclear Boundaries**: Tools mix platform-specific and generic operations

## Proposed New Structure (Revised)

### Directory Organization
```
src/music_agent/tools/
├── __init__.py                     # Tool registry and exports
├── operations/                     # Generic operation templates
│   ├── __init__.py
│   ├── search.py                  # Generic search operations
│   ├── download.py                # Generic download operations
│   ├── playlist.py                # Generic playlist operations
│   ├── metadata.py                # Generic metadata operations
│   └── streaming.py               # Generic streaming operations
├── integrations/                   # Integration-specific implementations
│   ├── __init__.py
│   ├── soundcloud.py              # SoundCloud-specific tools
│   ├── mixcloud.py                # Mixcloud-specific tools
│   ├── bandcamp.py                # Bandcamp-specific tools
│   ├── beatport.py                # Beatport-specific tools
│   ├── youtube.py                 # YouTube-specific tools
│   ├── spotify.py                 # Spotify-specific tools
│   ├── deezer.py                  # Deezer-specific tools
│   ├── soulseek.py                # Soulseek-specific tools
│   ├── discogs.py                 # Discogs-specific tools
│   ├── tracklists_1001.py         # 1001 Tracklists-specific tools
│   └── rekordbox.py               # Rekordbox-specific tools
├── specialized/                    # Unique integration features
│   ├── __init__.py
│   ├── beatport_charts.py         # Beatport chart operations
│   ├── spotify_recommendations.py # Spotify recommendation engine
│   ├── discogs_marketplace.py     # Discogs buying/selling
│   ├── soulseek_p2p.py           # Soulseek P2P operations
│   ├── tracklists_analysis.py     # DJ set analysis
│   └── rekordbox_sync.py          # DJ software sync
├── core/                          # Multi-platform operations
│   ├── __init__.py
│   ├── search.py                  # Multi-platform search orchestration
│   ├── download.py                # Multi-platform download orchestration
│   ├── playlist.py                # Cross-platform playlist management
│   ├── metadata.py                # Unified metadata handling
│   └── recommendations.py         # Cross-platform recommendations
├── database/                      # Database operations
│   ├── __init__.py
│   ├── tracks.py                  # Track CRUD operations
│   ├── playlists.py               # Playlist CRUD operations
│   ├── history.py                 # Listening/search history
│   └── sync.py                    # Cross-platform sync
└── utils/                         # Utility tools
    ├── __init__.py
    ├── file_operations.py         # File management
    ├── format_conversion.py       # Audio format conversion
    ├── url_parsing.py             # URL validation/parsing
    └── text_processing.py         # Text cleaning/normalization
```

## Tool Categories & Duplication Prevention

### 1. Generic Operation Templates (`operations/`)
**Purpose**: Provide reusable base classes and functions for common operations

**Example Structure**:
```python
# operations/search.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional

class SearchOperation(ABC):
    """Base class for all search operations."""
    
    @abstractmethod
    async def search_tracks(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod 
    async def search_albums(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        pass
    
    def standardize_track_result(self, raw_result: Dict) -> Dict[str, Any]:
        """Convert platform-specific result to standard format."""
        return {
            'id': raw_result.get('id'),
            'title': raw_result.get('title') or raw_result.get('name'),
            'artist': self._extract_artist(raw_result),
            'duration': self._extract_duration(raw_result),
            'platform': self.platform_name,
            'url': raw_result.get('url'),
            'preview_url': raw_result.get('preview_url'),
        }
```

**Benefits**:
- **No Code Duplication**: All integrations inherit common patterns
- **Consistent Interfaces**: Same method signatures across platforms  
- **Standardized Output**: Unified data format regardless of source
- **Easy Testing**: Mock the base classes for testing

### 2. Integration-Specific Implementations (`integrations/`)
**Purpose**: Implement platform-specific logic using operation templates

**Example Structure**:
```python
# integrations/soundcloud.py
from ..operations.search import SearchOperation
from ..operations.download import DownloadOperation
from ...integrations.soundcloud import SoundCloudClient

class SoundCloudSearch(SearchOperation):
    platform_name = "soundcloud"
    
    def __init__(self):
        self.client = SoundCloudClient()
    
    async def search_tracks(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        raw_results = await self.client.search_tracks(query, **kwargs)
        return [self.standardize_track_result(r) for r in raw_results]
    
    def _extract_artist(self, raw_result: Dict) -> str:
        # SoundCloud-specific artist extraction
        return raw_result.get('user', {}).get('username', 'Unknown')

class SoundCloudDownload(DownloadOperation):
    # Similar pattern for downloads
    pass

# Export standardized tools
soundcloud_search = SoundCloudSearch()
soundcloud_download = SoundCloudDownload()

def search_soundcloud_tracks(query: str, **kwargs):
    """Search SoundCloud tracks."""
    return soundcloud_search.search_tracks(query, **kwargs)
```

### 3. Specialized Features (`specialized/`)
**Purpose**: Handle unique platform features that don't fit common patterns

**Examples**:
- `beatport_charts.py` - Beatport's genre-specific charts
- `spotify_recommendations.py` - Spotify's recommendation engine
- `discogs_marketplace.py` - Discogs buying/selling
- `soulseek_p2p.py` - Soulseek's P2P network features
- `tracklists_analysis.py` - DJ set analysis algorithms

### 4. Multi-Platform Orchestration (`core/`)
**Purpose**: Coordinate operations across multiple platforms

**Example**:
```python
# core/search.py
from ..integrations import (
    soundcloud_search, spotify_search, youtube_search, 
    beatport_search, bandcamp_search
)

async def search_all_platforms(
    query: str, 
    platforms: Optional[List[str]] = None,
    limit_per_platform: int = 10
) -> Dict[str, List[Dict[str, Any]]]:
    """Search across multiple platforms simultaneously."""
    
    if not platforms:
        platforms = ['soundcloud', 'spotify', 'youtube', 'beatport', 'bandcamp']
    
    results = {}
    search_tasks = []
    
    # Create async tasks for each platform
    for platform in platforms:
        if platform == 'soundcloud':
            task = soundcloud_search.search_tracks(query, limit=limit_per_platform)
        elif platform == 'spotify':
            task = spotify_search.search_tracks(query, limit=limit_per_platform)
        # ... etc
        
        search_tasks.append((platform, task))
    
    # Execute searches concurrently
    for platform, task in search_tasks:
        try:
            results[platform] = await task
        except Exception as e:
            logger.error(f"Search failed for {platform}: {e}")
            results[platform] = []
    
    return results
```

## Duplication Prevention Strategy

### 1. Template Method Pattern
- Base classes define the algorithm structure
- Subclasses implement platform-specific details
- Common logic is shared, unique logic is isolated

### 2. Standardized Data Models
All platforms return data in the same format:
```python
# Standard track format
{
    'id': str,
    'title': str, 
    'artist': str,
    'album': Optional[str],
    'duration': Optional[int],  # seconds
    'platform': str,
    'url': str,
    'preview_url': Optional[str],
    'metadata': Dict[str, Any]  # Platform-specific extras
}
```

### 3. Shared Utility Functions
Common operations extracted to utils:
- URL parsing and validation
- Audio file processing
- Text normalization
- Rate limiting
- Error handling

### 4. Configuration-Driven Tools
Instead of hardcoding platform logic:
```python
# Platform configurations
PLATFORM_CONFIGS = {
    'soundcloud': {
        'search_endpoint': '/tracks',
        'artist_field': 'user.username',
        'duration_field': 'duration_ms',
        'title_field': 'title'
    },
    'spotify': {
        'search_endpoint': '/search',
        'artist_field': 'artists.0.name', 
        'duration_field': 'duration_ms',
        'title_field': 'name'
    }
}
```

## Comparison: Before vs After

### Before (Current - Lots of Duplication)
```
soundcloud/search.py     -> 100 lines of search logic
spotify/search.py        -> 95 lines of similar search logic  
beatport/search.py       -> 105 lines of similar search logic
youtube/search.py        -> 90 lines of similar search logic
...                      -> 13 more files with similar patterns
Total: ~1,300 lines with 80% duplication
```

### After (Proposed - Minimal Duplication)
```
operations/search.py     -> 200 lines of shared search logic
soundcloud.py           -> 30 lines of SoundCloud specifics
spotify.py              -> 25 lines of Spotify specifics  
beatport.py             -> 35 lines of Beatport specifics
youtube.py              -> 20 lines of YouTube specifics
...                     -> 13 more files, ~25 lines each
Total: ~725 lines with <10% duplication
```

**Savings**: ~575 lines of code, much easier maintenance

### 5. Integration-Specific Tools
Each integration gets its own folder with specialized tools:

**Search Tools** (`search.py`)
- Platform-specific search functionality
- Handle platform-specific parameters
- Return standardized results

**Download Tools** (`download.py`)  
- Platform-specific download logic
- Handle authentication/permissions
- Manage file naming/organization

**Metadata Tools** (`metadata.py`)
- Extract platform-specific metadata
- Handle rich data (BPM, key, genre)
- Manage artwork/images

**Specialized Tools**
- `charts.py` (Beatport, Deezer) - Chart data
- `social.py` (SoundCloud, Spotify) - Social features
- `stream.py` (Mixcloud, Bandcamp) - Stream extraction
- `analysis.py` (1001 Tracklists) - Advanced analysis

### 2. Core Tools
Generic operations that work across platforms:

**Multi-Platform Search** (`core/search.py`)
- Search across multiple platforms
- Aggregate and deduplicate results
- Intelligent fallback logic

**Download Orchestration** (`core/download.py`)
- Route downloads to appropriate integration
- Handle download prioritization
- Manage download queue/batch operations

**Metadata Management** (`core/metadata.py`)
- Standardize metadata across platforms
- Handle audio file tagging
- Manage artwork embedding

### 3. Database Tools
Database operations for persistence:

**Track Operations** (`database/tracks.py`)
- Store/retrieve track information
- Handle deduplication
- Manage track relationships

**History Management** (`database/history.py`)
- Store search/listening history
- Generate recommendations
- Track usage patterns

### 4. Utility Tools
Helper functions and utilities:

**File Operations** (`utils/file_operations.py`)
- File management and organization
- Directory structure creation
- Cleanup operations

**Format Conversion** (`utils/format_conversion.py`)
- Audio format conversion
- Bitrate/quality adjustment
- Batch processing

## Migration Strategy

### Phase 1: Create New Structure
1. Create new directory structure
2. Set up `__init__.py` files with proper exports
3. Create empty skeleton files

### Phase 2: Extract Integration-Specific Code
1. **Soulseek**: Move `soulseek_tools.py` → `integrations/soulseek/`
2. **Discogs**: Move `discogs_tools.py` → `integrations/discogs/`
3. **1001 Tracklists**: Consolidate both tracklists files → `integrations/tracklists_1001/`
4. **Deezer**: Extract Deezer-specific code → `integrations/deezer/`

### Phase 3: Create Core Tools
1. **Generic Search**: Extract multi-platform logic from `music_tools.py`
2. **Generic Download**: Create platform-agnostic download orchestration
3. **Database Tools**: Extract database operations
4. **Utility Tools**: Create helper functions

### Phase 4: Add Missing Integration Tools
Create tools for existing integrations without tools:
1. **SoundCloud**: Search, download, playlist, social
2. **Mixcloud**: Search, shows, stream
3. **Bandcamp**: Search, download, metadata
4. **Beatport**: Search, charts, metadata
5. **YouTube**: Search, download, playlist
6. **Spotify**: Search, playlist, recommendations, library
7. **Rekordbox**: Sync, playlists, metadata

## Tool Implementation Standards

### File Structure Template
```python
"""
[Integration Name] [Tool Type] tools.

Provides [specific functionality] for [platform].
"""

from typing import List, Dict, Any, Optional
from ...integrations.[integration_name] import [IntegrationClass]

# Initialize integration
integration = [IntegrationClass]()

def [tool_function_name](
    param1: str,
    param2: Optional[int] = None
) -> Dict[str, Any]:
    """
    [Tool description].
    
    Args:
        param1: [Description]
        param2: [Description]
    
    Returns:
        [Description of return value]
    
    Example:
        >>> result = [tool_function_name]("query")
        >>> print(result["key"])
    """
    # Implementation
    pass

# Export for tool registration
__all__ = ["[tool_function_name]"]
```

### Naming Conventions
- **Search Tools**: `{platform}_search`, `{platform}_search_tracks`, etc.
- **Download Tools**: `{platform}_download`, `{platform}_download_playlist`, etc.
- **Metadata Tools**: `{platform}_get_metadata`, `{platform}_get_track_info`, etc.
- **Generic Tools**: `search_music`, `download_track`, `get_metadata`, etc.

### Error Handling
All tools should:
- Handle integration-specific errors gracefully
- Return consistent error formats
- Log errors appropriately
- Provide fallback behavior where possible

## Benefits of New Structure

### 1. Clear Organization
- Integration-specific tools are clearly separated
- Generic operations are in dedicated core folder
- Database and utility tools have their own spaces

### 2. Scalability  
- Easy to add new integrations without confusion
- Each integration's tools are self-contained
- No cross-contamination of platform-specific logic

### 3. Maintainability
- Each tool file has single responsibility
- Easy to locate and modify specific functionality
- Clear dependencies between tools and integrations

### 4. Reusability
- Core tools can work with any integration
- Utility tools are platform-agnostic
- Database tools provide consistent data layer

### 5. Testability
- Each tool can be tested independently
- Mock integrations for testing generic tools
- Clear boundaries for unit testing

## Compatibility Considerations

### Backward Compatibility
- Keep old tool files temporarily with deprecation warnings
- Provide import aliases for existing tool names
- Update agent configuration gradually

### Tool Registration
Update `tools/__init__.py` to:
- Export all tools from new structure
- Maintain backward compatibility
- Provide clear tool discovery

### Agent Integration
Update agent core to:
- Import from new tool structure
- Handle tool categorization
- Support tool selection by category

## Implementation Timeline

**Week 1**: Create structure, migrate existing tools
**Week 2**: Create core tools, add missing integration tools  
**Week 3**: Update agent integration, testing
**Week 4**: Documentation, cleanup, remove deprecated code

This refactoring will create a clean, scalable foundation for the growing collection of music integrations and tools.
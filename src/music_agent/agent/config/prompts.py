"""
System prompt management for the music agent.
"""

from typing import Dict, Any, List, Optional
from enum import Enum

from ..tools_manager.tools_manager import ToolsProfile


class PromptTemplate(Enum):
    """Available system prompt templates."""
    DEFAULT = "default"
    SEARCH_FOCUSED = "search_focused"
    DOWNLOAD_FOCUSED = "download_focused"
    ANALYTICS_FOCUSED = "analytics_focused"
    DJ_FOCUSED = "dj_focused"
    MINIMAL = "minimal"


class SystemPromptManager:
    """Manages system prompts for different agent configurations."""
    
    def __init__(self):
        self._templates = self._load_templates()
    
    def get_prompt(
        self, 
        template: PromptTemplate = PromptTemplate.DEFAULT,
        enabled_platforms: Optional[List[str]] = None,
        tools_profile: Optional[ToolsProfile] = None,
        custom_instructions: Optional[str] = None
    ) -> str:
        """
        Generate system prompt based on configuration.
        
        Args:
            template: Prompt template to use
            enabled_platforms: List of enabled platforms
            tools_profile: Tools profile being used
            custom_instructions: Additional custom instructions
        
        Returns:
            Complete system prompt
        """
        base_prompt = self._templates[template]
        
        # Customize prompt based on enabled platforms
        if enabled_platforms:
            platform_section = self._generate_platform_section(enabled_platforms)
            base_prompt = base_prompt.replace("{PLATFORMS}", platform_section)
        else:
            base_prompt = base_prompt.replace("{PLATFORMS}", self._get_default_platforms())
        
        # Add tools profile information
        if tools_profile:
            tools_section = self._generate_tools_section(tools_profile)
            base_prompt = base_prompt.replace("{TOOLS_INFO}", tools_section)
        else:
            base_prompt = base_prompt.replace("{TOOLS_INFO}", "")
        
        # Add custom instructions
        if custom_instructions:
            base_prompt += f"\n\nAdditional Instructions:\n{custom_instructions}"
        
        return base_prompt.strip()
    
    def _load_templates(self) -> Dict[PromptTemplate, str]:
        """Load all prompt templates."""
        return {
            PromptTemplate.DEFAULT: self._get_default_template(),
            PromptTemplate.SEARCH_FOCUSED: self._get_search_focused_template(),
            PromptTemplate.DOWNLOAD_FOCUSED: self._get_download_focused_template(),
            PromptTemplate.ANALYTICS_FOCUSED: self._get_analytics_focused_template(),
            PromptTemplate.DJ_FOCUSED: self._get_dj_focused_template(),
            PromptTemplate.MINIMAL: self._get_minimal_template()
        }
    
    def _get_default_template(self) -> str:
        """Default comprehensive system prompt."""
        return """You are an intelligent music discovery and management agent with comprehensive capabilities across multiple music platforms and services.

{PLATFORMS}

Your core capabilities include:
1. **Music Discovery & Search**
   - Search across multiple platforms simultaneously
   - Find rare, unavailable, or hard-to-find tracks
   - Intelligent cross-platform matching using metadata
   - Genre and style exploration

2. **Collection Management**
   - Create and manage playlists across platforms
   - Track metadata enrichment and standardization
   - Cross-platform synchronization
   - Export in various formats (JSON, M3U, CSV)

3. **Download & Acquisition**
   - High-quality audio downloads where available
   - Intelligent platform routing for best quality
   - Metadata preservation and enhancement
   - Format conversion capabilities

4. **Analytics & Discovery**
   - Listening pattern analysis
   - Music trend identification
   - DJ set analysis and track identification
   - Festival and event music discovery

5. **Database Integration**
   - Maintain local database of tracks and metadata
   - Track listening history and preferences
   - Cross-platform ID mapping and deduplication

{TOOLS_INFO}

**Search Strategy:**
- Always try multiple platforms for comprehensive results
- Use intelligent fallback when tracks aren't available on preferred platform
- Match tracks using ISRC codes and metadata when possible
- Prefer higher quality audio sources

**Quality Standards:**
- Prioritize lossless formats (FLAC) when available
- Maintain comprehensive metadata (BPM, key, genre, artwork)
- Ensure accurate track matching across platforms
- Preserve original quality and format information

Be helpful, accurate, and respect user preferences for music quality, platforms, and privacy. Always explain your search strategy and provide alternatives when primary options aren't available."""
    
    def _get_search_focused_template(self) -> str:
        """Search-focused system prompt."""
        return """You are a specialized music search and discovery agent focused on finding music across multiple platforms.

{PLATFORMS}

Your primary expertise is in:
1. **Advanced Music Search**
   - Multi-platform simultaneous searching
   - Fuzzy matching and intelligent queries
   - Genre and mood-based discovery
   - Artist and label exploration

2. **Track Identification**
   - Cross-platform track matching
   - Metadata comparison and validation
   - ISRC and catalog number lookups
   - Duplicate detection and consolidation

3. **Discovery & Exploration**
   - Related artist and track suggestions
   - Genre deep-dives and style exploration
   - Label catalog browsing
   - Rare and unreleased track finding

{TOOLS_INFO}

Focus on providing comprehensive search results with detailed metadata and multiple platform options for each track found."""
    
    def _get_download_focused_template(self) -> str:
        """Download-focused system prompt."""
        return """You are a music acquisition specialist focused on downloading and collecting high-quality music files.

{PLATFORMS}

Your expertise includes:
1. **High-Quality Downloads**
   - Prioritize lossless formats (FLAC, WAV)
   - Intelligent quality assessment and selection
   - Multi-source comparison for best quality
   - Format conversion and optimization

2. **Metadata Management**
   - Comprehensive tag preservation and enhancement
   - Artwork embedding and quality optimization
   - Batch processing and organization
   - File naming and directory structure

3. **Source Evaluation**
   - Quality assessment across platforms
   - Availability checking and monitoring
   - Alternative source identification
   - Download verification and validation

{TOOLS_INFO}

Always prioritize quality over speed, and ensure proper metadata and organization for all downloaded content."""
    
    def _get_analytics_focused_template(self) -> str:
        """Analytics-focused system prompt."""
        return """You are a music analytics and trends specialist focused on data analysis and insights.

{PLATFORMS}

Your analytical capabilities include:
1. **Listening Pattern Analysis**
   - User behavior and preference analysis
   - Trend identification and forecasting
   - Statistical analysis of music data
   - Recommendation system insights

2. **DJ Set Analysis**
   - Track progression and mixing analysis
   - BPM and key analysis for harmonic mixing
   - Style and genre classification
   - Festival and event trend analysis

3. **Market Intelligence**
   - Chart analysis and trend tracking
   - Genre popularity and emergence
   - Label and artist performance metrics
   - Regional and demographic insights

{TOOLS_INFO}

Focus on providing data-driven insights and actionable intelligence about music trends and patterns."""
    
    def _get_dj_focused_template(self) -> str:
        """DJ-focused system prompt."""
        return """You are a specialized DJ assistant focused on professional music management and mixing support.

{PLATFORMS}

Your DJ-specific capabilities include:
1. **Set Preparation**
   - Track selection and curation
   - BPM and key matching for harmonic mixing
   - Energy level and mood progression
   - Set timing and flow optimization

2. **Track Analysis**
   - Detailed audio analysis (BPM, key, energy)
   - Cue point suggestions and analysis
   - Mix compatibility assessment
   - Track transition recommendations

3. **Performance Support**
   - Live set tracking and analysis
   - Audience response prediction
   - Genre and style recommendations
   - Event-specific track selection

{TOOLS_INFO}

Focus on supporting professional DJ workflows with technical precision and performance optimization."""
    
    def _get_minimal_template(self) -> str:
        """Minimal system prompt."""
        return """You are a basic music search assistant.

{PLATFORMS}

You can help with:
- Basic music search across platforms
- Track information retrieval
- Simple playlist creation

{TOOLS_INFO}

Keep responses concise and focused on the user's immediate needs."""
    
    def _generate_platform_section(self, platforms: List[str]) -> str:
        """Generate platform description section."""
        platform_descriptions = {
            "deezer": "Deezer: High-quality streaming and downloads with FLAC support",
            "spotify": "Spotify: Comprehensive catalog with playlist and recommendation features",
            "youtube": "YouTube: Vast collection including rare tracks, remixes, and live performances",
            "soundcloud": "SoundCloud: Independent artists, remixes, and unreleased content",
            "bandcamp": "Bandcamp: Independent music with direct artist support and high-quality downloads",
            "soulseek": "Soulseek: P2P network for rare and hard-to-find music",
            "discogs": "Discogs: Comprehensive music database and marketplace for physical media",
            "tracklists_1001": "1001 Tracklists: DJ set analysis and track identification",
            "beatport": "Beatport: Electronic music specialist with DJ-focused features",
            "mixcloud": "Mixcloud: DJ mixes and radio shows"
        }
        
        enabled_descriptions = []
        for platform in platforms:
            if platform.lower() in platform_descriptions:
                enabled_descriptions.append(f"- {platform_descriptions[platform.lower()]}")
        
        return f"You have access to these music platforms:\n" + "\n".join(enabled_descriptions)
    
    def _get_default_platforms(self) -> str:
        """Get default platform description."""
        return """You have access to multiple music platforms:
- Deezer: Search, stream, and download music with high quality audio
- Spotify: Browse playlists, discover new music, and track recommendations  
- YouTube: Find music videos, live performances, and rare tracks"""
    
    def _generate_tools_section(self, profile: ToolsProfile) -> str:
        """Generate tools information section."""
        tool_descriptions = {
            ToolsProfile.MINIMAL: "You have access to basic search and information tools.",
            ToolsProfile.STANDARD: "You have access to comprehensive music tools including search, metadata, and playlist management.",
            ToolsProfile.FULL: "You have access to all available music tools including downloads, analytics, and specialized features.",
            ToolsProfile.SEARCH_FOCUSED: "You have specialized search and discovery tools optimized for finding music.",
            ToolsProfile.DOWNLOAD_FOCUSED: "You have comprehensive download and file management tools.",
            ToolsProfile.ANALYTICS_FOCUSED: "You have advanced analytics and trend analysis tools."
        }
        
        return f"\nTool Configuration: {tool_descriptions.get(profile, 'Standard tool configuration.')}"
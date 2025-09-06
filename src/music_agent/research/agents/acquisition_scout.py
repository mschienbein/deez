"""
Acquisition Scout - Track Source Discovery Agent

Finds where and how to acquire or access the identified track.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum

from .base import ResearchAgent, AgentRole
from ..core.research_context import (
    ResearchContext, AcquisitionOption, TrackQuality
)

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Types of acquisition sources."""
    PURCHASE = "purchase"      # Buy the track
    STREAM = "stream"          # Streaming service
    DOWNLOAD = "download"      # Free/legal download
    SUBSCRIPTION = "subscription"  # Subscription service
    VINYL = "vinyl"           # Physical media
    SOULSEEK = "soulseek"     # P2P network


class QualityLevel(Enum):
    """Quality levels for different sources."""
    LOSSLESS = 5  # WAV, FLAC, AIFF
    HIGH = 4      # 320kbps MP3, 256kbps AAC
    MEDIUM = 3    # 192-256kbps
    LOW = 2       # 128kbps or lower
    UNKNOWN = 1   # Quality not specified


class AcquisitionScout(ResearchAgent):
    """
    Specialist agent for finding acquisition sources for tracks.
    
    Responsibilities:
    - Search for purchase options
    - Find streaming availability
    - Identify download sources
    - Check physical media availability
    - Assess quality of each source
    - Prioritize options by quality and availability
    """
    
    # Platform acquisition capabilities
    PLATFORM_SOURCES = {
        'beatport': {
            'type': SourceType.PURCHASE,
            'quality': QualityLevel.LOSSLESS,
            'formats': ['WAV', 'AIFF', 'MP3 320'],
            'region_restricted': False,
            'typical_price': 2.49
        },
        'spotify': {
            'type': SourceType.STREAM,
            'quality': QualityLevel.HIGH,
            'formats': ['OGG 320'],
            'region_restricted': True,
            'requires_subscription': True
        },
        'bandcamp': {
            'type': SourceType.PURCHASE,
            'quality': QualityLevel.LOSSLESS,
            'formats': ['FLAC', 'WAV', 'MP3 V0'],
            'region_restricted': False,
            'pay_what_you_want': True
        },
        'itunes': {
            'type': SourceType.PURCHASE,
            'quality': QualityLevel.HIGH,
            'formats': ['AAC 256'],
            'region_restricted': True,
            'typical_price': 1.29
        },
        'amazon': {
            'type': SourceType.PURCHASE,
            'quality': QualityLevel.HIGH,
            'formats': ['MP3 320'],
            'region_restricted': True,
            'typical_price': 1.29
        },
        'soundcloud': {
            'type': SourceType.STREAM,
            'quality': QualityLevel.MEDIUM,
            'formats': ['MP3 128'],
            'region_restricted': False,
            'free_tier': True
        },
        'youtube': {
            'type': SourceType.STREAM,
            'quality': QualityLevel.MEDIUM,
            'formats': ['Various'],
            'region_restricted': True,
            'free_tier': True
        },
        'deezer': {
            'type': SourceType.STREAM,
            'quality': QualityLevel.LOSSLESS,
            'formats': ['FLAC', 'MP3 320'],
            'region_restricted': True,
            'requires_subscription': True
        },
        'tidal': {
            'type': SourceType.STREAM,
            'quality': QualityLevel.LOSSLESS,
            'formats': ['FLAC', 'MQA'],
            'region_restricted': True,
            'requires_subscription': True
        },
        'juno': {
            'type': SourceType.PURCHASE,
            'quality': QualityLevel.HIGH,
            'formats': ['MP3 320', 'WAV'],
            'region_restricted': False,
            'typical_price': 1.99
        },
        'traxsource': {
            'type': SourceType.PURCHASE,
            'quality': QualityLevel.LOSSLESS,
            'formats': ['WAV', 'AIFF', 'MP3 320'],
            'region_restricted': False,
            'typical_price': 2.49
        },
        'discogs': {
            'type': SourceType.VINYL,
            'quality': QualityLevel.LOSSLESS,
            'formats': ['Vinyl', 'CD'],
            'region_restricted': False,
            'marketplace': True
        },
        'soulseek': {
            'type': SourceType.SOULSEEK,
            'quality': QualityLevel.UNKNOWN,
            'formats': ['Various'],
            'region_restricted': False,
            'p2p': True
        }
    }
    
    def __init__(
        self,
        context: ResearchContext,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Acquisition Scout.
        
        Args:
            context: Shared research context
            config: Optional configuration
        """
        super().__init__(
            name="AcquisitionScout",
            role=AgentRole.ACQUISITION_SCOUT,
            context=context,
            config=config or {}
        )
        
        # Configuration
        self.check_all_sources = self.config.get('check_all_sources', True)
        self.include_streaming = self.config.get('include_streaming', True)
        self.include_physical = self.config.get('include_physical', False)
        self.max_price = self.config.get('max_price', None)
        self.preferred_quality = self.config.get('preferred_quality', 'lossless')
        
        # State
        self.sources_found: List[AcquisitionOption] = []
        self.unavailable_platforms: Set[str] = set()
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute acquisition source discovery.
        
        Returns:
            Discovery results with acquisition options
        """
        self.start()
        
        try:
            if not self.context.merged_metadata:
                self.log_error("No metadata available for acquisition search")
                self.complete(success=False)
                return {'success': False, 'error': 'No metadata available'}
            
            metadata = self.context.merged_metadata
            
            # Step 1: Check platforms we already searched
            self.log("Checking acquisition options from searched platforms")
            await self._check_searched_platforms()
            
            # Step 2: Search purchase platforms
            self.log("Searching purchase platforms")
            await self._search_purchase_platforms(metadata)
            
            # Step 3: Check streaming availability
            if self.include_streaming:
                self.log("Checking streaming availability")
                await self._check_streaming_services(metadata)
            
            # Step 4: Check physical media
            if self.include_physical:
                self.log("Checking physical media availability")
                await self._check_physical_media(metadata)
            
            # Step 5: Check alternative sources
            self.log("Checking alternative sources")
            await self._check_alternative_sources(metadata)
            
            # Step 6: Prioritize and filter options
            self.log("Prioritizing acquisition options")
            filtered_options = await self._prioritize_options()
            
            # Store in context
            for option in filtered_options:
                self.context.add_acquisition_option(option)
            
            # Generate summary
            summary = self._generate_summary(filtered_options)
            
            self.log(f"Found {len(filtered_options)} acquisition options")
            
            self.complete(success=True)
            
            return {
                'success': True,
                'options': filtered_options,
                'best_option': filtered_options[0] if filtered_options else None,
                'summary': summary,
                'total_found': len(self.sources_found),
                'filtered': len(filtered_options)
            }
            
        except Exception as e:
            self.log_error(f"Scout failed: {str(e)}")
            self.complete(success=False)
            return {'success': False, 'error': str(e)}
    
    async def _check_searched_platforms(self) -> None:
        """Check platforms we already searched for acquisition info."""
        for platform, result in self.context.platform_results.items():
            if not result.success or not result.data:
                continue
            
            platform_info = self.PLATFORM_SOURCES.get(platform)
            if not platform_info:
                continue
            
            # Extract acquisition info from platform data
            tracks = result.data.get('tracks', [])
            if tracks and isinstance(tracks, list):
                track = tracks[0]
                
                # Create acquisition option based on platform type
                option = self._create_option_from_platform(
                    platform,
                    platform_info,
                    track
                )
                
                if option:
                    self.sources_found.append(option)
                    self.log(f"Found {option.type} option on {platform}")
    
    def _create_option_from_platform(
        self,
        platform: str,
        platform_info: Dict[str, Any],
        track_data: Dict[str, Any]
    ) -> Optional[AcquisitionOption]:
        """
        Create acquisition option from platform data.
        
        Args:
            platform: Platform name
            platform_info: Platform capabilities
            track_data: Track data from platform
        
        Returns:
            AcquisitionOption or None
        """
        # Map quality level to TrackQuality
        quality_mapping = {
            QualityLevel.LOSSLESS: TrackQuality.LOSSLESS,
            QualityLevel.HIGH: TrackQuality.HIGH,
            QualityLevel.MEDIUM: TrackQuality.MEDIUM,
            QualityLevel.LOW: TrackQuality.LOW,
            QualityLevel.UNKNOWN: TrackQuality.UNKNOWN
        }
        
        quality = quality_mapping.get(
            platform_info['quality'],
            TrackQuality.UNKNOWN
        )
        
        # Build URL if available
        url = None
        if 'url' in track_data:
            url = track_data['url']
        elif 'external_urls' in track_data:
            url = track_data['external_urls'].get(platform)
        elif platform == 'beatport' and track_data.get('beatport_id'):
            url = f"https://www.beatport.com/track/-/{track_data['beatport_id']}"
        elif platform == 'spotify' and track_data.get('spotify_id'):
            url = f"https://open.spotify.com/track/{track_data['spotify_id']}"
        
        # Get price if available
        price = None
        currency = 'USD'
        
        if platform_info['type'] == SourceType.PURCHASE:
            price = track_data.get('price', platform_info.get('typical_price'))
        
        # Create option
        option = AcquisitionOption(
            source=platform,
            type=platform_info['type'].value,
            quality=quality,
            price=price,
            currency=currency if price else None,
            url=url,
            requires_subscription=platform_info.get('requires_subscription', False),
            region_restricted=platform_info.get('region_restricted', False),
            availability='available',
            notes=f"Formats: {', '.join(platform_info.get('formats', []))}"
        )
        
        return option
    
    async def _search_purchase_platforms(
        self,
        metadata: 'UniversalTrackMetadata'
    ) -> None:
        """
        Search dedicated purchase platforms.
        
        Args:
            metadata: Track metadata
        """
        purchase_platforms = [
            'beatport', 'bandcamp', 'juno', 'traxsource',
            'itunes', 'amazon'
        ]
        
        for platform in purchase_platforms:
            # Skip if already searched
            if platform in self.context.platforms_searched:
                continue
            
            platform_info = self.PLATFORM_SOURCES.get(platform)
            if not platform_info:
                continue
            
            # Simulate platform search (would use actual API)
            if await self._check_platform_availability(platform, metadata):
                option = self._create_mock_option(platform, platform_info, metadata)
                if option:
                    self.sources_found.append(option)
                    self.log(f"Found purchase option on {platform}")
            else:
                self.unavailable_platforms.add(platform)
    
    async def _check_streaming_services(
        self,
        metadata: 'UniversalTrackMetadata'
    ) -> None:
        """
        Check streaming service availability.
        
        Args:
            metadata: Track metadata
        """
        streaming_platforms = [
            'spotify', 'deezer', 'tidal', 'soundcloud',
            'youtube', 'apple_music'
        ]
        
        for platform in streaming_platforms:
            # Skip if already searched
            if platform in self.context.platforms_searched:
                continue
            
            platform_info = self.PLATFORM_SOURCES.get(platform)
            if not platform_info:
                continue
            
            # Check if track is available on streaming
            if await self._check_platform_availability(platform, metadata):
                option = self._create_mock_option(platform, platform_info, metadata)
                if option:
                    self.sources_found.append(option)
                    self.log(f"Found streaming option on {platform}")
    
    async def _check_physical_media(
        self,
        metadata: 'UniversalTrackMetadata'
    ) -> None:
        """
        Check physical media availability.
        
        Args:
            metadata: Track metadata
        """
        # Check Discogs marketplace
        if 'discogs' in self.context.platforms_searched:
            # Extract marketplace info from Discogs data
            discogs_result = self.context.platform_results.get('discogs')
            if discogs_result and discogs_result.success:
                # Create vinyl/CD options
                platform_info = self.PLATFORM_SOURCES['discogs']
                
                option = AcquisitionOption(
                    source='discogs',
                    type='vinyl',
                    quality=TrackQuality.LOSSLESS,
                    price=None,  # Varies by seller
                    currency=None,
                    url=f"https://www.discogs.com/sell/list?q={metadata.artist}+{metadata.title}",
                    requires_subscription=False,
                    region_restricted=False,
                    availability='marketplace',
                    notes="Physical media - check marketplace for availability"
                )
                
                self.sources_found.append(option)
                self.log("Found physical media option on Discogs")
    
    async def _check_alternative_sources(
        self,
        metadata: 'UniversalTrackMetadata'
    ) -> None:
        """
        Check alternative acquisition sources.
        
        Args:
            metadata: Track metadata
        """
        # Check if track might be on Bandcamp (for independent artists)
        if metadata.label and 'independent' in metadata.label.lower():
            platform_info = self.PLATFORM_SOURCES.get('bandcamp')
            if platform_info:
                option = self._create_mock_option('bandcamp', platform_info, metadata)
                if option:
                    option.notes = "May be available - check artist page"
                    self.sources_found.append(option)
        
        # Add Soulseek as last resort for rare tracks
        if self.config.get('include_p2p', False):
            option = AcquisitionOption(
                source='soulseek',
                type='soulseek',
                quality=TrackQuality.UNKNOWN,
                price=None,
                currency=None,
                url=None,
                requires_subscription=False,
                region_restricted=False,
                availability='p2p',
                notes="P2P network - quality varies"
            )
            self.sources_found.append(option)
    
    async def _check_platform_availability(
        self,
        platform: str,
        metadata: 'UniversalTrackMetadata'
    ) -> bool:
        """
        Check if track is available on platform.
        
        This is a mock implementation. Real implementation would
        use platform APIs or tools.
        
        Args:
            platform: Platform name
            metadata: Track metadata
        
        Returns:
            True if available
        """
        # Mock logic - in reality would search platform
        # For now, simulate availability based on metadata
        
        # Electronic music more likely on Beatport/Traxsource
        if platform in ['beatport', 'traxsource']:
            if metadata.genre and 'electronic' in metadata.genre.lower():
                return True
            if metadata.genre and any(
                g in metadata.genre.lower()
                for g in ['house', 'techno', 'trance', 'dubstep']
            ):
                return True
        
        # Major platforms likely have popular tracks
        if platform in ['spotify', 'itunes', 'amazon']:
            # Assume available if we have an ISRC
            if metadata.isrc:
                return True
        
        # Random availability for demo
        import random
        return random.random() > 0.5
    
    def _create_mock_option(
        self,
        platform: str,
        platform_info: Dict[str, Any],
        metadata: 'UniversalTrackMetadata'
    ) -> AcquisitionOption:
        """
        Create mock acquisition option for testing.
        
        Args:
            platform: Platform name
            platform_info: Platform capabilities
            metadata: Track metadata
        
        Returns:
            Mock AcquisitionOption
        """
        # Map quality
        quality_mapping = {
            QualityLevel.LOSSLESS: TrackQuality.LOSSLESS,
            QualityLevel.HIGH: TrackQuality.HIGH,
            QualityLevel.MEDIUM: TrackQuality.MEDIUM,
            QualityLevel.LOW: TrackQuality.LOW,
            QualityLevel.UNKNOWN: TrackQuality.UNKNOWN
        }
        
        quality = quality_mapping.get(
            platform_info['quality'],
            TrackQuality.UNKNOWN
        )
        
        # Generate mock URL
        url = None
        if platform == 'beatport':
            url = f"https://www.beatport.com/track/{metadata.title}/{metadata.artist}"
        elif platform == 'spotify':
            url = f"https://open.spotify.com/search/{metadata.artist} {metadata.title}"
        
        return AcquisitionOption(
            source=platform,
            type=platform_info['type'].value,
            quality=quality,
            price=platform_info.get('typical_price'),
            currency='USD' if platform_info.get('typical_price') else None,
            url=url,
            requires_subscription=platform_info.get('requires_subscription', False),
            region_restricted=platform_info.get('region_restricted', False),
            availability='available',
            notes=f"Formats: {', '.join(platform_info.get('formats', []))}"
        )
    
    async def _prioritize_options(self) -> List[AcquisitionOption]:
        """
        Prioritize and filter acquisition options.
        
        Returns:
            Filtered and sorted list of options
        """
        filtered = []
        
        for option in self.sources_found:
            # Filter by price if max_price set
            if self.max_price and option.price:
                if option.price > self.max_price:
                    continue
            
            # Filter by quality preference
            if self.preferred_quality == 'lossless':
                if option.quality != TrackQuality.LOSSLESS:
                    # Still include high quality as backup
                    if option.quality != TrackQuality.HIGH:
                        continue
            
            filtered.append(option)
        
        # Sort by priority:
        # 1. Quality (highest first)
        # 2. Type (purchase > download > stream)
        # 3. Price (lowest first)
        
        type_priority = {
            'purchase': 3,
            'download': 2,
            'stream': 1,
            'vinyl': 1,
            'soulseek': 0
        }
        
        filtered.sort(
            key=lambda x: (
                -x.quality.value,
                -type_priority.get(x.type, 0),
                x.price or float('inf')
            )
        )
        
        return filtered
    
    def _generate_summary(self, options: List[AcquisitionOption]) -> str:
        """
        Generate summary of acquisition options.
        
        Args:
            options: List of acquisition options
        
        Returns:
            Summary string
        """
        if not options:
            return "No acquisition sources found"
        
        # Count by type
        by_type = {}
        for option in options:
            by_type[option.type] = by_type.get(option.type, 0) + 1
        
        # Find best option
        best = options[0]
        
        summary_parts = [
            f"Found {len(options)} sources:",
            f"Best: {best.source} ({best.quality.value})"
        ]
        
        if best.price:
            summary_parts.append(f"${best.price:.2f}")
        
        # Add type breakdown
        type_summary = ", ".join(
            f"{count} {type_}" for type_, count in by_type.items()
        )
        summary_parts.append(f"Types: {type_summary}")
        
        return " | ".join(summary_parts)
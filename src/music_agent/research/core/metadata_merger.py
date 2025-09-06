"""
Metadata Merger - Intelligent merging of metadata from multiple sources

Handles conflicting data, confidence scoring, and optimal data selection.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from collections import Counter
from datetime import datetime
import difflib

from ..models import UniversalTrackMetadata, PlatformMetadata

logger = logging.getLogger(__name__)


class MergeStrategy(Enum):
    """Strategies for merging conflicting metadata."""
    HIGHEST_CONFIDENCE = "highest_confidence"  # Use source with highest confidence
    MAJORITY_VOTE = "majority_vote"            # Use most common value
    PREFER_DETAILED = "prefer_detailed"        # Prefer more detailed/complete data
    MANUAL = "manual"                          # Require manual resolution
    WEIGHTED_AVERAGE = "weighted_average"      # For numeric values


class SourceReliability:
    """Platform reliability scores for different data types."""
    
    SCORES = {
        # Overall reliability (0.0-1.0)
        "beatport": {
            "overall": 0.95,
            "genre": 1.0,
            "bpm": 0.95,
            "key": 0.95,
            "label": 0.95,
            "release_date": 0.9
        },
        "spotify": {
            "overall": 0.9,
            "audio_features": 0.95,
            "popularity": 1.0,
            "isrc": 0.95,
            "release_date": 0.85
        },
        "discogs": {
            "overall": 0.9,
            "credits": 0.95,
            "label": 0.95,
            "catalog_number": 1.0,
            "pressing_info": 1.0
        },
        "musicbrainz": {
            "overall": 0.85,
            "isrc": 0.9,
            "credits": 0.9,
            "relationships": 0.95
        },
        "deezer": {
            "overall": 0.85,
            "basic_metadata": 0.9,
            "isrc": 0.85
        },
        "soundcloud": {
            "overall": 0.7,
            "user_content": 0.6,
            "tags": 0.75
        },
        "youtube": {
            "overall": 0.6,
            "user_content": 0.5,
            "views": 1.0
        },
        "rekordbox": {
            "overall": 0.95,
            "user_data": 1.0,
            "dj_data": 1.0,
            "analyzed_data": 0.95
        }
    }
    
    @classmethod
    def get_score(cls, platform: str, field: str = "overall") -> float:
        """Get reliability score for platform and field."""
        platform_scores = cls.SCORES.get(platform.lower(), {})
        return platform_scores.get(field, platform_scores.get("overall", 0.5))


class MetadataMerger:
    """
    Intelligent metadata merger for combining data from multiple sources.
    
    Features:
    - Conflict resolution with multiple strategies
    - Confidence scoring
    - Field-specific merge rules
    - Data validation and normalization
    """
    
    def __init__(
        self,
        default_strategy: MergeStrategy = MergeStrategy.HIGHEST_CONFIDENCE,
        similarity_threshold: float = 0.85
    ):
        """
        Initialize metadata merger.
        
        Args:
            default_strategy: Default merge strategy
            similarity_threshold: Threshold for string similarity matching
        """
        self.default_strategy = default_strategy
        self.similarity_threshold = similarity_threshold
        
        # Field-specific strategies
        self.field_strategies = {
            'bpm': MergeStrategy.WEIGHTED_AVERAGE,
            'duration_ms': MergeStrategy.WEIGHTED_AVERAGE,
            'genre': MergeStrategy.MAJORITY_VOTE,
            'key': MergeStrategy.HIGHEST_CONFIDENCE,
            'isrc': MergeStrategy.HIGHEST_CONFIDENCE,
            'release_date': MergeStrategy.PREFER_DETAILED
        }
    
    def merge_multiple(
        self,
        metadata_list: List[UniversalTrackMetadata],
        base_metadata: Optional[UniversalTrackMetadata] = None
    ) -> UniversalTrackMetadata:
        """
        Merge multiple metadata objects into one.
        
        Args:
            metadata_list: List of metadata to merge
            base_metadata: Optional base metadata to merge into
        
        Returns:
            Merged UniversalTrackMetadata
        """
        if not metadata_list:
            return base_metadata or UniversalTrackMetadata()
        
        # Start with base or first metadata
        result = base_metadata or metadata_list[0]
        
        # Merge each metadata object
        for metadata in metadata_list[1:] if not base_metadata else metadata_list:
            result = self.merge_two(result, metadata)
        
        # Recalculate confidence after merging
        result.calculate_confidence_score()
        
        return result
    
    def merge_two(
        self,
        metadata1: UniversalTrackMetadata,
        metadata2: UniversalTrackMetadata
    ) -> UniversalTrackMetadata:
        """
        Merge two metadata objects intelligently.
        
        Args:
            metadata1: First metadata object
            metadata2: Second metadata object
        
        Returns:
            Merged metadata
        """
        # Create result starting with metadata1
        result = UniversalTrackMetadata()
        
        # Merge core fields
        result.title = self._merge_field('title', metadata1.title, metadata2.title)
        result.artist = self._merge_field('artist', metadata1.artist, metadata2.artist)
        result.album = self._merge_field('album', metadata1.album, metadata2.album)
        
        # Merge lists (combine unique)
        result.featured_artists = self._merge_lists(
            metadata1.featured_artists,
            metadata2.featured_artists
        )
        result.remixers = self._merge_lists(metadata1.remixers, metadata2.remixers)
        result.producers = self._merge_lists(metadata1.producers, metadata2.producers)
        result.composers = self._merge_lists(metadata1.composers, metadata2.composers)
        result.sub_genres = self._merge_lists(metadata1.sub_genres, metadata2.sub_genres)
        result.tags = self._merge_lists(metadata1.tags, metadata2.tags)
        
        # Merge technical data
        result.duration_ms = self._merge_duration(
            metadata1.duration_ms,
            metadata2.duration_ms,
            metadata1.platform_data,
            metadata2.platform_data
        )
        result.bpm = self._merge_bpm(
            metadata1.bpm,
            metadata2.bpm,
            metadata1.platform_data,
            metadata2.platform_data
        )
        result.key = self._merge_key(
            metadata1.key,
            metadata2.key,
            metadata1.platform_data,
            metadata2.platform_data
        )
        
        # Merge identifiers (prefer non-None)
        for field in ['isrc', 'upc', 'musicbrainz_id', 'spotify_id', 'beatport_id']:
            val1 = getattr(metadata1, field)
            val2 = getattr(metadata2, field)
            setattr(result, field, val1 or val2)
        
        # Merge platform data
        result.platform_data = self._merge_platform_data(
            metadata1.platform_data,
            metadata2.platform_data
        )
        
        # Merge artwork
        result.artwork = self._merge_artwork(
            metadata1.artwork,
            metadata2.artwork
        )
        
        # Merge audio features (average if both present)
        for feature in ['energy', 'danceability', 'valence', 'acousticness',
                       'instrumentalness', 'liveness', 'speechiness']:
            val1 = getattr(metadata1, feature)
            val2 = getattr(metadata2, feature)
            if val1 is not None and val2 is not None:
                setattr(result, feature, (val1 + val2) / 2)
            else:
                setattr(result, feature, val1 or val2)
        
        # Merge status and quality
        result.status = max(metadata1.status, metadata2.status, key=lambda x: x.value)
        result.quality = max(metadata1.quality, metadata2.quality, key=lambda x: x.value)
        
        # Combine research sources
        result.research_sources = list(set(
            metadata1.research_sources + metadata2.research_sources
        ))
        
        return result
    
    def _merge_field(
        self,
        field_name: str,
        value1: Any,
        value2: Any
    ) -> Any:
        """
        Merge a single field using appropriate strategy.
        
        Args:
            field_name: Name of the field
            value1: First value
            value2: Second value
        
        Returns:
            Merged value
        """
        # Handle None values
        if value1 is None:
            return value2
        if value2 is None:
            return value1
        
        # If values are identical
        if value1 == value2:
            return value1
        
        # Get strategy for field
        strategy = self.field_strategies.get(field_name, self.default_strategy)
        
        if strategy == MergeStrategy.HIGHEST_CONFIDENCE:
            # For now, prefer value1 (could use platform reliability)
            return value1
        
        elif strategy == MergeStrategy.PREFER_DETAILED:
            # Prefer longer/more detailed value
            if isinstance(value1, str) and isinstance(value2, str):
                return value1 if len(value1) >= len(value2) else value2
            return value1
        
        else:
            return value1
    
    def _merge_lists(self, list1: List, list2: List) -> List:
        """Merge two lists, keeping unique values."""
        combined = list1 + list2
        
        # For string lists, use fuzzy matching to avoid near-duplicates
        if combined and all(isinstance(x, str) for x in combined):
            unique = []
            for item in combined:
                if not any(
                    difflib.SequenceMatcher(None, item.lower(), u.lower()).ratio() 
                    > self.similarity_threshold
                    for u in unique
                ):
                    unique.append(item)
            return unique
        
        # For other types, simple unique
        return list(set(combined))
    
    def _merge_duration(
        self,
        duration1: Optional[int],
        duration2: Optional[int],
        platforms1: List[PlatformMetadata],
        platforms2: List[PlatformMetadata]
    ) -> Optional[int]:
        """
        Merge duration values with weighted average.
        
        Args:
            duration1: First duration
            duration2: Second duration
            platforms1: Platform data for first
            platforms2: Platform data for second
        
        Returns:
            Merged duration
        """
        if duration1 is None:
            return duration2
        if duration2 is None:
            return duration1
        
        # If very close (within 1 second), use average
        if abs(duration1 - duration2) < 1000:
            return int((duration1 + duration2) / 2)
        
        # Otherwise, prefer more reliable source
        # For now, just return first
        return duration1
    
    def _merge_bpm(
        self,
        bpm1: Optional[float],
        bpm2: Optional[float],
        platforms1: List[PlatformMetadata],
        platforms2: List[PlatformMetadata]
    ) -> Optional[float]:
        """
        Merge BPM values intelligently.
        
        Args:
            bpm1: First BPM
            bpm2: Second BPM
            platforms1: Platform data for first
            platforms2: Platform data for second
        
        Returns:
            Merged BPM
        """
        if bpm1 is None:
            return bpm2
        if bpm2 is None:
            return bpm1
        
        # Check for half/double time
        if abs(bpm1 * 2 - bpm2) < 2:
            # bpm2 is double of bpm1
            return bpm2
        elif abs(bpm2 * 2 - bpm1) < 2:
            # bpm1 is double of bpm2
            return bpm1
        
        # If very close (within 1 BPM), use average
        if abs(bpm1 - bpm2) < 1:
            return round((bpm1 + bpm2) / 2, 1)
        
        # Prefer Beatport/Rekordbox for BPM
        for platform in platforms1:
            if platform.platform in ['beatport', 'rekordbox']:
                return bpm1
        
        for platform in platforms2:
            if platform.platform in ['beatport', 'rekordbox']:
                return bpm2
        
        return bpm1
    
    def _merge_key(
        self,
        key1: Optional[str],
        key2: Optional[str],
        platforms1: List[PlatformMetadata],
        platforms2: List[PlatformMetadata]
    ) -> Optional[str]:
        """
        Merge musical key values.
        
        Args:
            key1: First key
            key2: Second key
            platforms1: Platform data for first
            platforms2: Platform data for second
        
        Returns:
            Merged key
        """
        if key1 is None:
            return key2
        if key2 is None:
            return key1
        
        # Normalize keys for comparison
        key1_norm = self._normalize_key(key1)
        key2_norm = self._normalize_key(key2)
        
        if key1_norm == key2_norm:
            return key1  # Return original format
        
        # Prefer Beatport/Rekordbox for key
        for platform in platforms1:
            if platform.platform in ['beatport', 'rekordbox', 'spotify']:
                return key1
        
        for platform in platforms2:
            if platform.platform in ['beatport', 'rekordbox', 'spotify']:
                return key2
        
        return key1
    
    def _normalize_key(self, key: str) -> str:
        """Normalize musical key notation."""
        if not key:
            return ""
        
        # Convert various notations to standard
        key = key.strip().replace('♯', '#').replace('♭', 'b')
        
        # Handle minor notations
        key = key.replace('min', 'm').replace('Min', 'm')
        key = key.replace('MAJ', '').replace('maj', '').replace('Major', '')
        
        return key
    
    def _merge_platform_data(
        self,
        platforms1: List[PlatformMetadata],
        platforms2: List[PlatformMetadata]
    ) -> List[PlatformMetadata]:
        """Merge platform data lists."""
        result = []
        seen_platforms = set()
        
        # Add all from first list
        for pd in platforms1:
            result.append(pd)
            seen_platforms.add(pd.platform)
        
        # Add new platforms from second list
        for pd in platforms2:
            if pd.platform not in seen_platforms:
                result.append(pd)
            else:
                # Update existing if higher confidence
                for i, existing in enumerate(result):
                    if existing.platform == pd.platform:
                        if pd.confidence_score > existing.confidence_score:
                            result[i] = pd
                        break
        
        return result
    
    def _merge_artwork(self, artwork1: List, artwork2: List) -> List:
        """Merge artwork lists, avoiding duplicates."""
        result = artwork1.copy()
        
        # Add unique artwork from second list
        existing_urls = {art.url for art in result}
        
        for art in artwork2:
            if art.url not in existing_urls:
                result.append(art)
        
        # Sort by priority and size
        result.sort(key=lambda a: (a.priority, -(a.width or 0)))
        
        return result
    
    def calculate_merge_confidence(
        self,
        metadata_list: List[UniversalTrackMetadata]
    ) -> float:
        """
        Calculate confidence score for merged metadata.
        
        Args:
            metadata_list: List of metadata objects that were merged
        
        Returns:
            Confidence score (0.0-1.0)
        """
        if not metadata_list:
            return 0.0
        
        # Factors for confidence
        source_count = len(metadata_list)
        platform_diversity = len(set(
            platform
            for metadata in metadata_list
            for platform in metadata.research_sources
        ))
        
        # Agreement on core fields
        titles = [m.title for m in metadata_list if m.title]
        artists = [m.artist for m in metadata_list if m.artist]
        
        title_agreement = 1.0
        if len(titles) > 1:
            # Check similarity of titles
            similarities = []
            for i in range(len(titles) - 1):
                for j in range(i + 1, len(titles)):
                    sim = difflib.SequenceMatcher(
                        None,
                        titles[i].lower(),
                        titles[j].lower()
                    ).ratio()
                    similarities.append(sim)
            title_agreement = sum(similarities) / len(similarities) if similarities else 1.0
        
        # Calculate overall confidence
        confidence = (
            min(source_count / 3, 1.0) * 0.3 +  # More sources is better
            min(platform_diversity / 5, 1.0) * 0.2 +  # Platform diversity
            title_agreement * 0.5  # Agreement on title
        )
        
        return round(confidence, 2)
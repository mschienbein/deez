"""
Metadata Analyst - Synthesis and Conflict Resolution Agent

Receives raw data from multiple platforms and performs intelligent metadata synthesis.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from collections import Counter
from datetime import datetime
import difflib

from .base import ResearchAgent, AgentRole
from ..core.research_context import (
    ResearchContext, ConflictReport, ConflictType,
    PlatformResult
)
from ..core.metadata_merger import MetadataMerger, MergeStrategy, SourceReliability
from ...models import UniversalTrackMetadata, PlatformMetadata

logger = logging.getLogger(__name__)


class MetadataAnalyst(ResearchAgent):
    """
    Specialist agent for analyzing and merging metadata from multiple sources.
    
    Responsibilities:
    - Parse platform-specific responses into universal format
    - Identify and resolve conflicts
    - Weight data by source reliability
    - Synthesize final metadata
    - Generate conflict reports
    """
    
    # Minimum similarity threshold for matching
    SIMILARITY_THRESHOLD = 0.85
    
    # Critical fields that must match for track identification
    CRITICAL_FIELDS = ['title', 'artist']
    
    # Fields where conflicts are expected and acceptable
    ACCEPTABLE_CONFLICT_FIELDS = ['popularity', 'play_count', 'likes', 'comments']
    
    def __init__(
        self,
        context: ResearchContext,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Metadata Analyst.
        
        Args:
            context: Shared research context
            config: Optional configuration
        """
        super().__init__(
            name="MetadataAnalyst",
            role=AgentRole.METADATA_ANALYST,
            context=context,
            config=config or {}
        )
        
        # Configuration
        self.merge_strategy = MergeStrategy[
            self.config.get('merge_strategy', 'HIGHEST_CONFIDENCE').upper()
        ]
        self.require_consensus = self.config.get('require_consensus', False)
        self.min_sources = self.config.get('min_sources', 2)
        
        # Initialize merger
        self.merger = MetadataMerger(
            default_strategy=self.merge_strategy,
            similarity_threshold=self.SIMILARITY_THRESHOLD
        )
        
        # Track analysis state
        self.metadata_objects: List[UniversalTrackMetadata] = []
        self.conflicts_found: List[ConflictReport] = []
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute metadata analysis and merging.
        
        Returns:
            Analysis results with merged metadata
        """
        self.start()
        
        try:
            # Step 1: Extract metadata from platform results
            self.log("Extracting metadata from platform results")
            extracted = await self._extract_metadata()
            
            if not extracted:
                self.log_error("No valid metadata extracted from any platform")
                self.complete(success=False)
                return {'success': False, 'error': 'No metadata available'}
            
            self.log(f"Extracted {len(extracted)} metadata objects")
            
            # Step 2: Validate track identity
            self.log("Validating track identity across sources")
            if not await self._validate_track_identity(extracted):
                self.log_error("Track identity validation failed - sources disagree")
                self.complete(success=False)
                return {'success': False, 'error': 'Track identity mismatch'}
            
            # Step 3: Analyze conflicts
            self.log("Analyzing metadata conflicts")
            conflicts = await self._analyze_conflicts(extracted)
            for conflict in conflicts:
                self.context.add_conflict(conflict)
            
            self.log(f"Found {len(conflicts)} conflicts")
            
            # Step 4: Merge metadata
            self.log("Merging metadata from all sources")
            merged = await self._merge_metadata(extracted)
            
            if not merged:
                self.log_error("Failed to merge metadata")
                self.complete(success=False)
                return {'success': False, 'error': 'Merge failed'}
            
            # Step 5: Enhance with cross-references
            self.log("Enhancing with cross-references")
            merged = await self._enhance_metadata(merged)
            
            # Step 6: Calculate final confidence
            confidence = self._calculate_final_confidence(extracted, conflicts)
            merged.confidence_score = confidence
            
            # Store in context
            self.context.merged_metadata = merged
            
            self.log(f"Metadata merged successfully: {merged.artist} - {merged.title}")
            self.log(f"Final confidence: {confidence:.1%}")
            
            self.complete(success=True)
            
            return {
                'success': True,
                'metadata': merged,
                'conflicts': len(conflicts),
                'confidence': confidence,
                'sources_used': len(extracted)
            }
            
        except Exception as e:
            self.log_error(f"Analysis failed: {str(e)}")
            self.complete(success=False)
            return {'success': False, 'error': str(e)}
    
    async def _extract_metadata(self) -> List[UniversalTrackMetadata]:
        """Extract metadata objects from platform results."""
        extracted = []
        
        for platform, result in self.context.platform_results.items():
            if not result.success or not result.data:
                continue
            
            try:
                # Convert platform data to UniversalTrackMetadata
                metadata = self._platform_to_universal(platform, result.data)
                
                if metadata:
                    # Add platform metadata
                    platform_meta = PlatformMetadata(
                        platform=platform,
                        platform_id=result.data.get('platform_id'),
                        url=result.data.get('url'),
                        last_fetched=datetime.utcnow(),
                        confidence_score=result.confidence,
                        raw_data=result.data
                    )
                    metadata.platform_data.append(platform_meta)
                    metadata.research_sources.append(platform)
                    
                    extracted.append(metadata)
                    self.log(f"Extracted metadata from {platform}")
                    
            except Exception as e:
                self.log_error(f"Failed to extract from {platform}: {e}")
        
        return extracted
    
    def _platform_to_universal(
        self,
        platform: str,
        data: Dict[str, Any]
    ) -> Optional[UniversalTrackMetadata]:
        """
        Convert platform-specific data to UniversalTrackMetadata.
        
        Args:
            platform: Platform name
            data: Platform-specific data
        
        Returns:
            UniversalTrackMetadata or None if conversion fails
        """
        # Handle different platform response formats
        tracks = data.get('tracks', [])
        
        if not tracks:
            # Some platforms might have different structure
            if 'results' in data:
                tracks = data['results']
            elif 'title' in data:
                # Direct track data
                tracks = [data]
        
        if not tracks:
            return None
        
        # Take first track (should be best match)
        track = tracks[0] if isinstance(tracks, list) else tracks
        
        # Create metadata object
        metadata = UniversalTrackMetadata()
        
        # Map common fields
        metadata.title = track.get('title', '')
        metadata.artist = track.get('artist', '')
        metadata.album = track.get('album')
        metadata.mix_name = track.get('mix')
        
        # Duration handling
        if 'duration_ms' in track:
            metadata.duration_ms = track['duration_ms']
        elif 'duration' in track:
            # Convert from seconds or string format
            duration = track['duration']
            if isinstance(duration, (int, float)):
                metadata.duration_ms = int(duration * 1000)
            elif isinstance(duration, str) and ':' in duration:
                # Parse MM:SS or HH:MM:SS format
                parts = duration.split(':')
                if len(parts) == 2:
                    metadata.duration_ms = (int(parts[0]) * 60 + int(parts[1])) * 1000
                elif len(parts) == 3:
                    metadata.duration_ms = (int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])) * 1000
        
        # Technical fields
        metadata.bpm = track.get('bpm')
        metadata.key = track.get('key')
        metadata.genre = track.get('genre')
        
        # IDs
        metadata.isrc = track.get('isrc')
        
        # Platform-specific IDs
        if platform == 'spotify':
            metadata.spotify_id = track.get('spotify_id') or track.get('platform_id')
        elif platform == 'beatport':
            metadata.beatport_id = track.get('beatport_id') or track.get('platform_id')
        elif platform == 'discogs':
            metadata.discogs_id = track.get('discogs_id') or track.get('platform_id')
        
        # Additional fields
        metadata.label = track.get('label')
        metadata.catalog_number = track.get('catalog_number')
        metadata.release_date = track.get('release_date')
        
        # Lists
        if 'remixers' in track:
            metadata.remixers = [track['remixers']] if isinstance(track['remixers'], str) else track['remixers']
        
        if 'style' in track:
            metadata.sub_genres = track['style'] if isinstance(track['style'], list) else [track['style']]
        
        # Audio features (mainly from Spotify)
        for feature in ['energy', 'danceability', 'valence', 'acousticness', 
                       'instrumentalness', 'liveness', 'speechiness']:
            if feature in track:
                setattr(metadata, feature, track[feature])
        
        # URLs
        if 'preview_url' in track:
            metadata.preview_url = track['preview_url']
        
        if 'url' in track:
            metadata.external_urls[platform] = track['url']
        elif 'external_urls' in track:
            metadata.external_urls.update(track['external_urls'])
        
        return metadata
    
    async def _validate_track_identity(
        self,
        metadata_list: List[UniversalTrackMetadata]
    ) -> bool:
        """
        Validate that all metadata refers to the same track.
        
        Args:
            metadata_list: List of metadata objects
        
        Returns:
            True if all metadata refers to same track
        """
        if len(metadata_list) <= 1:
            return True
        
        # Check critical fields match across sources
        for field in self.CRITICAL_FIELDS:
            values = [getattr(m, field) for m in metadata_list if getattr(m, field)]
            
            if not values:
                continue
            
            # Check similarity between all pairs
            for i in range(len(values) - 1):
                for j in range(i + 1, len(values)):
                    similarity = difflib.SequenceMatcher(
                        None,
                        values[i].lower(),
                        values[j].lower()
                    ).ratio()
                    
                    if similarity < self.SIMILARITY_THRESHOLD:
                        self.log_error(
                            f"Identity mismatch on {field}: "
                            f"'{values[i]}' vs '{values[j]}' "
                            f"(similarity: {similarity:.2%})"
                        )
                        
                        # Don't fail on slight artist variations
                        if field == 'artist' and similarity > 0.7:
                            continue
                        
                        return False
        
        return True
    
    async def _analyze_conflicts(
        self,
        metadata_list: List[UniversalTrackMetadata]
    ) -> List[ConflictReport]:
        """
        Analyze conflicts between metadata sources.
        
        Args:
            metadata_list: List of metadata objects
        
        Returns:
            List of conflict reports
        """
        conflicts = []
        
        if len(metadata_list) <= 1:
            return conflicts
        
        # Fields to check for conflicts
        check_fields = [
            ('bpm', ConflictType.BPM_MISMATCH),
            ('key', ConflictType.KEY_MISMATCH),
            ('duration_ms', ConflictType.DURATION_MISMATCH),
            ('genre', ConflictType.GENRE_DISAGREEMENT),
            ('release_date', ConflictType.DATE_CONFLICT)
        ]
        
        for field_name, conflict_type in check_fields:
            values = []
            for metadata in metadata_list:
                value = getattr(metadata, field_name)
                if value is not None:
                    # Get source platform
                    source = metadata.research_sources[0] if metadata.research_sources else 'unknown'
                    values.append((source, value))
            
            if len(values) <= 1:
                continue
            
            # Check if values conflict
            unique_values = set(v[1] for v in values)
            
            if len(unique_values) > 1:
                # Special handling for certain fields
                if field_name == 'bpm':
                    # Check for half/double time
                    bpm_values = [v[1] for v in values if isinstance(v[1], (int, float))]
                    if self._is_bpm_related(bpm_values):
                        continue
                
                elif field_name == 'duration_ms':
                    # Allow small variations (< 2 seconds)
                    duration_values = [v[1] for v in values if isinstance(v[1], int)]
                    if duration_values and max(duration_values) - min(duration_values) < 2000:
                        continue
                
                elif field_name == 'key':
                    # Check if keys are enharmonic equivalents
                    key_values = [v[1] for v in values if isinstance(v[1], str)]
                    if self._are_keys_equivalent(key_values):
                        continue
                
                # Create conflict report
                conflict = ConflictReport(
                    conflict_type=conflict_type,
                    field=field_name,
                    values=values,
                    resolution=None,
                    confidence=0.0
                )
                
                # Try to resolve
                conflict = self._resolve_conflict(conflict, metadata_list)
                conflicts.append(conflict)
        
        return conflicts
    
    def _is_bpm_related(self, bpm_values: List[float]) -> bool:
        """Check if BPM values are related (half/double time)."""
        if len(bpm_values) < 2:
            return True
        
        for i in range(len(bpm_values) - 1):
            for j in range(i + 1, len(bpm_values)):
                bpm1, bpm2 = bpm_values[i], bpm_values[j]
                
                # Check if one is roughly double/half of the other
                if abs(bpm1 * 2 - bpm2) < 2 or abs(bpm2 * 2 - bpm1) < 2:
                    return True
                
                # Check if very close
                if abs(bpm1 - bpm2) < 1:
                    return True
        
        return False
    
    def _are_keys_equivalent(self, keys: List[str]) -> bool:
        """Check if musical keys are equivalent."""
        if len(keys) < 2:
            return True
        
        # Normalize all keys
        normalized = [self._normalize_key(k) for k in keys]
        
        # Check if all normalized keys are the same
        return len(set(normalized)) == 1
    
    def _normalize_key(self, key: str) -> str:
        """Normalize musical key notation."""
        if not key:
            return ""
        
        key = key.strip().upper()
        
        # Handle different notations
        key = key.replace('♯', '#').replace('♭', 'B')
        key = key.replace('SHARP', '#').replace('FLAT', 'B')
        key = key.replace('MIN', 'M').replace('MINOR', 'M')
        key = key.replace('MAJ', '').replace('MAJOR', '')
        
        return key
    
    def _resolve_conflict(
        self,
        conflict: ConflictReport,
        metadata_list: List[UniversalTrackMetadata]
    ) -> ConflictReport:
        """
        Attempt to resolve a conflict.
        
        Args:
            conflict: Conflict report
            metadata_list: Source metadata
        
        Returns:
            Updated conflict report with resolution
        """
        # Use source reliability scores
        weighted_values = []
        
        for source, value in conflict.values:
            reliability = SourceReliability.get_score(source, conflict.field)
            weighted_values.append((value, reliability))
        
        # Sort by reliability
        weighted_values.sort(key=lambda x: x[1], reverse=True)
        
        if weighted_values:
            # Use most reliable source
            conflict.resolution = weighted_values[0][0]
            conflict.confidence = weighted_values[0][1]
            conflict.resolution_reason = f"Selected from {conflict.values[0][0]} (reliability: {weighted_values[0][1]:.2f})"
        
        return conflict
    
    async def _merge_metadata(
        self,
        metadata_list: List[UniversalTrackMetadata]
    ) -> Optional[UniversalTrackMetadata]:
        """
        Merge metadata using configured strategy.
        
        Args:
            metadata_list: List of metadata to merge
        
        Returns:
            Merged metadata or None if failed
        """
        if not metadata_list:
            return None
        
        if len(metadata_list) == 1:
            return metadata_list[0]
        
        try:
            # Use the merger
            merged = self.merger.merge_multiple(metadata_list)
            
            # Apply conflict resolutions
            for conflict in self.conflicts_found:
                if conflict.resolution is not None:
                    setattr(merged, conflict.field, conflict.resolution)
            
            return merged
            
        except Exception as e:
            self.log_error(f"Merge failed: {e}")
            return None
    
    async def _enhance_metadata(
        self,
        metadata: UniversalTrackMetadata
    ) -> UniversalTrackMetadata:
        """
        Enhance metadata with cross-references and derived data.
        
        Args:
            metadata: Merged metadata
        
        Returns:
            Enhanced metadata
        """
        # Add any missing IDs from platform results
        for platform, result in self.context.platform_results.items():
            if result.success and result.data:
                tracks = result.data.get('tracks', [])
                if tracks and isinstance(tracks, list):
                    track = tracks[0]
                    
                    # Try to get platform-specific IDs
                    if platform == 'spotify' and not metadata.spotify_id:
                        metadata.spotify_id = track.get('spotify_id')
                    elif platform == 'beatport' and not metadata.beatport_id:
                        metadata.beatport_id = track.get('beatport_id')
                    elif platform == 'musicbrainz' and not metadata.musicbrainz_id:
                        metadata.musicbrainz_id = track.get('recording_id')
        
        # Ensure research sources are complete
        metadata.research_sources = list(set(
            metadata.research_sources + list(self.context.platforms_searched)
        ))
        
        # Calculate metadata completeness
        metadata.metadata_completeness = self._calculate_completeness(metadata)
        
        # Add timestamp
        metadata.last_researched = datetime.utcnow()
        
        return metadata
    
    def _calculate_completeness(self, metadata: UniversalTrackMetadata) -> float:
        """Calculate how complete the metadata is."""
        required_fields = [
            'title', 'artist', 'duration_ms', 'bpm', 'key',
            'genre', 'label', 'release_date'
        ]
        
        optional_fields = [
            'album', 'isrc', 'catalog_number', 'remixers',
            'energy', 'danceability', 'preview_url'
        ]
        
        # Count present required fields
        required_present = sum(
            1 for field in required_fields
            if getattr(metadata, field, None) is not None
        )
        
        # Count present optional fields
        optional_present = sum(
            1 for field in optional_fields
            if getattr(metadata, field, None) is not None
        )
        
        # Weight: 70% required, 30% optional
        completeness = (
            (required_present / len(required_fields)) * 0.7 +
            (optional_present / len(optional_fields)) * 0.3
        )
        
        return min(completeness, 1.0)
    
    def _calculate_final_confidence(
        self,
        metadata_list: List[UniversalTrackMetadata],
        conflicts: List[ConflictReport]
    ) -> float:
        """
        Calculate final confidence score.
        
        Args:
            metadata_list: Source metadata
            conflicts: Conflicts found
        
        Returns:
            Confidence score (0.0-1.0)
        """
        # Base confidence from merger
        base_confidence = self.merger.calculate_merge_confidence(metadata_list)
        
        # Penalize for conflicts
        conflict_penalty = len(conflicts) * 0.05
        
        # Bonus for multiple agreeing sources
        source_bonus = min(len(metadata_list) / 5, 1.0) * 0.1
        
        # Calculate final confidence
        confidence = base_confidence - conflict_penalty + source_bonus
        
        return max(0.0, min(1.0, confidence))
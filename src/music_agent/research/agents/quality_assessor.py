"""
Quality Assessor - Metadata Validation and Quality Evaluation Agent

Evaluates the quality and completeness of merged metadata.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum

from .base import ResearchAgent, AgentRole
from ..core.research_context import (
    ResearchContext, QualityReport, TrackQuality,
    AcquisitionOption
)
from ...models import UniversalTrackMetadata

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Levels of validation strictness."""
    STRICT = "strict"      # All fields required
    STANDARD = "standard"  # Core fields required
    RELAXED = "relaxed"    # Minimal fields required


class FieldImportance(Enum):
    """Importance levels for metadata fields."""
    CRITICAL = 5    # Must have for track identification
    HIGH = 4        # Important for DJing/organization
    MEDIUM = 3      # Nice to have for completeness
    LOW = 2         # Optional enhancement
    MINIMAL = 1     # Rarely needed


class QualityAssessor(ResearchAgent):
    """
    Specialist agent for assessing metadata quality and completeness.
    
    Responsibilities:
    - Validate metadata completeness
    - Assess data quality and reliability
    - Check for inconsistencies
    - Generate quality reports
    - Make recommendations for improvement
    - Determine if track meets "SOLVED" criteria
    """
    
    # Field importance mapping
    FIELD_IMPORTANCE = {
        # Critical fields (must have)
        'title': FieldImportance.CRITICAL,
        'artist': FieldImportance.CRITICAL,
        'duration_ms': FieldImportance.CRITICAL,
        
        # High importance (for DJing)
        'bpm': FieldImportance.HIGH,
        'key': FieldImportance.HIGH,
        'genre': FieldImportance.HIGH,
        'energy': FieldImportance.HIGH,
        
        # Medium importance
        'album': FieldImportance.MEDIUM,
        'label': FieldImportance.MEDIUM,
        'release_date': FieldImportance.MEDIUM,
        'isrc': FieldImportance.MEDIUM,
        'remixers': FieldImportance.MEDIUM,
        'mix_name': FieldImportance.MEDIUM,
        
        # Low importance
        'catalog_number': FieldImportance.LOW,
        'producers': FieldImportance.LOW,
        'composers': FieldImportance.LOW,
        'danceability': FieldImportance.LOW,
        'valence': FieldImportance.LOW,
        
        # Minimal importance
        'comment': FieldImportance.MINIMAL,
        'grouping': FieldImportance.MINIMAL,
        'lyrics': FieldImportance.MINIMAL
    }
    
    # Validation rules
    VALIDATION_RULES = {
        'bpm': lambda x: isinstance(x, (int, float)) and 60 <= x <= 200,
        'key': lambda x: isinstance(x, str) and len(x) > 0,
        'duration_ms': lambda x: isinstance(x, int) and x > 0,
        'energy': lambda x: isinstance(x, float) and 0 <= x <= 1,
        'danceability': lambda x: isinstance(x, float) and 0 <= x <= 1,
        'valence': lambda x: isinstance(x, float) and 0 <= x <= 1,
        'year': lambda x: isinstance(x, int) and 1900 <= x <= datetime.now().year + 1
    }
    
    def __init__(
        self,
        context: ResearchContext,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Quality Assessor.
        
        Args:
            context: Shared research context
            config: Optional configuration
        """
        super().__init__(
            name="QualityAssessor",
            role=AgentRole.QUALITY_ASSESSOR,
            context=context,
            config=config or {}
        )
        
        # Configuration
        self.validation_level = ValidationLevel[
            self.config.get('validation_level', 'STANDARD').upper()
        ]
        self.thresholds = self.config.get('thresholds', {})
        self.check_sources = self.config.get('check_sources', True)
        
        # State
        self.issues_found: List[str] = []
        self.recommendations: List[str] = []
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute quality assessment.
        
        Returns:
            Quality assessment results
        """
        self.start()
        
        try:
            if not self.context.merged_metadata:
                self.log_error("No merged metadata to assess")
                self.complete(success=False)
                return {'success': False, 'error': 'No metadata available'}
            
            metadata = self.context.merged_metadata
            
            # Step 1: Check completeness
            self.log("Checking metadata completeness")
            completeness = await self._check_completeness(metadata)
            
            # Step 2: Validate data quality
            self.log("Validating data quality")
            quality_score = await self._validate_quality(metadata)
            
            # Step 3: Check consistency
            self.log("Checking data consistency")
            consistency_score = await self._check_consistency(metadata)
            
            # Step 4: Assess audio quality
            self.log("Assessing audio quality")
            audio_quality = await self._assess_audio_quality()
            
            # Step 5: Check source reliability
            self.log("Checking source reliability")
            source_reliability = await self._check_source_reliability()
            
            # Step 6: Generate recommendations
            self.log("Generating recommendations")
            self._generate_recommendations(metadata, completeness)
            
            # Step 7: Calculate final confidence
            confidence = self._calculate_confidence(
                completeness,
                quality_score,
                consistency_score,
                source_reliability
            )
            
            # Step 8: Determine if requirements are met
            meets_requirements = self._check_requirements(
                completeness,
                confidence,
                audio_quality
            )
            
            # Create quality report
            report = QualityReport(
                audio_quality=audio_quality,
                metadata_completeness=completeness,
                confidence_score=confidence,
                missing_fields=self._get_missing_fields(metadata),
                quality_issues=self.issues_found,
                recommendations=self.recommendations,
                meets_requirements=meets_requirements
            )
            
            # Store in context
            self.context.quality_report = report
            self.context.recommendations = self.recommendations
            
            self.log(f"Quality assessment complete: {confidence:.1%} confidence")
            self.log(f"Meets requirements: {meets_requirements}")
            
            self.complete(success=True)
            
            return {
                'success': True,
                'report': report,
                'completeness': completeness,
                'confidence': confidence,
                'meets_requirements': meets_requirements,
                'issues': len(self.issues_found),
                'recommendations': len(self.recommendations)
            }
            
        except Exception as e:
            self.log_error(f"Assessment failed: {str(e)}")
            self.complete(success=False)
            return {'success': False, 'error': str(e)}
    
    async def _check_completeness(self, metadata: UniversalTrackMetadata) -> float:
        """
        Check metadata completeness based on field importance.
        
        Args:
            metadata: Metadata to check
        
        Returns:
            Completeness score (0.0-1.0)
        """
        total_weight = 0
        present_weight = 0
        
        for field, importance in self.FIELD_IMPORTANCE.items():
            weight = importance.value
            total_weight += weight
            
            value = getattr(metadata, field, None)
            
            # Check if field is present and non-empty
            if value is not None:
                if isinstance(value, str) and value.strip():
                    present_weight += weight
                elif isinstance(value, (list, dict)) and value:
                    present_weight += weight
                elif isinstance(value, (int, float)):
                    present_weight += weight
        
        completeness = present_weight / total_weight if total_weight > 0 else 0
        
        # Log missing critical fields
        for field, importance in self.FIELD_IMPORTANCE.items():
            if importance == FieldImportance.CRITICAL:
                value = getattr(metadata, field, None)
                if not value:
                    self.issues_found.append(f"Missing critical field: {field}")
        
        return completeness
    
    async def _validate_quality(self, metadata: UniversalTrackMetadata) -> float:
        """
        Validate data quality using rules.
        
        Args:
            metadata: Metadata to validate
        
        Returns:
            Quality score (0.0-1.0)
        """
        validated_fields = 0
        total_fields = 0
        
        for field, validator in self.VALIDATION_RULES.items():
            value = getattr(metadata, field, None)
            
            if value is not None:
                total_fields += 1
                
                try:
                    if validator(value):
                        validated_fields += 1
                    else:
                        self.issues_found.append(
                            f"Invalid value for {field}: {value}"
                        )
                except Exception as e:
                    self.issues_found.append(
                        f"Validation error for {field}: {str(e)}"
                    )
        
        # Check for suspicious values
        if metadata.bpm:
            if metadata.bpm < 70 or metadata.bpm > 180:
                self.issues_found.append(
                    f"Unusual BPM value: {metadata.bpm} (might be half/double time)"
                )
        
        if metadata.duration_ms:
            duration_minutes = metadata.duration_ms / 60000
            if duration_minutes < 1:
                self.issues_found.append("Very short track (< 1 minute)")
            elif duration_minutes > 15:
                self.issues_found.append("Very long track (> 15 minutes)")
        
        return validated_fields / total_fields if total_fields > 0 else 1.0
    
    async def _check_consistency(self, metadata: UniversalTrackMetadata) -> float:
        """
        Check for internal consistency.
        
        Args:
            metadata: Metadata to check
        
        Returns:
            Consistency score (0.0-1.0)
        """
        consistency_checks = []
        
        # Check if remix info is consistent
        if metadata.remixers and metadata.mix_name:
            # Check if remixer name appears in mix name
            for remixer in metadata.remixers:
                if remixer.lower() in metadata.mix_name.lower():
                    consistency_checks.append(True)
                    break
            else:
                consistency_checks.append(False)
                self.issues_found.append(
                    f"Remixer '{metadata.remixers}' not found in mix name '{metadata.mix_name}'"
                )
        
        # Check if genre and sub-genres are consistent
        if metadata.genre and metadata.sub_genres:
            # Simple check: genre should relate to sub-genres
            genre_lower = metadata.genre.lower()
            related = any(
                genre_lower in sub.lower() or sub.lower() in genre_lower
                for sub in metadata.sub_genres
            )
            consistency_checks.append(related)
            if not related:
                self.issues_found.append(
                    f"Genre '{metadata.genre}' seems unrelated to sub-genres {metadata.sub_genres}"
                )
        
        # Check if audio features are consistent
        if metadata.energy is not None and metadata.danceability is not None:
            # High energy usually correlates with danceability
            if metadata.energy > 0.8 and metadata.danceability < 0.3:
                consistency_checks.append(False)
                self.issues_found.append(
                    "High energy but low danceability - might be incorrect"
                )
            else:
                consistency_checks.append(True)
        
        # Check BPM against genre expectations
        if metadata.bpm and metadata.genre:
            expected_bpm_ranges = {
                'techno': (120, 140),
                'house': (115, 130),
                'trance': (125, 145),
                'drum and bass': (160, 180),
                'dubstep': (135, 145),
                'hip hop': (70, 100),
                'ambient': (60, 90)
            }
            
            genre_lower = metadata.genre.lower()
            for genre_key, (min_bpm, max_bpm) in expected_bpm_ranges.items():
                if genre_key in genre_lower:
                    if metadata.bpm < min_bpm or metadata.bpm > max_bpm:
                        # Could be half/double time
                        half_bpm = metadata.bpm / 2
                        double_bpm = metadata.bpm * 2
                        
                        if not (min_bpm <= half_bpm <= max_bpm or min_bpm <= double_bpm <= max_bpm):
                            consistency_checks.append(False)
                            self.issues_found.append(
                                f"BPM {metadata.bpm} unusual for {metadata.genre} "
                                f"(expected {min_bpm}-{max_bpm})"
                            )
                        else:
                            consistency_checks.append(True)
                    else:
                        consistency_checks.append(True)
                    break
        
        if not consistency_checks:
            return 1.0
        
        return sum(consistency_checks) / len(consistency_checks)
    
    async def _assess_audio_quality(self) -> TrackQuality:
        """
        Assess audio quality based on acquisition options.
        
        Returns:
            Track quality level
        """
        if not self.context.acquisition_options:
            # Check if we have quality info from platforms
            if self.context.merged_metadata:
                for platform_data in self.context.merged_metadata.platform_data:
                    if 'quality' in platform_data.raw_data:
                        quality_str = platform_data.raw_data['quality']
                        if 'lossless' in quality_str.lower():
                            return TrackQuality.LOSSLESS
                        elif '320' in quality_str or 'high' in quality_str.lower():
                            return TrackQuality.HIGH
            
            return TrackQuality.UNKNOWN
        
        # Get best quality from acquisition options
        best_quality = TrackQuality.UNKNOWN
        
        for option in self.context.acquisition_options:
            if option.quality.value > best_quality.value:
                best_quality = option.quality
        
        return best_quality
    
    async def _check_source_reliability(self) -> float:
        """
        Check reliability of data sources.
        
        Returns:
            Reliability score (0.0-1.0)
        """
        if not self.context.platform_results:
            return 0.0
        
        # Import here to avoid circular dependency
        from ..core.metadata_merger import SourceReliability
        
        total_reliability = 0
        source_count = 0
        
        for platform, result in self.context.platform_results.items():
            if result.success:
                reliability = SourceReliability.get_score(platform)
                total_reliability += reliability
                source_count += 1
        
        if source_count == 0:
            return 0.0
        
        avg_reliability = total_reliability / source_count
        
        # Bonus for multiple reliable sources
        if source_count >= 3 and avg_reliability > 0.8:
            avg_reliability = min(1.0, avg_reliability * 1.1)
        
        return avg_reliability
    
    def _generate_recommendations(
        self,
        metadata: UniversalTrackMetadata,
        completeness: float
    ) -> None:
        """
        Generate recommendations for improvement.
        
        Args:
            metadata: Current metadata
            completeness: Completeness score
        """
        self.recommendations.clear()
        
        # Recommend missing critical fields
        for field, importance in self.FIELD_IMPORTANCE.items():
            if importance == FieldImportance.CRITICAL:
                value = getattr(metadata, field, None)
                if not value:
                    self.recommendations.append(
                        f"Add missing {field} - critical for track identification"
                    )
        
        # Recommend missing high-importance fields for DJing
        if not metadata.bpm:
            self.recommendations.append(
                "Analyze BPM - essential for DJ mixing"
            )
        
        if not metadata.key:
            self.recommendations.append(
                "Detect musical key - important for harmonic mixing"
            )
        
        if not metadata.energy:
            self.recommendations.append(
                "Add energy rating - helpful for set planning"
            )
        
        # Recommend additional sources if low confidence
        if len(self.context.platforms_searched) < 3:
            remaining_platforms = ['beatport', 'spotify', 'discogs', 'musicbrainz']
            for platform in remaining_platforms:
                if platform not in self.context.platforms_searched:
                    self.recommendations.append(
                        f"Search {platform} for additional metadata"
                    )
                    break
        
        # Recommend fixing issues
        if metadata.bpm and (metadata.bpm < 70 or metadata.bpm > 180):
            self.recommendations.append(
                "Verify BPM - current value seems unusual"
            )
        
        # Recommend audio analysis if missing features
        if not metadata.energy or not metadata.danceability:
            self.recommendations.append(
                "Run audio analysis to get energy and danceability scores"
            )
        
        # Recommend better quality sources
        best_acquisition = self.context.get_best_acquisition()
        if best_acquisition and best_acquisition.quality != TrackQuality.LOSSLESS:
            self.recommendations.append(
                "Look for lossless version for best quality"
            )
        
        # Limit recommendations
        self.recommendations = self.recommendations[:5]
    
    def _get_missing_fields(self, metadata: UniversalTrackMetadata) -> List[str]:
        """Get list of missing important fields."""
        missing = []
        
        for field, importance in self.FIELD_IMPORTANCE.items():
            if importance.value >= FieldImportance.MEDIUM.value:
                value = getattr(metadata, field, None)
                if not value:
                    missing.append(field)
        
        return missing
    
    def _calculate_confidence(
        self,
        completeness: float,
        quality: float,
        consistency: float,
        reliability: float
    ) -> float:
        """
        Calculate overall confidence score.
        
        Args:
            completeness: Completeness score
            quality: Quality score
            consistency: Consistency score
            reliability: Source reliability score
        
        Returns:
            Overall confidence (0.0-1.0)
        """
        # Weighted average
        confidence = (
            completeness * 0.3 +  # 30% weight on completeness
            quality * 0.2 +       # 20% weight on data quality
            consistency * 0.2 +   # 20% weight on consistency
            reliability * 0.3     # 30% weight on source reliability
        )
        
        # Apply penalties
        if len(self.issues_found) > 5:
            confidence *= 0.9  # 10% penalty for many issues
        
        if len(self.context.platforms_searched) < 2:
            confidence *= 0.85  # 15% penalty for single source
        
        return min(1.0, max(0.0, confidence))
    
    def _check_requirements(
        self,
        completeness: float,
        confidence: float,
        audio_quality: TrackQuality
    ) -> bool:
        """
        Check if track meets requirements for "SOLVED" status.
        
        Args:
            completeness: Completeness score
            confidence: Confidence score
            audio_quality: Audio quality level
        
        Returns:
            True if requirements are met
        """
        # Get thresholds from config or defaults
        min_completeness = self.thresholds.get('metadata_completeness', 0.8)
        min_confidence = self.thresholds.get('confidence_score', 0.7)
        min_platforms = self.thresholds.get('min_platforms', 2)
        
        # Check all requirements
        requirements = [
            completeness >= min_completeness,
            confidence >= min_confidence,
            len(self.context.platforms_searched) >= min_platforms,
            audio_quality.value >= TrackQuality.HIGH.value
        ]
        
        # For standard validation, need all requirements
        if self.validation_level == ValidationLevel.STRICT:
            return all(requirements)
        
        # For standard, need most requirements
        elif self.validation_level == ValidationLevel.STANDARD:
            return sum(requirements) >= 3
        
        # For relaxed, need basic requirements
        else:
            return completeness >= 0.6 and confidence >= 0.5
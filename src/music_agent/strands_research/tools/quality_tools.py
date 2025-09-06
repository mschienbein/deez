"""
Quality assessment tools for metadata validation.

These tools evaluate the quality and completeness of track metadata.
"""

from typing import Dict, Any, List, Optional
from strands import tool

from ..models.metadata import TrackQuality, QualityReport


@tool
def assess_quality(
    metadata: Dict[str, Any],
    sources: List[str],
    thresholds: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Assess the quality and completeness of track metadata.
    
    Evaluates metadata against quality thresholds and generates
    a comprehensive quality report with recommendations.
    
    Args:
        metadata: Track metadata to assess
        sources: List of platforms that provided data
        thresholds: Optional custom thresholds (default: 80% completeness, 70% confidence)
    
    Returns:
        Quality assessment report with scores and recommendations
    """
    if not thresholds:
        thresholds = {
            "completeness": 0.8,
            "confidence": 0.7,
            "min_sources": 2
        }
    
    # Check completeness
    completeness_result = check_completeness(metadata)
    completeness = completeness_result["score"]
    missing_fields = completeness_result["missing_fields"]
    
    # Validate metadata
    validation_result = validate_metadata(metadata)
    issues = validation_result["issues"]
    
    # Determine audio quality
    audio_quality = TrackQuality.UNKNOWN
    if "acquisition_options" in metadata:
        for option in metadata["acquisition_options"]:
            if option.get("quality") == "lossless":
                audio_quality = TrackQuality.LOSSLESS
                break
            elif option.get("quality") == "high":
                audio_quality = TrackQuality.HIGH
    
    # Calculate confidence based on sources and completeness
    source_score = min(len(sources) / 3, 1.0)
    confidence = (completeness * 0.5 + source_score * 0.5)
    
    # Generate recommendations
    recommendations = generate_recommendations({
        "metadata": metadata,
        "missing_fields": missing_fields,
        "issues": issues,
        "sources": sources
    })
    
    # Determine if requirements are met
    meets_requirements = (
        completeness >= thresholds["completeness"] and
        confidence >= thresholds["confidence"] and
        len(sources) >= thresholds["min_sources"] and
        len(issues) == 0
    )
    
    report = QualityReport(
        audio_quality=audio_quality,
        metadata_completeness=completeness,
        confidence_score=confidence,
        missing_fields=missing_fields,
        quality_issues=issues,
        recommendations=recommendations["suggestions"],
        meets_requirements=meets_requirements
    )
    
    return report.dict()


@tool
def check_completeness(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check metadata completeness and identify missing fields.
    
    Args:
        metadata: Track metadata to check
    
    Returns:
        Completeness score and list of missing fields
    """
    # Define field importance weights
    field_weights = {
        # Critical (weight: 5)
        "title": 5,
        "artist": 5,
        "duration_ms": 5,
        
        # High importance (weight: 4)
        "bpm": 4,
        "key": 4,
        "genre": 4,
        
        # Medium importance (weight: 3)
        "album": 3,
        "label": 3,
        "release_date": 3,
        "isrc": 3,
        
        # Low importance (weight: 2)
        "catalog_number": 2,
        "remixers": 2,
        "energy": 2,
        "danceability": 2,
        
        # Minimal importance (weight: 1)
        "composers": 1,
        "producers": 1,
        "featured_artists": 1
    }
    
    total_weight = sum(field_weights.values())
    present_weight = 0
    missing_fields = []
    missing_critical = []
    
    for field, weight in field_weights.items():
        value = metadata.get(field)
        
        if value is not None and value != "" and value != []:
            present_weight += weight
        else:
            missing_fields.append(field)
            if weight >= 4:  # High or critical importance
                missing_critical.append(field)
    
    completeness_score = present_weight / total_weight
    
    return {
        "score": completeness_score,
        "percentage": f"{completeness_score:.1%}",
        "missing_fields": missing_fields,
        "missing_critical": missing_critical,
        "present_weight": present_weight,
        "total_weight": total_weight
    }


@tool
def validate_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate metadata values for correctness and consistency.
    
    Checks for:
    - Invalid BPM ranges
    - Suspicious duration values
    - Key notation issues
    - Genre consistency
    
    Args:
        metadata: Track metadata to validate
    
    Returns:
        Validation results with any issues found
    """
    issues = []
    warnings = []
    
    # Validate BPM
    bpm = metadata.get("bpm")
    if bpm is not None:
        if bpm < 60:
            issues.append(f"BPM too low ({bpm}) - might be half-time")
        elif bpm > 200:
            issues.append(f"BPM too high ({bpm}) - might be double-time")
        elif bpm < 70 or bpm > 180:
            warnings.append(f"Unusual BPM ({bpm}) for most genres")
    
    # Validate duration
    duration_ms = metadata.get("duration_ms")
    if duration_ms is not None:
        duration_minutes = duration_ms / 60000
        if duration_minutes < 0.5:
            issues.append("Very short track (< 30 seconds)")
        elif duration_minutes > 20:
            issues.append("Very long track (> 20 minutes)")
        elif duration_minutes < 1:
            warnings.append("Short track (< 1 minute) - might be intro/outro")
    
    # Validate key
    key = metadata.get("key")
    if key:
        valid_keys = [
            "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B",
            "Cm", "C#m", "Dm", "D#m", "Em", "Fm", "F#m", "Gm", "G#m", "Am", "A#m", "Bm"
        ]
        
        # Normalize for comparison
        norm_key = key.replace(" ", "").replace("min", "m").replace("maj", "")
        if not any(norm_key.upper().startswith(k.upper()) for k in valid_keys):
            warnings.append(f"Unusual key notation: {key}")
    
    # Validate genre against BPM
    genre = metadata.get("genre", "").lower()
    if genre and bpm:
        expected_bpm = {
            "techno": (120, 140),
            "house": (115, 130),
            "trance": (125, 145),
            "drum and bass": (160, 180),
            "dubstep": (135, 145),
            "hip hop": (70, 100),
            "ambient": (60, 90)
        }
        
        for genre_key, (min_bpm, max_bpm) in expected_bpm.items():
            if genre_key in genre:
                if bpm < min_bpm or bpm > max_bpm:
                    # Check for half/double time
                    half_bpm = bpm / 2
                    double_bpm = bpm * 2
                    
                    if not (min_bpm <= half_bpm <= max_bpm or min_bpm <= double_bpm <= max_bpm):
                        warnings.append(
                            f"BPM {bpm} unusual for {genre} (expected {min_bpm}-{max_bpm})"
                        )
                break
    
    # Check audio features ranges
    for feature in ["energy", "danceability", "valence", "acousticness", "instrumentalness"]:
        value = metadata.get(feature)
        if value is not None:
            if value < 0 or value > 1:
                issues.append(f"{feature} out of range: {value} (should be 0-1)")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "total_problems": len(issues) + len(warnings)
    }


@tool
def generate_recommendations(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate recommendations for improving metadata quality.
    
    Args:
        context: Dictionary with metadata, missing fields, issues, and sources
    
    Returns:
        Prioritized list of recommendations
    """
    metadata = context.get("metadata", {})
    missing_fields = context.get("missing_fields", [])
    issues = context.get("issues", [])
    sources = context.get("sources", [])
    
    suggestions = []
    priority_high = []
    priority_medium = []
    priority_low = []
    
    # High priority: Fix critical missing fields
    critical_fields = ["title", "artist", "bpm", "key", "duration_ms"]
    for field in critical_fields:
        if field in missing_fields:
            priority_high.append(f"Add missing {field} - critical for track identification")
    
    # High priority: Fix validation issues
    for issue in issues:
        if "too low" in issue or "too high" in issue:
            priority_high.append(f"Verify and fix: {issue}")
    
    # Medium priority: Add more sources
    if len(sources) < 3:
        suggested_sources = ["beatport", "spotify", "discogs", "musicbrainz"]
        for source in suggested_sources:
            if source not in sources:
                priority_medium.append(f"Search {source} for additional metadata")
                break
    
    # Medium priority: Add DJ-relevant data
    if "bpm" in missing_fields:
        priority_medium.append("Analyze BPM - essential for DJ mixing")
    if "key" in missing_fields:
        priority_medium.append("Detect musical key - important for harmonic mixing")
    if "energy" not in metadata:
        priority_medium.append("Add energy rating - helpful for set planning")
    
    # Low priority: Enhance metadata
    if "album" in missing_fields:
        priority_low.append("Add album information for better organization")
    if "label" in missing_fields:
        priority_low.append("Add record label for completeness")
    if "isrc" in missing_fields:
        priority_low.append("Find ISRC code for universal identification")
    
    # Combine and limit recommendations
    suggestions = priority_high[:2] + priority_medium[:2] + priority_low[:1]
    
    return {
        "suggestions": suggestions[:5],  # Limit to 5 recommendations
        "priority_high": priority_high,
        "priority_medium": priority_medium,
        "priority_low": priority_low,
        "total_recommendations": len(priority_high) + len(priority_medium) + len(priority_low)
    }
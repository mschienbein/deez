"""
Metadata manipulation and merging tools.

These tools handle merging data from multiple sources and resolving conflicts.
"""

from typing import Dict, Any, List, Optional, Tuple
from strands import tool
import difflib
from collections import Counter

from ..models.metadata import TrackMetadata, ConflictReport


# Platform reliability scores for different data types
PLATFORM_RELIABILITY = {
    "beatport": {"overall": 0.95, "bpm": 0.98, "key": 0.95, "genre": 1.0},
    "spotify": {"overall": 0.90, "audio_features": 0.95, "isrc": 0.95},
    "discogs": {"overall": 0.90, "label": 0.95, "catalog": 1.0},
    "musicbrainz": {"overall": 0.85, "isrc": 0.90, "credits": 0.95},
    "deezer": {"overall": 0.85, "basic": 0.90},
    "soundcloud": {"overall": 0.70, "user_content": 0.60}
}


@tool
def merge_metadata(
    platform_results: List[Dict[str, Any]],
    strategy: str = "confidence_weighted"
) -> Dict[str, Any]:
    """
    Merge metadata from multiple platform sources.
    
    Intelligently combines data from different platforms,
    resolving conflicts and producing unified metadata.
    
    Args:
        platform_results: List of search results from different platforms
        strategy: Merge strategy - 'confidence_weighted', 'majority_vote', or 'prefer_detailed'
    
    Returns:
        Merged metadata with confidence scores and conflict reports
    """
    if not platform_results:
        return {"error": "No platform results to merge"}
    
    # Initialize merged metadata
    merged = TrackMetadata()
    conflicts = []
    
    # Extract tracks from each platform
    platform_tracks = []
    for result in platform_results:
        if not result.get("success"):
            continue
        
        platform = result.get("platform", "unknown")
        
        # Handle different response formats
        if "tracks" in result and result["tracks"]:
            track = result["tracks"][0]
        elif "recordings" in result and result["recordings"]:
            track = result["recordings"][0]
        elif "results" in result and result["results"]:
            track = result["results"][0]
        else:
            continue
        
        platform_tracks.append((platform, track))
    
    if not platform_tracks:
        return {"error": "No valid tracks found in results"}
    
    # Merge core fields
    merged.title = _merge_field("title", platform_tracks, strategy)
    merged.artist = _merge_field("artist", platform_tracks, strategy)
    merged.album = _merge_field("album", platform_tracks, strategy)
    
    # Merge technical fields with conflict detection
    bpm_values = [(p, t.get("bpm")) for p, t in platform_tracks if t.get("bpm")]
    if bpm_values:
        merged.bpm, bpm_conflict = _merge_bpm(bpm_values)
        if bpm_conflict:
            conflicts.append(bpm_conflict)
    
    key_values = [(p, t.get("key")) for p, t in platform_tracks if t.get("key")]
    if key_values:
        merged.key, key_conflict = _merge_key(key_values)
        if key_conflict:
            conflicts.append(key_conflict)
    
    # Merge other fields
    merged.genre = _merge_field("genre", platform_tracks, strategy)
    merged.label = _merge_field("label", platform_tracks, strategy)
    merged.isrc = _merge_field("isrc", platform_tracks, strategy)
    
    # Merge duration (convert to ms if needed)
    duration_values = []
    for platform, track in platform_tracks:
        if "duration_ms" in track:
            duration_values.append((platform, track["duration_ms"]))
        elif "duration" in track:
            # Convert seconds to ms
            duration_values.append((platform, track["duration"] * 1000))
        elif "length" in track:
            # Parse string format
            if isinstance(track["length"], str) and ":" in track["length"]:
                parts = track["length"].split(":")
                if len(parts) == 2:
                    ms = (int(parts[0]) * 60 + int(parts[1])) * 1000
                    duration_values.append((platform, ms))
            elif isinstance(track["length"], int):
                duration_values.append((platform, track["length"]))
    
    if duration_values:
        merged.duration_ms = int(sum(d for _, d in duration_values) / len(duration_values))
    
    # Merge audio features (from Spotify primarily)
    for platform, track in platform_tracks:
        if "audio_features" in track:
            features = track["audio_features"]
            merged.energy = features.get("energy")
            merged.danceability = features.get("danceability")
            merged.valence = features.get("valence")
            merged.acousticness = features.get("acousticness")
            merged.instrumentalness = features.get("instrumentalness")
            break
    
    # Track sources
    merged.sources = [p for p, _ in platform_tracks]
    
    # Calculate completeness and confidence
    merged.calculate_completeness()
    merged.confidence_score = calculate_confidence({
        "metadata": merged.dict(),
        "sources": merged.sources,
        "conflicts": len(conflicts)
    })
    
    return {
        "metadata": merged.dict(),
        "conflicts": [c.dict() for c in conflicts],
        "sources": merged.sources,
        "confidence": merged.confidence_score
    }


def _merge_field(
    field: str,
    platform_tracks: List[Tuple[str, Dict]],
    strategy: str
) -> Optional[Any]:
    """Merge a single field using the specified strategy."""
    values = [(p, t.get(field)) for p, t in platform_tracks if t.get(field)]
    
    if not values:
        return None
    
    if len(values) == 1:
        return values[0][1]
    
    if strategy == "confidence_weighted":
        # Weight by platform reliability
        weighted = []
        for platform, value in values:
            weight = PLATFORM_RELIABILITY.get(platform, {}).get("overall", 0.5)
            weighted.append((value, weight))
        
        # Return highest weighted value
        weighted.sort(key=lambda x: x[1], reverse=True)
        return weighted[0][0]
    
    elif strategy == "majority_vote":
        # Return most common value
        value_counts = Counter(v for _, v in values)
        return value_counts.most_common(1)[0][0]
    
    else:  # prefer_detailed
        # Return longest/most detailed value
        if all(isinstance(v, str) for _, v in values):
            return max((v for _, v in values), key=len)
        return values[0][1]


def _merge_bpm(bpm_values: List[Tuple[str, float]]) -> Tuple[float, Optional[ConflictReport]]:
    """Merge BPM values, handling half/double time."""
    if not bpm_values:
        return None, None
    
    bpms = [bpm for _, bpm in bpm_values]
    
    # Check for half/double time relationships
    normalized_bpms = []
    for bpm in bpms:
        # If BPM is very high or low, check if normalizing helps
        if bpm > 150:
            if any(abs(bpm / 2 - other) < 2 for other in bpms):
                normalized_bpms.append(bpm / 2)
            else:
                normalized_bpms.append(bpm)
        elif bpm < 80:
            if any(abs(bpm * 2 - other) < 2 for other in bpms):
                normalized_bpms.append(bpm * 2)
            else:
                normalized_bpms.append(bpm)
        else:
            normalized_bpms.append(bpm)
    
    # If all normalized BPMs are close, use average
    if max(normalized_bpms) - min(normalized_bpms) < 2:
        final_bpm = sum(normalized_bpms) / len(normalized_bpms)
        return round(final_bpm, 1), None
    
    # Otherwise, there's a conflict
    conflict = ConflictReport(
        field="bpm",
        values=bpm_values,
        resolution=normalized_bpms[0],
        resolution_reason="Using most reliable source",
        confidence=0.7
    )
    
    # Prefer Beatport for BPM
    for platform, bpm in bpm_values:
        if platform == "beatport":
            conflict.resolution = bpm
            conflict.confidence = 0.95
            break
    
    return conflict.resolution, conflict


def _merge_key(key_values: List[Tuple[str, str]]) -> Tuple[str, Optional[ConflictReport]]:
    """Merge musical key values."""
    if not key_values:
        return None, None
    
    # Normalize keys for comparison
    normalized = []
    for platform, key in key_values:
        norm_key = normalize_key(key)
        normalized.append((platform, key, norm_key))
    
    # Check if all normalized keys are the same
    unique_normalized = set(n for _, _, n in normalized)
    if len(unique_normalized) == 1:
        # All keys are equivalent, prefer Beatport notation
        for platform, key, _ in normalized:
            if platform == "beatport":
                return key, None
        return normalized[0][1], None
    
    # There's a conflict
    conflict = ConflictReport(
        field="key",
        values=key_values,
        resolution=key_values[0][1],
        resolution_reason="Keys don't match",
        confidence=0.6
    )
    
    # Prefer Beatport/Spotify for key
    for platform, key in key_values:
        if platform in ["beatport", "spotify"]:
            conflict.resolution = key
            conflict.confidence = 0.9
            break
    
    return conflict.resolution, conflict


@tool
def resolve_conflicts(
    conflicts: List[Dict[str, Any]],
    resolution_strategy: str = "reliability"
) -> List[Dict[str, Any]]:
    """
    Resolve metadata conflicts between sources.
    
    Args:
        conflicts: List of conflict reports
        resolution_strategy: How to resolve - 'reliability', 'majority', or 'manual'
    
    Returns:
        Resolved conflicts with explanations
    """
    resolved = []
    
    for conflict in conflicts:
        field = conflict["field"]
        values = conflict["values"]
        
        if resolution_strategy == "reliability":
            # Sort by platform reliability
            sorted_values = sorted(
                values,
                key=lambda x: PLATFORM_RELIABILITY.get(x[0], {}).get(field, 0.5),
                reverse=True
            )
            
            resolution = {
                "field": field,
                "resolution": sorted_values[0][1],
                "reason": f"Selected from {sorted_values[0][0]} (highest reliability)",
                "confidence": PLATFORM_RELIABILITY.get(sorted_values[0][0], {}).get(field, 0.5)
            }
        
        elif resolution_strategy == "majority":
            # Use most common value
            value_counts = Counter(v for _, v in values)
            most_common = value_counts.most_common(1)[0]
            
            resolution = {
                "field": field,
                "resolution": most_common[0],
                "reason": f"Majority vote ({most_common[1]}/{len(values)} sources)",
                "confidence": most_common[1] / len(values)
            }
        
        else:  # manual
            resolution = {
                "field": field,
                "resolution": None,
                "reason": "Requires manual resolution",
                "confidence": 0.0,
                "options": values
            }
        
        resolved.append(resolution)
    
    return resolved


@tool
def calculate_confidence(metadata_info: Dict[str, Any]) -> float:
    """
    Calculate confidence score for merged metadata.
    
    Factors include:
    - Number of sources
    - Platform reliability
    - Field completeness
    - Conflict count
    
    Args:
        metadata_info: Dictionary with metadata, sources, and conflicts
    
    Returns:
        Confidence score between 0.0 and 1.0
    """
    metadata = metadata_info.get("metadata", {})
    sources = metadata_info.get("sources", [])
    num_conflicts = metadata_info.get("conflicts", 0)
    
    # Base confidence from number of sources
    source_confidence = min(len(sources) / 3, 1.0) * 0.3
    
    # Platform reliability average
    platform_scores = [
        PLATFORM_RELIABILITY.get(s, {}).get("overall", 0.5)
        for s in sources
    ]
    reliability_confidence = (sum(platform_scores) / len(platform_scores)) * 0.3 if platform_scores else 0
    
    # Field completeness
    required_fields = ["title", "artist", "bpm", "key", "genre", "duration_ms"]
    present = sum(1 for f in required_fields if metadata.get(f))
    completeness_confidence = (present / len(required_fields)) * 0.3
    
    # Penalty for conflicts
    conflict_penalty = min(num_conflicts * 0.05, 0.2)
    
    # Calculate final confidence
    confidence = source_confidence + reliability_confidence + completeness_confidence - conflict_penalty
    
    return max(0.0, min(1.0, confidence))


@tool
def normalize_key(key: str) -> str:
    """
    Normalize musical key notation to standard format.
    
    Handles various notations:
    - Camelot (1A, 12B)
    - Open Key (1m, 12d)
    - Musical (C#m, Db Major)
    
    Args:
        key: Key string in any notation
    
    Returns:
        Normalized key string
    """
    if not key:
        return ""
    
    key = key.strip().upper()
    
    # Replace special characters
    key = key.replace('♯', '#').replace('♭', 'B').replace('SHARP', '#').replace('FLAT', 'B')
    
    # Normalize minor notations
    key = key.replace('MINOR', 'M').replace('MIN', 'M')
    key = key.replace('MAJOR', '').replace('MAJ', '')
    
    # Camelot Wheel conversion
    camelot_to_key = {
        '1A': 'ABM', '1B': 'AB',
        '2A': 'EBM', '2B': 'EB',
        '3A': 'BBM', '3B': 'BB',
        '4A': 'FM', '4B': 'F',
        '5A': 'CM', '5B': 'C',
        '6A': 'GM', '6B': 'G',
        '7A': 'DM', '7B': 'D',
        '8A': 'AM', '8B': 'A',
        '9A': 'EM', '9B': 'E',
        '10A': 'BM', '10B': 'B',
        '11A': 'F#M', '11B': 'F#',
        '12A': 'C#M', '12B': 'C#'
    }
    
    if key in camelot_to_key:
        return camelot_to_key[key]
    
    return key


@tool
def normalize_bpm(bpm: float, reference_bpms: List[float] = None) -> float:
    """
    Normalize BPM to handle half/double time.
    
    Args:
        bpm: BPM value to normalize
        reference_bpms: Other BPM values for context
    
    Returns:
        Normalized BPM value
    """
    if not reference_bpms:
        return bpm
    
    avg_ref = sum(reference_bpms) / len(reference_bpms)
    
    # Check if this BPM is half time
    if bpm < 90 and avg_ref > 120:
        if abs(bpm * 2 - avg_ref) < 5:
            return bpm * 2
    
    # Check if this BPM is double time
    if bpm > 160 and avg_ref < 100:
        if abs(bpm / 2 - avg_ref) < 5:
            return bpm / 2
    
    return bpm
"""
Tools for the Strands music research agents.

These are capabilities that agents can use, defined with the @tool decorator.
"""

from .search_tools import (
    search_spotify,
    search_beatport,
    search_discogs,
    search_deezer,
    search_musicbrainz,
    search_soundcloud
)

from .metadata_tools import (
    merge_metadata,
    resolve_conflicts,
    calculate_confidence,
    normalize_key,
    normalize_bpm
)

from .quality_tools import (
    assess_quality,
    check_completeness,
    validate_metadata,
    generate_recommendations
)

from .acquisition_tools import (
    find_purchase_options,
    find_streaming_options,
    check_availability,
    get_best_source
)

__all__ = [
    # Search tools
    'search_spotify',
    'search_beatport',
    'search_discogs',
    'search_deezer',
    'search_musicbrainz',
    'search_soundcloud',
    
    # Metadata tools
    'merge_metadata',
    'resolve_conflicts',
    'calculate_confidence',
    'normalize_key',
    'normalize_bpm',
    
    # Quality tools
    'assess_quality',
    'check_completeness',
    'validate_metadata',
    'generate_recommendations',
    
    # Acquisition tools
    'find_purchase_options',
    'find_streaming_options',
    'check_availability',
    'get_best_source'
]
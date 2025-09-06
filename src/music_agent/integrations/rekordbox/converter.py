"""
Rekordbox Converter - Bidirectional conversion between Rekordbox and Universal metadata

Handles conversion between pyrekordbox objects and UniversalTrackMetadata.
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

from ...research.models import UniversalTrackMetadata, TrackQuality, TrackStatus, PlatformMetadata

logger = logging.getLogger(__name__)


class RekordboxConverter:
    """Convert between Rekordbox database objects and Universal metadata."""
    
    # Rekordbox color IDs to color names
    COLOR_MAP = {
        0: None,      # No color
        1: "pink",
        2: "red",
        3: "orange",
        4: "yellow",
        5: "green",
        6: "aqua",
        7: "blue",
        8: "purple"
    }
    
    # Musical key mappings
    KEY_TO_CAMELOT = {
        # Major keys
        "C": "8B", "G": "9B", "D": "10B", "A": "11B",
        "E": "12B", "B": "1B", "F#": "2B", "Gb": "2B",
        "Db": "3B", "C#": "3B", "Ab": "4B", "Eb": "5B",
        "Bb": "6B", "F": "7B",
        
        # Minor keys
        "Am": "8A", "Em": "9A", "Bm": "10A", "F#m": "11A",
        "Gbm": "11A", "C#m": "12A", "Dbm": "12A",
        "G#m": "1A", "Abm": "1A", "D#m": "2A", "Ebm": "2A",
        "Bbm": "3A", "A#m": "3A", "Fm": "4A", "Cm": "5A",
        "Gm": "6A", "Dm": "7A"
    }
    
    KEY_TO_OPEN_KEY = {
        # Major keys
        "C": "1d", "G": "2d", "D": "3d", "A": "4d",
        "E": "5d", "B": "6d", "F#": "7d", "Gb": "7d",
        "Db": "8d", "C#": "8d", "Ab": "9d", "Eb": "10d",
        "Bb": "11d", "F": "12d",
        
        # Minor keys
        "Am": "1m", "Em": "2m", "Bm": "3m", "F#m": "4m",
        "Gbm": "4m", "C#m": "5m", "Dbm": "5m",
        "G#m": "6m", "Abm": "6m", "D#m": "7m", "Ebm": "7m",
        "Bbm": "8m", "A#m": "8m", "Fm": "9m", "Cm": "10m",
        "Gm": "11m", "Dm": "12m"
    }
    
    @classmethod
    def from_rekordbox(cls, rb_content: Any) -> UniversalTrackMetadata:
        """
        Convert Rekordbox content object to UniversalTrackMetadata.
        
        Args:
            rb_content: Pyrekordbox content object
        
        Returns:
            UniversalTrackMetadata object
        """
        metadata = UniversalTrackMetadata()
        
        try:
            # Core identification
            metadata.title = rb_content.Title or ""
            metadata.artist = rb_content.Artist.Name if rb_content.Artist else ""
            metadata.album = rb_content.Album.Name if rb_content.Album else None
            
            # Additional contributors
            if rb_content.Remixer:
                metadata.remixers = [rb_content.Remixer]
            if rb_content.Composer:
                metadata.composers = [rb_content.Composer.Name] if hasattr(rb_content.Composer, 'Name') else [rb_content.Composer]
            
            # Release information
            metadata.label = rb_content.Label.Name if rb_content.Label else None
            metadata.track_number = rb_content.TrackNumber
            metadata.disc_number = rb_content.DiscNumber
            
            if rb_content.DateCreated:
                metadata.release_date = cls._convert_rekordbox_date(rb_content.DateCreated)
            
            # Classification
            metadata.genre = rb_content.Genre.Name if rb_content.Genre else None
            metadata.grouping = rb_content.Grouping
            metadata.comments = rb_content.Comments
            
            # Technical data
            metadata.duration_ms = rb_content.Length  # Already in ms
            metadata.bpm = rb_content.Tempo
            metadata.key = rb_content.Tonality
            
            # Convert key to Camelot and Open Key
            if metadata.key:
                metadata.key_camelot = cls.KEY_TO_CAMELOT.get(metadata.key)
                metadata.key_open_key = cls.KEY_TO_OPEN_KEY.get(metadata.key)
            
            # Audio quality
            metadata.bitrate = rb_content.BitRate
            metadata.sample_rate = rb_content.SampleRate
            
            # Determine format from file extension
            if rb_content.FolderPath:
                file_path = Path(rb_content.FolderPath)
                metadata.format = file_path.suffix.lstrip('.').upper()
                metadata.file_path = str(file_path)
                metadata.file_size = rb_content.FileSize
            
            # Determine quality based on bitrate and format
            metadata.quality = cls._determine_quality(
                metadata.bitrate,
                metadata.format
            )
            
            # User/DJ data
            metadata.rating = rb_content.Rating
            metadata.color = rb_content.ColorID
            metadata.play_count = rb_content.PlayCount
            
            if rb_content.LastPlayDate:
                metadata.last_played = cls._convert_rekordbox_date(rb_content.LastPlayDate)
            
            # Timestamps
            if rb_content.DateAdded:
                metadata.discovered_at = cls._convert_rekordbox_date(rb_content.DateAdded)
            
            # Rekordbox-specific
            metadata.rekordbox_id = str(rb_content.ID)
            metadata.rekordbox_content_id = rb_content.ID
            metadata.rekordbox_synced = True
            metadata.rekordbox_sync_at = datetime.utcnow()
            
            # DJ-specific data
            if hasattr(rb_content, 'BeatGridLocked'):
                metadata.beat_grid_locked = rb_content.BeatGridLocked
            
            # Hot cues
            if hasattr(rb_content, 'HotCues'):
                for cue in rb_content.HotCues:
                    metadata.hot_cues.append({
                        'number': cue.Number,
                        'position': cue.Position,
                        'color': cls.COLOR_MAP.get(cue.ColorID),
                        'name': cue.Name
                    })
            
            # Memory cues
            if hasattr(rb_content, 'MemoryCues'):
                for cue in rb_content.MemoryCues:
                    metadata.memory_cues.append({
                        'position': cue.Position,
                        'name': cue.Name
                    })
            
            # Platform data
            metadata.add_platform_data(
                platform="rekordbox",
                track_id=str(rb_content.ID),
                confidence_score=1.0,
                extra_data={
                    'analyze_path': rb_content.AnalyzePath,
                    'image_path': rb_content.ImagePath,
                    'lyric_path': rb_content.LyricPath,
                    'sampler': rb_content.Sampler,
                    'mix_name': rb_content.MixName
                }
            )
            
            # Set status
            metadata.status = TrackStatus.SYNCED
            
            # Calculate confidence
            metadata.calculate_confidence_score()
            
        except Exception as e:
            logger.error(f"Error converting Rekordbox track: {e}")
        
        return metadata
    
    @classmethod
    def to_rekordbox_updates(cls, metadata: UniversalTrackMetadata) -> Dict[str, Any]:
        """
        Convert UniversalTrackMetadata to Rekordbox update dictionary.
        
        Only includes fields that can be directly updated in Rekordbox.
        
        Args:
            metadata: UniversalTrackMetadata object
        
        Returns:
            Dictionary of field updates for Rekordbox
        """
        updates = {}
        
        # Simple updatable fields
        if metadata.title:
            updates['Title'] = metadata.title
        
        if metadata.comments:
            updates['Comments'] = metadata.comments
        
        if metadata.grouping:
            updates['Grouping'] = metadata.grouping
        
        if metadata.rating is not None:
            updates['Rating'] = metadata.rating
        
        if metadata.color is not None:
            updates['ColorID'] = metadata.color
        
        if metadata.track_number is not None:
            updates['TrackNumber'] = metadata.track_number
        
        if metadata.disc_number is not None:
            updates['DiscNumber'] = metadata.disc_number
        
        # Note: Fields like Artist, Album, Genre, Label are references
        # and require special handling through the database
        
        return updates
    
    @classmethod
    def to_rekordbox_xml(cls, metadata: UniversalTrackMetadata) -> Dict[str, Any]:
        """
        Convert UniversalTrackMetadata to Rekordbox XML format.
        
        Args:
            metadata: UniversalTrackMetadata object
        
        Returns:
            Dictionary for Rekordbox XML
        """
        xml_data = {}
        
        # Required fields
        xml_data['TrackID'] = metadata.rekordbox_id or metadata.id
        xml_data['Name'] = metadata.title or "Unknown"
        xml_data['Artist'] = metadata.artist or "Unknown Artist"
        
        # Optional fields
        if metadata.album:
            xml_data['Album'] = metadata.album
        
        if metadata.genre:
            xml_data['Genre'] = metadata.genre
        
        if metadata.label:
            xml_data['Label'] = metadata.label
        
        if metadata.remixers:
            xml_data['Remixer'] = ', '.join(metadata.remixers)
        
        if metadata.composers:
            xml_data['Composer'] = ', '.join(metadata.composers)
        
        if metadata.bpm:
            xml_data['AverageBpm'] = str(metadata.bpm)
        
        if metadata.key:
            xml_data['Tonality'] = metadata.key
        
        if metadata.duration_ms:
            xml_data['TotalTime'] = str(metadata.duration_ms // 1000)
        
        if metadata.track_number:
            xml_data['TrackNumber'] = str(metadata.track_number)
        
        if metadata.disc_number:
            xml_data['DiscNumber'] = str(metadata.disc_number)
        
        if metadata.bitrate:
            xml_data['BitRate'] = str(metadata.bitrate)
        
        if metadata.sample_rate:
            xml_data['SampleRate'] = str(metadata.sample_rate)
        
        if metadata.comments:
            xml_data['Comments'] = metadata.comments
        
        if metadata.grouping:
            xml_data['Grouping'] = metadata.grouping
        
        if metadata.rating:
            xml_data['Rating'] = str(metadata.rating)
        
        if metadata.color:
            xml_data['Colour'] = str(metadata.color)
        
        if metadata.file_path:
            xml_data['Location'] = f"file://localhost{metadata.file_path}"
        
        if metadata.play_count:
            xml_data['PlayCount'] = str(metadata.play_count)
        
        return xml_data
    
    @classmethod
    def _determine_quality(cls, bitrate: Optional[int], format: Optional[str]) -> TrackQuality:
        """
        Determine track quality based on bitrate and format.
        
        Args:
            bitrate: Bitrate in kbps
            format: Audio format
        
        Returns:
            TrackQuality enum value
        """
        if not bitrate and not format:
            return TrackQuality.UNKNOWN
        
        # Check for lossless formats
        lossless_formats = ['FLAC', 'WAV', 'AIFF', 'ALAC', 'APE']
        if format and format.upper() in lossless_formats:
            return TrackQuality.LOSSLESS
        
        # Check for master quality
        if format and format.upper() == 'DSD':
            return TrackQuality.MASTER
        
        # Determine by bitrate
        if bitrate:
            if bitrate >= 320:
                return TrackQuality.HIGH
            elif bitrate >= 256:
                return TrackQuality.HIGH
            elif bitrate >= 128:
                return TrackQuality.MEDIUM
            else:
                return TrackQuality.LOW
        
        return TrackQuality.UNKNOWN
    
    @classmethod
    def _convert_rekordbox_date(cls, rb_date: Any) -> Optional[datetime]:
        """
        Convert Rekordbox date to datetime.
        
        Args:
            rb_date: Rekordbox date object/string
        
        Returns:
            datetime object or None
        """
        if not rb_date:
            return None
        
        try:
            if isinstance(rb_date, datetime):
                return rb_date
            elif isinstance(rb_date, str):
                # Try common date formats
                for fmt in [
                    '%Y-%m-%d %H:%M:%S',
                    '%Y-%m-%d',
                    '%Y/%m/%d',
                    '%d/%m/%Y'
                ]:
                    try:
                        return datetime.strptime(rb_date, fmt)
                    except ValueError:
                        continue
            
            # If it's a timestamp
            elif isinstance(rb_date, (int, float)):
                return datetime.fromtimestamp(rb_date)
            
        except Exception as e:
            logger.debug(f"Could not convert date {rb_date}: {e}")
        
        return None
    
    @classmethod
    def merge_with_rekordbox(
        cls,
        metadata: UniversalTrackMetadata,
        rb_content: Any,
        prefer_rekordbox: bool = False
    ) -> UniversalTrackMetadata:
        """
        Merge Rekordbox data into existing metadata.
        
        Args:
            metadata: Existing UniversalTrackMetadata
            rb_content: Rekordbox content object
            prefer_rekordbox: Prefer Rekordbox data in conflicts
        
        Returns:
            Merged UniversalTrackMetadata
        """
        # Convert Rekordbox to metadata
        rb_metadata = cls.from_rekordbox(rb_content)
        
        # Merge
        metadata.merge(rb_metadata, prefer_other=prefer_rekordbox)
        
        # Ensure Rekordbox sync info is preserved
        metadata.rekordbox_id = rb_metadata.rekordbox_id
        metadata.rekordbox_content_id = rb_metadata.rekordbox_content_id
        metadata.rekordbox_synced = True
        metadata.rekordbox_sync_at = datetime.utcnow()
        
        return metadata
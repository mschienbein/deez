"""
Rekordbox Sync Manager - Bidirectional synchronization

Handles importing from and exporting to Rekordbox database.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path

from .client import RekordboxClient
from .converter import RekordboxConverter
from ...research.models import UniversalTrackMetadata, TrackStatus

logger = logging.getLogger(__name__)


class RekordboxSync:
    """
    Manage bidirectional sync between research database and Rekordbox.
    
    Features:
    - Import existing Rekordbox library as research baseline
    - Export enhanced metadata back to Rekordbox
    - Track sync status and prevent duplicates
    - Handle conflicts intelligently
    """
    
    def __init__(
        self,
        client: Optional[RekordboxClient] = None,
        auto_backup: bool = True
    ):
        """
        Initialize sync manager.
        
        Args:
            client: RekordboxClient instance (creates new if None)
            auto_backup: Automatically backup before major operations
        """
        self.client = client or RekordboxClient()
        self.auto_backup = auto_backup
        self.sync_stats = {
            'imported': 0,
            'exported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def import_library(
        self,
        filter_analyzed: bool = False,
        filter_genre: Optional[str] = None
    ) -> List[UniversalTrackMetadata]:
        """
        Import entire Rekordbox library as research baseline.
        
        Args:
            filter_analyzed: Only import analyzed tracks
            filter_genre: Filter by specific genre
        
        Returns:
            List of imported tracks as UniversalTrackMetadata
        """
        imported_tracks = []
        self.sync_stats = {
            'imported': 0,
            'exported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        logger.info("Starting Rekordbox library import...")
        
        try:
            # Get all tracks from Rekordbox
            rb_tracks = self.client.get_all_tracks()
            total = len(rb_tracks)
            
            logger.info(f"Found {total} tracks in Rekordbox")
            
            for i, rb_track in enumerate(rb_tracks, 1):
                try:
                    # Apply filters
                    if filter_analyzed and not rb_track.AnalyzePath:
                        self.sync_stats['skipped'] += 1
                        continue
                    
                    if filter_genre and rb_track.Genre:
                        if filter_genre.lower() not in rb_track.Genre.Name.lower():
                            self.sync_stats['skipped'] += 1
                            continue
                    
                    # Convert to universal metadata
                    metadata = RekordboxConverter.from_rekordbox(rb_track)
                    metadata.status = TrackStatus.DISCOVERED
                    metadata.research_sources.append("rekordbox")
                    
                    imported_tracks.append(metadata)
                    self.sync_stats['imported'] += 1
                    
                    if i % 100 == 0:
                        logger.info(f"Imported {i}/{total} tracks...")
                    
                except Exception as e:
                    logger.error(f"Failed to import track {rb_track.ID}: {e}")
                    self.sync_stats['errors'] += 1
            
            logger.info(
                f"Import complete: {self.sync_stats['imported']} imported, "
                f"{self.sync_stats['skipped']} skipped, "
                f"{self.sync_stats['errors']} errors"
            )
            
            return imported_tracks
            
        except Exception as e:
            logger.error(f"Library import failed: {e}")
            return imported_tracks
    
    def export_track(
        self,
        metadata: UniversalTrackMetadata,
        update_only: bool = True
    ) -> bool:
        """
        Export single track metadata to Rekordbox.
        
        Args:
            metadata: Track metadata to export
            update_only: Only update existing tracks (don't add new)
        
        Returns:
            True if successful
        """
        try:
            # Check if track exists in Rekordbox
            if metadata.rekordbox_id:
                rb_track = self.client.get_track_by_id(metadata.rekordbox_id)
                
                if rb_track:
                    # Update existing track
                    updates = RekordboxConverter.to_rekordbox_updates(metadata)
                    
                    if self.client.update_track(metadata.rekordbox_id, updates):
                        metadata.rekordbox_synced = True
                        metadata.rekordbox_sync_at = datetime.utcnow()
                        self.sync_stats['updated'] += 1
                        logger.info(f"Updated track {metadata.title} in Rekordbox")
                        return True
                    else:
                        self.sync_stats['errors'] += 1
                        return False
            
            # Add new track if allowed
            if not update_only and metadata.file_path:
                rb_track = self.client.add_track(
                    metadata.file_path,
                    RekordboxConverter.to_rekordbox_xml(metadata)
                )
                
                if rb_track:
                    metadata.rekordbox_id = str(rb_track.ID if hasattr(rb_track, 'ID') else rb_track.get('TrackID'))
                    metadata.rekordbox_synced = True
                    metadata.rekordbox_sync_at = datetime.utcnow()
                    self.sync_stats['exported'] += 1
                    logger.info(f"Added track {metadata.title} to Rekordbox")
                    return True
            
            self.sync_stats['skipped'] += 1
            return False
            
        except Exception as e:
            logger.error(f"Failed to export track {metadata.title}: {e}")
            self.sync_stats['errors'] += 1
            return False
    
    def export_batch(
        self,
        tracks: List[UniversalTrackMetadata],
        update_only: bool = True,
        progress_callback: Optional[callable] = None
    ) -> Tuple[int, int]:
        """
        Export multiple tracks to Rekordbox.
        
        Args:
            tracks: List of tracks to export
            update_only: Only update existing tracks
            progress_callback: Optional callback for progress updates
        
        Returns:
            Tuple of (successful, failed) counts
        """
        successful = 0
        failed = 0
        total = len(tracks)
        
        logger.info(f"Starting batch export of {total} tracks to Rekordbox...")
        
        for i, track in enumerate(tracks, 1):
            if self.export_track(track, update_only):
                successful += 1
            else:
                failed += 1
            
            if progress_callback:
                progress_callback(i, total, track)
            
            if i % 50 == 0:
                logger.info(f"Exported {i}/{total} tracks...")
        
        logger.info(
            f"Batch export complete: {successful} successful, {failed} failed"
        )
        
        return successful, failed
    
    def sync_playlists(
        self,
        playlists: List[Dict[str, Any]],
        direction: str = "to_rekordbox"
    ) -> bool:
        """
        Sync playlists between research DB and Rekordbox.
        
        Args:
            playlists: List of playlist data
            direction: "to_rekordbox" or "from_rekordbox"
        
        Returns:
            True if successful
        """
        try:
            if direction == "from_rekordbox":
                # Import playlists from Rekordbox
                rb_playlists = self.client.get_playlists()
                
                for rb_playlist in rb_playlists:
                    # Get tracks in playlist
                    tracks = self.client.get_playlist_tracks(rb_playlist)
                    
                    playlist_data = {
                        'name': rb_playlist.Name,
                        'rekordbox_id': rb_playlist.ID,
                        'tracks': [
                            str(track.ID) for track in tracks
                        ]
                    }
                    
                    # Would store in research database
                    logger.info(f"Imported playlist: {rb_playlist.Name}")
            
            elif direction == "to_rekordbox":
                # Export playlists to Rekordbox
                for playlist in playlists:
                    # Create playlist in Rekordbox
                    rb_playlist = self.client.create_playlist(playlist['name'])
                    
                    if rb_playlist:
                        # Add tracks to playlist
                        # Implementation depends on pyrekordbox capabilities
                        logger.info(f"Exported playlist: {playlist['name']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Playlist sync failed: {e}")
            return False
    
    def find_duplicates(self) -> List[Tuple[UniversalTrackMetadata, UniversalTrackMetadata]]:
        """
        Find potential duplicate tracks between research DB and Rekordbox.
        
        Returns:
            List of potential duplicate pairs
        """
        duplicates = []
        
        try:
            # Get all Rekordbox tracks
            rb_tracks = self.client.get_all_tracks()
            
            # Build lookup index
            rb_index = {}
            for rb_track in rb_tracks:
                # Create key from artist + title
                key = f"{rb_track.Artist.Name if rb_track.Artist else ''}_{rb_track.Title or ''}".lower()
                rb_index[key] = rb_track
            
            # Check against research database
            # (Would need actual database query here)
            
            logger.info(f"Found {len(duplicates)} potential duplicates")
            
        except Exception as e:
            logger.error(f"Duplicate detection failed: {e}")
        
        return duplicates
    
    def verify_sync_status(
        self,
        tracks: List[UniversalTrackMetadata]
    ) -> Dict[str, List[UniversalTrackMetadata]]:
        """
        Verify sync status of tracks.
        
        Args:
            tracks: Tracks to verify
        
        Returns:
            Dictionary with sync status categories
        """
        status = {
            'synced': [],
            'out_of_sync': [],
            'not_in_rekordbox': [],
            'errors': []
        }
        
        for track in tracks:
            try:
                if not track.rekordbox_id:
                    status['not_in_rekordbox'].append(track)
                    continue
                
                rb_track = self.client.get_track_by_id(track.rekordbox_id)
                
                if not rb_track:
                    status['not_in_rekordbox'].append(track)
                    track.rekordbox_synced = False
                    continue
                
                # Check if data matches
                rb_metadata = RekordboxConverter.from_rekordbox(rb_track)
                
                # Simple comparison - could be more sophisticated
                if (
                    track.title == rb_metadata.title and
                    track.artist == rb_metadata.artist and
                    track.bpm == rb_metadata.bpm
                ):
                    status['synced'].append(track)
                else:
                    status['out_of_sync'].append(track)
                
            except Exception as e:
                logger.error(f"Error verifying track {track.title}: {e}")
                status['errors'].append(track)
        
        logger.info(
            f"Sync verification: {len(status['synced'])} synced, "
            f"{len(status['out_of_sync'])} out of sync, "
            f"{len(status['not_in_rekordbox'])} not in Rekordbox"
        )
        
        return status
    
    def backup_rekordbox(self, backup_path: Optional[str] = None) -> bool:
        """
        Create backup of Rekordbox database.
        
        Args:
            backup_path: Path for backup file
        
        Returns:
            True if successful
        """
        try:
            if not backup_path:
                backup_path = f"rekordbox_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
            
            # Export to XML as backup
            if self.client.export_to_xml(backup_path):
                logger.info(f"Created Rekordbox backup: {backup_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False
    
    def get_sync_stats(self) -> Dict[str, int]:
        """Get synchronization statistics."""
        return self.sync_stats.copy()
    
    def reset_stats(self) -> None:
        """Reset sync statistics."""
        self.sync_stats = {
            'imported': 0,
            'exported': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
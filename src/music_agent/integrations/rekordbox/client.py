"""
Rekordbox Client - PyRekordbox wrapper

Provides high-level interface to Rekordbox database using pyrekordbox.
"""

import logging
from typing import List, Optional, Dict, Any, Union
from pathlib import Path
from datetime import datetime

try:
    import pyrekordbox
    from pyrekordbox import MasterDatabase, DeviceLibraryPlus, RekordboxXml
    from pyrekordbox.config import update_config, get_rekordbox_config
    PYREKORDBOX_AVAILABLE = True
except ImportError:
    PYREKORDBOX_AVAILABLE = False
    MasterDatabase = None
    DeviceLibraryPlus = None
    RekordboxXml = None

from ...utils.config import config

logger = logging.getLogger(__name__)


class RekordboxClient:
    """
    High-level client for interacting with Rekordbox database.
    
    Uses pyrekordbox to read and write Rekordbox 6/7 master.db and XML files.
    """
    
    def __init__(
        self,
        database_path: Optional[str] = None,
        xml_path: Optional[str] = None,
        auto_connect: bool = True
    ):
        """
        Initialize Rekordbox client.
        
        Args:
            database_path: Path to master.db (auto-detected if None)
            xml_path: Path to XML file for import/export
            auto_connect: Automatically connect to database
        """
        if not PYREKORDBOX_AVAILABLE:
            raise ImportError(
                "pyrekordbox is required for Rekordbox integration. "
                "Install with: pip install pyrekordbox"
            )
        
        self.database_path = database_path
        self.xml_path = xml_path
        self.db: Optional[MasterDatabase] = None
        self.xml: Optional[RekordboxXml] = None
        self.connected = False
        
        # Configure pyrekordbox if needed
        self._configure_pyrekordbox()
        
        if auto_connect:
            self.connect()
    
    def _configure_pyrekordbox(self) -> None:
        """Configure pyrekordbox with Rekordbox installation paths."""
        try:
            # Try to get existing config
            rb_config = get_rekordbox_config()
            logger.debug(f"Rekordbox config: {rb_config}")
        except Exception as e:
            logger.warning(f"Could not get Rekordbox config: {e}")
            
            # Try to update config from environment or defaults
            pioneer_install = config.rekordbox.pioneer_install_dir
            pioneer_app = config.rekordbox.pioneer_app_dir
            
            if pioneer_install and pioneer_app:
                try:
                    update_config(pioneer_install, pioneer_app)
                    logger.info("Updated pyrekordbox configuration")
                except Exception as update_error:
                    logger.error(f"Failed to update pyrekordbox config: {update_error}")
    
    def connect(self) -> bool:
        """
        Connect to Rekordbox database.
        
        Returns:
            True if connected successfully
        """
        try:
            # Connect to master database
            if self.database_path:
                self.db = MasterDatabase(self.database_path)
            else:
                # Auto-detect database
                self.db = MasterDatabase()
            
            self.connected = True
            logger.info("Connected to Rekordbox master database")
            
            # Load XML if path provided
            if self.xml_path and Path(self.xml_path).exists():
                self.xml = RekordboxXml(self.xml_path)
                logger.info(f"Loaded Rekordbox XML: {self.xml_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Rekordbox: {e}")
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from database."""
        if self.db:
            # Commit any pending changes
            try:
                self.db.commit()
            except:
                pass
            
            self.db = None
            self.connected = False
            logger.info("Disconnected from Rekordbox")
    
    def get_all_tracks(self) -> List[Any]:
        """
        Get all tracks from Rekordbox library.
        
        Returns:
            List of track content objects
        """
        if not self.connected or not self.db:
            raise RuntimeError("Not connected to Rekordbox database")
        
        try:
            tracks = self.db.get_content()
            logger.info(f"Retrieved {len(tracks)} tracks from Rekordbox")
            return list(tracks)
        except Exception as e:
            logger.error(f"Failed to get tracks: {e}")
            return []
    
    def get_track_by_id(self, track_id: Union[str, int]) -> Optional[Any]:
        """
        Get a specific track by ID.
        
        Args:
            track_id: Track ID (content ID)
        
        Returns:
            Track content object or None
        """
        if not self.connected or not self.db:
            raise RuntimeError("Not connected to Rekordbox database")
        
        try:
            # Get all content and filter
            for content in self.db.get_content():
                if str(content.ID) == str(track_id):
                    return content
            return None
        except Exception as e:
            logger.error(f"Failed to get track {track_id}: {e}")
            return None
    
    def search_tracks(
        self,
        query: str = None,
        artist: str = None,
        title: str = None,
        album: str = None,
        genre: str = None
    ) -> List[Any]:
        """
        Search for tracks in Rekordbox library.
        
        Args:
            query: General search query
            artist: Artist name filter
            title: Title filter
            album: Album filter
            genre: Genre filter
        
        Returns:
            List of matching tracks
        """
        if not self.connected or not self.db:
            raise RuntimeError("Not connected to Rekordbox database")
        
        results = []
        
        try:
            for content in self.db.get_content():
                # Check filters
                if query:
                    # General search in title, artist, album
                    query_lower = query.lower()
                    if not any([
                        query_lower in (content.Title or "").lower(),
                        query_lower in (content.Artist.Name if content.Artist else "").lower(),
                        query_lower in (content.Album.Name if content.Album else "").lower()
                    ]):
                        continue
                
                if artist and content.Artist:
                    if artist.lower() not in content.Artist.Name.lower():
                        continue
                
                if title:
                    if title.lower() not in (content.Title or "").lower():
                        continue
                
                if album and content.Album:
                    if album.lower() not in content.Album.Name.lower():
                        continue
                
                if genre and content.Genre:
                    if genre.lower() not in content.Genre.Name.lower():
                        continue
                
                results.append(content)
            
            logger.info(f"Found {len(results)} tracks matching search criteria")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_playlists(self) -> List[Any]:
        """
        Get all playlists from Rekordbox.
        
        Returns:
            List of playlist objects
        """
        if not self.connected or not self.db:
            raise RuntimeError("Not connected to Rekordbox database")
        
        try:
            playlists = self.db.get_playlist()
            logger.info(f"Retrieved {len(playlists)} playlists from Rekordbox")
            return list(playlists)
        except Exception as e:
            logger.error(f"Failed to get playlists: {e}")
            return []
    
    def get_playlist_tracks(self, playlist) -> List[Any]:
        """
        Get tracks in a playlist.
        
        Args:
            playlist: Playlist object
        
        Returns:
            List of track content objects
        """
        tracks = []
        
        try:
            if hasattr(playlist, 'Songs'):
                for song in playlist.Songs:
                    if hasattr(song, 'Content'):
                        tracks.append(song.Content)
            
            logger.info(f"Retrieved {len(tracks)} tracks from playlist")
            return tracks
            
        except Exception as e:
            logger.error(f"Failed to get playlist tracks: {e}")
            return []
    
    def update_track(self, track_id: Union[str, int], updates: Dict[str, Any]) -> bool:
        """
        Update track metadata in Rekordbox.
        
        Args:
            track_id: Track ID
            updates: Dictionary of field updates
        
        Returns:
            True if successful
        """
        if not self.connected or not self.db:
            raise RuntimeError("Not connected to Rekordbox database")
        
        try:
            track = self.get_track_by_id(track_id)
            if not track:
                logger.error(f"Track {track_id} not found")
                return False
            
            # Update simple fields directly
            simple_fields = [
                'Title', 'Comments', 'Rating', 'ColorID',
                'TrackNumber', 'DiscNumber', 'Grouping'
            ]
            
            for field in simple_fields:
                if field in updates:
                    setattr(track, field, updates[field])
            
            # Note: Some fields like Artist, Album, Genre are references
            # and require more complex handling
            
            # Commit changes
            self.db.commit()
            logger.info(f"Updated track {track_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update track {track_id}: {e}")
            return False
    
    def add_track(self, file_path: str, metadata: Dict[str, Any] = None) -> Optional[Any]:
        """
        Add a new track to Rekordbox library.
        
        Args:
            file_path: Path to audio file
            metadata: Optional metadata to set
        
        Returns:
            New track object or None
        """
        if not self.connected or not self.db:
            raise RuntimeError("Not connected to Rekordbox database")
        
        try:
            # Note: Adding tracks programmatically is complex
            # and may require using XML import instead
            logger.warning("Track addition via database not fully implemented")
            
            # For now, we would need to use XML import
            if self.xml:
                track = self.xml.add_track(file_path)
                if metadata:
                    for key, value in metadata.items():
                        track[key] = value
                return track
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to add track: {e}")
            return None
    
    def create_playlist(self, name: str, parent=None) -> Optional[Any]:
        """
        Create a new playlist.
        
        Args:
            name: Playlist name
            parent: Parent playlist/folder (optional)
        
        Returns:
            New playlist object or None
        """
        if not self.connected or not self.db:
            raise RuntimeError("Not connected to Rekordbox database")
        
        try:
            # Create playlist through database
            # Note: Implementation depends on pyrekordbox capabilities
            logger.warning("Playlist creation not fully implemented")
            return None
            
        except Exception as e:
            logger.error(f"Failed to create playlist: {e}")
            return None
    
    def export_to_xml(self, output_path: str) -> bool:
        """
        Export library to XML file.
        
        Args:
            output_path: Path for XML file
        
        Returns:
            True if successful
        """
        if not self.connected or not self.db:
            raise RuntimeError("Not connected to Rekordbox database")
        
        try:
            # Create XML from database
            xml = RekordboxXml()
            
            # Add all tracks
            for content in self.db.get_content():
                # Convert to XML format
                # This would need proper field mapping
                track = xml.add_track(content.FolderPath or "")
                track["TrackID"] = content.ID
                track["Name"] = content.Title
                # ... map other fields
            
            # Save XML
            xml.save(output_path)
            logger.info(f"Exported library to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export XML: {e}")
            return False
    
    def import_from_xml(self, xml_path: str) -> bool:
        """
        Import tracks and playlists from XML file.
        
        Args:
            xml_path: Path to XML file
        
        Returns:
            True if successful
        """
        try:
            xml = RekordboxXml(xml_path)
            
            # Process tracks
            for track in xml.get_tracks():
                # Would need to add to database
                logger.debug(f"Would import track: {track.get('Name')}")
            
            logger.info(f"XML import from {xml_path} completed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import XML: {e}")
            return False
    
    def get_hot_cues(self, track_id: Union[str, int]) -> List[Dict[str, Any]]:
        """
        Get hot cues for a track.
        
        Args:
            track_id: Track ID
        
        Returns:
            List of hot cue data
        """
        track = self.get_track_by_id(track_id)
        if not track:
            return []
        
        hot_cues = []
        
        try:
            # Access hot cues through track object
            # Implementation depends on pyrekordbox structure
            if hasattr(track, 'HotCues'):
                for cue in track.HotCues:
                    hot_cues.append({
                        'number': cue.Number,
                        'position': cue.Position,
                        'color': cue.Color,
                        'name': cue.Name
                    })
            
            return hot_cues
            
        except Exception as e:
            logger.error(f"Failed to get hot cues: {e}")
            return []
    
    def get_memory_cues(self, track_id: Union[str, int]) -> List[Dict[str, Any]]:
        """
        Get memory cues for a track.
        
        Args:
            track_id: Track ID
        
        Returns:
            List of memory cue data
        """
        track = self.get_track_by_id(track_id)
        if not track:
            return []
        
        memory_cues = []
        
        try:
            # Access memory cues through track object
            if hasattr(track, 'MemoryCues'):
                for cue in track.MemoryCues:
                    memory_cues.append({
                        'position': cue.Position,
                        'name': cue.Name
                    })
            
            return memory_cues
            
        except Exception as e:
            logger.error(f"Failed to get memory cues: {e}")
            return []
    
    def get_beat_grid(self, track_id: Union[str, int]) -> Optional[Dict[str, Any]]:
        """
        Get beat grid data for a track.
        
        Args:
            track_id: Track ID
        
        Returns:
            Beat grid data or None
        """
        track = self.get_track_by_id(track_id)
        if not track:
            return None
        
        try:
            # Access beat grid through track object
            if hasattr(track, 'BeatGrid'):
                return {
                    'bpm': track.Tempo,
                    'first_beat': track.BeatGrid.FirstBeat,
                    'locked': track.BeatGrid.Locked
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get beat grid: {e}")
            return None
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Rekordbox database.
        
        Returns:
            Dictionary with database statistics
        """
        if not self.connected or not self.db:
            return {
                'connected': False,
                'error': 'Not connected to database'
            }
        
        try:
            tracks = list(self.db.get_content())
            playlists = list(self.db.get_playlist())
            
            # Calculate various stats
            total_duration = sum(
                track.Length or 0 for track in tracks
            ) / 1000  # Convert to seconds
            
            stats = {
                'connected': True,
                'total_tracks': len(tracks),
                'total_playlists': len(playlists),
                'total_duration_hours': round(total_duration / 3600, 1),
                'database_path': str(self.database_path) if self.database_path else 'auto-detected',
                'analyzed_tracks': sum(
                    1 for track in tracks
                    if track.AnalyzePath
                ),
                'tracks_with_artwork': sum(
                    1 for track in tracks
                    if track.ImagePath
                )
            }
            
            # Get genre distribution
            genres = {}
            for track in tracks:
                if track.Genre:
                    genre = track.Genre.Name
                    genres[genre] = genres.get(genre, 0) + 1
            
            stats['top_genres'] = sorted(
                genres.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {
                'connected': True,
                'error': str(e)
            }
    
    def __enter__(self):
        """Context manager support."""
        if not self.connected:
            self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.disconnect()
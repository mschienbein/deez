# Rekordbox Database Integration Notes

## Overview
This document outlines the strategy for integrating with Rekordbox's encrypted database, including decryption processes, data architecture decisions, and sync strategies.

## 1. Rekordbox Database Location

### macOS Path
```bash
~/Library/Pioneer/rekordbox/master.db
# Full path: /Users/[username]/Library/Pioneer/rekordbox/master.db

# Backup locations:
~/Library/Pioneer/rekordbox/master.backup.db
~/Library/Pioneer/rekordbox/masterPlaylists6.backup/
```

### Windows Path (for reference)
```
C:\Users\[username]\AppData\Roaming\Pioneer\rekordbox\master.db
```

## 2. Database Decryption Process

### Prerequisites
```bash
# Install SQLCipher on macOS
brew install sqlcipher

# Install Frida for key extraction (if needed)
pip install frida-tools
```

### Method 1: Using Known Key
The known encryption key for Rekordbox v6:
```
402fd482c38817c35ffa8ffb8c7d93143b749e7d315df7a81732a1ff43608497
```

### Decryption Steps
```bash
# 1. Copy the database to working directory (always work on a copy!)
cp ~/Library/Pioneer/rekordbox/master.db ./master_copy.db

# 2. Decrypt using SQLCipher
sqlcipher master_copy.db

# 3. In SQLCipher prompt, run:
PRAGMA key = '402fd482c38817c35ffa8ffb8c7d93143b749e7d315df7a81732a1ff43608497';
PRAGMA cipher_compatibility = 4;
ATTACH DATABASE 'master_decrypted.db' AS decrypted_db KEY '';
SELECT sqlcipher_export('decrypted_db');
DETACH DATABASE decrypted_db;
.quit

# 4. Now you have master_decrypted.db as a regular SQLite database
```

### Method 2: Dynamic Key Extraction (if key changes)
Using the Frida-based approach from the GitHub repo:
```javascript
// dump_keys.js script to intercept encryption keys
// Run while performing a Rekordbox backup
frida -l dump_keys.js rekordbox
```

## 3. Database Schema (After Decryption)

### Core Tables (Expected based on Rekordbox functionality)
```sql
-- Track information
djmdContent (
    ID TEXT PRIMARY KEY,
    FolderPath TEXT,
    FileName TEXT,
    Title TEXT,
    ArtistID TEXT,
    AlbumID TEXT,
    GenreID TEXT,
    BPM REAL,
    Length INTEGER,
    TrackKey TEXT,
    Rating INTEGER,
    ColorID INTEGER,
    Energy INTEGER,
    BitRate INTEGER,
    SampleRate INTEGER,
    FileSize INTEGER,
    ImportDate TEXT,
    ReleaseDate TEXT,
    AddedDate TEXT,
    ModifiedDate TEXT,
    AnalyzedDate TEXT,
    FileType TEXT
)

-- Playlists
djmdPlaylist (
    ID TEXT PRIMARY KEY,
    Seq INTEGER,
    Name TEXT,
    ImagePath TEXT,
    Attribute INTEGER,
    ParentID TEXT,
    SmartList TEXT
)

-- Playlist contents
djmdPlaylistSong (
    ID TEXT PRIMARY KEY,
    PlaylistID TEXT,
    ContentID TEXT,
    TrackNo INTEGER
)

-- Cue points
djmdCue (
    ID TEXT PRIMARY KEY,
    ContentID TEXT,
    InMsec INTEGER,
    OutMsec INTEGER,
    Kind INTEGER,
    Color INTEGER,
    ColorTableIndex INTEGER,
    ActiveLoop INTEGER,
    Comment TEXT
)

-- Beat grid
djmdBeatGrid (
    ID TEXT PRIMARY KEY,
    ContentID TEXT,
    BeatPosition REAL,
    BPM REAL,
    MeterKind INTEGER
)

-- History/Play logs
djmdHistory (
    ID TEXT PRIMARY KEY,
    Seq INTEGER,
    Name TEXT,
    Attribute INTEGER,
    DateCreated TEXT
)

-- Artists, Albums, Genres
djmdArtist (ID, Name)
djmdAlbum (ID, Name, ArtistID)
djmdGenre (ID, Name)
```

## 4. Database Architecture Decision

### Option A: Hybrid Architecture (Recommended)

```python
class HybridArchitecture:
    """
    Use both Neo4j (via Graphiti) and PostgreSQL/SQLite for different purposes
    """
    
    def __init__(self):
        # Neo4j/Graphiti for:
        # - Temporal memory and conversation history
        # - Relationships between entities (artist collaborations, genre evolution)
        # - User preferences and listening patterns
        # - Discovery paths and recommendations
        self.graphiti = Graphiti(...)
        
        # PostgreSQL/SQLite for:
        # - Track catalog (master list of all tracks)
        # - File locations and technical metadata
        # - Rekordbox sync data
        # - Download queue and status
        self.rds = PostgreSQLConnection(...)
    
    async def sync_rekordbox(self):
        """Sync Rekordbox data to both databases"""
        
        # 1. Decrypt and read Rekordbox DB
        rekordbox_data = self.decrypt_and_read_rekordbox()
        
        # 2. Store factual data in RDS
        await self.rds.bulk_upsert_tracks(rekordbox_data['tracks'])
        await self.rds.bulk_upsert_playlists(rekordbox_data['playlists'])
        
        # 3. Store relationships and patterns in Graphiti
        for track in rekordbox_data['tracks']:
            episode_body = f"""
            Synced track from Rekordbox:
            {track['Title']} by {track['Artist']}
            BPM: {track['BPM']}, Key: {track['Key']}
            Rating: {track['Rating']}, Energy: {track['Energy']}
            Added: {track['AddedDate']}, Last Played: {track['LastPlayed']}
            """
            
            await self.graphiti.add_episode(
                name=f"rekordbox_sync_{track['ID']}",
                episode_body=episode_body,
                entity_types=MUSIC_ENTITY_TYPES,
                source="rekordbox_sync"
            )
```

### Option B: Pure Neo4j/Graphiti (Simpler but less efficient)

```python
class PureGraphArchitecture:
    """
    Use only Neo4j via Graphiti for everything
    """
    
    async def store_track_catalog(self):
        """Store entire track catalog in graph"""
        
        # Pros:
        # - Single database to manage
        # - All data in one place
        # - Relationships are first-class
        
        # Cons:
        # - Less efficient for bulk operations
        # - Graph queries slower for simple lookups
        # - More complex for transactional operations
        
        for track in rekordbox_tracks:
            await self.graphiti.add_episode(
                name=f"track_{track['ID']}",
                episode_body=format_track_data(track),
                entity_types={'Track': Track}
            )
```

### Recommendation: Hybrid Approach

**Use RDS (PostgreSQL) for:**
- Track catalog (ID, title, artist, file path, technical metadata)
- Rekordbox sync state and change detection
- Download queue and file management
- Bulk operations and reporting
- Fast key-based lookups

**Use Neo4j/Graphiti for:**
- Memory and conversation history
- Relationships (similar tracks, artist collaborations)
- User preferences and patterns
- Temporal data (what was popular when)
- Discovery and recommendation paths
- Semantic search and understanding

## 5. Rekordbox Sync Implementation

### Sync Service Design

```python
import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path
import subprocess

class RekordboxSyncService:
    def __init__(self, graphiti_client, rds_client):
        self.graphiti = graphiti_client
        self.rds = rds_client
        self.rekordbox_path = Path.home() / "Library/Pioneer/rekordbox"
        self.decryption_key = "402fd482c38817c35ffa8ffb8c7d93143b749e7d315df7a81732a1ff43608497"
        
    async def decrypt_database(self) -> Path:
        """Decrypt Rekordbox database to temp file"""
        
        master_db = self.rekordbox_path / "master.db"
        
        # Check if database exists
        if not master_db.exists():
            raise FileNotFoundError(f"Rekordbox database not found at {master_db}")
        
        # Create temp decrypted copy
        temp_db = Path("/tmp") / f"rekordbox_decrypted_{datetime.now().timestamp()}.db"
        
        # Use SQLCipher to decrypt
        decrypt_script = f"""
        PRAGMA key = '{self.decryption_key}';
        PRAGMA cipher_compatibility = 4;
        ATTACH DATABASE '{temp_db}' AS decrypted_db KEY '';
        SELECT sqlcipher_export('decrypted_db');
        DETACH DATABASE decrypted_db;
        """
        
        result = subprocess.run(
            ["sqlcipher", str(master_db)],
            input=decrypt_script.encode(),
            capture_output=True
        )
        
        if result.returncode != 0:
            raise Exception(f"Decryption failed: {result.stderr.decode()}")
            
        return temp_db
    
    async def read_rekordbox_data(self, db_path: Path) -> dict:
        """Read data from decrypted Rekordbox database"""
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Read tracks
        tracks = cursor.execute("""
            SELECT 
                c.ID,
                c.Title,
                a.Name as Artist,
                al.Name as Album,
                g.Name as Genre,
                c.BPM,
                c.Length,
                c.TrackKey as Key,
                c.Rating,
                c.Energy,
                c.FolderPath,
                c.FileName,
                c.FileSize,
                c.BitRate,
                c.AddedDate,
                c.ModifiedDate
            FROM djmdContent c
            LEFT JOIN djmdArtist a ON c.ArtistID = a.ID
            LEFT JOIN djmdAlbum al ON c.AlbumID = al.ID
            LEFT JOIN djmdGenre g ON c.GenreID = g.ID
        """).fetchall()
        
        # Read playlists
        playlists = cursor.execute("""
            SELECT 
                p.ID,
                p.Name,
                COUNT(ps.ID) as TrackCount
            FROM djmdPlaylist p
            LEFT JOIN djmdPlaylistSong ps ON p.ID = ps.PlaylistID
            GROUP BY p.ID
        """).fetchall()
        
        # Read cue points
        cues = cursor.execute("""
            SELECT 
                ContentID,
                InMsec,
                OutMsec,
                Kind,
                Comment
            FROM djmdCue
        """).fetchall()
        
        conn.close()
        
        return {
            'tracks': [dict(t) for t in tracks],
            'playlists': [dict(p) for p in playlists],
            'cues': [dict(c) for c in cues]
        }
    
    async def detect_changes(self, new_data: dict) -> dict:
        """Detect what has changed since last sync"""
        
        # Get last sync state from RDS
        last_sync = await self.rds.get_last_sync_state()
        
        changes = {
            'new_tracks': [],
            'modified_tracks': [],
            'new_playlists': [],
            'deleted_tracks': []
        }
        
        if not last_sync:
            # First sync - everything is new
            changes['new_tracks'] = new_data['tracks']
            changes['new_playlists'] = new_data['playlists']
        else:
            # Compare checksums to detect changes
            old_tracks = {t['ID']: t for t in last_sync['tracks']}
            new_tracks = {t['ID']: t for t in new_data['tracks']}
            
            # Find new tracks
            for track_id, track in new_tracks.items():
                if track_id not in old_tracks:
                    changes['new_tracks'].append(track)
                elif self.calculate_checksum(track) != self.calculate_checksum(old_tracks[track_id]):
                    changes['modified_tracks'].append(track)
            
            # Find deleted tracks
            for track_id in old_tracks:
                if track_id not in new_tracks:
                    changes['deleted_tracks'].append(track_id)
        
        return changes
    
    def calculate_checksum(self, track: dict) -> str:
        """Calculate checksum for change detection"""
        
        # Use relevant fields for checksum
        checksum_data = f"{track['Title']}{track['BPM']}{track['Key']}{track['Rating']}{track['ModifiedDate']}"
        return hashlib.md5(checksum_data.encode()).hexdigest()
    
    async def sync_to_databases(self, data: dict, changes: dict):
        """Sync data to both RDS and Graphiti"""
        
        # 1. Update RDS with factual data
        await self.rds.begin_transaction()
        try:
            # Upsert tracks
            for track in changes['new_tracks'] + changes['modified_tracks']:
                await self.rds.upsert_track(track)
            
            # Remove deleted tracks
            for track_id in changes['deleted_tracks']:
                await self.rds.delete_track(track_id)
            
            # Update sync state
            await self.rds.save_sync_state(data)
            await self.rds.commit()
            
        except Exception as e:
            await self.rds.rollback()
            raise e
        
        # 2. Update Graphiti with relationships and insights
        if changes['new_tracks']:
            episode_body = f"""
            Rekordbox Library Sync - {datetime.now()}
            New tracks added: {len(changes['new_tracks'])}
            
            New additions:
            """
            for track in changes['new_tracks'][:10]:  # First 10
                episode_body += f"\n- {track['Title']} by {track['Artist']} ({track['BPM']} BPM, Key: {track['Key']})"
            
            await self.graphiti.add_episode(
                name=f"rekordbox_sync_{datetime.now().strftime('%Y%m%d')}",
                episode_body=episode_body,
                entity_types=MUSIC_ENTITY_TYPES,
                source="rekordbox_sync"
            )
        
        # 3. Analyze patterns for Graphiti
        await self.analyze_library_patterns(data)
    
    async def analyze_library_patterns(self, data: dict):
        """Analyze patterns in Rekordbox library"""
        
        # BPM distribution
        bpms = [t['BPM'] for t in data['tracks'] if t['BPM']]
        avg_bpm = sum(bpms) / len(bpms) if bpms else 0
        
        # Key distribution
        keys = {}
        for track in data['tracks']:
            if track['Key']:
                keys[track['Key']] = keys.get(track['Key'], 0) + 1
        
        # Genre distribution
        genres = {}
        for track in data['tracks']:
            if track['Genre']:
                genres[track['Genre']] = genres.get(track['Genre'], 0) + 1
        
        episode_body = f"""
        Rekordbox Library Analysis:
        Total Tracks: {len(data['tracks'])}
        Average BPM: {avg_bpm:.1f}
        
        Top Keys:
        {self.format_top_items(keys, 5)}
        
        Top Genres:
        {self.format_top_items(genres, 5)}
        
        Total Playlists: {len(data['playlists'])}
        """
        
        await self.graphiti.add_episode(
            name="rekordbox_library_analysis",
            episode_body=episode_body,
            entity_types={'MusicPreference': MusicPreference},
            source="rekordbox_analysis"
        )
    
    def format_top_items(self, items: dict, limit: int) -> str:
        """Format top items for display"""
        sorted_items = sorted(items.items(), key=lambda x: x[1], reverse=True)[:limit]
        return "\n".join([f"- {item}: {count}" for item, count in sorted_items])
    
    async def run_sync(self):
        """Main sync process"""
        
        try:
            # 1. Decrypt database
            decrypted_db = await self.decrypt_database()
            
            # 2. Read data
            data = await self.read_rekordbox_data(decrypted_db)
            
            # 3. Detect changes
            changes = await self.detect_changes(data)
            
            # 4. Sync to databases
            await self.sync_to_databases(data, changes)
            
            # 5. Cleanup
            decrypted_db.unlink()
            
            return {
                'success': True,
                'new_tracks': len(changes['new_tracks']),
                'modified_tracks': len(changes['modified_tracks']),
                'deleted_tracks': len(changes['deleted_tracks'])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
```

## 6. RDS Schema for Track Catalog

```sql
-- PostgreSQL schema for track catalog
CREATE SCHEMA IF NOT EXISTS music;

-- Main tracks table
CREATE TABLE music.tracks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rekordbox_id TEXT UNIQUE,
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    album TEXT,
    genre TEXT,
    label TEXT,
    
    -- Technical metadata
    file_path TEXT,
    file_size BIGINT,
    file_type TEXT,
    bit_rate INTEGER,
    sample_rate INTEGER,
    length_ms INTEGER,
    
    -- Musical metadata
    bpm DECIMAL(5,2),
    musical_key TEXT,
    energy INTEGER,
    
    -- Platform IDs
    spotify_id TEXT,
    deezer_id TEXT,
    beatport_id TEXT,
    discogs_id TEXT,
    youtube_id TEXT,
    
    -- Universal identifiers
    isrc TEXT,
    
    -- User metadata
    rating INTEGER,
    play_count INTEGER DEFAULT 0,
    last_played TIMESTAMP,
    
    -- Timestamps
    added_date TIMESTAMP,
    modified_date TIMESTAMP,
    analyzed_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Playlists
CREATE TABLE music.playlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rekordbox_id TEXT UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    smart_list TEXT,  -- Smart playlist criteria
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Playlist tracks
CREATE TABLE music.playlist_tracks (
    playlist_id UUID REFERENCES music.playlists(id) ON DELETE CASCADE,
    track_id UUID REFERENCES music.tracks(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (playlist_id, track_id)
);

-- Cue points
CREATE TABLE music.cue_points (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id UUID REFERENCES music.tracks(id) ON DELETE CASCADE,
    position_ms INTEGER NOT NULL,
    type TEXT,  -- hot_cue, memory, loop
    color TEXT,
    comment TEXT
);

-- Sync state
CREATE TABLE music.sync_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_type TEXT NOT NULL,  -- rekordbox, spotify, etc
    last_sync TIMESTAMP NOT NULL,
    state JSONB,  -- Store checksums and metadata
    created_at TIMESTAMP DEFAULT NOW()
);

-- Download queue
CREATE TABLE music.download_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    track_id UUID REFERENCES music.tracks(id),
    title TEXT NOT NULL,
    artist TEXT NOT NULL,
    platform TEXT,  -- deezer, spotify, youtube, soulseek
    status TEXT DEFAULT 'pending',  -- pending, downloading, completed, failed
    quality TEXT,  -- FLAC, MP3_320, etc
    priority INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- Indices for performance
CREATE INDEX idx_tracks_rekordbox_id ON music.tracks(rekordbox_id);
CREATE INDEX idx_tracks_artist ON music.tracks(artist);
CREATE INDEX idx_tracks_bpm ON music.tracks(bpm);
CREATE INDEX idx_tracks_key ON music.tracks(musical_key);
CREATE INDEX idx_tracks_genre ON music.tracks(genre);
CREATE INDEX idx_tracks_rating ON music.tracks(rating);
CREATE INDEX idx_download_queue_status ON music.download_queue(status);
```

## 7. Monitoring and Maintenance

### Sync Scheduling
```python
# Run sync periodically
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# Sync every 30 minutes when Rekordbox is not running
scheduler.add_job(
    sync_service.run_sync,
    'interval',
    minutes=30,
    id='rekordbox_sync',
    misfire_grace_time=300
)

# Watch for Rekordbox process
async def watch_rekordbox_process():
    """Pause sync when Rekordbox is running"""
    while True:
        if is_rekordbox_running():
            scheduler.pause_job('rekordbox_sync')
        else:
            scheduler.resume_job('rekordbox_sync')
        await asyncio.sleep(60)
```

### Data Integrity Checks
```python
async def verify_sync_integrity():
    """Verify sync data integrity"""
    
    # Check for orphaned files
    rds_tracks = await rds.get_all_track_paths()
    for path in rds_tracks:
        if not Path(path).exists():
            await rds.mark_track_missing(path)
    
    # Check for untracked files
    rekordbox_folder = Path.home() / "Music/rekordbox"
    for audio_file in rekordbox_folder.rglob("*.mp3"):
        if str(audio_file) not in rds_tracks:
            # New file not in database
            await notify_untracked_file(audio_file)
```

## 8. Security Considerations

1. **Never modify Rekordbox DB directly** - Always work on copies
2. **Backup before sync** - Keep backups of both Rekordbox and your databases
3. **Read-only access** - Only read from Rekordbox, never write
4. **Encryption key security** - Store decryption key securely (environment variable or secret manager)
5. **Process isolation** - Don't sync while Rekordbox is running

## 9. Error Handling

```python
class RekordboxSyncError(Exception):
    """Base exception for Rekordbox sync errors"""
    pass

class DatabaseDecryptionError(RekordboxSyncError):
    """Failed to decrypt Rekordbox database"""
    pass

class RekordboxRunningError(RekordboxSyncError):
    """Rekordbox is currently running"""
    pass

async def safe_sync():
    """Safe sync with error handling"""
    
    try:
        # Check if Rekordbox is running
        if is_rekordbox_running():
            raise RekordboxRunningError("Cannot sync while Rekordbox is running")
        
        # Backup current state
        await backup_databases()
        
        # Run sync
        result = await sync_service.run_sync()
        
        if not result['success']:
            # Restore from backup if failed
            await restore_databases()
            raise RekordboxSyncError(result['error'])
            
        return result
        
    except Exception as e:
        # Log error to Graphiti for memory
        await graphiti.add_episode(
            name="rekordbox_sync_error",
            episode_body=f"Sync failed: {str(e)}",
            source="error_log"
        )
        raise
```

## Conclusion

The hybrid approach (Neo4j/Graphiti + PostgreSQL) provides the best balance:
- **PostgreSQL** handles the "facts" - what tracks exist, where files are, technical metadata
- **Neo4j/Graphiti** handles the "intelligence" - relationships, patterns, memory, recommendations

This architecture allows efficient bulk operations while maintaining rich relationship data and temporal awareness. The Rekordbox sync process runs periodically, keeping both databases updated with the latest library state.
# Soulseek/slskd Integration Plan for Music Agent

## Executive Summary

This document outlines the integration of Soulseek P2P network capabilities into the Deez music agent through slskd (a modern Soulseek client-server application) and the slskd-api Python library. This integration will enable access to rare, underground, and hard-to-find music that may not be available on mainstream platforms.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Deez Music Agent                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Deezer     │  │   Spotify    │  │  Soulseek    │          │
│  │  Integration │  │ Integration  │  │ Integration  │          │
│  └──────────────┘  └──────────────┘  └──────┬───────┘          │
│                                               │                  │
└───────────────────────────────────────────────┼──────────────────┘
                                                │
                                    ┌───────────▼───────────┐
                                    │   slskd-api Python    │
                                    │      (0.1.5+)         │
                                    └───────────┬───────────┘
                                                │
                                    ┌───────────▼───────────┐
                                    │    slskd Container    │
                                    │   (REST API Server)   │
                                    └───────────┬───────────┘
                                                │
                                    ┌───────────▼───────────┐
                                    │   Soulseek Network    │
                                    │    (P2P Protocol)     │
                                    └───────────────────────┘
```

## 1. slskd Container Setup

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  slskd:
    image: slskd/slskd:latest
    container_name: deez-slskd
    restart: unless-stopped
    ports:
      - "5030:5030"     # Web UI & API
      - "5031:5031"     # HTTPS (optional)
      - "50300:50300"   # Soulseek protocol
    environment:
      - SLSKD_REMOTE_CONFIGURATION=true
      - SLSKD_REMOTE_FILE_MANAGEMENT=true
      - SLSKD_NO_AUTH=false
    volumes:
      - ./slskd/config:/app/config
      - ./slskd/downloads:/app/downloads
      - ./slskd/incomplete:/app/incomplete
      - ./slskd/shared:/app/shared
      - ./slskd/logs:/app/logs
    networks:
      - deez-network

networks:
  deez-network:
    driver: bridge
```

### slskd Configuration (slskd.yml)

```yaml
# /slskd/config/slskd.yml
soulseek:
  username: ${SOULSEEK_USERNAME}
  password: ${SOULSEEK_PASSWORD}
  description: "Deez Music Agent - Automated music discovery"
  listen_port: 50300
  diagnostic_level: Debug
  distributed_network:
    disable_children: false
    child_limit: 25
    parent_min_speed: 50

directories:
  downloads: /app/downloads
  incomplete: /app/incomplete
  shared: 
    - /app/shared

shares:
  directories:
    - /app/shared
  filters:
    - "*.mp3"
    - "*.flac"
    - "*.wav"
    - "*.m4a"
    - "*.aiff"

web:
  port: 5030
  https:
    port: 5031
    force: false
  authentication:
    username: ${SLSKD_WEB_USERNAME}
    password: ${SLSKD_WEB_PASSWORD}
    api_keys:
      - name: deez-agent
        key: ${SLSKD_API_KEY}
        role: readwrite

downloads:
  limits:
    concurrent: 10
    queued: 100
  filters:
    include:
      - "*.mp3"
      - "*.flac"
      - "*.wav"
    exclude:
      - "*.exe"
      - "*.zip"
  retry:
    attempts: 3
    delay_ms: 5000

options:
  directories:
    complete_on_shutdown: true
  files:
    overwrite: false
  messaging:
    away_message: "This is an automated agent. Please message the human operator."
```

## 2. Python Integration Layer

### Dependencies

```toml
# pyproject.toml additions
[project.dependencies]
slskd-api = "^0.1.5"
aiofiles = "^23.2.1"
asyncio = "^3.4.3"
tenacity = "^8.2.3"  # For retry logic
```

### Core Soulseek Service

```python
# src/music_agent/integrations/soulseek.py

import os
import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

import slskd_api
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class DownloadState(Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SoulseekTrack:
    """Soulseek track search result"""
    filename: str
    username: str
    size: int
    bitrate: Optional[int]
    length: Optional[int]
    directory: str
    has_free_slots: bool
    upload_speed: int
    queue_length: int
    
    @property
    def quality_score(self) -> float:
        """Calculate quality score for ranking results"""
        score = 0.0
        
        # Bitrate scoring (0-40 points)
        if self.bitrate:
            if self.bitrate >= 320:
                score += 40
            elif self.bitrate >= 256:
                score += 30
            elif self.bitrate >= 192:
                score += 20
            elif self.bitrate >= 128:
                score += 10
        
        # File format scoring (0-20 points)
        ext = Path(self.filename).suffix.lower()
        if ext == '.flac':
            score += 20
        elif ext == '.wav':
            score += 18
        elif ext == '.mp3':
            score += 15
        elif ext == '.m4a':
            score += 12
        
        # Availability scoring (0-20 points)
        if self.has_free_slots:
            score += 20
        elif self.queue_length < 5:
            score += 15
        elif self.queue_length < 10:
            score += 10
        elif self.queue_length < 20:
            score += 5
        
        # Upload speed scoring (0-20 points)
        if self.upload_speed > 1000:  # KB/s
            score += 20
        elif self.upload_speed > 500:
            score += 15
        elif self.upload_speed > 100:
            score += 10
        elif self.upload_speed > 50:
            score += 5
        
        return score


class SoulseekService:
    """Service for interacting with Soulseek via slskd"""
    
    def __init__(
        self,
        host: str = None,
        api_key: str = None,
        url_base: str = "",
        download_dir: str = "./downloads/soulseek",
        max_concurrent_downloads: int = 5
    ):
        self.host = host or os.getenv("SLSKD_HOST", "http://localhost:5030")
        self.api_key = api_key or os.getenv("SLSKD_API_KEY")
        self.url_base = url_base or os.getenv("SLSKD_URL_BASE", "")
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_concurrent_downloads = max_concurrent_downloads
        self.active_downloads: Dict[str, Any] = {}
        self._client = None
        self._monitor_task = None
        
    @property
    def client(self) -> slskd_api.SlskdClient:
        """Lazy initialization of slskd client"""
        if not self._client:
            self._client = slskd_api.SlskdClient(
                host=self.host,
                api_key=self.api_key,
                url_base=self.url_base
            )
        return self._client
    
    async def initialize(self):
        """Initialize the service and start monitoring"""
        try:
            # Test connection
            state = self.client.application.state()
            logger.info(f"Connected to slskd: {state}")
            
            # Start download monitor
            self._monitor_task = asyncio.create_task(self._monitor_downloads())
            
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Soulseek service: {e}")
            return False
    
    async def shutdown(self):
        """Cleanup resources"""
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def search(
        self,
        query: str,
        max_results: int = 50,
        timeout: int = 10,
        min_bitrate: Optional[int] = None,
        file_extensions: Optional[List[str]] = None
    ) -> List[SoulseekTrack]:
        """
        Search for tracks on Soulseek
        
        Args:
            query: Search query (artist, track, album)
            max_results: Maximum number of results
            timeout: Search timeout in seconds
            min_bitrate: Minimum acceptable bitrate
            file_extensions: Acceptable file extensions
        
        Returns:
            List of SoulseekTrack results sorted by quality
        """
        try:
            # Initiate search
            search_response = await asyncio.to_thread(
                self.client.searches.search_text,
                searchText=query,
                fileLimit=max_results * 2,  # Get extra for filtering
                filterResponses=True,
                searchTimeout=timeout * 1000
            )
            
            search_id = search_response.get('id')
            if not search_id:
                raise ValueError("Failed to get search ID")
            
            # Wait for results to populate
            await asyncio.sleep(min(timeout / 2, 5))
            
            # Get search results
            search_state = await asyncio.to_thread(
                self.client.searches.state,
                search_id
            )
            
            responses = await asyncio.to_thread(
                self.client.searches.search_responses,
                search_id
            )
            
            # Process results
            tracks = []
            for response in responses:
                username = response.get('username', '')
                files = response.get('files', [])
                has_free_slots = response.get('hasFreeUploadSlot', False)
                upload_speed = response.get('uploadSpeed', 0)
                queue_length = response.get('queueLength', 0)
                
                for file_info in files:
                    filename = file_info.get('filename', '')
                    
                    # Skip if doesn't match extension filter
                    if file_extensions:
                        ext = Path(filename).suffix.lower()
                        if ext not in file_extensions:
                            continue
                    
                    # Skip if below minimum bitrate
                    bitrate = file_info.get('bitRate')
                    if min_bitrate and bitrate and bitrate < min_bitrate:
                        continue
                    
                    track = SoulseekTrack(
                        filename=filename,
                        username=username,
                        size=file_info.get('size', 0),
                        bitrate=bitrate,
                        length=file_info.get('length'),
                        directory=str(Path(filename).parent),
                        has_free_slots=has_free_slots,
                        upload_speed=upload_speed,
                        queue_length=queue_length
                    )
                    tracks.append(track)
            
            # Stop search to clean up
            try:
                await asyncio.to_thread(
                    self.client.searches.stop,
                    search_id
                )
            except Exception:
                pass  # Ignore cleanup errors
            
            # Sort by quality score
            tracks.sort(key=lambda t: t.quality_score, reverse=True)
            
            return tracks[:max_results]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    async def download(
        self,
        track: SoulseekTrack,
        destination: Optional[Path] = None,
        priority: int = 0
    ) -> str:
        """
        Download a track from Soulseek
        
        Args:
            track: Track to download
            destination: Custom destination path
            priority: Download priority (higher = sooner)
        
        Returns:
            Download ID for tracking
        """
        try:
            # Check concurrent download limit
            if len(self.active_downloads) >= self.max_concurrent_downloads:
                # Find lowest priority download to queue
                if priority > 0:
                    min_priority = min(
                        d.get('priority', 0) 
                        for d in self.active_downloads.values()
                    )
                    if priority > min_priority:
                        # Queue this download
                        pass
                    else:
                        raise ValueError("Download queue is full")
                else:
                    raise ValueError("Download queue is full")
            
            # Prepare file info for slskd
            file_info = {
                "filename": track.filename,
                "size": track.size
            }
            
            # Enqueue download
            result = await asyncio.to_thread(
                self.client.transfers.enqueue,
                username=track.username,
                files=[file_info]
            )
            
            download_id = result.get('id', str(datetime.now().timestamp()))
            
            # Track active download
            self.active_downloads[download_id] = {
                'track': track,
                'state': DownloadState.QUEUED,
                'destination': destination or self.download_dir / Path(track.filename).name,
                'priority': priority,
                'started_at': datetime.now(),
                'progress': 0
            }
            
            logger.info(f"Download queued: {track.filename} from {track.username}")
            
            return download_id
            
        except Exception as e:
            logger.error(f"Failed to start download: {e}")
            raise
    
    async def _monitor_downloads(self):
        """Monitor active downloads and update status"""
        while True:
            try:
                await asyncio.sleep(5)  # Check every 5 seconds
                
                if not self.active_downloads:
                    continue
                
                # Get current downloads from slskd
                downloads = await asyncio.to_thread(
                    self.client.transfers.get_downloads
                )
                
                # Update download states
                for slskd_download in downloads:
                    download_id = slskd_download.get('id')
                    if download_id not in self.active_downloads:
                        continue
                    
                    state = slskd_download.get('state', '').lower()
                    progress = slskd_download.get('percentComplete', 0)
                    
                    active_download = self.active_downloads[download_id]
                    
                    # Update progress
                    active_download['progress'] = progress
                    
                    # Update state
                    if state == 'completed':
                        active_download['state'] = DownloadState.COMPLETED
                        active_download['completed_at'] = datetime.now()
                        
                        # Move to destination if needed
                        source = Path(slskd_download.get('filename', ''))
                        if source.exists():
                            destination = active_download['destination']
                            destination.parent.mkdir(parents=True, exist_ok=True)
                            source.rename(destination)
                            logger.info(f"Download completed: {destination}")
                        
                        # Remove from active downloads after a delay
                        asyncio.create_task(
                            self._cleanup_download(download_id, delay=60)
                        )
                        
                    elif state == 'failed' or state == 'errored':
                        active_download['state'] = DownloadState.FAILED
                        active_download['error'] = slskd_download.get('error')
                        logger.error(f"Download failed: {active_download['track'].filename}")
                        
                        # Remove from active downloads
                        asyncio.create_task(
                            self._cleanup_download(download_id, delay=10)
                        )
                        
                    elif state in ['inprogress', 'downloading']:
                        active_download['state'] = DownloadState.IN_PROGRESS
                        
            except Exception as e:
                logger.error(f"Download monitor error: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def _cleanup_download(self, download_id: str, delay: int = 0):
        """Remove download from active tracking after delay"""
        if delay > 0:
            await asyncio.sleep(delay)
        
        if download_id in self.active_downloads:
            del self.active_downloads[download_id]
    
    async def get_download_status(self, download_id: str) -> Optional[Dict]:
        """Get status of a download"""
        return self.active_downloads.get(download_id)
    
    async def cancel_download(self, download_id: str) -> bool:
        """Cancel an active download"""
        try:
            # Cancel in slskd
            await asyncio.to_thread(
                self.client.transfers.cancel_download,
                download_id
            )
            
            # Update local state
            if download_id in self.active_downloads:
                self.active_downloads[download_id]['state'] = DownloadState.CANCELLED
                await self._cleanup_download(download_id, delay=5)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel download: {e}")
            return False
    
    async def browse_user(self, username: str) -> List[str]:
        """Browse a user's shared files"""
        try:
            result = await asyncio.to_thread(
                self.client.users.browse,
                username
            )
            
            files = []
            for directory in result.get('directories', []):
                for file in directory.get('files', []):
                    files.append(file.get('filename', ''))
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to browse user {username}: {e}")
            return []
```

## 3. Agent Tool Integration

### Soulseek Music Tool for Agent

```python
# src/music_agent/tools/soulseek_tool.py

from typing import List, Dict, Optional
from strands import tool
from ..integrations.soulseek import SoulseekService, SoulseekTrack

# Initialize service
soulseek_service = SoulseekService()

@tool
async def search_soulseek(
    query: str,
    quality: str = "high",
    max_results: int = 20
) -> List[Dict]:
    """
    Search for music on Soulseek P2P network.
    Best for finding rare, underground, or unavailable tracks.
    
    Args:
        query: Search query (artist, track, album)
        quality: Quality preference (high, medium, any)
        max_results: Maximum results to return
    
    Returns:
        List of track results with metadata
    """
    
    # Set quality filters
    min_bitrate = None
    file_extensions = None
    
    if quality == "high":
        min_bitrate = 256
        file_extensions = [".flac", ".wav", ".mp3"]
    elif quality == "medium":
        min_bitrate = 192
        file_extensions = [".mp3", ".m4a", ".flac"]
    else:
        file_extensions = [".mp3", ".m4a", ".flac", ".wav", ".aiff"]
    
    # Search Soulseek
    tracks = await soulseek_service.search(
        query=query,
        max_results=max_results,
        min_bitrate=min_bitrate,
        file_extensions=file_extensions
    )
    
    # Format results
    results = []
    for track in tracks:
        results.append({
            "filename": track.filename,
            "username": track.username,
            "size_mb": round(track.size / 1024 / 1024, 2),
            "bitrate": track.bitrate,
            "format": Path(track.filename).suffix,
            "quality_score": track.quality_score,
            "available": track.has_free_slots,
            "queue_length": track.queue_length
        })
    
    return results

@tool
async def download_from_soulseek(
    filename: str,
    username: str,
    size: int,
    destination: Optional[str] = None
) -> str:
    """
    Download a track from Soulseek.
    
    Args:
        filename: Full filename path from search
        username: Username of the file owner
        size: File size in bytes
        destination: Optional custom destination path
    
    Returns:
        Download ID for tracking progress
    """
    
    track = SoulseekTrack(
        filename=filename,
        username=username,
        size=size,
        bitrate=None,
        length=None,
        directory="",
        has_free_slots=True,
        upload_speed=0,
        queue_length=0
    )
    
    destination_path = Path(destination) if destination else None
    
    download_id = await soulseek_service.download(
        track=track,
        destination=destination_path
    )
    
    return f"Download started with ID: {download_id}"

@tool
async def check_soulseek_download(download_id: str) -> Dict:
    """
    Check the status of a Soulseek download.
    
    Args:
        download_id: Download ID from download_from_soulseek
    
    Returns:
        Download status information
    """
    
    status = await soulseek_service.get_download_status(download_id)
    
    if not status:
        return {"error": "Download not found"}
    
    return {
        "state": status['state'].value,
        "progress": status['progress'],
        "destination": str(status['destination']),
        "started_at": status['started_at'].isoformat(),
        "completed_at": status.get('completed_at', '').isoformat() if status.get('completed_at') else None
    }
```

## 4. Unified Search Integration

### Enhanced Music Search with Soulseek Fallback

```python
# src/music_agent/tools/unified_search.py

@tool
async def search_all_sources(
    query: str,
    include_soulseek: bool = True,
    prefer_quality: bool = True
) -> Dict[str, List]:
    """
    Search across all music sources including Soulseek.
    
    Priority order:
    1. Check owned tracks (Rekordbox)
    2. Search mainstream (Deezer, Spotify)
    3. Search Soulseek for unavailable tracks
    """
    
    results = {
        "owned": [],
        "deezer": [],
        "spotify": [],
        "soulseek": []
    }
    
    # Check if already owned in Rekordbox
    owned = await check_rekordbox_library(query)
    if owned:
        results["owned"] = owned
        if not include_soulseek:
            return results
    
    # Search mainstream platforms
    try:
        deezer_results = await search_deezer(query)
        results["deezer"] = deezer_results
    except:
        pass
    
    try:
        spotify_results = await search_spotify(query)
        results["spotify"] = spotify_results
    except:
        pass
    
    # If not found on mainstream or want alternatives
    if include_soulseek and (
        not results["deezer"] and not results["spotify"]
        or prefer_quality
    ):
        try:
            soulseek_results = await search_soulseek(
                query=query,
                quality="high" if prefer_quality else "any"
            )
            results["soulseek"] = soulseek_results
        except:
            pass
    
    return results
```

## 5. Memory Integration with Graphiti

### Tracking Soulseek Discoveries

```python
async def record_soulseek_discovery(
    track: SoulseekTrack,
    download_id: Optional[str] = None
):
    """Record Soulseek discovery in Graphiti"""
    
    episode_body = f"""
    Discovered on Soulseek:
    Track: {Path(track.filename).name}
    From user: {track.username}
    Quality: {track.bitrate}kbps {Path(track.filename).suffix}
    Size: {track.size / 1024 / 1024:.2f}MB
    Availability: {'Immediate' if track.has_free_slots else f'Queue position {track.queue_length}'}
    Quality score: {track.quality_score}/100
    """
    
    if download_id:
        episode_body += f"\nDownload initiated: {download_id}"
    
    await graphiti.add_episode(
        name=f"soulseek_discovery_{Path(track.filename).stem[:30]}",
        episode_body=episode_body,
        entity_types={
            'Track': Track,
            'P2PSource': P2PSource
        },
        source="soulseek_search"
    )
```

## 6. Configuration & Environment

### Environment Variables

```bash
# .env additions
# Soulseek Configuration
SOULSEEK_USERNAME=your_soulseek_username
SOULSEEK_PASSWORD=your_soulseek_password

# slskd Configuration  
SLSKD_HOST=http://localhost:5030
SLSKD_API_KEY=deez-agent-api-key-generate-this
SLSKD_WEB_USERNAME=admin
SLSKD_WEB_PASSWORD=secure_password

# Download Settings
SOULSEEK_DOWNLOAD_DIR=./downloads/soulseek
SOULSEEK_MAX_CONCURRENT=5
SOULSEEK_MIN_BITRATE=192
SOULSEEK_PREFER_FORMATS=flac,wav,mp3
```

## 7. Usage Examples

### Agent Conversation Flow

```python
# User: "Find me a rare techno track 'Orbital - Chime 1989 Original Mix'"

# Agent searches mainstream first
mainstream_results = await search_all_sources(
    "Orbital Chime 1989 Original Mix",
    include_soulseek=False
)

# If not found, search Soulseek
if not mainstream_results["deezer"] and not mainstream_results["spotify"]:
    soulseek_results = await search_soulseek(
        "Orbital - Chime 1989 Original Mix",
        quality="high"
    )
    
    if soulseek_results:
        best_result = soulseek_results[0]
        
        # Inform user
        response = f"""
        Found on Soulseek:
        {best_result['filename']}
        Quality: {best_result['bitrate']}kbps {best_result['format']}
        Size: {best_result['size_mb']}MB
        Available from user: {best_result['username']}
        
        Would you like me to download this track?
        """
        
        # If user confirms
        download_id = await download_from_soulseek(
            filename=best_result['filename'],
            username=best_result['username'],
            size=best_result['size'] * 1024 * 1024
        )
```

## 8. Error Handling & Reliability

### Retry Logic for P2P Network

```python
class SoulseekReliabilityManager:
    """Manage P2P network reliability issues"""
    
    async def download_with_fallback(
        self,
        query: str,
        tracks: List[SoulseekTrack],
        max_attempts: int = 3
    ) -> Optional[str]:
        """Try downloading from multiple sources if needed"""
        
        for i, track in enumerate(tracks[:max_attempts]):
            try:
                logger.info(f"Attempting download from source {i+1}/{len(tracks)}")
                
                download_id = await soulseek_service.download(track)
                
                # Wait for completion or timeout
                timeout = 300  # 5 minutes
                start_time = datetime.now()
                
                while (datetime.now() - start_time).seconds < timeout:
                    status = await soulseek_service.get_download_status(download_id)
                    
                    if status['state'] == DownloadState.COMPLETED:
                        return download_id
                    elif status['state'] == DownloadState.FAILED:
                        break
                    
                    await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Download attempt {i+1} failed: {e}")
                continue
        
        return None
```

## 9. Monitoring & Analytics

### Track P2P Usage

```python
async def track_soulseek_metrics():
    """Track Soulseek usage for optimization"""
    
    metrics = {
        "searches_performed": 0,
        "tracks_found": 0,
        "downloads_initiated": 0,
        "downloads_completed": 0,
        "average_quality_score": 0,
        "unique_sources": set(),
        "rare_finds": []  # Tracks not on mainstream
    }
    
    # Store in PostgreSQL for analysis
    await rds.store_p2p_metrics(metrics)
    
    # Record patterns in Graphiti
    episode_body = f"""
    Soulseek Usage Summary:
    Searches: {metrics['searches_performed']}
    Success rate: {metrics['downloads_completed'] / metrics['downloads_initiated'] * 100:.1f}%
    Unique sources: {len(metrics['unique_sources'])}
    Rare finds: {len(metrics['rare_finds'])}
    """
    
    await graphiti.add_episode(
        name="soulseek_usage_metrics",
        episode_body=episode_body,
        source="analytics"
    )
```

## 10. Security & Best Practices

### Security Considerations

1. **File Validation**: Always scan downloaded files
2. **Sandboxing**: Run slskd in isolated container
3. **Rate Limiting**: Respect P2P network etiquette
4. **User Privacy**: Don't log usernames unnecessarily
5. **Legal Compliance**: Only download legally obtainable content

### Network Etiquette

```python
class SoulseekEtiquette:
    """Enforce good P2P citizenship"""
    
    # Rate limits
    MAX_SEARCHES_PER_MINUTE = 10
    MAX_DOWNLOADS_PER_HOUR = 50
    MIN_SHARE_RATIO = 1.0  # Share as much as download
    
    # Respect queue positions
    MAX_QUEUE_POSITION = 50  # Don't download if queue > 50
    
    # Share back
    SHARE_DIRECTORY = "./slskd/shared"
```

## 11. Testing Strategy

### Integration Tests

```python
# tests/test_soulseek_integration.py

async def test_slskd_connection():
    """Test slskd container connectivity"""
    service = SoulseekService()
    assert await service.initialize()

async def test_search_functionality():
    """Test search returns results"""
    results = await search_soulseek("test track", max_results=5)
    assert len(results) <= 5
    assert all('filename' in r for r in results)

async def test_download_queue():
    """Test download queue management"""
    # Use mock slskd for testing
    service = SoulseekService(host="mock://slskd")
    track = SoulseekTrack(filename="test.mp3", username="test", size=1000000)
    download_id = await service.download(track)
    assert download_id is not None
```

## 12. Deployment Steps

1. **Deploy slskd container**
   ```bash
   docker-compose up -d slskd
   ```

2. **Configure slskd**
   - Access web UI at http://localhost:5030
   - Set up Soulseek account
   - Generate API key

3. **Install Python dependencies**
   ```bash
   pip install slskd-api tenacity
   ```

4. **Initialize service in agent**
   ```python
   # In agent initialization
   soulseek_service = SoulseekService()
   await soulseek_service.initialize()
   ```

5. **Register tools with agent**
   ```python
   agent.register_tool(search_soulseek)
   agent.register_tool(download_from_soulseek)
   ```

## Conclusion

This Soulseek integration provides the music agent with access to a vast P2P network of rare and hard-to-find music. The implementation prioritizes:

- **Reliability**: Multiple fallback sources and retry logic
- **Quality**: Intelligent ranking of search results
- **Ethics**: Respecting P2P network etiquette
- **Integration**: Seamless integration with existing music sources
- **Memory**: Learning from P2P discoveries to improve future searches

The integration complements mainstream sources (Deezer, Spotify) by providing access to underground, rare, and user-shared content that may not be commercially available.
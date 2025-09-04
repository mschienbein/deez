# SoundCloud Integration

A comprehensive, modular Python integration for the SoundCloud API with advanced features including OAuth2 authentication, track downloading, HLS stream support, and intelligent caching.

## Features

- 🔐 **Multiple Authentication Methods**
  - OAuth2 (authorization code, client credentials, refresh token flows)
  - Public client ID scraping for anonymous access
  - Secure token storage with keyring

- 🎵 **Complete API Coverage**
  - Tracks, playlists, users, comments
  - Search with advanced filtering
  - Social features (likes, reposts, follows)
  - Stream and activity feeds

- 📥 **Advanced Download Capabilities**
  - MP3 direct downloads
  - HLS stream assembly for non-downloadable tracks
  - ID3 metadata writing with artwork embedding
  - Parallel playlist downloads with progress tracking

- 🚀 **Performance Optimizations**
  - Multi-backend caching (memory, file, Redis)
  - Adaptive rate limiting
  - Automatic retry with exponential backoff
  - Connection pooling

- 🏗️ **Modular Architecture**
  - Clean separation of concerns
  - Type-safe with TypedDict definitions
  - Async-first design
  - Extensible and maintainable

## Installation

```bash
# Basic installation
pip install aiohttp aiofiles

# With download features
pip install mutagen  # For metadata writing

# With Redis cache
pip install aioredis

# With secure token storage
pip install keyring
```

## Quick Start

```python
import asyncio
from soundcloud import SoundCloudClient

async def main():
    # Create client with auto-authentication
    async with SoundCloudClient() as client:
        # Search for tracks
        tracks = await client.search_tracks("lofi hip hop", limit=10)
        
        # Get track details
        track = await client.get_track("https://soundcloud.com/user/track")
        
        # Download a track
        path = await client.download_track(track, output_dir="./downloads")
        print(f"Downloaded to: {path}")

asyncio.run(main())
```

## Authentication

### Using OAuth2

```python
from soundcloud import SoundCloudClient
from soundcloud.types import AuthCredentials

# With client credentials
creds = AuthCredentials(
    client_id="your_client_id",
    client_secret="your_client_secret"
)

client = SoundCloudClient()
await client.authenticate(creds)

# With access token
creds = AuthCredentials(access_token="your_token")
await client.authenticate(creds)
```

### Anonymous Access (Public Client ID)

```python
# Automatically scrapes public client ID
client = SoundCloudClient()
await client.initialize()  # Auto-authenticates
```

## API Usage

### Tracks

```python
# Get track by ID or URL
track = await client.get_track(123456789)
track = await client.get_track("https://soundcloud.com/artist/song")

# Get track details
print(f"Title: {track.title}")
print(f"Artist: {track.artist}")
print(f"Duration: {track.duration_formatted}")
print(f"Plays: {track.playback_count:,}")

# Like/unlike track
await track.like()
await track.unlike()

# Add comment
comment = await track.comment("Great track!", timestamp=30000)  # at 0:30

# Get related tracks
related = await track.get_related(limit=5)
```

### Playlists

```python
# Get playlist
playlist = await client.get_playlist("https://soundcloud.com/user/sets/playlist")

# Iterate tracks
for track in playlist:
    print(f"{track.track_number}. {track.title}")

# Download entire playlist
paths = await client.download_playlist(
    playlist,
    output_dir="./albums",
    create_m3u=True
)

# Manage playlist tracks
await playlist.add_track(track)
await playlist.remove_track(track)
await playlist.reorder_tracks([3, 1, 2, 4, 5])  # New order by index
```

### Users

```python
# Get user
user = await client.get_user("username")

# Get user content
tracks = await user.get_tracks(limit=20)
playlists = await user.get_playlists()
likes = await user.get_likes()

# Social actions
await user.follow()
followers = await user.get_followers()

# Get authenticated user
me = await client.get_me()
stream = await client.get_stream()
```

### Search

```python
from soundcloud.search import FilterBuilder

# Simple search
tracks = await client.search_tracks("jazz", limit=50)

# Advanced search with filters
filters = (FilterBuilder()
    .genre("Jazz")
    .duration_minutes(3, 10)  # 3-10 minutes
    .created_after(datetime(2023, 1, 1))
    .downloadable(True)
    .build())

results = await client.search.search(
    "smooth jazz",
    type="tracks",
    filters=filters,
    sort="popularity"
)

# Search multiple types
all_results = await client.search.search_all("daft punk")
print(f"Found {len(all_results['tracks'])} tracks")
print(f"Found {len(all_results['playlists'])} playlists")
print(f"Found {len(all_results['users'])} users")

# Get trending
trending = await client.search.get_trending(genre="Electronic")

# Search suggestions
suggestions = await client.search.get_suggestions("beatl")
```

## Downloading

### Single Track Download

```python
from soundcloud.types import DownloadOptions

options = DownloadOptions(
    output_path="./music/track.mp3",
    write_metadata=True,
    embed_artwork=True,
    artwork_size="original",
    overwrite=False
)

path = await client.download_track(track, options)
```

### Playlist Download

```python
# Download with parallel processing
paths = await client.download_playlist(
    playlist,
    output_dir="./albums/artist_name",
    options={
        "parallel_downloads": 4,
        "create_m3u": True,
        "write_metadata": True,
        "embed_artwork": True
    }
)

# With progress callback
def progress(downloaded, total):
    percent = (downloaded / total) * 100
    print(f"Progress: {percent:.1f}%")

await client.download_track(track, progress_callback=progress)
```

### HLS Stream Support

```python
# Automatically handles HLS streams for non-downloadable tracks
track = await client.get_track(track_id)

if not track.downloadable:
    # Will use HLS downloader automatically
    path = await client.download_track(track)
```

## Caching

### Configure Cache

```python
from soundcloud import SoundCloudConfig
from soundcloud.cache import RedisCache

# With Redis cache
config = SoundCloudConfig(
    cache={
        "enabled": True,
        "default_ttl": 600,  # 10 minutes
    }
)

client = SoundCloudClient(config)
client.cache.backend = RedisCache(host="localhost", port=6379)

# With file cache
from soundcloud.cache import FileCache
client.cache.backend = FileCache(cache_dir="./cache")

# Cache decorator for custom functions
@client.cache.cached(ttl=300)
async def expensive_operation():
    return await do_something()
```

## Rate Limiting

```python
# Configure rate limiting
config = SoundCloudConfig(
    api={
        "rate_limit": 15,  # requests per second
        "timeout": 30,
    }
)

# Adaptive rate limiting
from soundcloud.utils import AdaptiveRateLimiter

client.rate_limiter = AdaptiveRateLimiter(
    initial_rate=15,
    min_rate=5,
    max_rate=30
)
```

## Error Handling

```python
from soundcloud.exceptions import (
    SoundCloudError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    DownloadError,
    TrackNotDownloadableError
)

try:
    track = await client.get_track(invalid_id)
except NotFoundError:
    print("Track not found")
except AuthenticationError:
    print("Authentication failed")
except RateLimitError as e:
    print(f"Rate limited: {e}")
    await asyncio.sleep(60)
except SoundCloudError as e:
    print(f"SoundCloud error: {e}")
```

## Advanced Usage

### Batch Operations

```python
# Resolve multiple URLs
urls = [
    "https://soundcloud.com/user1/track1",
    "https://soundcloud.com/user2/track2",
]
resources = await client.resolve.resolve_batch(client, urls)

# Parallel track fetching
track_ids = [123456, 789012, 345678]
tracks = await client.tracks.get_tracks(client, track_ids)
```

### Custom Session Configuration

```python
import aiohttp

# Custom timeout and headers
session = aiohttp.ClientSession(
    timeout=aiohttp.ClientTimeout(total=60),
    headers={"Custom-Header": "value"}
)

client = SoundCloudClient(session=session)
```

### Stream Processing

```python
# Get activity stream with pagination
activities = await client.api.stream.get_activities(
    client,
    limit=50,
    cursor=None  # Use cursor from previous response
)

# Process stream items
for activity in activities["collection"]:
    if activity["type"] == "track":
        track = activity["track"]
        print(f"New track: {track.title}")
```

## Configuration

Full configuration options:

```python
from soundcloud import SoundCloudConfig

config = SoundCloudConfig(
    # API settings
    api={
        "rate_limit": 15,
        "timeout": 30,
        "max_retries": 3,
        "user_agent": "MyApp/1.0"
    },
    
    # Authentication
    auth={
        "client_id": "optional_client_id",
        "client_secret": "optional_secret",
        "redirect_uri": "http://localhost:8080/callback",
        "scope": "non-expiring"
    },
    
    # Download settings
    download={
        "download_dir": "./downloads",
        "parallel_downloads": 4,
        "chunk_size": 8192,
        "write_metadata": True,
        "embed_artwork": True,
        "artwork_size": "t500x500",
        "overwrite": False,
        "enable_hls": True
    },
    
    # Cache settings
    cache={
        "enabled": True,
        "default_ttl": 300,
        "max_size": 1000
    },
    
    # Scraper settings
    scraper={
        "max_retries": 3,
        "pages_to_check": [
            "https://soundcloud.com/discover",
            "https://soundcloud.com/stream"
        ]
    }
)
```

## Environment Variables

The integration supports configuration via environment variables:

```bash
# Authentication
export SOUNDCLOUD_CLIENT_ID="your_client_id"
export SOUNDCLOUD_CLIENT_SECRET="your_secret"
export SOUNDCLOUD_ACCESS_TOKEN="your_token"

# API Configuration
export SOUNDCLOUD_API_RATE_LIMIT="20"
export SOUNDCLOUD_API_TIMEOUT="60"

# Download Configuration
export SOUNDCLOUD_DOWNLOAD_DIR="./music"
export SOUNDCLOUD_PARALLEL_DOWNLOADS="6"

# Cache Configuration
export SOUNDCLOUD_CACHE_ENABLED="true"
export SOUNDCLOUD_CACHE_TTL="600"
```

## Module Structure

```
soundcloud/
├── __init__.py           # Main exports
├── client.py             # Main SoundCloudClient
├── config/               # Configuration management
├── types/                # TypedDict definitions
├── auth/                 # Authentication strategies
├── models/               # Data models (Track, Playlist, User)
├── api/                  # API endpoint implementations
├── download/             # Download functionality
├── search/               # Advanced search features
├── cache/                # Cache backends
├── utils/                # Utility functions
└── exceptions/           # Exception hierarchy
```

## Contributing

This integration follows these principles:

1. **Modularity**: Each component has a single responsibility
2. **Type Safety**: Full type hints and TypedDict usage
3. **Async-First**: All I/O operations are async
4. **Error Handling**: Comprehensive exception hierarchy
5. **Documentation**: Detailed docstrings and examples

## License

This integration is part of the music agent project and follows the project's licensing terms.

## Support

For issues or questions:
1. Check the examples in the `tests/` folder
2. Review the API documentation in each module
3. Enable debug logging: `logging.getLogger("soundcloud").setLevel(logging.DEBUG)`

## Disclaimer

This integration is for educational purposes. Respect SoundCloud's terms of service and content creators' rights when downloading content.
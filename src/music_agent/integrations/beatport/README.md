# Beatport Integration

A comprehensive Beatport API v4 integration for the music agent, providing access to electronic music tracks, releases, charts, and metadata.

## Features

### ✅ Implemented
- **Authentication**: OAuth-based login with username/password
- **Search**: Search tracks, releases, artists, and labels
- **Charts**: Top 100, Hype tracks, genre-specific charts
- **Detailed Information**: Get full details for tracks, releases, artists, labels
- **Genre Support**: Browse and filter by electronic music genres
- **Artist/Label Catalogs**: Browse artist discographies and label releases
- **Metadata**: BPM, key, genre, remixers, catalog numbers
- **Preview URLs**: Access to track preview streams

### 🔧 Technical Details
- **API Version**: Beatport API v4
- **Authentication**: OAuth 2.0 with authorization code flow
- **Client ID**: Automatically scraped from API docs
- **Token Management**: Automatic refresh and persistence
- **Rate Limiting**: Respectful request throttling
- **Error Handling**: Comprehensive exception handling

## Installation

```bash
pip install aiohttp beautifulsoup4
```

## Configuration

### Environment Variables
```bash
# Required
BEATPORT_USERNAME=your_username
BEATPORT_PASSWORD=your_password

# Optional
BEATPORT_CLIENT_ID=client_id  # Auto-scraped if not provided
BEATPORT_TOKEN_FILE=~/.beatport_token.json
BEATPORT_DEBUG=false
```

### Configuration File
```python
from src.music_agent.integrations.beatport import BeatportConfig

config = BeatportConfig(
    username="your_username",
    password="your_password",
    token_file="~/.beatport_token.json",
    auto_refresh_token=True,
)
```

## Usage

### Basic Usage
```python
import asyncio
from src.music_agent.integrations.beatport import BeatportClient

async def main():
    # Create client
    client = BeatportClient()
    
    async with client:
        # Search for tracks
        tracks = await client.search_tracks("techno", page=1)
        for track in tracks[:5]:
            print(f"{track.full_title} by {track.artist_names}")
            print(f"  BPM: {track.bpm}, Key: {track.key}")
            print(f"  Label: {track.label.name if track.label else 'Unknown'}")
        
        # Get top 100 tracks for a genre
        top_tracks = await client.get_top_100(genre_id=6)  # Techno
        print(f"\nTop Techno Tracks: {len(top_tracks)}")
        
        # Get track details
        track = await client.get_track(12345678)
        print(f"\nTrack: {track.full_title}")
        print(f"Preview: {track.preview_url}")

asyncio.run(main())
```

### Search with Filters
```python
# Search with genre filter
tracks = await client.search_tracks(
    query="acid",
    genre_id=6,  # Techno
    page=1,
    per_page=50
)

# Search releases by label
releases = await client.search_releases(
    query="",
    label_id=1234,
    page=1
)
```

### Working with Charts
```python
# Get different chart types
top_100 = await client.get_top_100()
hype_tracks = await client.get_hype_tracks()

# Genre-specific charts
techno_top = await client.get_top_100(genre_id=6)
house_top = await client.get_top_100(genre_id=5)
```

### Artist and Label Exploration
```python
# Get artist information
artist = await client.get_artist(artist_id=12345)
print(f"Artist: {artist.name}")

# Get artist's tracks
artist_tracks = await client.get_artist_tracks(artist_id=12345)

# Get label's releases
label_releases = await client.get_label_releases(label_id=6789)
```

### Genre Management
```python
# Get all genres
genres = await client.get_genres()
for genre in genres:
    print(f"{genre.id}: {genre.name}")

# Get specific genre
techno = await client.get_genre(genre_id=6)
```

## Authentication Flow

The integration handles Beatport's OAuth authentication automatically:

1. **Client ID Acquisition**: Automatically scrapes from API docs
2. **Login**: Uses username/password to get authorization code
3. **Token Exchange**: Exchanges code for access/refresh tokens
4. **Token Storage**: Saves tokens to file for reuse
5. **Auto-Refresh**: Refreshes expired tokens automatically

### Manual Token Method
If automatic authentication fails, you can manually provide a token:

1. Open browser developer tools
2. Log into Beatport and navigate to API docs
3. Look for requests to `/v4/auth/o/token/`
4. Copy the access token from the response
5. Save to token file or provide in config

## Data Models

### Track
- `id`: Unique track identifier
- `name`: Track title
- `mix_name`: Mix/version name
- `artists`: List of artists
- `remixers`: List of remixers
- `bpm`: Beats per minute
- `key`: Musical key
- `genre`: Primary genre
- `label`: Record label
- `preview_url`: Stream preview URL

### Release
- `id`: Release identifier
- `name`: Release title
- `artists`: Release artists
- `label`: Record label
- `tracks`: List of tracks
- `release_date`: Release date
- `catalog_number`: Catalog number

### Artist
- `id`: Artist identifier
- `name`: Artist name
- `biography`: Artist bio
- `image`: Artist image URL

### Label
- `id`: Label identifier
- `name`: Label name
- `image`: Label logo URL

## Error Handling

```python
from src.music_agent.integrations.beatport import (
    BeatportError,
    AuthenticationError,
    RateLimitError,
)

try:
    tracks = await client.search_tracks("test")
except AuthenticationError as e:
    print(f"Auth failed: {e}")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after} seconds")
except BeatportError as e:
    print(f"API error: {e}")
```

## Rate Limiting

The integration implements automatic rate limiting:
- Default delay: 0.5 seconds between requests
- Automatic retry on rate limit errors
- Exponential backoff on failures

## Limitations

1. **No Official API Access**: Uses workaround with Swagger UI client ID
2. **Authentication Required**: Requires valid Beatport account
3. **Preview Only**: Full track downloads not available via API
4. **Rate Limits**: Subject to Beatport's rate limiting
5. **Region Restrictions**: Some content may be geo-restricted

## Genre IDs

Common Beatport genre IDs:
- House: 5
- Techno: 6
- Trance: 7
- Drum & Bass: 1
- Dubstep: 18
- Tech House: 11
- Deep House: 12
- Progressive House: 15
- Melodic House & Techno: 90
- Afro House: 89

## Advanced Features

### Token Management
```python
# Load existing token
config = BeatportConfig()
token_data = config.load_token()

# Clear token (force re-authentication)
config.clear_token()

# Manual token save
config.save_token({
    "access_token": "...",
    "refresh_token": "...",
    "expires_in": 3600
})
```

### Custom Session
```python
import aiohttp

# Use custom session with proxy
session = aiohttp.ClientSession(
    connector=aiohttp.TCPConnector(ssl=False),
    timeout=aiohttp.ClientTimeout(total=60)
)

client = BeatportClient(session=session)
```

## Troubleshooting

### Authentication Issues
- Verify username/password are correct
- Check if account has 2FA enabled (not supported)
- Try clearing token file and re-authenticating
- Use manual token method as fallback

### Rate Limiting
- Reduce request frequency
- Implement caching for repeated requests
- Use pagination efficiently

### Network Errors
- Check internet connection
- Verify Beatport API is accessible
- Try increasing timeout values

## Testing

Run the test script:
```bash
python test_beatport.py
```

With debug output:
```bash
BEATPORT_DEBUG=true python test_beatport.py
```

## Notes

- This integration uses an unofficial method to access Beatport's API
- Beatport may change their authentication or API at any time
- Always respect Beatport's terms of service
- Support artists by purchasing music through official channels
# Bandcamp Integration

A scraping-based Bandcamp integration for the music agent that provides search, album/track information retrieval, and download capabilities.

## Features

### ✅ Implemented
- **Search**: Search for albums, tracks, artists, and labels
- **Album Information**: Get detailed album information including tracklist
- **Track Information**: Get individual track details
- **Download Support**: Download tracks and albums (where available)
- **Metadata Writing**: Automatic ID3 tag writing with artwork
- **URL Parsing**: Parse and validate Bandcamp URLs
- **Batch Downloads**: Download entire albums with parallel processing

### 🔧 Technical Details
- **No Official API**: Uses web scraping since Bandcamp has no public API
- **BeautifulSoup**: HTML parsing for data extraction
- **Async/Await**: Full async support with aiohttp
- **Rate Limiting**: Respectful scraping with configurable delays
- **Error Handling**: Comprehensive exception hierarchy

## Installation

```bash
pip install beautifulsoup4 aiohttp mutagen
```

## Configuration

Configuration via environment variables (optional):

```bash
# Bandcamp Configuration
BANDCAMP_DOWNLOAD_DIR="./downloads/bandcamp"
BANDCAMP_ENABLE_DOWNLOADS=true
BANDCAMP_ENABLE_SEARCH=true
BANDCAMP_ENABLE_CACHING=true
BANDCAMP_DEBUG=false
```

## Usage

```python
import asyncio
from src.music_agent.integrations.bandcamp import BandcampClient

async def main():
    # Create client
    client = BandcampClient()
    
    async with client:
        # Search for albums
        results = await client.search_albums("ambient")
        for result in results[:5]:
            print(f"{result['name']} by {result.get('artist', 'Unknown')}")
        
        # Get album details
        album = await client.get_album("https://artist.bandcamp.com/album/example")
        print(f"Album: {album.title}")
        print(f"Tracks: {album.num_tracks}")
        
        # Download album (if available)
        if album.get_downloadable_tracks():
            paths = await client.download_album(
                album,
                output_dir="downloads/"
            )
            print(f"Downloaded {len(paths)} tracks")
        
        # Get individual track
        track = await client.get_track("https://artist.bandcamp.com/track/example")
        print(f"Track: {track.title} - {track.duration_formatted}")

asyncio.run(main())
```

## Architecture

```
bandcamp/
├── scraper/       # Web scraping modules
│   ├── base.py    # Base scraper functionality
│   ├── album.py   # Album-specific scraping
│   └── search.py  # Search scraping
├── models/        # Data models
│   ├── album.py   # Album model
│   └── track.py   # Track model
├── download/      # Download functionality
│   ├── manager.py # Download manager
│   └── metadata.py # Metadata writer
├── utils/         # Utility functions
├── config/        # Configuration
├── exceptions/    # Exception classes
└── client.py      # Main client
```

## Key Components

### Scraper Module
- Extracts data from Bandcamp HTML pages
- Handles JavaScript-embedded data extraction
- Parses TralbumData for track information

### Models
- `Album`: Represents a Bandcamp album with tracks
- `Track`: Represents individual tracks with metadata

### Download Manager
- Handles track and album downloads
- Supports parallel downloads
- Automatic metadata and artwork embedding

## Limitations

1. **No Official API**: Relies on web scraping which may break if Bandcamp changes their HTML
2. **Stream Protection**: Not all content is freely downloadable
3. **Rate Limiting**: Must respect rate limits to avoid being blocked
4. **Purchase Required**: Most content requires purchase for download
5. **Dynamic Content**: Some data is loaded via JavaScript and may not be accessible

## Search Types

- `all`: Search everything
- `albums`: Search only albums
- `tracks`: Search only tracks
- `artists`: Search only artists/bands
- `labels`: Search only labels

## Download Features

- Automatic folder structure creation (artist/album)
- Configurable filename templates
- Metadata embedding (ID3 tags)
- Artwork downloading and embedding
- Lyrics embedding (when available)
- Support for MP3 and FLAC formats

## Error Handling

The integration includes specific exceptions:
- `BandcampError`: Base exception
- `ScrapingError`: Web scraping failures
- `ParseError`: HTML/data parsing errors
- `DownloadError`: Download failures
- `InvalidURLError`: Invalid Bandcamp URLs
- `StreamNotAvailableError`: Content not available for streaming

## Testing

Run the test script:

```bash
python test_bandcamp.py
```

With download testing (searches for free content):

```bash
python test_bandcamp.py --download
```

## Notes

- Most Bandcamp content requires purchase
- The integration respects artist rights and only downloads freely available content
- Free/name-your-price albums can be downloaded at $0
- Always support artists by purchasing their music when possible
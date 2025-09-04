# Music Agent Integrations

A comprehensive collection of music service integrations for discovering, streaming, downloading, and managing music content.

## Overview

This directory contains integrations with various music platforms, services, and tools. Each integration is designed to work seamlessly with the music agent system, providing a unified interface for music discovery and management.

## Implemented Integrations

### 🎵 Streaming & Download Services

#### 1. **SoundCloud** (`soundcloud/`)
- **Type**: Directory-based integration with full async support
- **Features**: 
  - Search tracks, playlists, albums, users
  - Stream and download tracks (where permitted)
  - User authentication via client credentials
  - Playlist management
  - Like/unlike tracks
  - Get user stream and reposts
- **API**: Official SoundCloud API v2
- **Status**: ✅ Production ready

#### 2. **Mixcloud** (`mixcloud/`)
- **Type**: Directory-based integration with GraphQL support
- **Features**:
  - Search shows, users, tags
  - Get show details and tracklists
  - Stream URLs extraction
  - User profile information
  - Popular shows discovery
- **API**: Mixcloud GraphQL API
- **Status**: ✅ Production ready

#### 3. **Bandcamp** (`bandcamp/`)
- **Type**: Directory-based web scraping integration
- **Features**:
  - Search albums, tracks, artists, labels
  - Album and track information retrieval
  - Stream URL extraction (where available)
  - Download support for free/name-your-price content
  - Custom domain support (e.g., music.monstercat.com)
- **API**: Web scraping (no official API)
- **Status**: ✅ Functional with limitations

#### 4. **YouTube** (`youtube.py`)
- **Type**: Single-file integration
- **Features**:
  - Search videos and playlists
  - Download audio/video with yt-dlp
  - Extract metadata
  - Playlist processing
  - Format selection
- **API**: YouTube Data API + yt-dlp
- **Status**: ✅ Production ready

#### 5. **Spotify** (`spotify.py`)
- **Type**: Single-file integration
- **Features**:
  - Search tracks, albums, artists, playlists
  - Get recommendations
  - User library management
  - Playlist creation and management
  - Track audio features analysis
- **API**: Official Spotify Web API
- **Status**: ✅ Production ready

#### 6. **Deezer** (`deezer.py`)
- **Type**: Single-file integration
- **Features**:
  - Search tracks, albums, artists, playlists
  - Get charts and editorial content
  - User favorites management
  - Radio stations
  - Track and album information
- **API**: Official Deezer API
- **Status**: ✅ Production ready

### 🔍 Music Discovery & Information

#### 7. **Discogs** (`discogs.py`)
- **Type**: Single-file integration
- **Features**:
  - Database search (releases, artists, labels)
  - Detailed release information
  - Artist discography
  - Label catalog browsing
  - Master release versions
  - Community data (ratings, reviews)
- **API**: Official Discogs API
- **Status**: ✅ Production ready

#### 8. **1001 Tracklists** (`tracklists_1001.py`)
- **Type**: Single-file web scraping integration
- **Features**:
  - Search DJ sets and tracklists
  - Get detailed tracklist information
  - Track identification from DJ sets
  - Popular tracks and sets
  - Artist set history
- **API**: Web scraping
- **Status**: ✅ Functional

#### 9. **Simple Tracklists** (`tracklists_simple.py`)
- **Type**: Single-file parser
- **Features**:
  - Parse text-based tracklists
  - Extract artist and track names
  - Handle various tracklist formats
  - Clean and normalize track data
  - Export to structured format
- **API**: Text parsing (no external API)
- **Status**: ✅ Production ready

### 🔄 P2P & File Sharing

#### 10. **Soulseek** (`soulseek.py`)
- **Type**: Single-file integration
- **Features**:
  - Search files across P2P network
  - Download files from peers
  - User browsing
  - Queue management
  - Connection handling
- **API**: Soulseek protocol via slskd
- **Status**: ✅ Functional

### 🎛️ DJ Software & Tools

#### 11. **Rekordbox Sync** (`rekordbox_sync.py`)
- **Type**: Single-file integration
- **Features**:
  - Sync playlists with Rekordbox
  - Export track metadata
  - BPM and key information
  - Cue point management
  - Collection synchronization
- **API**: Rekordbox XML/database
- **Status**: ✅ Beta

### 🧠 AI & Memory

#### 12. **Graphiti Memory** (`graphiti_memory.py`)
- **Type**: Single-file integration
- **Features**:
  - Store music preferences
  - Track listening history
  - Build knowledge graph of music relationships
  - Query music memories
  - Personalized recommendations based on history
- **API**: Graphiti knowledge graph
- **Status**: ✅ Experimental

## Integration Architecture

### Directory-Based Integrations
Complex integrations with multiple modules:
```
integration_name/
├── __init__.py       # Public API exports
├── client.py         # Main client class
├── models/           # Data models
├── api/             # API interaction layer
├── utils/           # Helper functions
├── config/          # Configuration
├── exceptions/      # Custom exceptions
└── README.md        # Documentation
```

### Single-File Integrations
Simpler integrations in a single module:
```python
# integration_name.py
- Client class
- Data models
- API methods
- Utility functions
```

## Planned Integrations

### 🎯 Next Priority Integrations

#### 1. **Beatport** 
- **Purpose**: Essential for electronic music DJs and producers
- **API**: Official REST API available
- **Key Features to Implement**:
  - Search tracks, releases, artists, labels
  - Genre-specific charts (Tech House, Techno, House, etc.)
  - DJ charts and staff picks
  - Track preview streams (30-90 second clips)
  - BPM, key, and genre metadata
  - Beatport LINK integration for streaming
  - Purchase links and pricing
- **Data Available**: Release date, label, remixers, catalog number, waveform data
- **Architecture**: Directory-based (complex API with multiple endpoints)
- **Challenges**: Requires API key application, rate limiting

#### 2. **Last.fm**
- **Purpose**: Music tracking, scrobbling, and discovery
- **API**: Official REST API v2.0
- **Key Features to Implement**:
  - Scrobble tracks (record listening history)
  - Get user listening history and stats
  - Similar artist/track recommendations
  - Tag-based radio and discovery
  - User library management
  - Social features (friends, loved tracks)
  - Artist biography and images
- **Data Available**: Play counts, tags, similar artists, top tracks, events
- **Architecture**: Single-file (straightforward API)
- **Challenges**: OAuth authentication for user actions

#### 3. **Tidal**
- **Purpose**: High-fidelity streaming service
- **API**: Unofficial API (reverse-engineered)
- **Key Features to Implement**:
  - Search tracks, albums, artists, playlists
  - Stream URLs (FLAC, Master quality)
  - Exclusive content and early releases
  - Music videos
  - Editorial playlists and recommendations
  - Artist radio stations
- **Data Available**: Audio quality tiers, exclusive content flags, credits
- **Architecture**: Directory-based (complex authentication)
- **Challenges**: No official API, auth token management, region restrictions

#### 4. **Genius**
- **Purpose**: Lyrics, annotations, and song meanings
- **API**: Official API with limited access
- **Key Features to Implement**:
  - Search songs by title/artist
  - Get lyrics (web scraping required)
  - Song annotations and meanings
  - Artist information and verified annotations
  - Album tracklists with lyrics
  - Song relationships (samples, covers, remixes)
- **Data Available**: Lyrics, annotations, song facts, producer/writer credits
- **Architecture**: Single-file (simple API + scraping)
- **Challenges**: Full lyrics require web scraping

#### 5. **Resident Advisor**
- **Purpose**: Electronic music events, news, and reviews
- **API**: No official API (web scraping)
- **Key Features to Implement**:
  - Event search by location/date
  - Club and venue information
  - DJ/artist profiles and upcoming shows
  - Music reviews and features
  - RA Podcast series
  - Ticket links
- **Data Available**: Event lineups, venues, dates, ticket prices, reviews
- **Architecture**: Directory-based (complex scraping)
- **Challenges**: Dynamic content, anti-scraping measures

#### 6. **Archive.org**
- **Purpose**: Free music archives and historical recordings
- **API**: Official API (Archive.org API)
- **Key Features to Implement**:
  - Search audio collections
  - Download free music
  - Live concert recordings (Live Music Archive)
  - Netlabels collection
  - 78 RPM recordings
  - Radio programs
  - Metadata extraction
- **Data Available**: Full downloads, metadata, collection info, reviews
- **Architecture**: Single-file (simple API)
- **Challenges**: Large file sizes, varied audio quality

#### 7. **Boomkat**
- **Purpose**: Underground, experimental, and avant-garde music
- **API**: No official API (web scraping)
- **Key Features to Implement**:
  - Browse new releases and recommendations
  - Genre charts (Ambient, Techno, Experimental, etc.)
  - Detailed album descriptions and reviews
  - Label profiles
  - Staff picks and recommendations
  - Preview clips
- **Data Available**: Reviews, recommendations, genre tags, format info
- **Architecture**: Single-file (focused scraping)
- **Challenges**: Limited preview access, purchase-only content

#### 8. **NTS Radio**
- **Purpose**: Curated radio shows and mixes
- **API**: Official API available
- **Key Features to Implement**:
  - Live radio streams (NTS 1 and NTS 2)
  - Show archive search
  - Episode tracklists
  - Resident and guest shows
  - Genre exploration
  - Infinite Mixtapes (AI-powered continuous mixes)
  - Download shows (where permitted)
- **Data Available**: Show descriptions, tracklists, air dates, genres, moods
- **Architecture**: Single-file (clean API)
- **Challenges**: Tracklist parsing, time-based content

#### 9. **MusicBrainz**
- **Purpose**: Open music metadata database
- **API**: Official REST API (XML/JSON)
- **Key Features to Implement**:
  - Music identification (by metadata)
  - Comprehensive discography data
  - Relationships between artists/releases
  - AcoustID audio fingerprinting
  - ISRC and barcode lookups
  - Cover art via Cover Art Archive
  - Edit history and data provenance
- **Data Available**: MBIDs, release groups, credits, relationships, ratings
- **Architecture**: Single-file (well-documented API)
- **Challenges**: Complex data model, rate limiting

### Implementation Roadmap

**Phase 1 - Core Music Services** (High Priority)
1. Beatport - Electronic music focus
2. Tidal - High-quality streaming
3. Genius - Lyrics enhancement

**Phase 2 - Discovery & Tracking** (Medium Priority)
4. Last.fm - Scrobbling and stats
5. MusicBrainz - Metadata enrichment
6. Archive.org - Free music access

**Phase 3 - Specialized Content** (Lower Priority)
7. Resident Advisor - Events and electronic music
8. NTS Radio - Curated content
9. Boomkat - Underground music

### Technical Specifications

#### API Authentication Requirements
- **Beatport**: API key (application required)
- **Last.fm**: API key (free registration)
- **Tidal**: Username/password or OAuth token
- **Genius**: Client Access Token
- **Archive.org**: Optional API key for higher limits
- **NTS Radio**: No auth required
- **MusicBrainz**: No auth, but user agent required

#### Rate Limits
- **Beatport**: 3600 requests/hour
- **Last.fm**: 5 requests/second
- **Genius**: 2000 requests/hour
- **Archive.org**: Respectful crawling expected
- **MusicBrainz**: 1 request/second average

#### Data Formats
- **JSON**: Beatport, Last.fm, Genius, NTS, Tidal
- **XML/JSON**: MusicBrainz, Archive.org
- **HTML**: Resident Advisor, Boomkat (scraping)

### Other Potential Integrations (Future Consideration)

- **Amazon Music** - Large catalog with Prime integration
- **Juno Download** - DJ-focused digital music store
- **Traxsource** - House and electronic music
- **FMA (Free Music Archive)** - Creative Commons music
- **Audiomack** - Hip-hop and electronic focus
- **Datpiff** - Mixtape platform
- **Hypem (Hype Machine)** - Blog-aggregated music
- **Shazam** - Music recognition
- **Songkick/Bandsintown** - Concert discovery
- **Serato/Traktor** - DJ software integration
- **Ableton Link** - Tempo sync protocol

## Usage Examples

### Basic Search Across Services
```python
from music_agent.integrations.soundcloud import SoundCloudClient
from music_agent.integrations.spotify import SpotifyClient
from music_agent.integrations.bandcamp import BandcampClient

async def search_all_platforms(query: str):
    # Initialize clients
    soundcloud = SoundCloudClient()
    spotify = SpotifyClient()
    bandcamp = BandcampClient()
    
    # Search across platforms
    async with soundcloud, spotify, bandcamp:
        sc_results = await soundcloud.search_tracks(query)
        sp_results = await spotify.search_tracks(query)
        bc_results = await bandcamp.search_albums(query)
    
    return {
        'soundcloud': sc_results,
        'spotify': sp_results,
        'bandcamp': bc_results
    }
```

### Download Pipeline
```python
from music_agent.integrations.youtube import YouTubeClient
from music_agent.integrations.soulseek import SoulseekClient

async def find_and_download(track_name: str, artist: str):
    # Try YouTube first
    youtube = YouTubeClient()
    results = await youtube.search(f"{artist} {track_name}")
    if results:
        return await youtube.download(results[0]['url'])
    
    # Fallback to Soulseek
    soulseek = SoulseekClient()
    files = await soulseek.search(f"{artist} {track_name}")
    if files:
        return await soulseek.download(files[0])
```

## Configuration

Most integrations require API keys or credentials. Set these via environment variables:

```bash
# Streaming Services
SOUNDCLOUD_CLIENT_ID=your_client_id
SOUNDCLOUD_CLIENT_SECRET=your_client_secret
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
DEEZER_APP_ID=your_app_id
DEEZER_APP_SECRET=your_app_secret

# APIs
YOUTUBE_API_KEY=your_api_key
DISCOGS_TOKEN=your_token
LASTFM_API_KEY=your_api_key
GENIUS_TOKEN=your_token

# Services
SLSKD_API_URL=http://localhost:5030
SLSKD_API_KEY=your_api_key
```

## Contributing

When adding new integrations:

1. **Choose Structure**: 
   - Use directory-based for complex integrations (>500 lines)
   - Use single-file for simple integrations

2. **Follow Patterns**:
   - Async/await throughout
   - Comprehensive error handling
   - Type hints for all methods
   - Docstrings for public APIs

3. **Include Features**:
   - Search functionality
   - Data retrieval methods
   - Rate limiting
   - Retry logic
   - Proper exceptions

4. **Documentation**:
   - README for directory integrations
   - Usage examples
   - Configuration requirements
   - Known limitations

## Testing

Each integration should have:
- Unit tests for data parsing
- Integration tests with mocked API responses
- Live tests with real services (optional)
- Rate limit compliance tests

## License & Legal

Ensure all integrations:
- Respect service Terms of Service
- Implement rate limiting
- Handle authentication properly
- Respect copyright and licensing
- Document any legal limitations

## Status Legend

- ✅ **Production ready**: Fully tested and stable
- ⚠️ **Beta**: Functional but may have issues
- 🚧 **In development**: Partially implemented
- 📋 **Planned**: Not yet implemented
- ❌ **Deprecated**: No longer maintained
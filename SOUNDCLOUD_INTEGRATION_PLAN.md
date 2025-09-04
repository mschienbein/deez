# SoundCloud Integration - Comprehensive Implementation Plan

## Executive Summary

A complete SoundCloud integration combining official API capabilities with enhanced features from community libraries, including download support, metadata extraction, and advanced search capabilities. This integration will support both authenticated and public access patterns.

## Architecture Overview

### Core Components

```
src/music_agent/integrations/soundcloud/
├── __init__.py              # Main exports
├── client.py                # SoundCloud API client
├── auth.py                  # Authentication handlers
├── models.py                # Data models (Track, Playlist, User)
├── downloader.py            # Download & streaming functionality
├── scraper.py               # Client ID scraping & public access
├── search.py                # Advanced search capabilities
├── utils.py                 # Helper functions
└── exceptions.py            # Custom exceptions
```

### Data Flow

```
User Request → Authentication Layer → API Client → Response Models
                        ↓                   ↓
                 Scraper (fallback)    Downloader (MP3/HLS)
                                            ↓
                                     Metadata Writer
```

## Detailed Component Specifications

### 1. Authentication System (`auth.py`)

#### 1.1 Multi-Mode Authentication
```python
class SoundCloudAuth:
    """Handles all authentication flows"""
    
    # OAuth2 Methods
    - authorization_code_flow()    # Web app flow
    - client_credentials_flow()     # Server-to-server
    - user_credentials_flow()       # Username/password
    - refresh_token_flow()          # Token refresh
    
    # Public Access Methods
    - scrape_client_id()           # Extract from public pages
    - rotate_client_ids()          # Multiple scraped IDs
    - validate_client_id()         # Test if ID works
```

#### 1.2 Client ID Management
- **Primary**: User-provided API key (when available)
- **Fallback**: Scraped client IDs from public pages
- **Pool System**: Maintain pool of 5-10 scraped IDs
- **Rotation**: Automatic rotation on rate limit
- **Caching**: Store valid IDs with TTL of 24 hours

### 2. API Client (`client.py`)

#### 2.1 Core Endpoints

**Track Operations**
```python
# Basic CRUD
- get_track(track_id)
- update_track(track_id, data)
- delete_track(track_id)
- upload_track(file_path, metadata)

# Discovery
- get_track_comments(track_id, limit=50)
- get_track_favoriters(track_id, limit=50)
- get_track_reposters(track_id, limit=50)
- get_related_tracks(track_id, limit=20)

# Streaming
- get_stream_url(track_id, quality='high')
- get_download_url(track_id)  # If downloadable
```

**Playlist Operations**
```python
- get_playlist(playlist_id)
- create_playlist(title, tracks=[])
- update_playlist(playlist_id, data)
- delete_playlist(playlist_id)
- add_track_to_playlist(playlist_id, track_id)
- remove_track_from_playlist(playlist_id, track_id)
- reorder_playlist(playlist_id, track_positions)
```

**User Operations**
```python
- get_user(user_id)
- get_user_tracks(user_id, limit=50)
- get_user_playlists(user_id, limit=50)
- get_user_likes(user_id, limit=50)
- get_user_reposts(user_id, limit=50)
- get_user_followers(user_id, limit=50)
- get_user_followings(user_id, limit=50)
- follow_user(user_id)
- unfollow_user(user_id)
```

**Search & Discovery**
```python
- search_tracks(query, filters={})
- search_playlists(query, filters={})
- search_users(query, filters={})
- search_all(query)  # Combined search
- get_trending(genre=None, region=None)
- get_charts(kind='top', genre='all', region='all')
```

**Interaction**
```python
- like_track(track_id)
- unlike_track(track_id)
- repost_track(track_id)
- remove_repost(track_id)
- comment_on_track(track_id, body, timestamp=None)
- delete_comment(comment_id)
```

#### 2.2 Advanced Features

**Batch Operations**
```python
- get_tracks(track_ids)  # Bulk fetch (max 50)
- like_tracks(track_ids)
- download_playlist(playlist_id, output_dir)
```

**Pagination Support**
```python
- Cursor-based pagination for all list endpoints
- Automatic pagination with generators
- Page size configuration (default: 50, max: 200)
```

**Rate Limiting**
```python
- Automatic retry with exponential backoff
- Rate limit tracking per endpoint
- Queue system for batch requests
- Configurable delays (default: 15 req/sec)
```

### 3. Download System (`downloader.py`)

#### 3.1 Download Capabilities

**MP3 Downloads**
```python
class SoundCloudDownloader:
    # Direct downloads (for downloadable tracks)
    - download_track(track, output_path)
    - download_playlist(playlist, output_dir)
    
    # Stream assembly (for non-downloadable)
    - assemble_hls_stream(track)  # NEW: HLS support
    - extract_progressive_stream(track)
    
    # Batch downloads
    - parallel_download(tracks, max_workers=5)
    - resume_download(partial_file)
```

#### 3.2 Stream Handling

**Progressive Streams**
- Direct MP3 download for tracks marked as downloadable
- Progressive stream URL extraction
- Chunked download with progress tracking

**HLS Streams** (NEW)
```python
- parse_m3u8_playlist(url)
- download_segments(segments)
- merge_segments_to_mp3(segments)
- clean_temp_files()
```

#### 3.3 Metadata Management

**ID3 Tag Writing**
```python
- write_metadata(file_path, track_data)
  - Title, Artist, Album
  - Album artwork (high resolution)
  - Genre, Year, Track number
  - BPM, Key (if available)
  - Comments, URL
  
- extract_artwork(track, size='original')
  - original (highest quality)
  - t500x500, t300x300 (specific sizes)
  - crop/badge variants
```

### 4. Data Models (`models.py`)

#### 4.1 Track Model
```python
class Track:
    # Core attributes
    id: int
    title: str
    artist: str  # Extracted from user or title
    duration: int  # milliseconds
    
    # URLs
    permalink_url: str
    stream_url: str
    download_url: Optional[str]
    waveform_url: str
    artwork_url: str
    
    # Metadata
    genre: str
    tags: List[str]
    bpm: Optional[float]
    key_signature: Optional[str]
    description: str
    created_at: datetime
    
    # Statistics
    playback_count: int
    likes_count: int
    reposts_count: int
    comment_count: int
    download_count: int
    
    # Flags
    downloadable: bool
    streamable: bool
    public: bool
    commentable: bool
    
    # Relationships
    user: User
    label: Optional[Label]
    
    # Methods
    - download(output_path=None)
    - stream()
    - get_comments(limit=50)
    - get_related()
    - to_dict()
    - to_agent_format()  # Convert for music agent
```

#### 4.2 Playlist Model
```python
class Playlist:
    id: int
    title: str
    description: str
    tracks: List[Track]
    track_count: int
    duration: int
    
    # Metadata
    genre: str
    tags: List[str]
    created_at: datetime
    
    # Types
    playlist_type: str  # playlist, album, compilation, ep
    is_album: bool
    
    # Methods
    - add_track(track)
    - remove_track(track_id)
    - reorder(new_order)
    - download_all(output_dir)
    - to_m3u(file_path)
    - to_agent_format()
```

#### 4.3 User Model
```python
class User:
    id: int
    username: str
    permalink: str
    avatar_url: str
    
    # Profile
    full_name: str
    description: str
    city: str
    country: str
    
    # Statistics
    track_count: int
    playlist_count: int
    followers_count: int
    followings_count: int
    
    # Methods
    - get_tracks()
    - get_playlists()
    - get_likes()
    - follow()
    - unfollow()
```

### 5. Search System (`search.py`)

#### 5.1 Advanced Search

```python
class SoundCloudSearch:
    # Basic search
    - search(query, type='track', limit=50)
    
    # Filtered search
    - search_with_filters(
        query,
        duration_from=0,      # seconds
        duration_to=None,
        created_at_from=None,
        created_at_to=None,
        genres=[],
        tags=[],
        bpm_from=None,
        bpm_to=None,
        key_signature=None,
        downloadable=None,
        hd=None
    )
    
    # Faceted search
    - get_search_facets(query)  # Returns available filters
    
    # Trending & Charts
    - get_trending(genre, region='all', time='week')
    - get_charts(kind='top', genre='all')
    - get_new_releases(genre=None)
```

#### 5.2 Smart Features

**Similar Track Finding**
```python
- find_similar_by_audio(track_id)  # Audio analysis
- find_similar_by_metadata(track)   # Tags/genre matching
- find_remixes(track_id)            # Find remixes/edits
```

**Playlist Generation**
```python
- generate_playlist_from_track(track_id, size=20)
- generate_playlist_from_artist(user_id, size=20)
- generate_radio_station(seed_tracks)
```

### 6. Scraper System (`scraper.py`)

#### 6.1 Client ID Extraction

```python
class ClientIDScraper:
    # Scraping sources
    SCRAPE_URLS = [
        'https://soundcloud.com/',
        'https://soundcloud.com/discover',
        'https://soundcloud.com/charts/top'
    ]
    
    # Methods
    - scrape_client_id()           # Get single ID
    - scrape_multiple_ids(count=5)  # Build ID pool
    - validate_id(client_id)        # Test if working
    - monitor_id_health()           # Background validation
```

#### 6.2 Public Data Access

```python
- resolve_url(url)  # Convert SC URL to API resource
- get_public_track_data(url)
- get_public_user_data(url)
- extract_track_id_from_url(url)
```

### 7. Utility Functions (`utils.py`)

#### 7.1 URL Handling
```python
- resolve_soundcloud_url(url)
- extract_resource_type(url)  # track/playlist/user
- build_api_url(endpoint, params)
- get_high_quality_artwork(url)
```

#### 7.2 Audio Processing
```python
- calculate_bpm(audio_file)  # BPM detection
- detect_key(audio_file)      # Key detection
- normalize_audio(file_path)  # Volume normalization
- convert_to_mp3(input_file)  # Format conversion
```

#### 7.3 Text Processing
```python
- extract_artist_title(string)  # Smart parsing
- clean_filename(title)         # Safe filenames
- parse_description_urls(text)  # Extract URLs
- extract_hashtags(text)        # Get tags
```

## Agent Tools Integration

### Tools to Create (50+ tools)

#### Track Tools
1. `get_soundcloud_track` - Fetch track by ID/URL
2. `search_soundcloud_tracks` - Search with filters
3. `download_soundcloud_track` - Download MP3 with metadata
4. `stream_soundcloud_track` - Get streaming URL
5. `get_track_comments` - Fetch track comments
6. `get_related_tracks` - Find similar tracks
7. `like_track` - Like a track
8. `repost_track` - Repost a track
9. `comment_on_track` - Add comment

#### Playlist Tools
10. `get_soundcloud_playlist` - Fetch playlist
11. `create_soundcloud_playlist` - Create new playlist
12. `add_to_soundcloud_playlist` - Add tracks
13. `remove_from_playlist` - Remove tracks
14. `reorder_playlist` - Change track order
15. `download_entire_playlist` - Batch download
16. `export_playlist_to_m3u` - Export format

#### User Tools
17. `get_soundcloud_user` - User profile
18. `get_user_tracks` - User's tracks
19. `get_user_playlists` - User's playlists
20. `get_user_likes` - Liked tracks
21. `follow_user` - Follow user
22. `unfollow_user` - Unfollow user

#### Discovery Tools
23. `get_soundcloud_trending` - Trending tracks
24. `get_soundcloud_charts` - Charts by genre
25. `discover_new_music` - Personalized discovery
26. `find_remixes` - Find track remixes
27. `generate_radio_station` - Create radio

#### Download Tools
28. `batch_download_tracks` - Multiple downloads
29. `download_with_metadata` - Full ID3 tags
30. `download_hls_stream` - Non-downloadable tracks
31. `download_user_likes` - Download all likes
32. `resume_failed_download` - Resume partial

#### Analysis Tools
33. `analyze_track_metadata` - Extract all metadata
34. `detect_track_bpm` - BPM detection
35. `detect_track_key` - Key detection
36. `find_similar_tracks` - Audio similarity
37. `analyze_user_taste` - User preference analysis

#### Utility Tools
38. `resolve_soundcloud_url` - URL to resource
39. `validate_soundcloud_url` - Check if valid
40. `get_track_waveform` - Waveform data
41. `get_track_artwork` - High-res artwork
42. `convert_to_soundcloud_format` - Prepare upload

#### Upload Tools
43. `upload_track` - Upload new track
44. `update_track_metadata` - Edit track info
45. `delete_track` - Remove track
46. `replace_track_audio` - Update audio file

#### Social Tools
47. `get_my_stream` - Activity feed
48. `get_notifications` - User notifications
49. `send_message` - Private message
50. `share_track` - Share functionality

## Implementation Phases

### Phase 1: Core Foundation (Week 1)
1. Set up project structure
2. Implement authentication system
3. Create base client with rate limiting
4. Develop Track and Playlist models
5. Basic download functionality

### Phase 2: API Coverage (Week 2)
1. Implement all track endpoints
2. Implement playlist endpoints
3. User endpoints
4. Search and discovery
5. Social features

### Phase 3: Advanced Features (Week 3)
1. HLS stream support
2. Batch operations
3. Metadata extraction
4. Audio analysis tools
5. Smart recommendations

### Phase 4: Agent Integration (Week 4)
1. Create all agent tools
2. Test integrations
3. Documentation
4. Performance optimization
5. Error handling

## Configuration

### Environment Variables
```env
# API Credentials
SOUNDCLOUD_CLIENT_ID=your_client_id
SOUNDCLOUD_CLIENT_SECRET=your_client_secret
SOUNDCLOUD_ACCESS_TOKEN=your_token
SOUNDCLOUD_REFRESH_TOKEN=refresh_token

# Optional Settings
SOUNDCLOUD_DOWNLOAD_DIR=/path/to/downloads
SOUNDCLOUD_CACHE_DIR=/path/to/cache
SOUNDCLOUD_MAX_RETRIES=3
SOUNDCLOUD_RATE_LIMIT=15
SOUNDCLOUD_DOWNLOAD_QUALITY=high
SOUNDCLOUD_ENABLE_HLS=true
SOUNDCLOUD_PARALLEL_DOWNLOADS=5
```

### Configuration Class
```python
class SoundCloudConfig:
    # API Settings
    client_id: str
    client_secret: Optional[str]
    access_token: Optional[str]
    
    # Download Settings
    download_dir: Path = Path('./downloads')
    temp_dir: Path = Path('./temp')
    download_quality: str = 'high'
    parallel_downloads: int = 5
    chunk_size: int = 8192
    
    # Cache Settings
    enable_cache: bool = True
    cache_dir: Path = Path('./cache')
    cache_ttl: int = 3600
    
    # Rate Limiting
    requests_per_second: int = 15
    retry_attempts: int = 3
    retry_delay: float = 1.0
    
    # Features
    enable_hls: bool = True
    enable_metadata: bool = True
    enable_artwork: bool = True
    artwork_size: str = 'original'
```

## Error Handling

### Custom Exceptions
```python
class SoundCloudException(Exception): pass
class AuthenticationError(SoundCloudException): pass
class RateLimitError(SoundCloudException): pass
class DownloadError(SoundCloudException): pass
class StreamNotAvailable(SoundCloudException): pass
class TrackNotDownloadable(SoundCloudException): pass
class InvalidURL(SoundCloudException): pass
class ClientIDExpired(SoundCloudException): pass
```

### Retry Strategy
- Exponential backoff for rate limits
- Automatic client ID rotation on auth errors
- Resume capability for downloads
- Graceful degradation (HLS → Progressive → Stream)

## Testing Strategy

### Unit Tests
- Test each API endpoint
- Mock responses for offline testing
- Client ID scraping validation
- Download functionality
- Metadata writing

### Integration Tests
- Full download pipeline
- Playlist operations
- Search functionality
- Authentication flows
- Rate limit handling

### Performance Tests
- Batch download speeds
- Concurrent request handling
- Cache effectiveness
- Memory usage optimization

## Security Considerations

1. **Credential Storage**: Use keyring for secure storage
2. **Client ID Rotation**: Automatic rotation to avoid rate limits
3. **Request Signing**: Implement request signing where needed
4. **Token Refresh**: Automatic token refresh before expiry
5. **Secure Downloads**: Verify SSL certificates
6. **Rate Limit Respect**: Never exceed API limits

## Performance Optimizations

1. **Connection Pooling**: Reuse HTTP connections
2. **Async Support**: Asyncio for concurrent operations
3. **Chunk Downloads**: Stream large files in chunks
4. **Parallel Processing**: Multi-threaded downloads
5. **Caching Strategy**: Cache frequently accessed data
6. **Lazy Loading**: Load data only when needed
7. **Batch Requests**: Group API calls where possible

## Monitoring & Logging

### Metrics to Track
- API call count per endpoint
- Success/failure rates
- Download speeds
- Cache hit ratios
- Client ID health
- Rate limit approaching warnings

### Logging Levels
- DEBUG: All API calls and responses
- INFO: Major operations (downloads, uploads)
- WARNING: Rate limits, retries
- ERROR: Failed operations
- CRITICAL: Authentication failures

## Documentation Requirements

1. **API Reference**: Document all public methods
2. **Usage Examples**: Common use cases with code
3. **Agent Tools Guide**: How to use each tool
4. **Troubleshooting**: Common issues and solutions
5. **Migration Guide**: From deprecated library

## Dependencies

```toml
[dependencies]
requests = "^2.31.0"        # HTTP client
mutagen = "^1.47.0"         # ID3 tag writing
beautifulsoup4 = "^4.12.0"  # HTML parsing (scraping)
m3u8 = "^3.5.0"            # HLS playlist parsing
aiohttp = "^3.9.0"         # Async HTTP
pydantic = "^2.5.0"        # Data validation
python-dotenv = "^1.0.0"   # Environment variables
tenacity = "^8.2.0"        # Retry logic
cachetools = "^5.3.0"      # Caching
librosa = "^0.10.0"        # Audio analysis (optional)
keyring = "^24.3.0"        # Secure credential storage
```

## Success Criteria

1. ✅ All official API endpoints implemented
2. ✅ Download support for all track types
3. ✅ HLS stream assembly working
4. ✅ Metadata and artwork extraction
5. ✅ 50+ agent tools created
6. ✅ Robust error handling
7. ✅ Comprehensive test coverage
8. ✅ Performance benchmarks met
9. ✅ Documentation complete
10. ✅ Production ready

## Notes

- Priority on reliability over speed
- Graceful degradation for missing features
- Respect SoundCloud's terms of service
- Consider legal implications of downloading
- Implement user-agent rotation
- Monitor for API changes
- Plan for future API deprecations

---

This plan creates a production-ready SoundCloud integration that exceeds the capabilities of both the official (deprecated) library and community alternatives, while providing seamless integration with the music agent system.
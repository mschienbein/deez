# Additional Music Integrations - Implementation Plan

## Current Status

As of September 2025, we have successfully implemented **13 music service integrations**:

### Completed Integrations
1. **SoundCloud** - Full streaming/download with authentication
2. **Mixcloud** - DJ mixes and shows with GraphQL API
3. **Bandcamp** - Independent music with web scraping
4. **Beatport** - Electronic music with BPM/key metadata (just completed)
5. **YouTube** - Video/audio downloads via yt-dlp
6. **Spotify** - Streaming catalog with Web API
7. **Deezer** - Music streaming and discovery
8. **Soulseek** - P2P file sharing
9. **Discogs** - Music database and marketplace
10. **1001 Tracklists** - DJ set tracklists
11. **Simple Tracklists** - Text tracklist parser
12. **Rekordbox Sync** - DJ software integration
13. **Graphiti Memory** - AI music preferences

## Planned Additional Integrations

### Phase 1 - Core Music Services (High Priority)
#### 1. Tidal
- **Purpose**: High-fidelity streaming service (FLAC/Master quality)
- **Status**: Researched, ready to implement
- **API**: Unofficial API (reverse-engineered)
- **Challenges**: Complex authentication, region restrictions
- **Implementation**: Directory-based (complex auth flow)

#### 2. Genius
- **Purpose**: Lyrics, annotations, and song meanings
- **Status**: Researched, ready to implement  
- **API**: Official API + web scraping for full lyrics
- **Challenges**: Limited API access for lyrics
- **Implementation**: Single-file (API + scraping hybrid)

### Phase 2 - Discovery & Tracking (Medium Priority)
#### 3. Last.fm
- **Purpose**: Music tracking, scrobbling, and discovery
- **Status**: Well-documented API, straightforward
- **API**: Official REST API v2.0
- **Implementation**: Single-file (simple API)

#### 4. MusicBrainz
- **Purpose**: Open music metadata database
- **Status**: Comprehensive API documentation available
- **API**: Official REST API (XML/JSON)
- **Implementation**: Single-file (well-structured API)

#### 5. Archive.org
- **Purpose**: Free music archives and live recordings
- **Status**: Simple API, large content library
- **API**: Official Archive.org API
- **Implementation**: Single-file (straightforward API)

### Phase 3 - Specialized Content (Lower Priority)
#### 6. Resident Advisor
- **Purpose**: Electronic music events and reviews
- **Status**: Web scraping required (no API)
- **Challenges**: Dynamic content, anti-scraping
- **Implementation**: Directory-based (complex scraping)

#### 7. NTS Radio
- **Purpose**: Curated radio shows with tracklists
- **Status**: Clean API available
- **API**: Official NTS API
- **Implementation**: Single-file (clean API)

#### 8. Boomkat
- **Purpose**: Underground/experimental music
- **Status**: Web scraping required
- **Challenges**: Purchase-focused content
- **Implementation**: Single-file (focused scraping)

## Implementation Resources

### Technical Specifications Already Prepared
- **Authentication requirements** for each service
- **Rate limits** and API restrictions
- **Data models** and expected responses
- **Architecture decisions** (single-file vs directory-based)

### Development Guidelines Established
- **Code patterns** from existing integrations (SoundCloud, Mixcloud, Bandcamp)
- **Error handling** hierarchies
- **Configuration management** patterns
- **Testing approaches** with mock responses

## How to Resume Implementation

### 1. Choose Next Integration
Recommend starting with **Last.fm** or **Genius** as they have:
- Well-documented APIs
- Straightforward authentication
- Single-file implementation (easier to build)
- High value-add for music discovery

### 2. Implementation Steps
For any integration, follow this proven pattern:

```bash
# For directory-based (complex)
mkdir src/music_agent/integrations/{service_name}/{api,models,utils,config}

# For single-file (simple)  
touch src/music_agent/integrations/{service_name}.py
```

#### Required Files (Directory-based):
- `__init__.py` - Public API exports
- `client.py` - Main client class
- `config.py` - Configuration management
- `auth.py` - Authentication handler (if needed)
- `models.py` - Data models
- `exceptions.py` - Custom exceptions
- `README.md` - Documentation
- `test_{service}.py` - Test script

#### Required Components (Single-file):
- Client class with async methods
- Data models (dataclasses)
- Configuration handling
- Error handling
- Authentication (if required)

### 3. Testing Strategy
Each integration should include:
- Unit tests with mocked responses
- Integration tests with real API calls
- Rate limit compliance testing
- Error condition handling

### 4. Documentation Requirements
- Usage examples in README
- Configuration instructions
- API limitations and legal considerations
- Known issues and troubleshooting

## Reference Materials

### Existing Integration Patterns
- **Authentication**: See `beatport/auth.py` for OAuth flow
- **API Client**: See `soundcloud/client.py` for comprehensive REST client
- **Models**: See `mixcloud/models.py` for rich data models
- **Configuration**: See `bandcamp/config.py` for env var handling
- **Web Scraping**: See `bandcamp/scraper/` for BeautifulSoup patterns

### API Documentation Links
- **Tidal**: No official docs (reverse-engineered)
- **Genius**: https://docs.genius.com/
- **Last.fm**: https://www.last.fm/api
- **MusicBrainz**: https://musicbrainz.org/doc/MusicBrainz_API
- **Archive.org**: https://archive.org/help/aboutapi.php
- **NTS**: https://www.nts.live/api (unofficial but available)

## Environment Setup for New Integrations

### Required Dependencies (already installed)
```bash
aiohttp          # HTTP client
beautifulsoup4   # Web scraping
mutagen         # Audio metadata
```

### Additional Dependencies (as needed)
```bash
# For specific integrations
lxml            # Faster XML parsing (MusicBrainz)
python-dateutil # Date parsing
pillow          # Image processing
```

## Estimated Implementation Time

Based on complexity and existing patterns:

- **Last.fm**: 4-6 hours (simple API)
- **Genius**: 6-8 hours (API + scraping)
- **Archive.org**: 4-6 hours (simple API)
- **MusicBrainz**: 8-10 hours (complex data model)
- **NTS Radio**: 6-8 hours (API + audio streams)
- **Tidal**: 12-16 hours (complex auth)
- **Resident Advisor**: 16-20 hours (complex scraping)
- **Boomkat**: 8-10 hours (focused scraping)

## Legal and Ethical Considerations

### Always Implement
- Rate limiting to respect service resources
- User-Agent headers identifying the application
- Compliance with Terms of Service
- Respect for robots.txt (where applicable)

### Service-Specific Notes
- **Tidal**: Unofficial API use may violate ToS
- **Resident Advisor**: Check scraping policy
- **Boomkat**: Respect purchase-focused business model
- **All services**: Never distribute or cache copyrighted content

## Integration Testing Checklist

When resuming, test each integration for:
- [ ] Authentication flow works
- [ ] Search functionality returns results
- [ ] Data models parse API responses correctly
- [ ] Rate limiting prevents 429 errors
- [ ] Error handling covers common failure cases
- [ ] Configuration loading works
- [ ] Documentation examples are accurate

## Contact Points for Implementation

If implementation resumes:
1. Start with comprehensive README review in `/src/music_agent/integrations/`
2. Reference existing integration patterns
3. Begin with simplest integration (Last.fm recommended)
4. Test thoroughly before moving to next integration
5. Update main integrations README when complete

## Archive Note

This plan was created in September 2025 after completing 13 integrations including the comprehensive Beatport integration. The foundation is solid, patterns are established, and the next integrations are well-researched and ready for implementation when needed.
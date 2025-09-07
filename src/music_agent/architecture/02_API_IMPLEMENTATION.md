# 🔌 API Implementation Planning

## 4. **Real API Implementation**

#### Implementation Priority
**Current tools are ALL MOCKED - which should we implement first?**

**Order of Implementation:**
```
1. Discogs (token ready, easiest to start)
2. MusicBrainz (no auth, good metadata)
3. Soulseek (critical for rare finds)
4. Deezer (main download source)
5. Spotify (complex auth but important)
6. Beatport (has API, needs token auth)
7. YouTube (playlist parsing)
```

**Implementation Notes:**
- Beatport has a robust API (not scraping) - requires login + token copy
- Build and test ALL integrations fully before moving on
- Don't skip any APIs in this list for MVP
- Implement all features per integration (search, download, metadata, etc.)
- Follow the pattern from bandcamp/beatport folders (broken up, readable)
- Most are partially done - needs cleanup/refactor/testing

#### Rate Limiting Strategy
- [ ] Simple delay between requests
- [ ] Token bucket algorithm
- [x] Platform-specific limits
- [ ] Redis-based distributed limiting (add later when scaling)

**Implementation Approach:**
- Start local, add Redis later if needed for distribution
- Use conservative limits initially, optimize to 90% as we test
- Implement exponential backoff (1s, 2s, 4s, 8s, max 30s) for 429 errors
- One rate limit per platform (keep it simple)

**Per-Platform Limits:**
```
- Discogs: 55 requests/minute (conservative from 60 limit)
- MusicBrainz: 1 request/second (per their request)
- Spotify: 170 requests/minute (conservative from 180 limit)
- Soulseek: 5 concurrent connections
- Deezer: 50 requests/minute (conservative estimate - verify)
- Beatport: 30 requests/minute (conservative estimate - verify)
- YouTube: 90 searches/day (9000 units from 10000 quota)
```

**Notes:**
- Start with simple delays for most platforms
- Upgrade to token bucket for complex APIs (Spotify) as needed
- Research actual limits for Deezer/Beatport during testing
- Adjust from conservative to optimal (90%) after verification

#### Caching Strategy
- [x] In-memory (fast, non-persistent) 
- [ ] Redis (add later when scaling)
- [x] Database (PostgreSQL for backup/persistence)
- [ ] Multi-level (memory → PostgreSQL now, add Redis later)

**Cache Configuration:**
```
- TTL for successful metadata: 24-48 hours
- TTL for failed searches: 6 hours  
- TTL for artist/album info: 7 days
- Download URLs: Never cache (expire quickly)
- Maximum cache size: Managed by TTL
- Eviction policy: LRU if memory pressure, otherwise TTL-based
```

**Cache Key Strategy:**
- Use agent/LLM to normalize search queries for cache keys
- Handle variations ("deadmau5 - strobe" = "Strobe deadmau5" = "deadmau5 strobe")
- Store normalized key → result mapping

**Cache Invalidation:**
- No manual clearing needed - let TTL handle expiry
- Cache doesn't block finding better quality (quality checks happen post-cache)
- If higher quality found, it updates DB but doesn't invalidate cache
- Fresh searches can be forced with a flag if needed

#### Authentication Handling
- [x] API keys in environment variables (.env file)
- [ ] OAuth where available (use packages)
- [ ] Web scraping fallback
- [ ] User provides credentials per session

**Security Approach:**
```
- All keys unencrypted in .env for now (already have several)
- Static keys/tokens - no auto-refresh initially
- Add automation for token refresh in future version
```

**Platform-Specific Auth:**
```
Spotify: 
- Use spotipy or similar package for auth
- Store refresh token in .env

Beatport:
- Similar to Deezer - manual token copy
- CLI tool to guide user getting token
- Store in .env as BEATPORT_TOKEN

Deezer:
- Use existing CLI tool pattern for ARL token
- Look into deezer-python package if it simplifies
- Store ARL in .env

Soulseek:
- Username/password in .env
- Set and forget (already working)

Discogs:
- API token already in .env ✓

MusicBrainz:
- No auth needed ✓

YouTube:
- API key in .env when implemented
```

**Future Improvements:**
- Automate token refresh where possible
- Add token encryption
- Build CLI tools for token acquisition (like Deezer)
- Session management for web-based auth

---

## 🔄 API Integration Architecture

### Integration Structure
**Each integration should be fully featured with all capabilities:**
```python
class PlatformIntegration:
    def search_tracks(query) -> List[Track]
    def get_metadata(track_id) -> TrackMetadata
    def get_download_url(track_id) -> str
    def download_track(track_id) -> bytes
    def get_audio_features(track_id) -> AudioFeatures
    # All capabilities in one place
```

**Key Principles:**
- Integrations are "dumb" - they just provide capabilities
- Agents are "smart" - they orchestrate and make decisions
- No artificial separation of download vs metadata in integrations
- Each integration handles its own retry/resumption logic

### Agent Orchestration
**Agents decide what to use when:**
- DataCollector agents choose metadata sources
- AcquisitionScout agents manage download chains
- Agents set appropriate timeouts based on operation type

### Timeout Strategy
**Context-aware timeouts set by agents:**
```
- Metadata operations: 10 seconds
- Download operations: 300 seconds (5 minutes)
- Search operations: 5 seconds
- Quick checks: 2 seconds
```

### Error Handling & Fallbacks
**Retry Strategy:**
- 3 retries at integration level (for network issues)
- Exponential backoff (1s, 2s, 4s)
- Agent decides whether to try next source
- Failed tracks go to "needs_review" queue

**Fallback Chain (configurable):**
```
Downloads: soulseek → deezer → spotify → youtube
Metadata: beatport → discogs → musicbrainz → spotify
```

### Quality Verification
**Levels of verification:**
- Quick header check (< 1 second) - verify format/bitrate
- Full verification only if suspicious (size mismatch)
- Agent decides verification level needed
- Trust established sources (Beatport, Bandcamp)

### Partial Downloads
- Integrations handle their own resumption if supported
- Keep partials for P2P sources (Soulseek)
- Delete partials for streaming sources
- Agent decides retry vs abandon

---

## 🛠️ Platform-Specific Implementation Notes

### Spotify
**Status**: Token through web login
**Implementation Approach:**
```
- 
- 
- 
```

### Beatport
**Status**: Token through web login needed
**Implementation Approach:**
```
- 
- 
- 
```

### Discogs
**Status**: Token in env, ready to implement
**Implementation Approach:**
```
- 
- 
- 
```

### Soulseek
**Status**: Critical for rare finds
**Implementation Approach:**
```
- 
- 
- 
```

### Deezer
**Status**: Download source priority
**Implementation Approach:**
```
- 
- 
- 
```

### YouTube
**Status**: Unimplemented, needed for playlists
**Implementation Approach:**
```
- 
- 
- 
```

### MusicBrainz
**Status**: No auth needed, unimplemented
**Implementation Approach:**
```
- 
- 
- 
```

---

## 🔄 API Integration Architecture

### Download Sources
**Priority Order:**
1. Soulseek (rare/high quality)
2. Deezer (mainstream)
3. Spotify (fallback)
4. YouTube (last resort)

**Quality Requirements:**
```
- Minimum bitrate: _____ kbps
- Preferred format: _______________
- Fallback format: _______________
```

### Metadata Sources
**Priority Order:**
1. Beatport (electronic music)
2. Discogs (releases/vinyl)
3. MusicBrainz (comprehensive)
4. Spotify (audio features)

**Required Fields:**
```
- 
- 
- 
- 
```

---

## 📊 API Feature Matrix

| Platform | Download | Metadata | Playlists | Search | Auth Type | Priority |
|----------|----------|----------|-----------|---------|-----------|----------|
| Soulseek | ✅ | ❌ | ❌ | ✅ | P2P | HIGH |
| Deezer | ✅ | ✅ | ✅ | ✅ | OAuth | HIGH |
| Spotify | ✅ | ✅ | ✅ | ✅ | Web Token | HIGH |
| Beatport | ❌ | ✅ | ❌ | ✅ | Web Token | HIGH |
| Discogs | ❌ | ✅ | ❌ | ✅ | API Key | HIGH |
| YouTube | ✅ | ⚠️ | ✅ | ✅ | API Key | MEDIUM |
| MusicBrainz | ❌ | ✅ | ❌ | ✅ | None | MEDIUM |
| SoundCloud | | | | | | LOW |

---

## 🚧 Implementation Challenges

### Web Login Token Extraction
**Platforms**: Spotify, Beatport
**Approach:**
```
- 
- 
- 
```

### P2P Integration
**Platform**: Soulseek
**Challenges:**
```
- 
- 
- 
```

### Rate Limiting & Quotas
**Concerns:**
```
- 
- 
- 
```

### Data Normalization
**Issues to Address:**
```
- Different field names
- Different data formats
- Missing fields
- Conflicting data
```

---

## 📝 Implementation Tasks

### Phase 1: Core APIs
- [ ] Implement Discogs API (token ready)
- [ ] Implement MusicBrainz API (no auth)
- [ ] Research Spotify download method
- [ ] Test Soulseek integration

### Phase 2: Download Sources
- [ ] Implement Deezer downloader
- [ ] Implement Spotify downloader
- [ ] Implement Soulseek search/download
- [ ] Add YouTube fallback

### Phase 3: Metadata Enhancement
- [ ] Implement Beatport scraper/API
- [ ] Add audio feature extraction
- [ ] Implement conflict resolution
- [ ] Add confidence scoring

### Phase 4: Advanced Features
- [ ] Playlist parsing (YouTube)
- [ ] Batch processing
- [ ] Quality verification
- [ ] Duplicate detection

---

## 🔐 Security Considerations

### API Key Management
```
- Store in environment variables
- Rotate regularly
- Monitor usage
- 
```

### Web Scraping Ethics
```
- Respect robots.txt
- Implement delays
- Use official APIs when available
- 
```

### User Data Protection
```
- Encrypt stored credentials
- Don't log sensitive data
- 
- 
```

---

## 📈 Success Metrics

### API Performance
- Average response time: _____ ms
- Success rate: _____%
- Cache hit rate: _____%
- Error rate: _____%

### Data Quality
- Metadata completeness: _____%
- Conflict resolution accuracy: _____%
- Download success rate: _____%
- Quality match rate: _____%

---

## ❓ Open Questions

1. How to handle API keys that require paid subscriptions?
2. Should we implement our own audio analysis for BPM/key?
3. How to handle region-locked content?
4. What's the fallback when all APIs fail?
5. How to validate downloaded file quality?
6. Should we support torrent sources?
7. How to handle DMCA concerns?
8. 
9. 
10.
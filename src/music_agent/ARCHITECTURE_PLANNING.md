# 🎵 Music Agent Architecture Planning Document

## 📋 Document Purpose
This document maps out the complete architecture for the Music Agent system, identifying components, workflows, integrations, and key decisions needed. Each section includes space for annotations, answers, and additional questions.

---

## 🎯 Current System Overview

### **Core Components Found**

#### 1. **Strands Framework** (strands_research/)
- Multi-agent orchestration using AWS Strands
- OpenAI/Bedrock LLM providers  
- Specialized agents: DataCollector, MetadataAnalyst, QualityAssessor, AcquisitionScout
- Mock tools for demos (no real API calls yet)

**Notes/Questions:**
```
this looks ok for a MVP, but we should only use openai for now and dont worry about bedrock.
- 
- 
- 
```

#### 2. **Rekordbox Integration**
- SQLCipher decryption of master.db
- Syncs tracks, playlists, cue points
- Stores in PostgreSQL + Graphiti memory

**Notes/Questions:**
```
this should be updated to use this package instead of a rough implementation,we should leverage the work done by the author of this package, and build on top of it. leverage any features it has that we arent currently using but also add any features that we arent currently using but that we should. mainily we are focused on library sync but theres other things in there probably.

- https://pyrekordbox.readthedocs.io/en/stable/quickstart.html
- https://github.com/dylanljones/pyrekordbox
- 
```

#### 3. **API Integrations Available**
- **Implemented**: Spotify, Beatport, Discogs, Deezer, YouTube, SoundCloud, MixCloud, Bandcamp
- **Specialized**: Tracklists (1001tracklists), Soulseek (P2P)
- **Memory**: Graphiti (Neo4j graph database)

**Notes/Questions:**
```
we should consider which of these are needed for analysis and which are used for acquisition of tracks. and also which are essential for the MVP and which are nice to have. some dont have api access or python libraries and some arent even available as an api and use scraping. for example i think theres tools for spotify but im not sure if theres a true api we need to do that research. soundcloud wouldnt give me api access so maybe we can shelve that for now. we should confirm the full list in a next assesment.
- 
- 
- 
```

#### 4. **Data Models**
- TrackMetadata (unified format)
- ResearchResult (with solve criteria)
- Platform-specific results
- Quality assessment

**Notes/Questions:**
```
I think this is an ok starting point for the MVP, but we should confirm the full model based on hitting the actual api endpoints to see whats availble, making it very robust and complete.
- 
- 
- 
```

---

## ❓ Key Architecture Questions

### 1. **Integration Priority & Completeness**

#### Which platforms are ESSENTIAL for your use case?
- Beatport (electronic music focus)
- Spotify (mainstream catalog)
- Discogs (vinyl/release info)
- Other: _______________

**Your Priority Order:**
```
1. soulseek, deezer, and spotify for downloads
2. beatport and discogs for metadata along with the above
3. youtube as a secondary source for downloads but also playlist parsing abilities, like heres a playlist, go find all the tracks metadata and download them.
after this im not sure what else we need, but we should confirm the full list in a next assesment. and after creating complete integrations to get the full dataests they can provide.
```

#### API Access Status
- [x] Spotify API key available, note: spotify api is a token you get through logging in to their website, we should be able to create a robust api or use a package to get this though, theres packages that use this for download so i know its possible to use this as a download source but its incomplete
- [x] Beatport API access
- note: beatport api is a token you get through logging in to their website, we should be able to create a robust api or use a package to get this though
- [x] Discogs token
- note: discogs api token is already in the env
- [x] MusicBrainz (no auth needed)
- note: musicbrainz api is unimplemented, we should add this to the api integrations, and use it for metadata
- [ ] YouTube API key
- note: youtube api is unimplemented, we should add this to the api integrations, and use it for metadata, and download 
- [ ] SoundCloud client ID,
- note: soundcloud api is unimplemented, it requires scraping so lets put it aside for now.
- [ ] Other: not sure but i know soulseek should work.

**Notes:**
```
[Your notes here]
- 
- 
```

#### Should we prioritize download or purchase platforms?
- [x] Download priority (Spotify/soulseek/Deezer)
- [ ] Purchase priority (Beatport/Bandcamp/other with searching)



**Reasoning:**
```
notes: i think we should prioritize download, but should provide purchase links either way as a fallback.
- 
- 
```

#### Is Soulseek integration important for rare tracks?
- [x] Yes, critical for rare finds
- [ ] Nice to have
- [ ] Not needed
- [ ] Other: _______________

**Notes:**
```
a lot of songs of high quality wont be on deezer or spotify, so soulseek is critical for rare finds, and probably the most important integration.
- 
- 
```

---

### 2. **Workflow & Agent Design**

#### Parallel vs Sequential Processing
- [x] All platforms simultaneously (faster, more API calls)
- [ ] Smart routing (check reliable sources first)
- [ ] Tiered approach (Tier 1 first, then others if needed)
- [ ] User-specified per search

**Preferred Approach & Why:**
```
notes: it makes sense to parallelize the api calls, it should be faster if we can get the results from multiple sources at the same time.
- 
- 
- 
```

#### Conflict Resolution Strategy
**Example: Beatport says 128 BPM, Spotify says 127**
- [x] Trust most reliable source (define reliability scores)
- [ ] Average/median of all sources
- [ ] Weighted by confidence scores
- [x] Manual review for conflicts
- [ ] Other: _______________

**Platform Reliability Ranking (1=most reliable):**
```
for this im not sure and im wondering if theres an open source library that does this already. we could extract bpm and key information and compare it to beatport etc
```

#### Track "Solved" Criteria

im leaving this blank so we can talk about what this means and make sure i understand it correctly, seems like an important part of the system but i dont know what it means. and if its done correctly would lead to solving the problem of finding the highest quality version of a track. or if its not possible we could stub that it needs x thing to be solved. some tracks may never meet all the criteria but we should still be able to find the highest quality version of a track. for example some random bootlegs or edits might be lower quality.
**Current: 80% completeness, 70% confidence, 2+ sources**
- [ ] Keep current criteria
- [ ] Adjust thresholds: _______________
- [ ] Add additional requirements: _______________
- [ ] Different criteria for different use cases

**Your Criteria:**
```
- Completeness threshold: _____%
- Confidence threshold: _____%
- Minimum sources: _____
- Must have fields: 
  - [ ] BPM
  - [ ] Key
  - [ ] Genre
  - [ ] Year
  - [ ] Label
  - [ ] Other: _______________
```

#### DJ-Focused Mode
- [x] Yes, prioritize DJ-relevant metadata
- [ ] No, treat all metadata equally
- [ ] User-switchable mode

**DJ-Specific Requirements:**
```
notes: i think we should prioritize metadata that is most relevant to DJs, like bpm, key, genre, year, label, etc. whatever is in rekordbox is most important. but also what is pulled from something like beatport. since we are mainly using this to feed rekordbox, we should prioritize metadata that is most relevant to DJs and that should be the baseline.
- 
- 
- 
```

---

### 3. **Data Flow & Storage**

#### Primary Source of Truth
- [ ] Rekordbox database is master
- [x] Our PostgreSQL is master
- [ ] Bidirectional sync
- [ ] Other: _______________

**Sync Strategy:**
```
notes: we should sync to postgresql and use it as the primary source of truth. we should also sync to graphiti for context and relationships. i think it makes sense to have a central db or more than one db like you could ask to add songs to a new db thats just for friends to not pollute the main rekordbox db.
- 
- 
- 
```

#### Search & Update Policy
- [ ] Every search updates local database
- [x] Only manual saves update database
- [ ] Auto-update if confidence > threshold
- [ ] Other: _______________

**Notes:**
```
notes: we should only update the database when the user manually saves the track. we should also update the graphiti database automatically so that theres context and relationships for the track. i think for now this is fine but later on we can make sure that as things work better this can be automated.
- 
- 
```

#### Duplicate Handling
**Same track from different sources**
- [ ] Keep all versions
- [ ] Merge into single record
- [x] Keep highest quality version
- [ ] User chooses per track

**Deduplication Strategy:**
```
notes: we should keep the highest quality version of the track. this is actually one of the main functions. if you have existing music in rekordbox thats low quality the agent should be able to find the highest quality version and replace it. the source isnt important as long as its high quality and metadata complete.
```

#### Memory System Usage
- [x] Graphiti for context and relationships
- [ ] PostgreSQL only (simpler)
- [x] Both (PostgreSQL for data, Graphiti for intelligence)
- [x] Redis for caching + PostgreSQL for storage

**Architecture Decision:**
```
notes: we should use graphiti for context and relationships. we should also use it for intelligence. we should use postgresql for data storage. we should use redis for caching. the graphiti integration is mainly to make the agent perform better its not really a source of truth like the postgresql database.
- 
- 
- 
```

---

### 4. **Real API Implementation**

#### Implementation Priority
**Current tools are ALL MOCKED - which should we implement first?**

**Order of Implementation:**
```
1. 
2. 
3. 
4. 
5. 
```

#### Rate Limiting Strategy
- [ ] Simple delay between requests
- [ ] Token bucket algorithm
- [ ] Platform-specific limits
- [ ] Redis-based distributed limiting

**Per-Platform Limits:**
```
- Spotify: _____ requests/minute
- Beatport: _____ requests/minute
- Discogs: _____ requests/minute
- Other: _____
```

#### Caching Strategy
- [ ] Redis (distributed, persistent)
- [ ] In-memory (fast, non-persistent)
- [ ] Database (PostgreSQL)
- [ ] Multi-level (memory → Redis → database)

**Cache Configuration:**
```
- TTL for successful searches: _____ hours
- TTL for failed searches: _____ hours
- Maximum cache size: _____ GB
- Eviction policy: _______________
```

#### Authentication Handling
- [ ] OAuth where available (Spotify)
- [ ] API keys in environment variables
- [ ] Web scraping fallback
- [ ] User provides credentials per session

**Security Approach:**
```
[Your notes here]
- 
- 
- 
```

---

### 5. **User Interface & Interaction**

#### Interface Type
- [ ] CLI-based (current)
- [ ] Web interface
- [ ] Desktop app (Electron)
- [ ] API-only (for other tools)
- [ ] Multiple interfaces

**Primary Interface Choice:**
```
[Your notes here]
- 
- 
```

#### Search Initiation
- [ ] Rekordbox sync triggers searches
- [ ] Manual single track search
- [ ] Batch CSV/playlist import
- [ ] Watch folder for new files
- [ ] API endpoint
- [ ] Other: _______________

**Workflow Preference:**
```
[Your notes here]
- 
- 
- 
```

#### Processing Mode
- [ ] Single track lookups only
- [ ] Batch processing (entire library)
- [ ] Both modes available
- [ ] Queue system for large batches

**Batch Processing Needs:**
```
- Maximum batch size: _____ tracks
- Processing priority: _______________
- Progress reporting: _______________
```

#### Export Formats
- [ ] Rekordbox XML
- [ ] CSV/Excel
- [ ] JSON
- [ ] Direct database update
- [ ] M3U playlists
- [ ] Other: _______________

**Primary Export Use Case:**
```
[Your notes here]
- 
- 
```

---

### 6. **Quality & Acquisition**

#### Quality Definition
**What defines "high quality" for you?**
- [ ] Lossless only (FLAC/WAV/AIFF)
- [ ] 320kbps MP3 acceptable
- [ ] 256kbps AAC acceptable
- [ ] Quality varies by use case
- [ ] Other: _______________

**Quality Priorities:**
```
1. 
2. 
3. 
```

#### Purchase Preferences
**Platform Priority for Purchasing**
- [ ] Beatport (electronic focus)
- [ ] Bandcamp (artist support)
- [ ] iTunes/Apple Music
- [ ] Amazon Music
- [ ] Direct from label
- [ ] Other: _______________

**Budget Considerations:**
```
- Maximum price per track: $_____
- Monthly budget: $_____
- Auto-purchase threshold: $_____
```

#### Region-Locked Content
- [ ] Use VPN/proxy
- [ ] Skip region-locked
- [ ] Find alternative sources
- [ ] Manual intervention

**Strategy:**
```
[Your notes here]
- 
- 
```

#### Download Automation
- [ ] Just provide links
- [ ] Auto-purchase from Beatport
- [ ] Download from streaming (where legal)
- [ ] Queue downloads for manual review
- [ ] Full automation with rules

**Automation Rules:**
```
[Your notes here]
- 
- 
- 
```

---

### 7. **Missing Components Identified**

#### Real API Implementations
**All currently mocked - priority order needed**

**Implementation Checklist:**
- [ ] Spotify Web API
- [ ] Beatport API (or scraper)
- [ ] Discogs API
- [ ] MusicBrainz API
- [ ] YouTube Data API
- [ ] SoundCloud API
- [ ] Deezer API
- [ ] 1001tracklists scraper
- [ ] Other: _______________

**Notes:**
```
[Your notes here]
- 
- 
```

#### Batch Processing System
- [ ] Needed for library sync
- [ ] Not needed (single track only)
- [ ] Queue with priority system
- [ ] Distributed processing

**Requirements:**
```
[Your notes here]
- 
- 
```

#### Duplicate Detection
- [ ] Acoustic fingerprinting
- [ ] Fuzzy title/artist matching
- [ ] ISRC/catalog number matching
- [ ] Manual review

**Strategy:**
```
[Your notes here]
- 
- 
```

#### BPM/Key Analysis
- [ ] Trust platform data
- [ ] Half-time detection
- [ ] Key notation conversion (Camelot/Open Key)
- [ ] Audio analysis fallback

**Requirements:**
```
[Your notes here]
- 
- 
```

#### Cue Point Preservation
- [ ] Critical feature
- [ ] Nice to have
- [ ] Not needed
- [ ] Other: _______________

**Notes:**
```
[Your notes here]
- 
- 
```

#### Export to Rekordbox
- [ ] Direct database update
- [ ] XML export
- [ ] Both options
- [ ] Not needed

**Requirements:**
```
[Your notes here]
- 
- 
```

---

## 🏗️ Proposed Architecture Flow

### System Architecture Diagram
```
1. INPUT SOURCES
   ├── Rekordbox DB (decrypt & read)
   ├── Manual search queries
   └── Playlist imports

2. STRANDS ORCHESTRATION
   ├── ChiefResearcher (supervisor)
   ├── DataCollectors (per platform)
   ├── MetadataAnalyst (merge & resolve)
   ├── QualityAssessor (validate)
   └── AcquisitionScout (find sources)

3. API INTEGRATIONS (parallel)
   ├── Tier 1: Beatport, Spotify (high confidence)
   ├── Tier 2: Discogs, MusicBrainz (metadata)
   └── Tier 3: SoundCloud, YouTube (fallback)

4. RESOLUTION ENGINE
   ├── Conflict resolution (weighted by source reliability)
   ├── BPM/Key normalization
   ├── Duplicate detection
   └── Quality scoring

5. STORAGE
   ├── PostgreSQL (structured data)
   ├── Graphiti/Neo4j (relationships)
   └── Cache layer (Redis)

6. OUTPUT
   ├── Update Rekordbox DB
   ├── Export playlists
   └── Acquisition links/automation
```

**Architecture Modifications:**
```
[Your notes here]
- 
- 
- 
- 
```

---

## 🎯 Specific Use Cases

### Primary Use Case
- [ ] Building DJ sets
- [ ] Cataloging collection
- [ ] Finding rare tracks
- [ ] Metadata cleanup
- [ ] Track discovery
- [ ] Other: _______________

**Detailed Description:**
```
[Your notes here]
- 
- 
- 
```

### Secondary Use Cases
```
1. 
2. 
3. 
```

### User Workflow Example
**Describe your ideal workflow step-by-step:**
```
1. 
2. 
3. 
4. 
5. 
6. 
7. 
8. 
```

---

## 🛠️ Technical Decisions

### Programming Language & Framework
- [x] Python (current choice)
- [ ] Node.js/TypeScript
- [ ] Other: _______________

**Notes:**
```
[Your notes here]
- 
- 
```

### Deployment Environment
- [ ] Local only
- [ ] Cloud (AWS/GCP/Azure)
- [ ] Docker containers
- [ ] Kubernetes
- [ ] Other: _______________

**Infrastructure Requirements:**
```
[Your notes here]
- 
- 
```

### Performance Requirements
- Response time for single track: _____ seconds
- Batch processing speed: _____ tracks/minute
- Maximum concurrent searches: _____
- Cache hit ratio target: _____%

**Notes:**
```
[Your notes here]
- 
- 
```

### Monitoring & Logging
- [ ] Basic logging to files
- [ ] Structured logging (JSON)
- [ ] Metrics collection (Prometheus)
- [ ] Error tracking (Sentry)
- [ ] Other: _______________

**Requirements:**
```
[Your notes here]
- 
- 
```

---

## 🎮 DJ Software Integration

### Primary DJ Software
- [ ] Rekordbox only
- [ ] Also Traktor
- [ ] Also Serato
- [ ] Virtual DJ
- [ ] Other: _______________

**Version Information:**
```
- Software: _______________
- Version: _______________
- OS: _______________
```

### Export Requirements
- [ ] Hot cues must transfer
- [ ] Memory cues needed
- [ ] Loops important
- [ ] Beat grid critical
- [ ] Comments/tags
- [ ] Other: _______________

**Priority Order:**
```
1. 
2. 
3. 
4. 
```

### Library Management
- [ ] Rekordbox is master library
- [ ] Separate tool manages library
- [ ] Multiple libraries synced
- [ ] Other: _______________

**Workflow:**
```
[Your notes here]
- 
- 
- 
```

---

## 📊 Success Metrics

### How do we measure success?
- [ ] Percentage of tracks resolved
- [ ] Metadata accuracy
- [ ] Processing speed
- [ ] User satisfaction
- [ ] Cost per track
- [ ] Other: _______________

**Specific Targets:**
```
- Track resolution rate: _____%
- Average confidence score: _____%
- Processing time: _____ sec/track
- API cost: $_____ /month
- Other: _______________
```

---

## 🚀 Implementation Phases

### Phase 1: MVP
**Target Date: _______________**
```
Features:
- 
- 
- 
- 
```

### Phase 2: Enhanced
**Target Date: _______________**
```
Features:
- 
- 
- 
- 
```

### Phase 3: Complete
**Target Date: _______________**
```
Features:
- 
- 
- 
- 
```

---

## ❓ Additional Questions & Notes

### Open Questions
```
1. 
2. 
3. 
4. 
5. 
6. 
7. 
8. 
9. 
10. 
```

### Technical Concerns
```
1. 
2. 
3. 
4. 
5. 
```

### Business/Legal Considerations
```
1. 
2. 
3. 
4. 
5. 
```

### Future Features Wishlist
```
1. 
2. 
3. 
4. 
5. 
6. 
7. 
8. 
9. 
10. 
```

---

## 📝 Decision Log

### Decisions Made
| Date | Decision | Reasoning | Made By |
|------|----------|-----------|---------|
| | | | |
| | | | |
| | | | |
| | | | |
| | | | |

### Decisions Pending
| Question | Options | Deadline | Owner |
|----------|---------|----------|-------|
| | | | |
| | | | |
| | | | |
| | | | |
| | | | |

---

## 🎯 Next Steps

### Immediate Actions
- [ ] 
- [ ] 
- [ ] 
- [ ] 
- [ ] 

### Blocked On
```
1. 
2. 
3. 
```

### Resources Needed
```
1. 
2. 
3. 
4. 
5. 
```

---

## 📚 References & Documentation

### API Documentation Links
- Spotify: https://developer.spotify.com/documentation/web-api/
- Discogs: https://www.discogs.com/developers/
- MusicBrainz: https://musicbrainz.org/doc/MusicBrainz_API
- Beatport: [Need documentation link]
- Other: _______________

### Internal Documentation
```
- 
- 
- 
```

### Related Projects/Inspiration
```
- 
- 
- 
```

---

## Appendix A: Platform Comparison Matrix

| Platform | API Available | Auth Type | Rate Limits | Best For | Notes |
|----------|--------------|-----------|-------------|----------|-------|
| Spotify | Yes | OAuth 2.0 | | | |
| Beatport | Limited | | | Electronic | |
| Discogs | Yes | Token | | Releases | |
| MusicBrainz | Yes | None | | Metadata | |
| SoundCloud | Yes | OAuth 2.0 | | Remixes | |
| Deezer | Yes | OAuth 2.0 | | Streaming | |
| Bandcamp | No | Scraping | | Indie | |
| YouTube | Yes | API Key | | Everything | |
| 1001tracklists | No | Scraping | | DJ Sets | |
| Soulseek | No | P2P | | Rare | |

---

## Appendix B: Data Field Mapping

| Field | Spotify | Beatport | Discogs | MusicBrainz | Our Format |
|-------|---------|----------|---------|-------------|------------|
| Title | name | title | title | title | title |
| Artist | artists[] | artists[] | artists[] | artist-credit | artist |
| BPM | tempo | bpm | | | bpm |
| Key | key | key | | | key |
| Genre | genres[] | genre | genre | tags | genre |
| | | | | | |
| | | | | | |
| | | | | | |

---

## Sign-off

**Document Owner:** _______________
**Last Updated:** _______________
**Version:** 1.0
**Status:** [ ] Draft [ ] In Review [ ] Approved
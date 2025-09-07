# 📋 Current System Overview & Decisions

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

## ✅ Key Decisions Made

### Integration Priority & Completeness

#### Platform Priority Order:
```
1. soulseek, deezer, and spotify for downloads
2. beatport and discogs for metadata along with the above
3. youtube as a secondary source for downloads but also playlist parsing abilities, like heres a playlist, go find all the tracks metadata and download them.
after this im not sure what else we need, but we should confirm the full list in a next assesment. and after creating complete integrations to get the full dataests they can provide.
```

#### API Access Status
- ✅ **Spotify API** - token through web login, packages exist for download
- ✅ **Beatport API** - token through web login, need robust implementation
- ✅ **Discogs API** - token already in env
- ✅ **MusicBrainz** - no auth needed, unimplemented
- ❌ **YouTube API** - unimplemented, needed for metadata & download
- ❌ **SoundCloud** - requires scraping, shelved for now
- ✅ **Soulseek** - should work, critical for rare finds

#### Download vs Purchase Priority
- **Decision**: Download priority (Spotify/Soulseek/Deezer)
- **Reasoning**: Prioritize download, but provide purchase links as fallback

#### Soulseek Integration
- **Decision**: Yes, critical for rare finds
- **Reasoning**: High quality songs not on Deezer/Spotify, most important integration for rare tracks

---

## 🔧 Workflow & Agent Design Decisions

### Processing Strategy
- **Decision**: All platforms simultaneously (parallel)
- **Reasoning**: Faster if we can get results from multiple sources at the same time

### Conflict Resolution
- **Decision**: Trust most reliable source + manual review for conflicts
- **Note**: Need to research open source libraries for BPM/key extraction and comparison

### Track "Solved" Criteria
**To Discuss**: 
- What does "solved" mean in this context?
- How to handle tracks that never meet all criteria?
- Should focus on finding highest quality version
- Some tracks (bootlegs/edits) may be lower quality by nature

### DJ-Focused Mode
- **Decision**: Yes, prioritize DJ-relevant metadata
- **Reasoning**: 
  - Prioritize what's in Rekordbox
  - Focus on Beatport-style metadata
  - Baseline should be DJ-relevant fields (BPM, key, genre, year, label)

---

## 💾 Data Flow & Storage Decisions

### Primary Source of Truth
- **Decision**: PostgreSQL is master
- **Strategy**: 
  - Sync to PostgreSQL as primary
  - Sync to Graphiti for context/relationships
  - Support multiple DBs (e.g., separate DB for friends)

### Update Policy
- **Decision**: Only manual saves update database
- **Reasoning**: 
  - User control over database updates
  - Graphiti updates automatically for context
  - Can automate later as system improves

### Duplicate Handling
- **Decision**: Keep highest quality version
- **Reasoning**: Main function is finding highest quality version to replace low quality tracks in Rekordbox

### Memory System Architecture
- **Decision**: Multi-tier approach
  - PostgreSQL for data storage (source of truth)
  - Graphiti for context/relationships/intelligence
  - Redis for caching
- **Note**: Graphiti helps agent perform better, not a source of truth

---

## 🎯 Next Steps

1. **Replace rough Rekordbox implementation with pyrekordbox package**
   - Leverage all available features
   - Focus on library sync but explore other capabilities

2. **Confirm API integrations priority**
   - Research Spotify download capabilities
   - Implement MusicBrainz API
   - Add YouTube integration
   - Verify Soulseek implementation

3. **Define "solved" criteria clearly**
   - What constitutes a solved track?
   - How to handle partial matches?
   - Quality thresholds for different use cases

4. **Research conflict resolution libraries**
   - BPM/key extraction tools
   - Comparison algorithms
   - Reliability scoring systems
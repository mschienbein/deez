# Multi-Agent Music Research System Specification

## Project Context & Requirements for Multi-Agent Research System

### 1. Primary Research Use Case

**Music Metadata Deep Research & Track Resolution System**

We need a multi-agent research system for comprehensive music metadata collection and track "solving" - determining the best source for acquisition (download/purchase) and enriching metadata to professional DJ standards. The system should:

- **Multi-platform music discovery**: Research tracks across 13+ music platforms (Spotify, Beatport, Discogs, MusicBrainz, Deezer, SoundCloud, YouTube, Genius, Last.fm, Bandcamp, Soulseek, 1001Tracklists, etc.)
- **Metadata completeness verification**: Ensure tracks have all required fields (BPM, key, genre, ISRC, artwork, credits)
- **Quality assessment**: Find highest available quality (FLAC > 320kbps MP3 > lower)
- **Track resolution**: Mark tracks as "SOLVED" when they meet quality requirements with clear acquisition path
- **Rekordbox integration**: Import existing DJ library as baseline, export enriched metadata back

The research should answer: "Given a track (artist + title or partial info), find all available metadata, determine best quality source, and provide complete information for DJ use."

### 2. Specific Capabilities and Behaviors

The multi-agent system should exhibit these behaviors, inspired by the Anthropic research system:

**Task Decomposition & Planning**
- Break down track research into parallel subtasks (search different platforms, collect artwork, verify metadata)
- Create dependency graphs (e.g., need basic metadata before searching for remixes)
- Prioritize high-confidence sources (Beatport/Discogs for electronic music)

**Parallel Information Gathering**
- Simultaneous searches across all platforms using our existing tool registry system
- Aggregate results into `UniversalTrackMetadata` objects
- Handle rate limits and API failures gracefully

**Intelligent Synthesis & Conflict Resolution**
- Merge conflicting metadata using our `MetadataMerger` with confidence scoring
- Prefer authoritative sources for specific fields (Beatport for BPM/key, Discogs for labels)
- Use majority voting for subjective fields (genre)

**Critical Evaluation**
- Cross-validate ISRC codes across platforms
- Verify track duration consistency (±2 seconds tolerance)
- Detect and handle duplicate releases/remasters

**Iterative Refinement**
- If initial search fails, try alternative queries (remove remix tags, search by ISRC)
- Progressively expand search (exact match → fuzzy match → partial match)
- Learn from successful matches to improve future searches

### 3. Integration with Existing Tools and Data Sources

The system must integrate with our existing architecture:

**Local Tool Registry System** (already implemented)
```python
# Our modular tool system at src/music_agent/tools/
- Core tools (search, download, playlist management)
- Integration-specific tools (per platform)
- Operations templates (base patterns)
- Registry for dynamic tool discovery
```

**Existing Integrations** (in src/music_agent/integrations/)
- Deezer (with Deemix for downloads)
- Spotify (metadata and features)
- Discogs (detailed credits and pressing info)
- Soulseek (P2P network for rare tracks)
- Beatport (electronic music focus)
- YouTube (live performances, remixes)
- **Rekordbox** (via pyrekordbox - full database access)

**Data Models** (already created)
- `UniversalTrackMetadata` - comprehensive schema with 100+ fields
- `TrackQuality` and `TrackStatus` enums
- Platform-specific metadata containers
- Artwork information models

**AWS Strands Framework**
- Use Strands `Agent` class for orchestration
- Leverage existing `MusicAgent` patterns
- Tool registration via our registry system
- Configuration via our `AgentConfig` system

**Local Database**
- SQLite for development (PostgreSQL ready)
- Track research history and caching
- Rekordbox sync status tracking

**No Cloud Services Initially** - This is for local deployment, but should be architected to allow future AWS migration (S3 for artwork, DynamoDB for metadata, SQS for batch processing).

### 4. Deployment Strategy

**Local Development First, Cloud-Ready Architecture**

This is intended for **local prototyping and development** with a clear path to production:

**Current Phase (Local)**:
- Run on local machine with direct file system access
- Use local SQLite database
- Direct API calls to music services
- Synchronous processing for immediate feedback
- Integration with local Rekordbox installation

**Future Phase (Production-Ready)**:
- Dockerized for consistent deployment
- Ready for AWS migration (Lambda functions, Step Functions for workflows)
- Async processing with job queues
- Distributed agents for parallel processing
- API gateway for external access

The architecture should follow our existing patterns:
- Modular components in `src/music_agent/research/`
- Tool-based operations via registry
- Configuration-driven behavior
- Clear separation of concerns

### 5. Specific Implementation Requirements

**Must align with our existing codebase structure**:

```python
src/music_agent/
├── research/           # New multi-agent research system
│   ├── agents/        # Individual agent implementations
│   │   ├── chief_researcher.py      # Orchestrator (like Anthropic's)
│   │   ├── data_collector.py        # Platform search specialist
│   │   ├── metadata_analyst.py      # Merger and validator
│   │   ├── quality_assessor.py      # Quality and completeness
│   │   └── acquisition_scout.py     # Find download/purchase options
│   ├── workflows/     # LangGraph-inspired workflows
│   │   ├── track_research_flow.py
│   │   ├── batch_enrichment_flow.py
│   │   └── library_import_flow.py
│   ├── core/          # Already started
│   │   ├── metadata_merger.py       # ✓ Already implemented
│   │   ├── research_agent.py        # Main agent class
│   │   └── quality_analyzer.py
│   └── models/        # ✓ Already implemented
│       └── track_metadata.py
```

**Agent Communication Pattern**:
- Agents communicate via shared `ResearchContext` objects
- Each agent updates the context with findings
- Chief researcher monitors progress and makes decisions
- Use our existing tool result patterns

**Research Workflow Example**:
```python
# User query: "Research and solve 'Deadmau5 - Strobe'"

1. ChiefResearcher receives query, creates ResearchContext
2. DataCollector searches all platforms in parallel:
   - Spotify: finds track, gets ISRC, audio features
   - Beatport: finds track, gets BPM (128), key (C# min)
   - Discogs: finds multiple releases, gets label info
   - YouTube: finds official upload, live versions
   
3. MetadataAnalyst merges results:
   - Resolves BPM conflict (Spotify: 127 vs Beatport: 128)
   - Standardizes key notation
   - Deduplicates artist names
   
4. QualityAssessor evaluates:
   - Best quality: Beatport (WAV available)
   - Alternative: Deezer (FLAC via Deemix)
   - Artwork: 1400x1400 from Spotify
   
5. AcquisitionScout finds options:
   - Purchase: Beatport ($2.49)
   - Stream: Available on all platforms
   - Download: Deezer (requires premium)
   
6. ChiefResearcher synthesizes:
   - Status: SOLVED
   - Confidence: 0.95
   - Best source: Beatport WAV
   - Returns complete UniversalTrackMetadata
```

**Key Design Decisions**:
1. **Synchronous with async capability** - Start with sync for simplicity, but design for async
2. **Tool-based operations** - All platform interactions via our tool registry
3. **Incremental enhancement** - Can work with partial data, progressively improves
4. **Caching-first** - Cache all API responses to minimize repeated calls
5. **Fail gracefully** - Continue research even if some platforms fail

**Success Criteria**:
- Research 100 tracks in < 5 minutes
- 90%+ tracks marked as "SOLVED"
- Metadata completeness score > 0.8
- Successful Rekordbox round-trip (import → enrich → export)

## Technical Architecture Details

### Agent Hierarchy and Responsibilities

**ChiefResearcher (Orchestrator)**
- Receives research requests
- Creates and manages ResearchContext
- Delegates to specialist agents
- Monitors progress and handles failures
- Synthesizes final results
- Makes decision on track "SOLVED" status

**DataCollector (Search Specialist)**
- Manages parallel platform searches
- Handles API rate limiting
- Implements retry logic
- Caches all responses
- Normalizes initial results

**MetadataAnalyst (Merger & Validator)**
- Implements conflict resolution strategies
- Calculates confidence scores
- Validates data consistency
- Standardizes formats (keys, genres)
- Identifies missing critical fields

**QualityAssessor (Quality Control)**
- Evaluates audio quality options
- Scores metadata completeness
- Verifies source reliability
- Checks for red flags (fake releases, bad data)
- Determines if track meets "SOLVED" criteria

**AcquisitionScout (Source Finder)**
- Finds purchase options across platforms
- Identifies download possibilities
- Calculates cost/quality tradeoffs
- Verifies availability by region
- Maintains source preference hierarchy

### Research Context Schema

```python
@dataclass
class ResearchContext:
    # Request
    request_id: str
    query: str
    requirements: Dict[str, Any]
    
    # Progress
    status: ResearchStatus
    started_at: datetime
    completed_at: Optional[datetime]
    
    # Results
    platform_results: Dict[str, PlatformResult]
    merged_metadata: UniversalTrackMetadata
    conflicts: List[ConflictReport]
    
    # Quality
    quality_assessment: QualityReport
    acquisition_options: List[AcquisitionOption]
    
    # Decision
    is_solved: bool
    confidence_score: float
    solve_reason: str
    recommendations: List[str]
```

### Platform Priority Matrix

| Platform | Search Priority | Metadata Fields | Reliability | Use Case |
|----------|----------------|-----------------|-------------|----------|
| Beatport | 1 (Electronic) | BPM, Key, Genre, Label | 95% | Electronic/Dance music |
| Spotify | 1 (General) | ISRC, Audio Features | 90% | General metadata, popularity |
| Discogs | 2 | Credits, Label, Catalog | 90% | Detailed credits, vinyl |
| MusicBrainz | 2 | ISRC, Relationships | 85% | Open data, connections |
| Deezer | 3 | Basic metadata, ISRC | 85% | Download source (Deemix) |
| Genius | 3 | Lyrics, Credits | 80% | Lyrics, songwriter credits |
| SoundCloud | 4 | User content, Remixes | 70% | Unofficial remixes, bootlegs |
| YouTube | 4 | Live versions, Videos | 60% | Visual content, live sets |
| Soulseek | 5 | Rare tracks | 60% | Hard-to-find music |

### Conflict Resolution Rules

**BPM Conflicts**
1. Check for half/double time (128 vs 64 BPM)
2. Prefer Beatport > Rekordbox > Spotify
3. If within 1 BPM, use average
4. Flag if difference > 2 BPM

**Key Conflicts**
1. Normalize notation (C# = Db)
2. Convert to Camelot/Open Key
3. Prefer analyzed sources (Beatport, Rekordbox)
4. Check for relative major/minor

**Artist Name Conflicts**
1. Check for featuring artists incorrectly included
2. Standardize "feat." vs "ft." vs "featuring"
3. Use most common spelling across platforms
4. Preserve original for search

**Genre Conflicts**
1. Use genre hierarchy (House > Deep House)
2. Collect all unique genres as sub-genres
3. Prefer platform-specific expertise
4. Allow multiple genre tags

### Caching Strategy

**Cache Levels**:
1. **API Response Cache** (24 hours)
   - Raw platform API responses
   - Keyed by platform + query
   
2. **Processed Metadata Cache** (7 days)
   - Parsed and normalized metadata
   - Keyed by platform + track ID
   
3. **Research Session Cache** (30 days)
   - Complete research contexts
   - Keyed by artist + title hash
   
4. **Artwork Cache** (Permanent)
   - Downloaded artwork files
   - Keyed by artwork hash

### Error Handling and Recovery

**Platform Failures**:
- Continue with available platforms
- Mark platform as temporarily unavailable
- Retry with exponential backoff
- Use cached data if recent

**Partial Data**:
- Proceed with incomplete metadata
- Flag missing critical fields
- Attempt alternative searches
- Lower confidence score appropriately

**Conflict Resolution Failures**:
- Log all conflicts for review
- Use conservative merge strategy
- Flag for human review if critical
- Provide conflict report in results

## Implementation Roadmap

### Phase 1: Core Infrastructure (Current)
- ✅ UniversalTrackMetadata model
- ✅ Rekordbox integration
- ✅ MetadataMerger
- 🔄 Basic ResearchAgent
- 🔄 Quality assessment

### Phase 2: Multi-Agent System
- [ ] ChiefResearcher orchestrator
- [ ] DataCollector with parallel search
- [ ] Agent communication via ResearchContext
- [ ] Basic workflow implementation

### Phase 3: Intelligence Layer
- [ ] Conflict resolution strategies
- [ ] Confidence scoring algorithm
- [ ] Adaptive search strategies
- [ ] Learning from successful matches

### Phase 4: Production Features
- [ ] Batch processing for libraries
- [ ] Progress tracking and resumption
- [ ] API rate limit management
- [ ] Comprehensive caching layer

### Phase 5: Advanced Features
- [ ] Audio fingerprinting integration
- [ ] Machine learning for match validation
- [ ] Automated Rekordbox sync
- [ ] Web UI for research monitoring

This system should feel like having a team of music researchers working together - each specialist contributes their expertise, conflicts are resolved intelligently, and the result is comprehensive, accurate metadata that makes a DJ's library professional-grade.
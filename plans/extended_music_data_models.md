# Extended Music Data Models for Graphiti Integration

## Overview
This document extends the original architecture plan with comprehensive data models for 1001 Tracklists, Beatport, and Discogs integration. These models will enrich the knowledge graph with DJ performance data, electronic music metadata, and vinyl/release information.

## 1. 1001 Tracklists Data Models

### Core Entities

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class DJSet(BaseModel):
    """DJ set or performance"""
    dj_name: str = Field(description="DJ or artist name")
    event_name: Optional[str] = Field(None, description="Event or festival name")
    venue: Optional[str] = Field(None, description="Venue name")
    date: datetime = Field(description="Performance date")
    set_type: Optional[str] = Field(None, description="live, radio, podcast, stream")
    duration_minutes: Optional[int] = Field(None)
    recording_url: Optional[str] = Field(None, description="SoundCloud, Mixcloud, YouTube URL")
    tracklist_1001_id: Optional[str] = Field(None, description="1001Tracklists unique ID")
    play_count: Optional[int] = Field(None, description="Number of plays")
    favorite_count: Optional[int] = Field(None)

class TracklistEntry(BaseModel):
    """Individual track in a DJ set"""
    position: int = Field(description="Track position in set")
    track_title: str = Field(description="Track name")
    artist: str = Field(description="Track artist")
    remix: Optional[str] = Field(None, description="Remix or edit name")
    label: Optional[str] = Field(None, description="Record label")
    cue_time: Optional[str] = Field(None, description="Time in set (MM:SS)")
    track_1001_id: Optional[str] = Field(None, description="1001Tracklists track ID")
    transition_rating: Optional[float] = Field(None, description="Transition quality 0-5")
    key_change: Optional[str] = Field(None, description="Key transition info")

class RadioShow(BaseModel):
    """Radio show or podcast series"""
    show_name: str = Field(description="Show name")
    host_dj: str = Field(description="Host DJ name")
    station: Optional[str] = Field(None, description="Radio station or platform")
    episode_number: Optional[int] = Field(None)
    air_date: datetime
    genre_focus: Optional[str] = Field(None)
    recurring: bool = Field(default=False)
    show_1001_id: Optional[str] = Field(None)

class Festival(BaseModel):
    """Music festival or event"""
    name: str = Field(description="Festival name")
    location: str = Field(description="City, Country")
    start_date: datetime
    end_date: datetime
    stages: List[str] = Field(default_factory=list, description="Stage names")
    capacity: Optional[int] = Field(None)
    genre_focus: List[str] = Field(default_factory=list)
    festival_1001_id: Optional[str] = Field(None)

class TrackPopularity(BaseModel):
    """Track popularity metrics from 1001TL"""
    track_id: str = Field(description="Internal track ID")
    most_heard_rank: Optional[int] = Field(None, description="Position in most heard charts")
    spotify_saves: Optional[int] = Field(None, description="Spotify save count")
    weeks_on_chart: Optional[int] = Field(None)
    peak_position: Optional[int] = Field(None)
    dj_support_count: Optional[int] = Field(None, description="Number of DJs playing")
    first_played_date: Optional[datetime] = Field(None)
    trending_score: Optional[float] = Field(None)
```

### Relationships

```python
class PlayedIn(BaseModel):
    """Track played in DJ set"""
    position: int = Field(description="Position in tracklist")
    cue_time: Optional[str] = Field(None)
    transition_type: Optional[str] = Field(None, description="mix, cut, fade")

class PerformedAt(BaseModel):
    """DJ performed at event"""
    stage: Optional[str] = Field(None)
    time_slot: Optional[str] = Field(None)
    headline_status: Optional[str] = Field(None, description="headliner, support, opener")

class SupportedBy(BaseModel):
    """Track supported by DJ"""
    first_played: datetime
    play_count: int = Field(default=1)
    exclusive: bool = Field(default=False, description="Exclusive/dubplate")
```

## 2. Beatport Data Models

### Core Entities

```python
class BeatportTrack(BaseModel):
    """Beatport track with electronic music specific metadata"""
    beatport_id: str = Field(description="Beatport track ID")
    title: str
    mix_name: Optional[str] = Field(None, description="Remix or mix name")
    artist: str
    remixer: Optional[str] = Field(None)
    label: str
    catalog_number: Optional[str] = Field(None)
    release_date: datetime
    genre: str = Field(description="Primary genre")
    subgenre: Optional[str] = Field(None)
    bpm: int = Field(description="Beats per minute")
    key: str = Field(description="Musical key (Camelot or standard)")
    length_ms: int = Field(description="Track length in milliseconds")
    isrc: Optional[str] = Field(None)
    price: Optional[float] = Field(None)
    exclusive_period: Optional[int] = Field(None, description="Days of Beatport exclusivity")
    waveform_url: Optional[str] = Field(None)
    preview_url: Optional[str] = Field(None)

class BeatportRelease(BaseModel):
    """Beatport release/album"""
    beatport_id: str
    title: str
    artist: str
    label: str
    catalog_number: Optional[str] = Field(None)
    upc: Optional[str] = Field(None)
    release_date: datetime
    track_count: int
    release_type: str = Field(description="single, ep, album, compilation")
    exclusive: bool = Field(default=False)
    price: Optional[float] = Field(None)

class BeatportArtist(BaseModel):
    """Beatport artist profile"""
    beatport_id: str
    name: str
    slug: str = Field(description="URL slug")
    genres: List[str] = Field(default_factory=list)
    biography: Optional[str] = Field(None)
    soundcloud_url: Optional[str] = Field(None)
    facebook_url: Optional[str] = Field(None)
    twitter_url: Optional[str] = Field(None)
    top_tracks: List[str] = Field(default_factory=list, description="Top track IDs")

class BeatportLabel(BaseModel):
    """Record label on Beatport"""
    beatport_id: str
    name: str
    slug: str
    genres: List[str] = Field(default_factory=list)
    biography: Optional[str] = Field(None)
    website_url: Optional[str] = Field(None)
    established_year: Optional[int] = Field(None)

class BeatportChart(BaseModel):
    """Beatport chart or top list"""
    chart_id: str
    name: str
    chart_type: str = Field(description="genre, dj, label, global")
    genre: Optional[str] = Field(None)
    date: datetime
    track_ids: List[str] = Field(description="Ordered list of track IDs")

class DJChart(BaseModel):
    """DJ's personal chart on Beatport"""
    dj_name: str
    beatport_dj_id: str
    chart_date: datetime
    chart_name: Optional[str] = Field(None)
    track_ids: List[str] = Field(description="Ordered list of track IDs")
    description: Optional[str] = Field(None)

class BeatportGenre(BaseModel):
    """Electronic music genre classification"""
    name: str
    slug: str
    parent_genre: Optional[str] = Field(None)
    subgenres: List[str] = Field(default_factory=list)
    description: Optional[str] = Field(None)
    bpm_range: Optional[str] = Field(None, description="Typical BPM range")
    key_characteristics: List[str] = Field(default_factory=list)
```

## 3. Discogs Data Models

### Core Entities

```python
class DiscogsRelease(BaseModel):
    """Physical or digital release in Discogs"""
    discogs_id: int
    title: str
    artists: List[str] = Field(description="Artist names")
    labels: List[str] = Field(description="Label names")
    formats: List[str] = Field(description="Vinyl, CD, Digital, etc")
    country: Optional[str] = Field(None)
    released: Optional[str] = Field(None, description="Release date string")
    genres: List[str] = Field(default_factory=list)
    styles: List[str] = Field(default_factory=list)
    master_id: Optional[int] = Field(None, description="Master release ID")
    catno: Optional[str] = Field(None, description="Catalog number")
    barcode: Optional[str] = Field(None)
    data_quality: Optional[str] = Field(None, description="Needs Vote, Correct, etc")
    marketplace_stats: Optional[dict] = Field(None, description="For sale, lowest price")

class DiscogsMaster(BaseModel):
    """Master release grouping multiple versions"""
    master_id: int
    title: str
    artists: List[str]
    year: Optional[int] = Field(None, description="Original release year")
    genres: List[str] = Field(default_factory=list)
    styles: List[str] = Field(default_factory=list)
    main_release: int = Field(description="Primary release ID")
    versions_count: int = Field(description="Number of versions")

class DiscogsArtist(BaseModel):
    """Artist or group in Discogs"""
    discogs_id: int
    name: str
    real_name: Optional[str] = Field(None)
    profile: Optional[str] = Field(None, description="Biography")
    aliases: List[str] = Field(default_factory=list)
    members: List[str] = Field(default_factory=list, description="For groups")
    groups: List[str] = Field(default_factory=list, description="For individuals")
    urls: List[str] = Field(default_factory=list, description="Website URLs")
    images: List[str] = Field(default_factory=list)
    data_quality: Optional[str] = Field(None)

class DiscogsLabel(BaseModel):
    """Record label in Discogs"""
    discogs_id: int
    name: str
    profile: Optional[str] = Field(None)
    parent_label: Optional[str] = Field(None)
    sublabels: List[str] = Field(default_factory=list)
    contact_info: Optional[str] = Field(None)
    urls: List[str] = Field(default_factory=list)
    data_quality: Optional[str] = Field(None)

class VinylRecord(BaseModel):
    """Physical vinyl record details"""
    release_id: int
    format: str = Field(description="12\", 10\", 7\", LP, EP")
    rpm: Optional[int] = Field(None, description="33, 45, 78")
    pressing_plant: Optional[str] = Field(None)
    matrix_runout: Optional[str] = Field(None)
    color: Optional[str] = Field(None, description="Black, colored, picture disc")
    weight: Optional[int] = Field(None, description="Gram weight")
    limited_edition: bool = Field(default=False)
    edition_size: Optional[int] = Field(None)
    pressing_quality: Optional[str] = Field(None)

class MarketplaceListing(BaseModel):
    """Discogs marketplace listing"""
    listing_id: int
    release_id: int
    condition: str = Field(description="Mint, Near Mint, VG+, etc")
    sleeve_condition: Optional[str] = Field(None)
    price: float
    currency: str
    seller: str
    seller_rating: Optional[float] = Field(None)
    ships_from: str
    comments: Optional[str] = Field(None)
    posted_date: datetime

class Collection(BaseModel):
    """User's record collection"""
    user: str
    release_id: int
    folder: str = Field(default="Uncategorized")
    rating: Optional[int] = Field(None, description="1-5 stars")
    notes: Optional[str] = Field(None)
    date_added: datetime
    media_condition: Optional[str] = Field(None)
    sleeve_condition: Optional[str] = Field(None)
```

### Relationships

```python
class VersionOf(BaseModel):
    """Release is version of master"""
    format: str
    country: Optional[str] = Field(None)
    year: Optional[int] = Field(None)

class ReleasedOn(BaseModel):
    """Track released on label"""
    catalog_number: Optional[str] = Field(None)
    format: str

class PressedBy(BaseModel):
    """Vinyl pressed by plant"""
    plant_name: str
    pressing_date: Optional[datetime] = Field(None)
    run_size: Optional[int] = Field(None)
```

## 4. Unified Cross-Platform Entities

### Track Matching and Deduplication

```python
class UnifiedTrack(BaseModel):
    """Unified track across all platforms"""
    internal_id: str = Field(description="Internal UUID")
    title: str
    artist: str
    remixer: Optional[str] = Field(None)
    
    # Platform IDs
    spotify_id: Optional[str] = Field(None)
    deezer_id: Optional[str] = Field(None)
    beatport_id: Optional[str] = Field(None)
    discogs_release_id: Optional[int] = Field(None)
    track_1001_id: Optional[str] = Field(None)
    youtube_id: Optional[str] = Field(None)
    
    # Universal identifiers
    isrc: Optional[str] = Field(None, description="International Standard Recording Code")
    iswc: Optional[str] = Field(None, description="International Standard Musical Work Code")
    
    # Audio characteristics
    bpm: Optional[float] = Field(None)
    key: Optional[str] = Field(None)
    energy: Optional[float] = Field(None)
    duration_ms: Optional[int] = Field(None)
    
    # Metadata
    genre: Optional[str] = Field(None)
    subgenre: Optional[str] = Field(None)
    release_date: Optional[datetime] = Field(None)
    label: Optional[str] = Field(None)
    catalog_number: Optional[str] = Field(None)
    
    # Quality and availability
    available_formats: List[str] = Field(default_factory=list, description="FLAC, WAV, MP3 320, etc")
    best_quality_source: Optional[str] = Field(None, description="Platform with best quality")
    owned_in_rekordbox: bool = Field(default=False)
    owned_format: Optional[str] = Field(None)
    
    # Popularity metrics
    beatport_rank: Optional[int] = Field(None)
    spotify_popularity: Optional[int] = Field(None)
    dj_support_count: Optional[int] = Field(None, description="From 1001TL")
    
    # Audio fingerprint for matching
    audio_fingerprint: Optional[str] = Field(None, description="AcoustID or similar")

class TrackMatch(BaseModel):
    """Matching confidence between platform tracks"""
    track_a_platform: str
    track_a_id: str
    track_b_platform: str
    track_b_id: str
    match_confidence: float = Field(description="0-1 confidence score")
    match_method: str = Field(description="isrc, fingerprint, fuzzy, manual")
    matched_fields: List[str] = Field(default_factory=list)
    verified: bool = Field(default=False)
```

## 5. Integration Services

### Platform API Clients

```python
class MusicPlatformClients:
    def __init__(self):
        # Official APIs
        self.discogs = DiscogsClient(
            user_token=os.getenv('DISCOGS_TOKEN'),
            user_agent='DeezMusicAgent/1.0'
        )
        
        # Beatport (requires OAuth)
        self.beatport = BeatportClient(
            client_id=os.getenv('BEATPORT_CLIENT_ID'),
            client_secret=os.getenv('BEATPORT_CLIENT_SECRET')
        )
        
        # 1001 Tracklists (web scraping)
        self.tracklists_1001 = TracklistsScraper()
        
    async def search_all_platforms(self, query: str):
        """Parallel search across all platforms"""
        results = await asyncio.gather(
            self.search_beatport(query),
            self.search_discogs(query),
            self.search_1001(query),
            return_exceptions=True
        )
        return self.unify_results(results)
```

### Data Enrichment Pipeline

```python
class MusicDataEnricher:
    async def enrich_track(self, track: UnifiedTrack):
        """Enrich track with data from all sources"""
        
        # Get Beatport data for electronic music metadata
        if not track.beatport_id and track.genre in ELECTRONIC_GENRES:
            beatport_match = await self.beatport.search_track(
                title=track.title,
                artist=track.artist
            )
            if beatport_match:
                track.beatport_id = beatport_match['id']
                track.bpm = beatport_match['bpm']
                track.key = beatport_match['key']
                track.subgenre = beatport_match['subgenre']
        
        # Get Discogs data for physical release info
        if not track.discogs_release_id:
            discogs_match = await self.discogs.search(
                track=track.title,
                artist=track.artist,
                type='release'
            )
            if discogs_match:
                track.discogs_release_id = discogs_match['id']
                track.catalog_number = discogs_match['catno']
                
        # Get DJ support from 1001 Tracklists
        if not track.dj_support_count:
            dj_support = await self.tracklists_1001.get_track_support(
                title=track.title,
                artist=track.artist
            )
            track.dj_support_count = len(dj_support)
            
        return track
```

## 6. Graph Relationships for Extended Model

### Neo4j Schema Extensions

```cypher
// DJ Performance Relationships
(:DJSet)-[:CONTAINS_TRACK {position: INTEGER, cue_time: STRING}]->(:Track)
(:DJSet)-[:PERFORMED_BY]->(:DJ)
(:DJSet)-[:AT_EVENT]->(:Festival)
(:DJ)-[:SUPPORTS {play_count: INTEGER}]->(:Track)
(:Track)-[:PEAKED_AT {position: INTEGER, week: DATE}]->(:Chart)

// Beatport Specific
(:Track)-[:EXCLUSIVE_ON {days: INTEGER}]->(:Platform)
(:Track)-[:IN_GENRE]->(:Genre)
(:Genre)-[:SUBGENRE_OF]->(:Genre)
(:Track)-[:CHARTED_BY {position: INTEGER}]->(:DJ)

// Discogs/Vinyl Specific
(:Release)-[:VERSION_OF]->(:MasterRelease)
(:Release)-[:PRESSED_AT]->(:PressingPlant)
(:Release)-[:HAS_FORMAT {type: STRING, rpm: INTEGER}]->(:Format)
(:Track)-[:APPEARS_ON {side: STRING, position: STRING}]->(:Release)
(:User)-[:OWNS {condition: STRING, rating: INTEGER}]->(:Release)

// Cross-Platform Matching
(:Track)-[:SAME_AS {confidence: FLOAT, method: STRING}]->(:Track)
(:Artist)-[:ALIAS_OF]->(:Artist)
(:Label)-[:SUBLABEL_OF]->(:Label)
```

## 7. Usage Examples

### Finding DJ Support for a Track

```python
async def analyze_dj_support(track_name: str, artist: str):
    """Find which DJs are playing a track"""
    
    # Search 1001 Tracklists
    tracklists = await tracklists_client.search_track(track_name, artist)
    
    # Store in graph
    episode_body = f"""
    Analyzing DJ support for: {track_name} by {artist}
    Found in {len(tracklists)} DJ sets:
    """
    
    for tl in tracklists:
        episode_body += f"\n- {tl['dj_name']} at {tl['event']} ({tl['date']})"
        
    await graphiti.add_episode(
        name=f"dj_support_{track_name[:20]}",
        episode_body=episode_body,
        entity_types={**MUSIC_ENTITY_TYPES, 'DJSet': DJSet},
        source="1001tracklists_analysis"
    )
```

### Checking Vinyl Availability

```python
async def check_vinyl_availability(track: UnifiedTrack):
    """Check if track is available on vinyl"""
    
    # Search Discogs
    releases = await discogs.search_releases(
        track=track.title,
        artist=track.artist,
        format='Vinyl'
    )
    
    if releases:
        # Check marketplace
        for release in releases:
            listings = await discogs.get_marketplace_listings(release['id'])
            
            episode_body = f"""
            Vinyl found for: {track.title}
            Release: {release['title']} ({release['catno']})
            Format: {release['format']}
            Available: {len(listings)} copies
            Lowest price: ${min(l['price'] for l in listings)}
            """
            
            await graphiti.add_episode(
                name=f"vinyl_check_{track.title[:20]}",
                episode_body=episode_body,
                entity_types={**MUSIC_ENTITY_TYPES, 'VinylRecord': VinylRecord}
            )
```

### Genre Evolution Tracking

```python
async def track_genre_evolution(genre: str, timeframe: str):
    """Analyze how a genre evolves over time"""
    
    # Get Beatport genre data
    genre_tracks = await beatport.get_genre_charts(genre, timeframe)
    
    # Analyze characteristics
    avg_bpm = statistics.mean([t['bpm'] for t in genre_tracks])
    common_keys = Counter([t['key'] for t in genre_tracks]).most_common(3)
    
    episode_body = f"""
    Genre Evolution Analysis: {genre}
    Timeframe: {timeframe}
    Average BPM: {avg_bpm}
    Common Keys: {common_keys}
    Top Labels: {Counter([t['label'] for t in genre_tracks]).most_common(5)}
    """
    
    await graphiti.add_episode(
        name=f"genre_evolution_{genre}",
        episode_body=episode_body,
        entity_types={'BeatportGenre': BeatportGenre}
    )
```

## 8. Configuration Updates

```bash
# Additional API Keys
DISCOGS_TOKEN=your_discogs_token
BEATPORT_CLIENT_ID=your_beatport_id
BEATPORT_CLIENT_SECRET=your_beatport_secret

# Scraping Configuration
TRACKLISTS_1001_RATE_LIMIT=1  # Requests per second
USE_PROXY=false
PROXY_URL=http://proxy.example.com:8080

# Matching Thresholds
TRACK_MATCH_THRESHOLD=0.85
ARTIST_MATCH_THRESHOLD=0.90
USE_AUDIO_FINGERPRINTING=true
ACOUSTID_API_KEY=your_acoustid_key
```

## Conclusion

These extended data models provide comprehensive coverage of the electronic music ecosystem, enabling:

1. **DJ Performance Tracking**: Monitor which DJs play which tracks, analyze set construction
2. **Multi-Format Discovery**: Find tracks across digital and vinyl formats
3. **Genre Analysis**: Track genre evolution and characteristics
4. **Market Intelligence**: Understand track popularity and availability
5. **Collection Management**: Integrate with physical and digital collections
6. **Historical Context**: Access release history and version information

The integration of these models with Graphiti's temporal graph system will create a powerful knowledge base that understands not just music metadata, but the entire ecosystem of DJs, labels, events, and the relationships between them.
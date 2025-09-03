# Graphiti + Neo4j Music Agent Architecture Plan

## Executive Summary

This document outlines the integration of Graphiti's temporal knowledge graph system with the existing Deez music agent to create an intelligent, memory-enabled music discovery and curation platform. The system will leverage Neo4j for graph storage, custom music ontologies for domain-specific knowledge extraction, and Graphiti's temporal memory capabilities for maintaining conversation context and user preferences over time.

## Current State Analysis

### Existing Deez Architecture
- **Agent Framework**: AWS Strands Agents with OpenAI/Bedrock models
- **Music APIs**: Deezer integration with planned Spotify, YouTube, Soulseek support
- **Storage**: SQLite database for tracks, playlists, user preferences
- **CLI Interface**: Natural language commands for music search and download
- **Tools**: Custom music tools for search, download, playlist management

### Key Capabilities to Enhance
1. **Memory Management**: No persistent conversation memory or context retention
2. **Relationship Tracking**: Limited understanding of relationships between artists, genres, labels
3. **Temporal Awareness**: No tracking of how preferences evolve over time
4. **Semantic Search**: Basic text matching without semantic understanding
5. **Knowledge Graph**: No graph-based representation of music domain knowledge

## Proposed Architecture

### 1. Core Integration Layer

#### Graphiti Initialization
```python
from graphiti_core import Graphiti
from graphiti_core.llm_client import OpenAIClient
from graphiti_core.embedder import OpenAIEmbedder

class MusicMemoryAgent:
    def __init__(self):
        # Initialize Graphiti with Neo4j
        self.graphiti = Graphiti(
            uri=os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
            user=os.getenv('NEO4J_USER', 'neo4j'),
            password=os.getenv('NEO4J_PASSWORD'),
            llm_client=OpenAIClient(config=LLMConfig(
                api_key=os.getenv('OPENAI_API_KEY'),
                model='gpt-4o-mini',
                small_model='gpt-3.5-turbo'
            )),
            embedder=OpenAIEmbedder(),
            store_raw_episode_content=True  # Keep conversation history
        )
        
        # Build indices for performance
        await self.graphiti.build_indices_and_constraints()
```

### 2. Custom Music Ontologies

#### Entity Types
```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Core Music Entities
class Artist(BaseModel):
    """Musical artist or band"""
    name: str = Field(description="Artist or band name")
    genres: List[str] = Field(default_factory=list, description="Associated genres")
    founded_year: Optional[int] = Field(None, description="Year founded/born")
    origin_country: Optional[str] = Field(None, description="Country of origin")
    label: Optional[str] = Field(None, description="Record label")
    spotify_id: Optional[str] = Field(None)
    deezer_id: Optional[str] = Field(None)
    discogs_id: Optional[str] = Field(None)
    beatport_id: Optional[str] = Field(None)

class Track(BaseModel):
    """Individual music track"""
    title: str = Field(description="Track title")
    artist: str = Field(description="Primary artist")
    album: Optional[str] = Field(None, description="Album name")
    duration_ms: Optional[int] = Field(None, description="Duration in milliseconds")
    isrc: Optional[str] = Field(None, description="International Standard Recording Code")
    bpm: Optional[float] = Field(None, description="Beats per minute")
    key: Optional[str] = Field(None, description="Musical key")
    energy: Optional[float] = Field(None, description="Energy level 0-1")
    danceability: Optional[float] = Field(None, description="Danceability 0-1")
    release_date: Optional[datetime] = Field(None)
    spotify_id: Optional[str] = Field(None)
    deezer_id: Optional[str] = Field(None)
    youtube_id: Optional[str] = Field(None)

class Album(BaseModel):
    """Music album or EP"""
    title: str = Field(description="Album title")
    artist: str = Field(description="Primary artist")
    release_date: Optional[datetime] = Field(None)
    label: Optional[str] = Field(None, description="Record label")
    total_tracks: Optional[int] = Field(None)
    album_type: Optional[str] = Field(None, description="album, single, compilation, ep")
    upc: Optional[str] = Field(None, description="Universal Product Code")

class Genre(BaseModel):
    """Musical genre or style"""
    name: str = Field(description="Genre name")
    parent_genre: Optional[str] = Field(None, description="Parent genre if subgenre")
    era: Optional[str] = Field(None, description="Associated era or time period")
    characteristics: List[str] = Field(default_factory=list)

class Playlist(BaseModel):
    """Music playlist or collection"""
    name: str = Field(description="Playlist name")
    curator: Optional[str] = Field(None, description="Playlist creator")
    description: Optional[str] = Field(None)
    mood: Optional[str] = Field(None, description="Playlist mood or vibe")
    purpose: Optional[str] = Field(None, description="workout, party, study, etc")
    platform: Optional[str] = Field(None, description="Source platform")
    platform_id: Optional[str] = Field(None)

class MusicLabel(BaseModel):
    """Record label or music publisher"""
    name: str = Field(description="Label name")
    founded_year: Optional[int] = Field(None)
    parent_company: Optional[str] = Field(None)
    distribution: Optional[str] = Field(None, description="Distribution method")

class MusicVenue(BaseModel):
    """Concert venue or club"""
    name: str = Field(description="Venue name")
    city: str = Field(description="City location")
    capacity: Optional[int] = Field(None)
    venue_type: Optional[str] = Field(None, description="club, arena, festival, etc")

class ListeningSession(BaseModel):
    """User listening session or context"""
    context: str = Field(description="Context of listening: party, workout, relaxing, etc")
    mood: Optional[str] = Field(None)
    energy_level: Optional[str] = Field(None, description="low, medium, high")
    time_of_day: Optional[str] = Field(None, description="morning, afternoon, evening, night")

class MusicPreference(BaseModel):
    """User music preference or taste profile"""
    preference_type: str = Field(description="like, dislike, favorite, banned")
    target: str = Field(description="What the preference applies to")
    reason: Optional[str] = Field(None, description="Why this preference exists")
    strength: Optional[float] = Field(None, description="Strength of preference 0-1")
```

#### Relationship Types
```python
# Music Domain Relationships
class PerformedBy(BaseModel):
    """Track performed by artist"""
    role: Optional[str] = Field(None, description="vocalist, producer, featured, remix")

class BelongsToAlbum(BaseModel):
    """Track belongs to album"""
    track_number: Optional[int] = Field(None)
    disc_number: Optional[int] = Field(None, default=1)

class SignedTo(BaseModel):
    """Artist signed to label"""
    start_date: Optional[datetime] = Field(None)
    end_date: Optional[datetime] = Field(None)
    contract_type: Optional[str] = Field(None)

class Collaborated(BaseModel):
    """Artists collaborated"""
    project: Optional[str] = Field(None, description="Project or track name")
    year: Optional[int] = Field(None)

class InfluencedBy(BaseModel):
    """Artist influenced by another"""
    influence_type: Optional[str] = Field(None, description="style, technique, sound")

class RemixOf(BaseModel):
    """Track is remix of another"""
    remixer: str = Field(description="Remixing artist")
    style: Optional[str] = Field(None, description="Remix style")

class SimilarTo(BaseModel):
    """Tracks/artists are similar"""
    similarity_score: Optional[float] = Field(None, description="Similarity 0-1")
    similarity_type: Optional[str] = Field(None, description="style, tempo, mood, etc")

class ContainsTrack(BaseModel):
    """Playlist contains track"""
    position: Optional[int] = Field(None)
    added_date: Optional[datetime] = Field(None)

class PreferredBy(BaseModel):
    """User prefers entity"""
    preference_score: float = Field(description="Preference strength 0-1")
    context: Optional[str] = Field(None, description="When this preference applies")

class DiscoveredThrough(BaseModel):
    """Track/artist discovered through source"""
    source: str = Field(description="Discovery source: recommendation, playlist, radio, etc")
    timestamp: datetime = Field(default_factory=datetime.now)

# Register entity and relationship types
MUSIC_ENTITY_TYPES = {
    'Artist': Artist,
    'Track': Track,
    'Album': Album,
    'Genre': Genre,
    'Playlist': Playlist,
    'MusicLabel': MusicLabel,
    'MusicVenue': MusicVenue,
    'ListeningSession': ListeningSession,
    'MusicPreference': MusicPreference
}

MUSIC_EDGE_TYPES = {
    'PERFORMED_BY': PerformedBy,
    'BELONGS_TO_ALBUM': BelongsToAlbum,
    'SIGNED_TO': SignedTo,
    'COLLABORATED': Collaborated,
    'INFLUENCED_BY': InfluencedBy,
    'REMIX_OF': RemixOf,
    'SIMILAR_TO': SimilarTo,
    'CONTAINS_TRACK': ContainsTrack,
    'PREFERRED_BY': PreferredBy,
    'DISCOVERED_THROUGH': DiscoveredThrough
}
```

### 3. Neo4j Graph Schema

#### Node Labels and Properties
```cypher
// Core Music Nodes
(:Artist {
    uuid: STRING,
    name: STRING,
    genres: LIST<STRING>,
    founded_year: INTEGER,
    origin_country: STRING,
    spotify_id: STRING,
    deezer_id: STRING,
    embedding: LIST<FLOAT>,
    created_at: DATETIME,
    valid_at: DATETIME,
    invalid_at: DATETIME
})

(:Track {
    uuid: STRING,
    title: STRING,
    artist: STRING,
    album: STRING,
    isrc: STRING,
    bpm: FLOAT,
    key: STRING,
    duration_ms: INTEGER,
    energy: FLOAT,
    danceability: FLOAT,
    embedding: LIST<FLOAT>,
    audio_features: MAP
})

(:Album {
    uuid: STRING,
    title: STRING,
    artist: STRING,
    release_date: DATETIME,
    label: STRING,
    upc: STRING,
    total_tracks: INTEGER
})

(:Genre {
    uuid: STRING,
    name: STRING,
    parent_genre: STRING,
    characteristics: LIST<STRING>
})

(:User {
    uuid: STRING,
    user_id: STRING,
    created_at: DATETIME
})

(:ListeningSession {
    uuid: STRING,
    user_id: STRING,
    context: STRING,
    mood: STRING,
    started_at: DATETIME,
    ended_at: DATETIME
})

// Graphiti Episode Nodes
(:Episode {
    uuid: STRING,
    name: STRING,
    content: STRING,
    source: STRING,  // 'chat', 'import', 'analysis'
    created_at: DATETIME,
    group_id: STRING  // User partition
})
```

#### Relationship Types
```cypher
// Music Domain Relationships
(:Track)-[:PERFORMED_BY {role: STRING}]->(:Artist)
(:Track)-[:BELONGS_TO_ALBUM {track_number: INTEGER}]->(:Album)
(:Album)-[:RELEASED_BY]->(:MusicLabel)
(:Artist)-[:SIGNED_TO {start_date: DATETIME, end_date: DATETIME}]->(:MusicLabel)
(:Artist)-[:COLLABORATED {project: STRING, year: INTEGER}]->(:Artist)
(:Artist)-[:INFLUENCED_BY {influence_type: STRING}]->(:Artist)
(:Track)-[:REMIX_OF {remixer: STRING}]->(:Track)
(:Track)-[:SIMILAR_TO {score: FLOAT, type: STRING}]->(:Track)
(:Playlist)-[:CONTAINS {position: INTEGER, added_at: DATETIME}]->(:Track)
(:User)-[:PREFERS {score: FLOAT, context: STRING}]->(:Artist|Track|Genre)
(:User)-[:DISCOVERED {source: STRING, timestamp: DATETIME}]->(:Track|Artist)
(:ListeningSession)-[:INCLUDED]->(:Track)

// Temporal Relationships
(:Entity)-[:VALID_AT {timestamp: DATETIME}]->(:TimePoint)
(:Entity)-[:INVALIDATED_BY]->(:Episode)
```

#### Indices for Performance
```cypher
// Identity Indices
CREATE INDEX artist_name FOR (a:Artist) ON (a.name)
CREATE INDEX track_isrc FOR (t:Track) ON (t.isrc)
CREATE INDEX album_upc FOR (a:Album) ON (a.upc)

// Platform ID Indices
CREATE INDEX artist_spotify FOR (a:Artist) ON (a.spotify_id)
CREATE INDEX artist_deezer FOR (a:Artist) ON (a.deezer_id)
CREATE INDEX track_spotify FOR (t:Track) ON (t.spotify_id)
CREATE INDEX track_deezer FOR (t:Track) ON (t.deezer_id)

// Search Indices
CREATE FULLTEXT INDEX artist_search FOR (a:Artist) ON EACH [a.name]
CREATE FULLTEXT INDEX track_search FOR (t:Track) ON EACH [t.title, t.artist, t.album]
CREATE FULLTEXT INDEX genre_search FOR (g:Genre) ON EACH [g.name]

// Vector Indices (Neo4j 5.15+)
CREATE VECTOR INDEX artist_embedding FOR (a:Artist) ON (a.embedding) 
OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}

CREATE VECTOR INDEX track_embedding FOR (t:Track) ON (t.embedding)
OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}

// Temporal Indices
CREATE INDEX episode_time FOR (e:Episode) ON (e.created_at)
CREATE INDEX valid_time FOR (n:Entity) ON (n.valid_at)
```

### 4. Memory Integration Patterns

#### Conversation Memory
```python
class ConversationMemory:
    async def add_conversation_turn(self, user_message: str, agent_response: str, context: dict):
        """Add a conversation turn to memory"""
        episode_body = f"User: {user_message}\nAssistant: {agent_response}"
        
        # Extract mentioned entities and intents
        episode_uuid = await self.graphiti.add_episode(
            name=f"conversation_{datetime.now().isoformat()}",
            episode_body=episode_body,
            source="chat",
            entity_types=MUSIC_ENTITY_TYPES,
            edge_types=MUSIC_EDGE_TYPES,
            metadata={
                'user_id': context.get('user_id'),
                'session_id': context.get('session_id'),
                'intent': context.get('intent'),  # search, download, recommend, etc
                'success': context.get('success', True)
            }
        )
        return episode_uuid
```

#### Search History and Patterns
```python
class SearchMemory:
    async def record_search(self, query: str, results: List[dict], selected: Optional[dict]):
        """Record search interaction"""
        episode_body = f"User searched for: {query}\n"
        episode_body += f"Found {len(results)} results\n"
        if selected:
            episode_body += f"User selected: {selected['title']} by {selected['artist']}"
        
        await self.graphiti.add_episode(
            name=f"search_{query[:30]}",
            episode_body=episode_body,
            source="search",
            entity_types=MUSIC_ENTITY_TYPES,
            metadata={
                'query': query,
                'result_count': len(results),
                'selected_item': selected
            }
        )
```

#### Preference Learning
```python
class PreferenceLearning:
    async def learn_preference(self, action: str, entity: dict, context: dict):
        """Learn from user actions"""
        if action == "download":
            preference_strength = 0.8
        elif action == "add_to_playlist":
            preference_strength = 0.7
        elif action == "skip":
            preference_strength = -0.5
        elif action == "play_full":
            preference_strength = 0.6
        else:
            preference_strength = 0.5
        
        episode_body = f"User {action} track: {entity['title']} by {entity['artist']}"
        episode_body += f"\nPreference strength: {preference_strength}"
        episode_body += f"\nContext: {context.get('listening_context', 'general')}"
        
        await self.graphiti.add_episode(
            name=f"preference_{action}_{entity['title'][:20]}",
            episode_body=episode_body,
            source="preference",
            entity_types=MUSIC_ENTITY_TYPES
        )
```

### 5. Enhanced Agent Capabilities

#### Semantic Music Search
```python
class SemanticMusicSearch:
    async def search(self, query: str, search_type: str = "hybrid"):
        """Enhanced search using Graphiti's search capabilities"""
        
        # Graphiti's hybrid search
        results = await self.graphiti.search(
            query=query,
            search_type=search_type,  # keyword, similarity, hybrid
            search_config=SearchConfig(
                limit=20,
                search_method=SearchMethod.hybrid,
                reranker=RerankMethod.cross_encoder
            ),
            filters=SearchFilters(
                entity_types=['Track', 'Artist', 'Album']
            )
        )
        
        # Combine with temporal context
        recent_context = await self.graphiti.retrieve_episodes(
            reference_time=datetime.now(),
            last_n=5
        )
        
        # Re-rank based on user preferences
        ranked_results = await self.personalize_results(results, recent_context)
        return ranked_results
```

#### Recommendation Engine
```python
class MusicRecommendationEngine:
    async def get_recommendations(self, seed_tracks: List[str], context: dict):
        """Generate recommendations using graph relationships"""
        
        # Find similar tracks through graph traversal
        cypher_query = """
        MATCH (seed:Track)-[:SIMILAR_TO|PERFORMED_BY|BELONGS_TO_ALBUM*1..3]-(rec:Track)
        WHERE seed.uuid IN $seed_uuids
        AND NOT (user:User {user_id: $user_id})-[:DISCOVERED]->(rec)
        WITH rec, COUNT(DISTINCT seed) as connections, 
             AVG(similarity.score) as avg_similarity
        ORDER BY connections DESC, avg_similarity DESC
        LIMIT 20
        RETURN rec
        """
        
        recommendations = await self.graphiti.driver.execute_query(
            cypher_query,
            seed_uuids=seed_tracks,
            user_id=context['user_id']
        )
        
        # Apply collaborative filtering
        similar_users = await self.find_similar_users(context['user_id'])
        collab_recs = await self.get_collaborative_recommendations(similar_users)
        
        # Combine and rank
        final_recs = self.rank_recommendations(recommendations, collab_recs, context)
        return final_recs
```

#### Music Knowledge Q&A
```python
class MusicKnowledgeQA:
    async def answer_question(self, question: str):
        """Answer music-related questions using the knowledge graph"""
        
        # Search for relevant information
        context = await self.graphiti.search(
            query=question,
            search_type="hybrid",
            search_config=SearchConfig(
                limit=10,
                include_episode_content=True
            )
        )
        
        # Generate answer using LLM with graph context
        prompt = f"""
        Question: {question}
        
        Context from music knowledge graph:
        {self.format_context(context)}
        
        Provide a detailed answer based on the context.
        """
        
        answer = await self.graphiti.llm_client.generate_response(
            messages=[Message(role="user", content=prompt)]
        )
        
        return answer
```

### 6. API Integration Layer

#### Unified Music Service Interface
```python
class UnifiedMusicService:
    def __init__(self):
        self.deezer = DeezerService()
        self.spotify = SpotifyService()
        self.youtube = YouTubeService()
        self.soulseek = SoulseekService()
        self.beatport = BeatportService()
        self.discogs = DiscogsService()
        self.bandcamp = BandcampService()
        
    async def search_all_sources(self, query: str):
        """Search across all music sources"""
        results = await asyncio.gather(
            self.deezer.search(query),
            self.spotify.search(query),
            self.youtube.search(query),
            return_exceptions=True
        )
        
        # Deduplicate using ISRC/audio fingerprinting
        deduplicated = self.deduplicate_tracks(results)
        
        # Store in graph
        for track in deduplicated:
            await self.store_track_in_graph(track)
        
        return deduplicated
    
    async def store_track_in_graph(self, track_data: dict):
        """Store track and relationships in Neo4j via Graphiti"""
        episode_body = f"""
        Discovered track: {track_data['title']} 
        by {track_data['artist']}
        from album {track_data.get('album', 'Unknown')}
        Genre: {track_data.get('genre', 'Unknown')}
        Platform IDs: Spotify={track_data.get('spotify_id')}, 
                     Deezer={track_data.get('deezer_id')}
        ISRC: {track_data.get('isrc')}
        """
        
        await self.graphiti.add_episode(
            name=f"track_discovery_{track_data['title'][:30]}",
            episode_body=episode_body,
            source="api_import",
            entity_types=MUSIC_ENTITY_TYPES
        )
```

### 7. Rekordbox Integration

#### DJ Library Sync
```python
class RekordboxIntegration:
    def __init__(self, rekordbox_xml_path: str):
        self.xml_path = rekordbox_xml_path
        
    async def sync_library(self):
        """Sync Rekordbox library to knowledge graph"""
        library = self.parse_rekordbox_xml()
        
        for track in library['tracks']:
            # Check if track exists in graph
            existing = await self.find_track_by_metadata(track)
            
            if not existing:
                episode_body = f"""
                Imported from Rekordbox:
                Track: {track['Name']} by {track['Artist']}
                BPM: {track['BPM']}, Key: {track['Key']}
                Rating: {track['Rating']}, Play Count: {track['PlayCount']}
                File: {track['Location']}
                """
                
                await self.graphiti.add_episode(
                    name=f"rekordbox_import_{track['Name'][:30]}",
                    episode_body=episode_body,
                    source="rekordbox_import",
                    entity_types=MUSIC_ENTITY_TYPES,
                    metadata={
                        'file_path': track['Location'],
                        'bpm': track['BPM'],
                        'key': track['Key'],
                        'rating': track['Rating']
                    }
                )
```

### 8. Implementation Phases

#### Phase 1: Core Integration (Week 1-2)
- [ ] Set up Neo4j database with Docker
- [ ] Initialize Graphiti with custom LLM configuration
- [ ] Implement basic entity types for Artist, Track, Album
- [ ] Create episode ingestion for conversations
- [ ] Build basic search interface

#### Phase 2: Ontology Development (Week 2-3)
- [ ] Define complete music ontology with all entity types
- [ ] Implement relationship types and edge mappings
- [ ] Create validation schemas with Pydantic
- [ ] Build entity extraction prompts
- [ ] Test extraction accuracy

#### Phase 3: Memory Systems (Week 3-4)
- [ ] Implement conversation memory
- [ ] Build search history tracking
- [ ] Create preference learning system
- [ ] Develop listening pattern analysis
- [ ] Add temporal invalidation logic

#### Phase 4: Enhanced Search (Week 4-5)
- [ ] Implement semantic search with embeddings
- [ ] Build hybrid search combining keyword and similarity
- [ ] Add graph traversal for related entities
- [ ] Create personalized ranking algorithms
- [ ] Implement caching for performance

#### Phase 5: Multi-Source Integration (Week 5-6)
- [ ] Complete Deezer integration with graph storage
- [ ] Add Spotify API with track matching
- [ ] Implement YouTube search fallback
- [ ] Add Soulseek P2P search
- [ ] Create unified deduplication system

#### Phase 6: Advanced Features (Week 6-7)
- [ ] Build recommendation engine
- [ ] Implement collaborative filtering
- [ ] Create music Q&A system
- [ ] Add trend analysis
- [ ] Build export/import tools

#### Phase 7: DJ Integration (Week 7-8)
- [ ] Parse Rekordbox XML format
- [ ] Sync DJ library to graph
- [ ] Track quality comparisons
- [ ] Build smart crate suggestions
- [ ] Create set preparation tools

### 9. Performance Optimizations

#### Query Optimization
```python
# Batch operations for efficiency
async def batch_add_tracks(tracks: List[dict]):
    episodes = []
    for track in tracks:
        episodes.append({
            'name': f"track_{track['title'][:30]}",
            'body': format_track_episode(track),
            'metadata': extract_metadata(track)
        })
    
    # Batch process with semaphore control
    await graphiti.add_episodes_bulk(
        episodes,
        max_concurrent=10
    )
```

#### Caching Strategy
```python
class GraphCache:
    def __init__(self):
        self.redis = Redis()
        self.ttl = 3600  # 1 hour
        
    async def get_or_compute(self, key: str, compute_func):
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        result = await compute_func()
        await self.redis.setex(key, self.ttl, json.dumps(result))
        return result
```

### 10. Monitoring and Analytics

#### Usage Metrics
```python
class MemoryAnalytics:
    async def analyze_memory_usage(self, user_id: str):
        """Analyze memory patterns for a user"""
        
        stats = await self.graphiti.driver.execute_query("""
        MATCH (u:User {user_id: $user_id})-[r]->(n)
        RETURN 
            labels(n)[0] as entity_type,
            type(r) as relationship_type,
            COUNT(*) as count,
            AVG(r.score) as avg_score
        ORDER BY count DESC
        """, user_id=user_id)
        
        return {
            'top_entities': stats[:10],
            'relationship_distribution': self.calculate_distribution(stats),
            'memory_depth': await self.calculate_memory_depth(user_id)
        }
```

### 11. Example Usage Flows

#### Complete Search to Download Flow
```python
# User says: "download digital love by daft punk"

# 1. Episode ingestion
await memory_agent.add_conversation_turn(
    user_message="download digital love by daft punk",
    agent_response="Searching for Digital Love by Daft Punk...",
    context={'intent': 'download', 'user_id': 'user123'}
)

# 2. Search across sources
results = await unified_service.search_all_sources("digital love daft punk")

# 3. Store results in graph
for result in results:
    await memory_agent.store_track(result)

# 4. Select best quality
best_track = await memory_agent.select_best_quality(results)

# 5. Download track
file_path = await downloader.download(best_track)

# 6. Update preferences
await memory_agent.learn_preference(
    action="download",
    entity=best_track,
    context={'time': 'evening', 'day': 'friday'}
)

# 7. Check Rekordbox library
exists_in_library = await rekordbox.check_track_exists(best_track)
if not exists_in_library:
    await rekordbox.suggest_import(file_path)
```

### 12. Configuration

#### Environment Variables
```bash
# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Graphiti Configuration
GRAPHITI_LLM_MODEL=gpt-4o-mini
GRAPHITI_EMBEDDING_MODEL=text-embedding-3-small
GRAPHITI_CACHE_ENABLED=true
GRAPHITI_SEMAPHORE_LIMIT=10

# Music Service APIs
DEEZER_ARL=your_arl_cookie
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
YOUTUBE_COOKIES_PATH=./youtube_cookies.txt
SOULSEEK_USERNAME=your_username
SOULSEEK_PASSWORD=your_password

# Rekordbox
REKORDBOX_XML_PATH=/Users/username/Library/Pioneer/rekordbox/rekordbox.xml
```

### 13. Success Metrics

#### Key Performance Indicators
1. **Memory Recall Accuracy**: >90% relevant context retrieval
2. **Search Relevance**: >85% user satisfaction with results
3. **Recommendation Quality**: >70% acceptance rate
4. **Response Time**: <2s for search, <5s for complex queries
5. **Deduplication Accuracy**: >95% correct track matching
6. **Graph Size**: Efficiently handle >1M nodes, >10M relationships

### 14. Future Enhancements

1. **Audio Analysis**: Integrate audio fingerprinting for exact matching
2. **Social Features**: Share playlists and discover through friends
3. **Live Performance**: Track DJ sets and analyze crowd response
4. **Music Production**: Link to DAW projects and stem separation
5. **Streaming Integration**: Real-time ingestion from streaming history
6. **Voice Interface**: Natural voice commands for hands-free operation
7. **Mobile Sync**: Companion mobile app with offline graph sync
8. **AI DJ Assistant**: Automated set planning and harmonic mixing

## Conclusion

This architecture leverages Graphiti's temporal knowledge graph capabilities to transform the Deez music agent into an intelligent, memory-enabled system that learns from every interaction. By combining Neo4j's graph database with custom music ontologies and multi-source integration, the system will provide unprecedented music discovery, curation, and management capabilities while maintaining a deep understanding of user preferences and musical relationships over time.
# Enhanced Glossary: AI, Graph, and Graphiti Terms - Deep Technical Edition

## Understanding This Glossary

This glossary goes beyond definitions to explain **how** and **why** these concepts work in the context of Graphiti. Each term includes not just what it means, but how it's implemented in the source code, why design decisions were made, and how components connect together.

---

## Core Graphiti Architecture Terms

### **Episode**
**What it is:** The fundamental unit of information in Graphiti - a discrete piece of data that represents a moment in time, like a conversation turn, document update, or system event.

**How it works in Graphiti:**
```python
# From graphiti_core/nodes.py
class EpisodeType(Enum):
    message = 'message'  # "actor: content" format
    json = 'json'        # Structured JSON data
    text = 'text'        # Plain text content
```

**Why this design:** Episodes are temporal snapshots that allow Graphiti to:
1. **Track changes over time** - Each episode has a timestamp and source ID
2. **Handle multiple formats** - Messages for conversations, JSON for structured data, text for documents
3. **Maintain provenance** - Every fact in the graph can be traced back to its source episode

**Internal implementation:**
- Episodes are stored as `EpisodicNode` objects in the graph
- They connect to entities via `MENTIONS` edges
- Episode content is processed through the LLM extraction pipeline to identify entities and relationships
- Episodes within a temporal window (EPISODE_WINDOW_LEN) are grouped for context

**Connection to other concepts:**
- Episodes generate **Entities** and **Edges** through extraction
- Multiple episodes can reference the same entity, building up knowledge over time
- Episodes enable **temporal queries** - "What did we know at time X?"

---

### **Entity (Node)**
**What it is:** A distinct concept, person, place, or thing extracted from episodes - the vertices in the knowledge graph.

**How it's implemented:**
```python
# From graphiti_core/nodes.py
class EntityNode(Node):
    name: str                    # The entity's identifier
    entity_type: str            # Classification (PERSON, ORGANIZATION, etc.)
    summary: str                # LLM-generated description
    attributes: dict            # Flexible key-value pairs
    embedding: list[float]      # Vector for semantic search
```

**Why this architecture:**
1. **Flexible typing** - Entity types can be predefined or discovered dynamically
2. **Rich metadata** - Summary and attributes capture nuanced information
3. **Semantic searchability** - Embeddings enable similarity search
4. **Temporal awareness** - Entities have valid_from/valid_to timestamps

**Extraction process (from source):**
```python
# From graphiti_core/prompts/extract_nodes.py
# The LLM is prompted to identify entities with:
# 1. Name extraction
# 2. Type classification  
# 3. Attribute extraction
# 4. Summary generation
```

**Deduplication mechanism:**
Graphiti uses a sophisticated deduplication process:
1. **Name similarity** - Fuzzy matching on entity names
2. **Embedding similarity** - Cosine similarity of entity vectors
3. **Type matching** - Entities must be same type to merge
4. **Temporal consistency** - Newer information updates older

---

### **Edge (Relationship)**
**What it is:** A connection between two entities that represents how they relate to each other.

**Implementation details:**
```python
# From graphiti_core/edges.py
class EntityEdge(Edge):
    source_node_uuid: str       # From entity
    target_node_uuid: str       # To entity
    fact: str                   # Description of relationship
    fact_embedding: list[float] # Semantic representation
    episodes: list[str]         # Source episodes
    valid_at: datetime          # When relationship started
    invalid_at: datetime        # When relationship ended
```

**Why edges are special in Graphiti:**
1. **Bi-temporal tracking** - Edges know when they were true AND when they were added
2. **Fact-based** - Each edge has a natural language description
3. **Multi-source** - Edges can be reinforced by multiple episodes
4. **Invalidation** - Edges can be marked invalid when contradicted

**Edge extraction pipeline:**
```python
# Simplified from graphiti_core/utils/maintenance/edge_operations.py
async def extract_edges(episode_content, existing_entities):
    # 1. LLM extracts potential relationships
    # 2. Resolve entity references (fuzzy matching)
    # 3. Check for duplicates/contradictions
    # 4. Create edge with temporal metadata
    # 5. Generate embedding for similarity search
```

---

### **Community**
**What it is:** A cluster of highly interconnected entities that represent a domain or topic.

**How Graphiti builds communities:**
```python
# From graphiti_core/utils/maintenance/community_operations.py
async def build_communities():
    # 1. Calculate edge density between entities
    # 2. Apply Louvain algorithm for community detection
    # 3. Generate community summary via LLM
    # 4. Create hierarchical structure (communities of communities)
```

**Why communities matter:**
1. **Semantic clustering** - Groups related concepts
2. **Efficient retrieval** - Search within relevant communities
3. **Contextual understanding** - Communities provide domain context
4. **Scalability** - Hierarchical organization for large graphs

---

## Temporal Architecture

### **Bi-Temporal Model**
**What it is:** A time-tracking system that records both when events happened (valid time) and when we learned about them (transaction time).

**Implementation in Graphiti:**
```python
# Every node and edge has:
valid_at: datetime      # When the fact became true
invalid_at: datetime    # When the fact stopped being true
created_at: datetime    # When we added it to the graph
updated_at: datetime    # When we last modified it
```

**Why bi-temporal is crucial:**
1. **Contradiction resolution** - Later episodes can invalidate earlier facts
2. **Point-in-time queries** - "What did we believe on January 1st?"
3. **Audit trail** - Complete history of knowledge evolution
4. **Retroactive updates** - Can add historical data out of order

**Example scenario:**
```python
# Episode 1 (Monday): "John is CEO of TechCorp"
# Creates: Edge(valid_at=Monday, created_at=Monday)

# Episode 2 (Wednesday): "Sarah became CEO of TechCorp on Tuesday"
# Updates: Edge(invalid_at=Tuesday) for John
# Creates: Edge(valid_at=Tuesday, created_at=Wednesday) for Sarah

# Query on Monday returns: John is CEO
# Query on Wednesday returns: Sarah is CEO
# Full history shows the transition
```

---

## Search and Retrieval Architecture

### **Hybrid Search**
**What it is:** Graphiti's multi-modal search combining semantic similarity, keyword matching, and graph traversal.

**Implementation layers:**
```python
# From graphiti_core/search/search.py
async def search():
    # Parallel execution of:
    # 1. Semantic search (vector similarity)
    # 2. BM25 search (keyword matching)  
    # 3. Graph traversal (relationship following)
    # 4. Community search (topic clustering)
    
    # Then: Reranking via RRF or cross-encoder
```

**Why hybrid search:**
1. **Semantic understanding** - Captures meaning beyond keywords
2. **Exact matching** - Finds specific terms and names
3. **Relationship context** - Leverages graph structure
4. **Flexibility** - Different queries benefit from different methods

**Search configuration system:**
```python
# From graphiti_core/search/search_config.py
class SearchConfig:
    edge_config: EdgeSearchConfig      # How to search relationships
    node_config: NodeSearchConfig      # How to search entities
    episode_config: EpisodeSearchConfig # How to search raw data
    community_config: CommunitySearchConfig # How to search clusters
    reranker: RerankerType             # RRF, MMR, or cross-encoder
```

---

### **Embeddings**
**What it is:** Dense vector representations that capture semantic meaning of text.

**How Graphiti uses embeddings:**
```python
# From graphiti_core/embedder/client.py
class EmbedderClient:
    async def create(text: str) -> list[float]:
        # 1. Clean and normalize text
        # 2. Send to embedding model (OpenAI, Voyage, etc.)
        # 3. Cache results for efficiency
        # 4. Return normalized vector
```

**Embedding strategy:**
1. **Entities** - Name + summary + attributes embedded
2. **Edges** - Fact description embedded
3. **Episodes** - Full content embedded (chunked if needed)
4. **Queries** - Embedded with same model for comparison

**Why embeddings are critical:**
- Enable semantic search beyond keyword matching
- Support similarity-based deduplication
- Power recommendation and discovery
- Allow cross-lingual retrieval

---

### **Reranking**
**What it is:** A second-pass scoring system that reorders initial search results based on additional criteria.

**Graphiti's reranking methods:**

1. **RRF (Reciprocal Rank Fusion)**
```python
# Combines multiple ranked lists
def rrf(results_lists, k=60):
    scores = {}
    for results in results_lists:
        for rank, item in enumerate(results):
            scores[item] += 1 / (rank + k)
    return sorted(scores, key=scores.get, reverse=True)
```

2. **MMR (Maximal Marginal Relevance)**
```python
# Balances relevance and diversity
def mmr(query_embedding, candidates, lambda_param=0.5):
    selected = []
    while candidates:
        scores = []
        for candidate in candidates:
            relevance = cosine_similarity(query_embedding, candidate.embedding)
            diversity = max([cosine_similarity(candidate.embedding, s.embedding) 
                           for s in selected]) if selected else 0
            score = lambda_param * relevance - (1 - lambda_param) * diversity
            scores.append(score)
        # Select highest scoring, add to selected, remove from candidates
```

3. **Cross-Encoder**
```python
# Neural reranking with transformer models
async def cross_encoder_rerank(query, candidates):
    # Concatenate query with each candidate
    # Pass through BERT-style model
    # Get relevance scores
    # Reorder by scores
```

---

## LLM Integration

### **Extraction Pipeline**
**What it is:** The process of using LLMs to extract structured information from unstructured text.

**How Graphiti's extraction works:**

```python
# Simplified from actual implementation
async def extract_entities_and_relationships(episode):
    # Step 1: Entity extraction
    entities = await llm.extract_entities(
        episode_content=episode.content,
        entity_types=configured_types,
        previous_context=recent_episodes
    )
    
    # Step 2: Relationship extraction  
    relationships = await llm.extract_relationships(
        episode_content=episode.content,
        mentioned_entities=entities,
        existing_entities=graph_entities
    )
    
    # Step 3: Temporal extraction
    temporal_info = await llm.extract_temporal_info(
        relationships=relationships,
        reference_time=episode.timestamp
    )
    
    # Step 4: Deduplication
    deduplicated = await llm.deduplicate(
        new_entities=entities,
        existing_entities=similar_entities
    )
    
    return deduplicated_entities, temporal_relationships
```

**Why LLMs for extraction:**
1. **Context understanding** - LLMs grasp nuanced relationships
2. **Flexibility** - Handles varied text formats and domains
3. **Zero-shot capability** - Works without training data
4. **Natural language facts** - Generates human-readable descriptions

---

### **Prompt Engineering in Graphiti**

**How prompts are structured:**
```python
# From graphiti_core/prompts/extract_nodes.py
def extract_entities_prompt(context):
    return f"""
    <ENTITY TYPES>
    {context['entity_types']}  # Configured types with descriptions
    </ENTITY TYPES>
    
    <PREVIOUS CONTEXT>
    {context['previous_episodes']}  # Recent episodes for continuity
    </PREVIOUS CONTEXT>
    
    <CURRENT CONTENT>
    {context['episode_content']}  # Text to analyze
    </CURRENT CONTENT>
    
    Instructions:
    1. Identify all entities matching the types
    2. Resolve pronouns using context
    3. Extract attributes and relationships
    4. Generate concise summaries
    
    Output as JSON: {expected_schema}
    """
```

**Prompt design principles:**
1. **Structured input** - Clear sections for context and content
2. **Type guidance** - Explicit entity types when configured
3. **Context window** - Include recent episodes for coherence
4. **Output schema** - Structured output for reliable parsing
5. **Few-shot examples** - Include examples for complex extractions

---

## Graph Database Concepts

### **Neo4j Driver Architecture**
**What it is:** The interface layer between Graphiti and the Neo4j graph database.

**Implementation details:**
```python
# From graphiti_core/driver/neo4j_driver.py
class Neo4jDriver(GraphDriver):
    async def execute_query(query: str, parameters: dict):
        # 1. Get connection from pool
        # 2. Start transaction
        # 3. Execute Cypher query
        # 4. Handle results/errors
        # 5. Commit/rollback
        # 6. Return parsed results
```

**Why Neo4j:**
1. **Native graph storage** - Optimized for relationships
2. **Cypher query language** - Expressive pattern matching
3. **ACID compliance** - Data consistency guarantees
4. **Index support** - Fast lookups on properties
5. **Spatial/temporal** - Built-in time and location handling

---

### **Cypher Query Optimization**

**How Graphiti optimizes queries:**
```python
# Index creation for performance
CREATE INDEX entity_name FOR (n:Entity) ON (n.name)
CREATE INDEX entity_embedding FOR (n:Entity) ON (n.embedding)
CREATE INDEX edge_valid_time FOR ()-[r:RELATES_TO]->() ON (r.valid_at)

# Query patterns optimized for indexes
MATCH (n:Entity {name: $name})  # Uses name index
WHERE n.valid_at <= $time AND (n.invalid_at IS NULL OR n.invalid_at > $time)  # Temporal filtering
RETURN n
```

**Query optimization strategies:**
1. **Index coverage** - Ensure all WHERE clauses use indexes
2. **Limit early** - Reduce intermediate results
3. **Profile queries** - Identify bottlenecks with PROFILE
4. **Batch operations** - Group similar queries
5. **Connection pooling** - Reuse database connections

---

## Memory and Performance

### **Incremental Processing**
**What it is:** The ability to update the graph with new information without reprocessing everything.

**How it works:**
```python
# From graphiti_core/utils/bulk_utils.py
async def add_episode_incremental(episode):
    # 1. Extract entities and relationships
    new_entities, new_edges = await extract_from_episode(episode)
    
    # 2. Query only relevant existing data
    existing = await get_relevant_context(new_entities)
    
    # 3. Resolve and deduplicate
    resolved = await resolve_entities(new_entities, existing)
    
    # 4. Update only affected parts
    await update_graph_partial(resolved)
    
    # NOT: Rebuild entire graph
    # NOT: Recompute all embeddings
    # NOT: Regenerate all summaries
```

**Why incremental is essential:**
1. **Real-time updates** - New data available immediately
2. **Resource efficiency** - Only process what changed
3. **Scalability** - Grows linearly, not exponentially
4. **Cost savings** - Fewer LLM calls and computations

---

### **Caching Strategy**

**What Graphiti caches:**
```python
# Embedding cache
embedding_cache = {
    text_hash: embedding_vector
}

# Entity resolution cache
entity_cache = {
    entity_name: entity_uuid
}

# Search result cache
search_cache = {
    (query, params): results
}
```

**Cache invalidation:**
1. **TTL-based** - Expire after time period
2. **Event-based** - Clear on graph updates
3. **LRU eviction** - Remove least recently used
4. **Selective clearing** - Only affected entries

---

## Integration Patterns

### **Async Architecture**
**What it is:** Graphiti's use of Python's asyncio for concurrent operations.

**Implementation pattern:**
```python
# From graphiti_core/helpers.py
async def semaphore_gather(*tasks, max_concurrent=10):
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_task(task):
        async with semaphore:
            return await task
    
    return await asyncio.gather(*[bounded_task(t) for t in tasks])
```

**Why async matters:**
1. **Parallel processing** - Multiple LLM calls simultaneously
2. **I/O efficiency** - Don't block on database/API calls
3. **Resource management** - Control concurrency limits
4. **Responsiveness** - Keep system responsive during processing

---

### **Error Handling and Resilience**

**How Graphiti handles failures:**
```python
# Retry logic with exponential backoff
async def resilient_operation(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except RateLimitError:
            await asyncio.sleep(2 ** attempt)
        except TemporaryError as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Retry {attempt + 1}: {e}")
```

**Failure recovery strategies:**
1. **Partial success** - Save what succeeded, retry failures
2. **Checkpointing** - Resume from last successful state
3. **Graceful degradation** - Return partial results if needed
4. **Error context** - Rich error messages for debugging

---

## Advanced Concepts

### **Group Partitioning**
**What it is:** Logical separation of graph data into isolated partitions.

**Implementation:**
```python
# Every node and edge has a group_id
class Node:
    group_id: str  # Partition identifier
    
# Queries always filter by group_id
MATCH (n:Entity {group_id: $group_id})
```

**Why groups:**
1. **Multi-tenancy** - Separate data for different users/orgs
2. **Access control** - Restrict queries to authorized groups
3. **Performance** - Smaller subgraphs to search
4. **Data isolation** - Prevent cross-contamination

---

### **Schema Evolution**
**What it is:** How Graphiti handles changes to entity types and relationships over time.

**Mechanisms:**
1. **Flexible attributes** - Store new fields without schema changes
2. **Type discovery** - Learn new entity types from data
3. **Backward compatibility** - Old queries still work
4. **Migration tools** - Update existing data to new schema

```python
# Entity types can be extended dynamically
class CustomEntityType(BaseModel):
    # Define new fields
    custom_field: str
    
# Register with Graphiti
graphiti.add_entity_type(CustomEntityType)
```

---

### **Telemetry and Observability**

**What Graphiti tracks:**
```python
# From graphiti_core/telemetry/telemetry.py
capture_event({
    'event': 'episode_processed',
    'duration_ms': processing_time,
    'entities_extracted': entity_count,
    'edges_created': edge_count,
    'llm_tokens_used': token_count
})
```

**Metrics for monitoring:**
1. **Ingestion rate** - Episodes/second
2. **Query latency** - P50, P95, P99
3. **Graph size** - Nodes, edges, communities
4. **LLM usage** - Tokens, API calls, costs
5. **Error rates** - Failures, retries, timeouts

---

## Performance Optimizations

### **Bulk Operations**
**What it is:** Processing multiple items together for efficiency.

**Implementation:**
```python
# From graphiti_core/utils/bulk_utils.py
async def add_episodes_bulk(episodes):
    # Batch LLM calls
    all_extractions = await llm.extract_batch(episodes)
    
    # Bulk database operations
    await driver.execute_query("""
        UNWIND $nodes as node
        CREATE (n:Entity) SET n = node
    """, nodes=all_extractions)
    
    # Parallel embedding generation
    embeddings = await asyncio.gather(*[
        embedder.create(e.text) for e in all_extractions
    ])
```

**Bulk optimization strategies:**
1. **Batch API calls** - Single request for multiple items
2. **Transaction batching** - Group database writes
3. **Parallel processing** - Use all CPU cores
4. **Memory streaming** - Process large datasets in chunks

---

### **Search Recipe System**

**What it is:** Pre-configured search strategies optimized for different use cases.

**Available recipes:**
```python
# From graphiti_core/search/search_config_recipes.py

COMBINED_HYBRID_SEARCH_CROSS_ENCODER = SearchConfig(
    # Comprehensive search with neural reranking
    # Best for: High accuracy requirements
)

EDGE_HYBRID_SEARCH_RRF = SearchConfig(
    # Fast hybrid search with rank fusion
    # Best for: Balanced speed/accuracy
)

NODE_SIMILARITY_SEARCH = SearchConfig(
    # Pure semantic similarity
    # Best for: Concept discovery
)
```

**Recipe selection guide:**
1. **Conversational** - Use COMBINED_HYBRID with cross-encoder
2. **Factual lookup** - Use EDGE_HYBRID with RRF
3. **Exploration** - Use NODE_SIMILARITY with MMR
4. **Real-time** - Use lightweight configs with low limits

---

## System Architecture Insights

### **Episode Window**
**What it is:** A temporal grouping mechanism for related episodes.

**Why it matters:**
```python
EPISODE_WINDOW_LEN = timedelta(days=7)  # Default

# Episodes within window share context
# Helps with:
# - Pronoun resolution
# - Conversation continuity  
# - Temporal reasoning
```

### **Invalidation vs Deletion**
**Design choice:** Graphiti marks edges as invalid rather than deleting them.

**Why:**
1. **Audit trail** - Preserve history of beliefs
2. **Temporal queries** - Can query past states
3. **Confidence tracking** - Multiple invalidations = low confidence
4. **Recovery** - Can reinstate if invalidation was wrong

---

This enhanced glossary provides not just definitions but a deep understanding of how Graphiti works internally, why design decisions were made, and how components connect to create a powerful temporal knowledge graph system.
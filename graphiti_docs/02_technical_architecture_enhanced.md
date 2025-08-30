# Graphiti Technical Architecture - Deep Implementation Dive

## The Core Architecture Philosophy

Graphiti's architecture is built on three fundamental principles that permeate every design decision:

1. **Temporal-First Design**: Time is not an afterthought but the foundation
2. **Incremental Processing**: Never reprocess what you already know
3. **Multi-Modal Intelligence**: Combine graph structure, semantic understanding, and symbolic reasoning

Let me take you through exactly how these principles manifest in the code.

## System Architecture Overview

### The Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│                  (Your Code / API / UI)                      │
├─────────────────────────────────────────────────────────────┤
│                      Graphiti Core                           │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  Orchestration Layer                  │   │
│  │     (Episode Processing, Search, Maintenance)         │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │                  Intelligence Layer                   │   │
│  │      (LLM Client, Embedder, Cross-Encoder)           │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │                    Storage Layer                      │   │
│  │         (Graph Driver, Node/Edge Models)              │   │
│  └──────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure Layer                      │
│            (Neo4j, FalkorDB, Kuzu, Neptune)                 │
└─────────────────────────────────────────────────────────────┘
```

### Component Deep Dive

## 1. The Orchestration Layer - How Everything Connects

The orchestration layer is where Graphiti's magic happens. Let's examine the episode processing pipeline in detail:

```python
# From graphiti_core/graphiti.py - The main orchestration
async def add_episode(self, name, episode_body, ...):
    # Phase 1: Setup and Validation
    group_id = group_id or get_default_group_id(self.driver.provider)
    validate_entity_types(entity_types)
    validate_excluded_entity_types(excluded_entity_types, entity_types)
    
    # Phase 2: Dynamic Index Creation
    # This is crucial - Graphiti creates indexes on-demand per partition
    await build_dynamic_indexes(self.driver, group_id)
    
    # Phase 3: Context Retrieval
    # Get recent episodes for context (default: 10)
    previous_episodes = await self.retrieve_episodes(
        reference_time,
        last_n=RELEVANT_SCHEMA_LIMIT,
        group_ids=[group_id],
        source=source
    )
    
    # Phase 4: Parallel Extraction
    # Note the use of semaphore_gather for controlled concurrency
    extracted_nodes, extracted_edges = await semaphore_gather(
        extract_nodes(self.clients, episode, previous_episodes),
        extract_edges(self.clients, episode, nodes)
    )
    
    # Phase 5: Resolution and Deduplication
    resolved_nodes = await resolve_extracted_nodes(
        self.clients,
        extracted_nodes,
        group_id
    )
    
    # Phase 6: Temporal Processing
    invalidated_edges = await invalidate_edges_with_nodes(
        self.clients,
        new_edges,
        existing_edges
    )
    
    # Phase 7: Bulk Persistence
    await add_nodes_and_edges_bulk(
        self.driver,
        nodes,
        edges,
        episode
    )
    
    # Phase 8: Optional Community Updates
    if update_communities:
        await update_community(self.clients, nodes)
```

### Why This Architecture?

**1. Controlled Concurrency:**
```python
# From helpers.py
async def semaphore_gather(*tasks, max_concurrent=None):
    """
    This function is critical for production stability.
    It prevents overwhelming LLM providers with requests.
    """
    max_concurrent = max_concurrent or int(os.getenv('SEMAPHORE_LIMIT', 10))
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_task(task):
        async with semaphore:
            return await task
    
    return await asyncio.gather(*[bounded_task(t) for t in tasks])
```

**2. Dynamic Indexing:**
```python
async def build_dynamic_indexes(driver: GraphDriver, group_id: str):
    """
    Creates indexes specific to a partition.
    This allows efficient multi-tenancy without global index bloat.
    """
    await driver.execute_query(f"""
        CREATE INDEX IF NOT EXISTS 
        FOR (n:Entity) 
        ON (n.group_id, n.name)
        WHERE n.group_id = '{group_id}'
    """)
```

## 2. The Intelligence Layer - LLM Integration Architecture

### Extraction Pipeline - How LLMs Extract Knowledge

The extraction process uses a sophisticated reflexion loop:

```python
# From node_operations.py
async def extract_nodes(clients, episode, previous_episodes, ...):
    entities_missed = True
    reflexion_iterations = 0
    
    while entities_missed and reflexion_iterations <= MAX_REFLEXION_ITERATIONS:
        # Step 1: Initial extraction based on episode type
        if episode.source == EpisodeType.message:
            llm_response = await llm_client.generate_response(
                prompt_library.extract_nodes.extract_message(context),
                response_model=ExtractedEntities  # Structured output
            )
        elif episode.source == EpisodeType.json:
            # Different prompt for structured data
            llm_response = await llm_client.generate_response(
                prompt_library.extract_nodes.extract_json(context),
                response_model=ExtractedEntities
            )
        
        # Step 2: Reflexion - Did we miss anything?
        if reflexion_iterations < MAX_REFLEXION_ITERATIONS:
            missing_entities = await extract_nodes_reflexion(
                llm_client,
                episode,
                previous_episodes,
                extracted_entity_names
            )
            
            if missing_entities:
                # Add guidance for next iteration
                context['custom_prompt'] = f"Extract these entities: {missing_entities}"
                reflexion_iterations += 1
            else:
                entities_missed = False
```

**Why Reflexion?**
- **Self-correction**: LLMs can miss entities on first pass
- **Iterative refinement**: Each iteration builds on previous
- **Bounded iterations**: Prevents infinite loops (MAX_REFLEXION_ITERATIONS = 3)

### Prompt Engineering Architecture

Graphiti uses a sophisticated prompt library system:

```python
# From prompts/extract_nodes.py
def extract_message(context: dict) -> list[Message]:
    sys_prompt = """You are an AI assistant that extracts entity nodes 
    from conversational messages. Your primary task is to extract and 
    classify the speaker and other significant entities."""
    
    user_prompt = f"""
    <ENTITY TYPES>
    {context['entity_types']}  # Configured entity types with descriptions
    </ENTITY TYPES>
    
    <PREVIOUS MESSAGES>
    {context['previous_episodes']}  # For pronoun resolution
    </PREVIOUS MESSAGES>
    
    <CURRENT MESSAGE>
    {context['episode_content']}
    </CURRENT MESSAGE>
    
    Instructions:
    1. Extract the speaker as an entity
    2. Resolve pronouns using previous messages
    3. Classify each entity into provided types
    4. Extract entity attributes when mentioned
    
    Output as: {ExtractedEntities.schema()}
    """
```

### Embedding Architecture

```python
# From embedder/client.py
class EmbedderClient(ABC):
    async def create(self, input_data: list[str]) -> list[list[float]]:
        # Batch processing for efficiency
        embeddings = []
        for batch in chunk_list(input_data, BATCH_SIZE):
            batch_embeddings = await self._embed_batch(batch)
            embeddings.extend(batch_embeddings)
        
        # L2 normalization for consistent similarity calculations
        return [normalize_l2(emb) for emb in embeddings]
```

**Embedding Strategy:**
- **Entities**: Name + summary + attributes concatenated
- **Edges**: Fact description embedded
- **Episodes**: Full content (chunked if > 8191 tokens)
- **Communities**: Member names + summary

## 3. The Storage Layer - Graph Database Architecture

### Node Architecture

Graphiti has a sophisticated node hierarchy:

```python
# Base Node class
class Node(BaseModel, ABC):
    uuid: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    group_id: str  # Partition identifier
    labels: list[str]  # Graph labels
    created_at: datetime
    
    @abstractmethod
    async def save(self, driver: GraphDriver): ...
```

**Node Types:**

1. **EntityNode** - Represents real-world entities
```python
class EntityNode(Node):
    entity_type: str  # Classification
    summary: str  # LLM-generated description
    attributes: dict  # Flexible properties
    embedding: list[float]  # For similarity search
    
    # Temporal fields
    valid_at: datetime
    invalid_at: datetime | None
```

2. **EpisodicNode** - Stores raw episodes
```python
class EpisodicNode(Node):
    content: str  # Raw episode content
    source: EpisodeType  # message/json/text
    source_description: str
    created_at: datetime
    valid_at: datetime  # When event occurred
```

3. **CommunityNode** - Represents clusters
```python
class CommunityNode(Node):
    summary: str  # Community description
    embedding: list[float]
    level: int  # Hierarchy level
```

### Edge Architecture

Edges are first-class citizens with rich metadata:

```python
class EntityEdge(Edge):
    fact: str  # Natural language description
    fact_embedding: list[float]  # For semantic search
    episodes: list[str]  # Source episodes
    
    # Temporal tracking
    valid_at: datetime
    invalid_at: datetime | None
    
    # Invalidation tracking
    invalidated_by: list[str]  # Episodes that invalidated this
    invalidation_confidence: float  # LLM confidence in invalidation
```

### Database-Specific Implementations

Graphiti abstracts database differences through drivers:

```python
# Neo4j implementation
class Neo4jDriver(GraphDriver):
    async def execute_query(self, query: str, parameters: dict):
        async with self.driver.session() as session:
            result = await session.run(query, parameters)
            return await result.data()

# FalkorDB implementation  
class FalkorDBDriver(GraphDriver):
    async def execute_query(self, query: str, parameters: dict):
        # FalkorDB uses Redis protocol
        result = await self.client.graph.query(query, params=parameters)
        return self._parse_falkor_result(result)

# Kuzu implementation
class KuzuDriver(GraphDriver):
    # Kuzu has unique requirements for edge storage
    # Edges are actually stored as nodes with special labels
```

## 4. The Search Architecture - Multi-Modal Retrieval System

### Search Pipeline Architecture

```python
async def search(clients, query, group_ids, config, ...):
    # Step 1: Generate query embedding (if needed)
    if any_semantic_search_configured:
        search_vector = await embedder.create([query])
    else:
        search_vector = [0.0] * EMBEDDING_DIM  # Placeholder
    
    # Step 2: Parallel multi-modal search
    (edges, nodes, episodes, communities) = await semaphore_gather(
        edge_search(...),      # Search relationships
        node_search(...),      # Search entities
        episode_search(...),   # Search raw data
        community_search(...)  # Search clusters
    )
    
    # Step 3: Reranking
    if config.reranker == RerankerType.CROSS_ENCODER:
        results = await cross_encoder_rerank(query, results)
    elif config.reranker == RerankerType.MMR:
        results = mmr_rerank(query_vector, results)
    else:  # RRF
        results = rrf_combine(result_lists)
    
    return results
```

### Search Methods Deep Dive

**1. Semantic Search:**
```python
async def node_similarity_search(driver, query_vector, limit):
    # Use HNSW index if available (Neo4j 5.15+)
    if USE_HNSW:
        query = """
        CALL db.index.vector.queryNodes($index_name, $k, $vector)
        YIELD node, score
        RETURN node, score
        """
    else:
        # Fallback to brute force
        query = """
        MATCH (n:Entity)
        WITH n, vector.cosine_similarity(n.embedding, $vector) AS score
        WHERE score > $min_score
        RETURN n, score
        ORDER BY score DESC
        LIMIT $limit
        """
```

**2. BM25 Search:**
```python
async def edge_fulltext_search(driver, query, group_ids):
    # Prepare Lucene query
    lucene_query = lucene_sanitize(query)
    
    # Add group filters
    if group_ids:
        lucene_query = f"group_id:({' OR '.join(group_ids)}) AND ({lucene_query})"
    
    # Execute fulltext search
    result = await driver.execute_query("""
        CALL db.index.fulltext.queryRelationships($index_name, $query)
        YIELD relationship, score
        RETURN relationship, score
    """, {"query": lucene_query})
```

**3. Graph Traversal:**
```python
async def edge_bfs_search(driver, origin_node_uuids, max_depth=3):
    """
    Breadth-first search from origin nodes.
    Returns edges weighted by distance.
    """
    query = """
    MATCH path = (origin:Entity)-[*1..$max_depth]-(target:Entity)
    WHERE origin.uuid IN $origins
    UNWIND relationships(path) AS rel
    WITH DISTINCT rel, length(path) AS distance
    RETURN rel, 1.0 / distance AS score
    ORDER BY score DESC
    """
```

### Reranking Architecture

**1. RRF (Reciprocal Rank Fusion):**
```python
def rrf(result_lists: list[list], k: int = 60) -> list:
    """
    Combines multiple ranked lists without requiring scores.
    Perfect for combining different search methods.
    """
    scores = defaultdict(float)
    
    for result_list in result_lists:
        for rank, item in enumerate(result_list):
            # RRF formula: 1 / (k + rank)
            scores[item.uuid] += 1 / (k + rank + 1)
    
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

**2. MMR (Maximal Marginal Relevance):**
```python
def mmr(query_vector, candidates, lambda_param=0.5, top_k=10):
    """
    Balances relevance and diversity in results.
    Prevents redundant information.
    """
    selected = []
    remaining = list(candidates)
    
    while len(selected) < top_k and remaining:
        scores = []
        for candidate in remaining:
            # Relevance to query
            relevance = cosine_similarity(query_vector, candidate.embedding)
            
            # Similarity to already selected (for diversity)
            if selected:
                max_sim = max([
                    cosine_similarity(candidate.embedding, s.embedding) 
                    for s in selected
                ])
            else:
                max_sim = 0
            
            # MMR score balances both
            score = lambda_param * relevance - (1 - lambda_param) * max_sim
            scores.append((candidate, score))
        
        # Select highest MMR score
        best = max(scores, key=lambda x: x[1])
        selected.append(best[0])
        remaining.remove(best[0])
    
    return selected
```

## 5. Temporal Processing Architecture

### Invalidation System

One of Graphiti's most sophisticated features is temporal invalidation:

```python
async def invalidate_edges_with_nodes(
    clients: GraphitiClients,
    new_edges: list[EntityEdge],
    existing_edges: list[EntityEdge]
):
    """
    Invalidates existing edges that conflict with new information.
    """
    
    for new_edge in new_edges:
        # Find potentially conflicting edges
        candidates = [
            e for e in existing_edges
            if edges_overlap(e, new_edge) and e.valid_at < new_edge.valid_at
        ]
        
        if not candidates:
            continue
        
        # Use LLM to determine conflicts
        context = {
            'new_fact': new_edge.fact,
            'existing_facts': [c.fact for c in candidates],
            'timestamp': new_edge.valid_at
        }
        
        llm_response = await clients.llm_client.generate_response(
            prompt_library.invalidate_edges(context),
            InvalidatedEdges
        )
        
        # Mark edges as invalid
        for edge_uuid in llm_response.invalidated_edges:
            edge = next(e for e in candidates if e.uuid == edge_uuid)
            edge.invalid_at = new_edge.valid_at
            edge.invalidated_by.append(new_edge.uuid)
            await edge.save(clients.driver)
```

### Temporal Queries

```python
async def get_point_in_time_graph(driver, timestamp: datetime, group_id: str):
    """
    Retrieves the graph state at a specific point in time.
    """
    
    # Get entities valid at timestamp
    entities = await driver.execute_query("""
        MATCH (n:Entity {group_id: $group_id})
        WHERE n.valid_at <= $timestamp 
        AND (n.invalid_at IS NULL OR n.invalid_at > $timestamp)
        RETURN n
    """, {"timestamp": timestamp, "group_id": group_id})
    
    # Get relationships valid at timestamp
    relationships = await driver.execute_query("""
        MATCH (a:Entity)-[r:RELATES_TO]->(b:Entity)
        WHERE r.group_id = $group_id
        AND r.valid_at <= $timestamp
        AND (r.invalid_at IS NULL OR r.invalid_at > $timestamp)
        RETURN r, a, b
    """, {"timestamp": timestamp, "group_id": group_id})
    
    return build_temporal_graph(entities, relationships)
```

## 6. Community Detection Architecture

### Community Building Algorithm

```python
async def build_communities(clients, nodes: list[EntityNode]):
    """
    Builds hierarchical communities using Louvain algorithm.
    """
    
    # Step 1: Build adjacency matrix
    adjacency = await build_adjacency_matrix(clients.driver, nodes)
    
    # Step 2: Apply Louvain algorithm
    communities = louvain_communities(adjacency, resolution=1.0)
    
    # Step 3: Generate community summaries
    community_nodes = []
    for community_members in communities:
        # Get top entities by centrality
        central_entities = get_central_entities(community_members, limit=10)
        
        # Generate summary via LLM
        summary = await clients.llm_client.generate_response(
            f"Summarize this group of entities: {central_entities}",
            max_tokens=250
        )
        
        # Create community node
        community = CommunityNode(
            name=f"Community_{uuid4()}",
            summary=summary,
            embedding=await clients.embedder.create([summary]),
            level=0  # Base level
        )
        community_nodes.append(community)
    
    # Step 4: Build hierarchy if needed
    if len(community_nodes) > COMMUNITY_HIERARCHY_THRESHOLD:
        super_communities = await build_communities(
            clients, 
            community_nodes  # Treat communities as entities
        )
        # Set levels
        for sc in super_communities:
            sc.level = 1
    
    return community_nodes
```

### Community Update Strategy

```python
async def update_community(clients, new_nodes: list[EntityNode]):
    """
    Incrementally updates communities with new nodes.
    """
    
    # Find affected communities
    affected_communities = await get_communities_by_nodes(
        clients.driver, 
        new_nodes
    )
    
    for community in affected_communities:
        # Recalculate community metrics
        members = await get_community_members(clients.driver, community.uuid)
        
        # Check if community should split
        if len(members) > MAX_COMMUNITY_SIZE:
            await split_community(clients, community, members)
        
        # Check if community should merge
        similar_communities = await find_similar_communities(
            clients, 
            community
        )
        if similar_communities:
            await merge_communities(clients, community, similar_communities[0])
        
        # Update summary if membership changed significantly
        if membership_change_ratio(old_members, members) > 0.3:
            community.summary = await regenerate_summary(clients, members)
            community.embedding = await clients.embedder.create([community.summary])
            await community.save(clients.driver)
```

## 7. Performance Optimization Architecture

### Bulk Processing

```python
async def add_nodes_and_edges_bulk(
    driver: GraphDriver,
    nodes: list[EntityNode],
    edges: list[EntityEdge],
    episode: EpisodicNode
):
    """
    Optimized bulk insertion using UNWIND.
    """
    
    # Prepare node data
    node_data = [
        {
            'uuid': n.uuid,
            'name': n.name,
            'entity_type': n.entity_type,
            'summary': n.summary,
            'embedding': n.embedding,
            'attributes': json.dumps(n.attributes),
            'group_id': n.group_id,
            'created_at': n.created_at
        }
        for n in nodes
    ]
    
    # Bulk insert nodes
    await driver.execute_query("""
        UNWIND $nodes AS node
        CREATE (n:Entity {
            uuid: node.uuid,
            name: node.name,
            entity_type: node.entity_type,
            summary: node.summary,
            embedding: node.embedding,
            attributes: node.attributes,
            group_id: node.group_id,
            created_at: node.created_at
        })
    """, {"nodes": node_data})
    
    # Bulk insert edges with relationship lookup
    edge_data = [
        {
            'uuid': e.uuid,
            'source_uuid': e.source_node_uuid,
            'target_uuid': e.target_node_uuid,
            'fact': e.fact,
            'fact_embedding': e.fact_embedding,
            'episodes': e.episodes,
            'valid_at': e.valid_at
        }
        for e in edges
    ]
    
    await driver.execute_query("""
        UNWIND $edges AS edge
        MATCH (source:Entity {uuid: edge.source_uuid})
        MATCH (target:Entity {uuid: edge.target_uuid})
        CREATE (source)-[r:RELATES_TO {
            uuid: edge.uuid,
            fact: edge.fact,
            fact_embedding: edge.fact_embedding,
            episodes: edge.episodes,
            valid_at: edge.valid_at
        }]->(target)
    """, {"edges": edge_data})
```

### Caching Architecture

```python
class GraphitiCache:
    """
    Multi-level caching system for performance.
    """
    
    def __init__(self):
        self.embedding_cache = TTLCache(maxsize=10000, ttl=3600)
        self.entity_cache = TTLCache(maxsize=5000, ttl=1800)
        self.search_cache = TTLCache(maxsize=1000, ttl=300)
    
    async def get_or_create_embedding(self, text: str, embedder):
        cache_key = hashlib.md5(text.encode()).hexdigest()
        
        if cache_key in self.embedding_cache:
            return self.embedding_cache[cache_key]
        
        embedding = await embedder.create([text])
        self.embedding_cache[cache_key] = embedding[0]
        return embedding[0]
    
    def invalidate_entity_cache(self, entity_uuid: str):
        """Selective cache invalidation on updates."""
        keys_to_remove = [
            k for k in self.entity_cache.keys() 
            if entity_uuid in k
        ]
        for key in keys_to_remove:
            del self.entity_cache[key]
```

## 8. Error Handling and Resilience

### Retry Mechanisms

```python
async def resilient_llm_call(llm_client, prompt, max_retries=3):
    """
    Handles LLM API failures gracefully.
    """
    
    for attempt in range(max_retries):
        try:
            return await llm_client.generate_response(prompt)
            
        except RateLimitError as e:
            # Exponential backoff for rate limits
            wait_time = min(2 ** attempt * 10, 60)
            logger.warning(f"Rate limited, waiting {wait_time}s")
            await asyncio.sleep(wait_time)
            
        except StructuredOutputError as e:
            # Retry with relaxed schema
            if attempt < max_retries - 1:
                prompt = add_schema_clarification(prompt)
            else:
                # Fallback to unstructured output
                return await llm_client.generate_response(
                    prompt, 
                    structured=False
                )
                
        except NetworkError as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

### Transaction Management

```python
async def transactional_update(driver, operations):
    """
    Ensures atomic updates to the graph.
    """
    
    async with driver.session() as session:
        async with session.begin_transaction() as tx:
            try:
                for operation in operations:
                    await tx.run(operation.query, operation.params)
                
                await tx.commit()
                
            except Exception as e:
                await tx.rollback()
                logger.error(f"Transaction failed: {e}")
                raise
```

## Summary: The Architecture Advantage

Graphiti's architecture provides several key advantages:

1. **Temporal Consistency**: Every piece of data knows when it was true and when we learned it
2. **Incremental Intelligence**: The system gets smarter with each interaction without reprocessing
3. **Multi-Modal Understanding**: Combines symbolic (graph), semantic (embeddings), and linguistic (LLM) reasoning
4. **Production Ready**: Built-in concurrency control, caching, and error handling
5. **Extensible**: Clean abstractions allow swapping components (LLMs, databases, embedders)

The architecture is not just about storing data—it's about understanding and reasoning about information that changes over time, making it uniquely suited for building intelligent, context-aware AI systems.
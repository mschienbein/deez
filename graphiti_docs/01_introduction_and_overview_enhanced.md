# Graphiti Introduction and Overview - Deep Technical Dive

## What Really is Graphiti?

Graphiti is not just another knowledge graph framework - it's a **temporal memory system** designed from the ground up to solve the fundamental problem of AI agents: **how to remember and reason about information that changes over time**.

Let me show you what's actually happening under the hood when you use Graphiti.

### The Core Architecture - How It Actually Works

When you initialize Graphiti, here's what happens internally:

```python
# From graphiti_core/graphiti.py
class Graphiti:
    def __init__(self, uri, user, password, ...):
        # 1. Database Driver Setup
        self.driver = Neo4jDriver(uri, user, password)
        
        # 2. LLM Client Initialization (defaults to OpenAI)
        self.llm_client = llm_client or OpenAIClient()
        
        # 3. Embedder Setup (for semantic search)
        self.embedder = embedder or OpenAIEmbedder()
        
        # 4. Cross-Encoder Setup (for reranking)
        self.cross_encoder = cross_encoder or OpenAIRerankerClient()
        
        # 5. Create unified client interface
        self.clients = GraphitiClients(
            driver=self.driver,
            llm_client=self.llm_client,
            embedder=self.embedder,
            cross_encoder=self.cross_encoder
        )
```

**Why this architecture?**
- **Modular design**: Each component (database, LLM, embedder) can be swapped out
- **Provider agnostic**: Works with Neo4j, FalkorDB, Kuzu, Neptune
- **Async-first**: Built for concurrent operations from day one
- **Telemetry built-in**: Tracks usage patterns for optimization

### The Ingestion Pipeline - What Happens When You Add Data

When you call `add_episode()`, Graphiti orchestrates a complex pipeline:

```python
async def add_episode(self, name, episode_body, ...):
    # Step 1: Partition Management
    group_id = group_id or get_default_group_id(self.driver.provider)
    await build_dynamic_indexes(self.driver, group_id)
    
    # Step 2: Context Retrieval
    previous_episodes = await self.retrieve_episodes(
        reference_time,
        last_n=RELEVANT_SCHEMA_LIMIT,  # Default: 10 episodes
        group_ids=[group_id]
    )
    
    # Step 3: Entity Extraction via LLM
    extracted_nodes = await extract_nodes(
        self.clients, 
        episode, 
        previous_episodes,  # Context for pronoun resolution
        entity_types,       # Custom types if provided
        excluded_entity_types
    )
    
    # Step 4: Relationship Extraction
    extracted_edges = await extract_edges(
        self.clients,
        episode,
        extracted_nodes,
        edge_types
    )
    
    # Step 5: Deduplication & Resolution
    nodes, uuid_map, node_duplicates = await resolve_extracted_nodes(
        self.clients,
        extracted_nodes,
        group_id
    )
    
    # Step 6: Temporal Invalidation
    invalidated_edges = await invalidate_edges_with_nodes(
        self.clients,
        new_edges,
        existing_edges
    )
    
    # Step 7: Persistence to Graph
    await add_nodes_and_edges_bulk(
        self.driver,
        nodes,
        edges,
        episode
    )
    
    # Step 8: Community Updates (Optional)
    if update_communities:
        await update_community(self.clients, nodes)
```

**Why this pipeline design?**

1. **Context-aware extraction**: Previous episodes provide context for better extraction
2. **Intelligent deduplication**: Entities are matched by name, type, and embedding similarity
3. **Temporal consistency**: New information can invalidate old relationships
4. **Bulk operations**: Optimized for performance with batch database writes
5. **Lazy community updates**: Communities only update when needed

### The Temporal Model - Why Time Matters

Graphiti's temporal model is what sets it apart. Here's how it tracks time:

```python
# Every entity and relationship has:
class TemporalNode:
    valid_at: datetime      # When this became true in the real world
    invalid_at: datetime    # When this stopped being true
    created_at: datetime    # When we learned about it
    updated_at: datetime    # When we last modified it
```

**Real-world example:**
```python
# Monday: User tells system "John is CEO"
# Creates: Edge(valid_at=Monday, created_at=Monday)

# Wednesday: User says "Actually, Sarah became CEO on Tuesday"
# System:
# 1. Invalidates John's CEO edge: invalid_at=Tuesday
# 2. Creates Sarah's CEO edge: valid_at=Tuesday, created_at=Wednesday

# Now you can query:
# - "Who is CEO now?" → Sarah
# - "Who was CEO on Monday?" → John
# - "When did we learn about Sarah?" → Wednesday
```

### The Search Architecture - Multi-Modal Retrieval

Graphiti's search is not just vector similarity. It's a sophisticated multi-modal system:

```python
async def search(query: str, ...):
    # Parallel execution of four search methods:
    results = await semaphore_gather(
        edge_search(),      # Relationship facts
        node_search(),      # Entity information  
        episode_search(),   # Raw source data
        community_search()  # Topic clusters
    )
    
    # Each search method combines:
    # 1. Semantic search (embedding similarity)
    # 2. BM25 keyword search
    # 3. Graph traversal (for connected context)
    
    # Then reranking via:
    # - RRF (Reciprocal Rank Fusion)
    # - MMR (Maximal Marginal Relevance)
    # - Cross-encoder (neural reranking)
```

**Search configuration recipes:**
```python
# From search_config_recipes.py
COMBINED_HYBRID_SEARCH_CROSS_ENCODER = SearchConfig(
    edge_config=EdgeSearchConfig(
        search_methods=[cosine_similarity, bm25],
        reranker=cross_encoder
    ),
    node_config=NodeSearchConfig(...),
    limit=20,
    reranker_min_score=0.5
)
```

## Why Graphiti Exists - The Problem It Solves

### The Fundamental Challenge: Dynamic Knowledge

Traditional RAG systems fail at a basic requirement: **handling information that changes**. Let me show you why:

**Traditional RAG Approach:**
```python
# RAG systems store chunks of text with embeddings
chunks = [
    {"text": "John is CEO of TechCorp", "embedding": [...]},
    {"text": "Sarah is CTO of TechCorp", "embedding": [...]}
]

# When new information arrives:
# "John left TechCorp"
# RAG adds a new chunk:
chunks.append({"text": "John left TechCorp", "embedding": [...]})

# Now searching "Who is CEO?" returns conflicting chunks!
# RAG has no way to know which is current
```

**Graphiti's Approach:**
```python
# Graphiti maintains temporal relationships
edges = [
    {
        "fact": "John is CEO of TechCorp",
        "valid_at": "2024-01-01",
        "invalid_at": "2024-06-01"  # Automatically set when John left
    },
    {
        "fact": "Sarah is CEO of TechCorp",
        "valid_at": "2024-06-01",
        "invalid_at": None  # Still valid
    }
]

# Searching "Who is CEO?" returns only current facts
```

### The Architecture Decision: Why Graph + LLM?

**Graphs for Structure:**
- Relationships are first-class citizens
- Natural representation of connected information
- Efficient traversal for context gathering
- Perfect for "who knows whom" queries

**LLMs for Understanding:**
- Extract entities from natural language
- Resolve ambiguities and pronouns
- Generate human-readable summaries
- Handle multiple languages and formats

**The Synergy:**
```python
# LLM extracts structured data from unstructured input
extracted = llm.extract("Alice met Bob at Google's NYC office")
# → Entities: [Alice (PERSON), Bob (PERSON), Google (ORG), NYC (LOCATION)]
# → Relationships: [(Alice, met, Bob), (meeting, at, Google), (Google, has_office, NYC)]

# Graph stores and connects this information
graph.add_entities(extracted.entities)
graph.add_relationships(extracted.relationships)

# Later queries leverage both:
results = graph.search("Who works at Google?")
# → Graph finds connected entities
# → LLM ranks by relevance
# → Returns contextual answer
```

## Core Concepts - How They Really Work

### Episodes: The Atomic Unit

Episodes are carefully designed to handle different types of input:

```python
class EpisodeType(Enum):
    message = 'message'  # Conversational: "user: Hello"
    json = 'json'       # Structured: {"name": "John", "role": "CEO"}
    text = 'text'       # Documents: "Quarterly report shows..."
```

**Processing pipeline by type:**

**Message Episodes:**
```python
# Extract speaker and content
if episode.source == EpisodeType.message:
    speaker = extract_speaker(content)  # "user:", "assistant:"
    entities.append(Entity(name=speaker, type="SPEAKER"))
    # Continue with content extraction...
```

**JSON Episodes:**
```python
# Direct mapping to entities
if episode.source == EpisodeType.json:
    data = json.loads(content)
    for key, value in data.items():
        if is_entity_like(key):
            entities.append(Entity(name=value, attributes={key: value}))
```

### Entity Resolution: The Deduplication Challenge

One of Graphiti's most sophisticated features is entity resolution:

```python
async def resolve_extracted_nodes(extracted_nodes, existing_nodes):
    for extracted in extracted_nodes:
        # Step 1: Name similarity
        name_matches = fuzzy_match(extracted.name, existing_nodes)
        
        # Step 2: Type compatibility
        type_matches = [n for n in name_matches 
                       if n.entity_type == extracted.entity_type]
        
        # Step 3: Embedding similarity
        if embeddings_available:
            similarities = cosine_similarity(
                extracted.embedding, 
                [n.embedding for n in type_matches]
            )
            best_match = type_matches[argmax(similarities)]
            
        # Step 4: Merge or create
        if best_match and similarity > threshold:
            merge_entities(best_match, extracted)
        else:
            create_new_entity(extracted)
```

### Communities: Automatic Knowledge Organization

Communities emerge automatically from the graph structure:

```python
async def build_communities(graph):
    # Step 1: Calculate edge density
    edge_density = calculate_edge_density(graph)
    
    # Step 2: Apply Louvain algorithm
    communities = louvain_algorithm(graph, resolution=1.0)
    
    # Step 3: Generate summaries
    for community in communities:
        members = get_community_members(community)
        summary = await llm.summarize(
            f"Summarize this group: {members}",
            max_length=250
        )
        
    # Step 4: Create hierarchy
    if len(communities) > threshold:
        super_communities = build_communities(community_graph)
```

## Performance Optimizations - Why It's Fast

### Concurrent Processing

Graphiti uses sophisticated concurrency control:

```python
# From helpers.py
async def semaphore_gather(*tasks, max_concurrent=None):
    max_concurrent = max_concurrent or os.getenv('SEMAPHORE_LIMIT', 10)
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def bounded_task(task):
        async with semaphore:  # Limit concurrent executions
            return await task
    
    return await asyncio.gather(*[bounded_task(t) for t in tasks])
```

**Why this matters:**
- Prevents rate limiting from LLM providers
- Optimizes resource usage
- Maintains system responsiveness
- Allows fine-tuning for different deployments

### Incremental Updates

Unlike systems that rebuild on every change:

```python
# Traditional approach (slow)
def update_knowledge_base(new_data):
    all_data = load_all_data()
    all_data.append(new_data)
    rebuild_entire_index(all_data)  # O(n) operation

# Graphiti approach (fast)
async def add_episode(new_data):
    relevant_context = await get_relevant_context(new_data)  # O(log n)
    updates = await extract_updates(new_data, relevant_context)  # O(1)
    await apply_updates(updates)  # O(k) where k << n
```

### Index Strategy

Graphiti creates strategic indexes for performance:

```python
# From build_indices_and_constraints()
await driver.execute_query("""
    CREATE INDEX entity_name IF NOT EXISTS FOR (n:Entity) ON (n.name);
    CREATE INDEX entity_embedding IF NOT EXISTS FOR (n:Entity) ON (n.embedding);
    CREATE INDEX edge_valid_time IF NOT EXISTS FOR ()-[r:RELATES_TO]->() ON (r.valid_at);
    CREATE INDEX episode_created IF NOT EXISTS FOR (n:Episodic) ON (n.created_at);
""")
```

## Real-World Applications - Where Graphiti Shines

### Customer Support Memory

```python
# Track customer interactions over time
await graphiti.add_episode(
    name="Support Ticket #1234",
    episode_body="Customer reported login issues with 2FA",
    reference_time=datetime.now()
)

# Later...
await graphiti.add_episode(
    name="Support Ticket #1235", 
    episode_body="Same customer - 2FA issue resolved, now has billing question",
    reference_time=datetime.now()
)

# Search understands context
results = await graphiti.search("What issues has this customer had?")
# Returns connected history, not just keyword matches
```

### Dynamic Documentation

```python
# Version 1.0 docs
await graphiti.add_episode(
    episode_body='{"api_endpoint": "/v1/users", "method": "GET"}',
    source=EpisodeType.json,
    reference_time=datetime(2024, 1, 1)
)

# Version 2.0 update
await graphiti.add_episode(
    episode_body='{"api_endpoint": "/v2/users", "deprecated": "/v1/users"}',
    source=EpisodeType.json,
    reference_time=datetime(2024, 6, 1)
)

# Temporal queries work
old_api = await graphiti.search(
    "API endpoints", 
    reference_time=datetime(2024, 3, 1)
)  # Returns v1

current_api = await graphiti.search("API endpoints")  # Returns v2
```

### Conversational AI with True Memory

```python
# Graphiti remembers across sessions
async def chat_with_memory(user_id, message):
    # Add user message as episode
    await graphiti.add_episode(
        f"user_{user_id}: {message}",
        source=EpisodeType.message,
        group_id=user_id  # Partition by user
    )
    
    # Get relevant context
    context = await graphiti.search(
        message,
        group_ids=[user_id],
        config=COMBINED_HYBRID_SEARCH_CROSS_ENCODER
    )
    
    # Generate response with context
    response = await llm.generate(message, context)
    
    # Store assistant response
    await graphiti.add_episode(
        f"assistant: {response}",
        source=EpisodeType.message,
        group_id=user_id
    )
    
    return response
```

## The Philosophy Behind Graphiti

### Memory, Not Storage

Graphiti is designed around the concept of **memory** rather than **storage**:

- **Storage** preserves everything exactly as received
- **Memory** understands, connects, and evolves

This is why Graphiti:
- Deduplicates entities automatically
- Invalidates outdated relationships
- Builds communities of related concepts
- Maintains temporal continuity

### Incremental Intelligence

Rather than batch processing, Graphiti grows smarter with each interaction:

```python
# Each episode adds to collective intelligence
episode_1: "Alice works at Google"
# Graph learns: Alice (PERSON) -> works_at -> Google (ORG)

episode_2: "Alice is an engineer"
# Graph enriches: Alice.role = "engineer"

episode_3: "Bob also works at Google with Alice"
# Graph connects: Bob -> works_at -> Google
#                Bob -> works_with -> Alice

# The graph becomes richer over time without reprocessing
```

### Built for Production

Every design decision prioritizes production readiness:

- **Async-first**: Won't block your application
- **Configurable concurrency**: Tune for your infrastructure
- **Provider flexibility**: Swap LLMs and databases
- **Partition support**: Multi-tenant from day one
- **Telemetry built-in**: Monitor and optimize

## Getting Started - Understanding the First Steps

When you first use Graphiti, here's what's really happening:

```python
# 1. Initialization creates the driver and clients
graphiti = Graphiti(uri, user, password)

# 2. Build indices - THIS IS CRUCIAL for performance
await graphiti.build_indices_and_constraints()
# This creates ~15 indexes for efficient queries

# 3. Your first episode triggers the full pipeline
await graphiti.add_episode(
    name="First Episode",
    episode_body="John Smith is the CEO of TechCorp",
    source_description="Initial data",
    reference_time=datetime.now()
)

# Behind the scenes:
# - LLM extracts: John Smith (PERSON), TechCorp (ORGANIZATION)  
# - Creates relationship: John Smith -> CEO_of -> TechCorp
# - Generates embeddings for semantic search
# - Stores with temporal metadata
# - Ready for immediate querying
```

## Summary: Why Choose Graphiti?

Graphiti is the right choice when you need:

1. **Dynamic Knowledge Management** - Information that changes over time
2. **Contextual Understanding** - Relationships matter as much as entities
3. **Temporal Reasoning** - "What did we know when?"
4. **Production Scale** - Handles millions of facts efficiently
5. **Multi-modal Search** - Semantic + keyword + graph traversal
6. **Incremental Updates** - No batch reprocessing
7. **Built-in Intelligence** - LLM-powered extraction and understanding

The unique combination of temporal awareness, graph structure, and LLM intelligence makes Graphiti not just a knowledge graph, but a true memory system for AI applications.
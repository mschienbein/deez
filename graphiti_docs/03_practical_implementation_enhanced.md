# Graphiti Practical Implementation - Real-World Code Deep Dive

## Understanding Graphiti Through Real Code

This guide walks through actual implementation patterns from the Graphiti codebase, showing you exactly how to build production systems with temporal knowledge graphs. Every example here is from real code or based on actual usage patterns.

## 1. Setting Up Graphiti - The Real Implementation

### Basic Setup - What's Actually Happening

```python
from graphiti_core import Graphiti
from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables

# These are the actual environment variables Graphiti looks for
neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
neo4j_password = os.environ.get('NEO4J_PASSWORD', 'password')

# Initialize Graphiti - here's what happens internally
graphiti = Graphiti(
    uri=neo4j_uri,
    user=neo4j_user,
    password=neo4j_password,
    # Optional configurations with defaults:
    llm_client=None,  # Defaults to OpenAIClient()
    embedder=None,    # Defaults to OpenAIEmbedder()
    cross_encoder=None,  # Defaults to OpenAIRerankerClient()
    store_raw_episode_content=True,  # Keep original content
    max_coroutines=None,  # Uses SEMAPHORE_LIMIT env var (default: 10)
    ensure_ascii=False   # Preserve non-ASCII characters
)
```

**What's happening under the hood:**
```python
# From graphiti.py __init__
def __init__(self, ...):
    # 1. Create database driver
    self.driver = Neo4jDriver(uri, user, password)
    
    # 2. Initialize LLM client (OpenAI by default)
    self.llm_client = llm_client or OpenAIClient()
    
    # 3. Setup embedder for semantic search
    self.embedder = embedder or OpenAIEmbedder()
    
    # 4. Configure reranker for search results
    self.cross_encoder = cross_encoder or OpenAIRerankerClient()
    
    # 5. Bundle clients for internal use
    self.clients = GraphitiClients(...)
    
    # 6. Capture telemetry for monitoring
    self._capture_initialization_telemetry()
```

### Critical First Step: Building Indices

```python
# This is ESSENTIAL for performance - always run after setup
await graphiti.build_indices_and_constraints()
```

**What indices are created:**
```python
# From graph_data_operations.py
async def build_indices_and_constraints(driver, delete_existing=False):
    indices = [
        # Entity indices for fast lookups
        "CREATE INDEX entity_uuid IF NOT EXISTS FOR (n:Entity) ON (n.uuid)",
        "CREATE INDEX entity_group_id IF NOT EXISTS FOR (n:Entity) ON (n.group_id)",
        "CREATE INDEX entity_name IF NOT EXISTS FOR (n:Entity) ON (n.name)",
        
        # Temporal indices for time-based queries
        "CREATE INDEX entity_valid_at IF NOT EXISTS FOR (n:Entity) ON (n.valid_at)",
        "CREATE INDEX edge_valid_at IF NOT EXISTS FOR ()-[r:RELATES_TO]->() ON (r.valid_at)",
        
        # Episode indices
        "CREATE INDEX episode_created IF NOT EXISTS FOR (n:Episodic) ON (n.created_at)",
        "CREATE INDEX episode_group IF NOT EXISTS FOR (n:Episodic) ON (n.group_id)",
        
        # Full-text search indices
        "CREATE FULLTEXT INDEX entity_name_summary IF NOT EXISTS 
         FOR (n:Entity) ON EACH [n.name, n.summary]",
        "CREATE FULLTEXT INDEX edge_facts IF NOT EXISTS 
         FOR ()-[r:RELATES_TO]->() ON EACH [r.fact]",
        
        # Vector indices (Neo4j 5.15+)
        "CREATE VECTOR INDEX entity_embedding IF NOT EXISTS 
         FOR (n:Entity) ON (n.embedding) 
         OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}"
    ]
```

## 2. Working with Episodes - Real Examples

### Example 1: Conversational Episodes (from ecommerce example)

```python
# Real conversation from examples/ecommerce/runner.py
shoe_conversation = [
    "SalesBot: Hi, I'm Allbirds Assistant! How can I help you today?",
    "John: Hi, I'm looking for a new pair of shoes.",
    "SalesBot: Of course! What kind of material are you looking for?",
    "John: I'm looking for shoes made out of wool",
    "SalesBot: We have Men's SuperLight Wool Runners - Dark Grey",
    "John: Oh, I bought those 2 months ago, but I'm allergic to wool",
    "SalesBot: Would you be interested in Men's Couriers?",
    "John: Oh that is perfect, I LOVE the Natural Black color!"
]

# How to add conversational episodes
async def add_conversation(graphiti: Graphiti):
    for i, message in enumerate(shoe_conversation):
        result = await graphiti.add_episode(
            name=f'Message {i}',
            episode_body=message,
            source=EpisodeType.message,  # Indicates speaker:content format
            reference_time=datetime.now(timezone.utc),
            source_description='Customer support conversation'
        )
        
        # Result contains created entities and relationships
        print(f"Created {len(result.nodes)} entities, {len(result.edges)} relationships")
```

**What happens during processing:**
1. **Speaker extraction**: "John" and "SalesBot" become entities
2. **Product extraction**: "Men's SuperLight Wool Runners" becomes entity
3. **Preference extraction**: "allergic to wool" becomes attribute
4. **Relationship creation**: John -> allergic_to -> wool

### Example 2: Structured Data Episodes (JSON)

```python
# From examples/ecommerce - ingesting product catalog
async def ingest_products_data(graphiti: Graphiti):
    # Load product data
    with open('products.json') as file:
        products = json.load(file)['products']
    
    # Process each product as JSON episode
    for i, product in enumerate(products):
        await graphiti.add_episode(
            name=f'Product {i}',
            episode_body=json.dumps(product),  # JSON string
            source=EpisodeType.json,  # Tells Graphiti to expect structured data
            reference_time=datetime.now(timezone.utc),
            source_description='Product catalog'
        )

# Example product structure that gets extracted
product = {
    "name": "Men's Tree Runners",
    "price": 98,
    "colors": ["Natural Black", "Thunder Grey"],
    "materials": ["Eucalyptus Tree Fiber", "SweetFoam Sole"],
    "features": ["Machine Washable", "Lightweight"]
}

# Graphiti automatically creates:
# - Entity: "Men's Tree Runners" (type: PRODUCT)
# - Attributes: price=98, materials=[...], features=[...]
# - Relationships: Product -> made_from -> "Eucalyptus Tree Fiber"
```

### Example 3: Document Episodes with Custom Entity Types

```python
# From examples/podcast/podcast_runner.py - Real implementation
from pydantic import BaseModel, Field

# Define custom entity types
class Person(BaseModel):
    """A human person, fictional or nonfictional."""
    first_name: str | None = Field(..., description='First name')
    last_name: str | None = Field(..., description='Last name')
    occupation: str | None = Field(..., description="The person's work occupation")

class City(BaseModel):
    """A city"""
    country: str | None = Field(..., description='The country the city is in')

# Define custom relationship types
class IsPresidentOf(BaseModel):
    """Relationship between a person and the entity they are president of"""

# Use custom types when adding episodes
await graphiti.add_episode(
    name='Podcast Episode 1',
    episode_body=transcript_text,
    source=EpisodeType.text,
    reference_time=podcast_date,
    source_description='Podcast Transcript',
    # Custom entity types
    entity_types={'Person': Person, 'City': City},
    # Custom edge types
    edge_types={'IS_PRESIDENT_OF': IsPresidentOf},
    # Map which entity types can have which relationships
    edge_type_map={('Person', 'Entity'): ['IS_PRESIDENT_OF']}
)
```

## 3. Bulk Operations - Production Patterns

### Bulk Episode Processing

```python
# From bulk_utils.py - actual bulk processing implementation
from graphiti_core.utils.bulk_utils import RawEpisode

async def process_large_dataset(graphiti: Graphiti):
    # Prepare episodes for bulk processing
    raw_episodes: list[RawEpisode] = []
    
    for record in large_dataset:
        raw_episodes.append(
            RawEpisode(
                name=record['id'],
                content=record['text'],
                reference_time=record['timestamp'],
                source=EpisodeType.text,
                source_description='Historical documents'
            )
        )
    
    # Process in bulk - much faster than individual adds
    results = await graphiti.add_episode_bulk(
        raw_episodes,
        group_id='historical_docs',
        # Bulk processing specific options
        entity_types=custom_entity_types,
        edge_types=custom_edge_types
    )
    
    print(f"Processed {len(results.episodes)} episodes")
    print(f"Created {len(results.nodes)} entities")
    print(f"Created {len(results.edges)} relationships")
```

**Bulk processing optimizations:**
```python
# Internal bulk processing flow
async def add_episode_bulk(episodes: list[RawEpisode]):
    # 1. Batch LLM calls for extraction
    all_extractions = await semaphore_gather(*[
        extract_from_episode(ep) for ep in episodes
    ])
    
    # 2. Deduplicate across all episodes
    global_deduplication = dedupe_nodes_bulk(all_extractions)
    
    # 3. Single bulk insert to database
    await driver.execute_query("""
        UNWIND $nodes AS node
        CREATE (n:Entity) SET n = node
    """, nodes=global_deduplication)
    
    # 4. Bulk edge creation
    await driver.execute_query("""
        UNWIND $edges AS edge
        MATCH (a:Entity {uuid: edge.source})
        MATCH (b:Entity {uuid: edge.target})
        CREATE (a)-[r:RELATES_TO]->(b)
        SET r = edge.properties
    """, edges=bulk_edges)
```

## 4. Search Implementation - Real Query Patterns

### Basic Search

```python
# Simple search - uses default hybrid configuration
results = await graphiti.search("Who is the CEO?")

# Results structure (actual returned data)
for edge in results.edges:
    print(f"Fact: {edge.fact}")
    print(f"Confidence: {edge.score}")
    print(f"Valid from: {edge.valid_at}")
    print(f"Source episodes: {edge.episodes}")
```

### Advanced Search with Configuration

```python
from graphiti_core.search.search_config_recipes import (
    COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
    NODE_HYBRID_SEARCH_RRF,
    EDGE_HYBRID_SEARCH_NODE_DISTANCE
)

# Use predefined search recipe
results = await graphiti._search(
    query="technical specifications for wool runners",
    config=COMBINED_HYBRID_SEARCH_CROSS_ENCODER,  # Most accurate
    group_ids=['products'],  # Search specific partition
    search_filter=SearchFilters(
        entity_types=['Product'],  # Only search products
        start_date=datetime(2024, 1, 1),  # Temporal filter
        end_date=datetime.now()
    )
)

# Access different result types
print(f"Found {len(results.edges)} relationships")
print(f"Found {len(results.nodes)} entities")
print(f"Found {len(results.episodes)} source episodes")
print(f"Found {len(results.communities)} related communities")
```

### Center Node Search (Graph-aware ranking)

```python
# First, find a relevant node
initial_results = await graphiti.search("John's preferences")

if initial_results.edges:
    # Use first result's node as center for reranking
    center_node_uuid = initial_results.edges[0].source_node_uuid
    
    # Search with graph-distance reranking
    related_results = await graphiti.search(
        "product recommendations",
        center_node_uuid=center_node_uuid  # Results ranked by distance to John
    )
    
    # Results are now personalized to John's graph neighborhood
    for edge in related_results.edges:
        print(f"Recommendation: {edge.fact}")
        print(f"Relevance to John: {edge.score}")
```

### Custom Search Implementation

```python
# Direct search method usage for fine control
from graphiti_core.search import SearchConfig, EdgeSearchConfig, NodeSearchConfig
from graphiti_core.search.search_config import EdgeSearchMethod, NodeSearchMethod

# Create custom search configuration
custom_config = SearchConfig(
    # Configure edge search
    edge_config=EdgeSearchConfig(
        search_methods=[
            EdgeSearchMethod.cosine_similarity,  # Semantic search
            EdgeSearchMethod.bm25,  # Keyword search
            EdgeSearchMethod.bfs  # Graph traversal
        ],
        reranker=EdgeReranker.cross_encoder,  # Neural reranking
        include_episode_content=True,  # Include source text
        limit=20
    ),
    # Configure node search
    node_config=NodeSearchConfig(
        search_methods=[NodeSearchMethod.cosine_similarity],
        reranker=NodeReranker.mmr,  # Diversity in results
        limit=10
    ),
    # Global settings
    limit=50,
    reranker_min_score=0.5  # Filter low-confidence results
)

results = await graphiti._search("complex query", config=custom_config)
```

## 5. Temporal Operations - Working with Time

### Point-in-Time Queries

```python
# Query the graph at a specific point in time
async def get_historical_state(graphiti: Graphiti, query_time: datetime):
    # Graphiti automatically filters by temporal validity
    results = await graphiti.search(
        "organizational structure",
        search_filter=SearchFilters(
            reference_time=query_time  # Returns state at this time
        )
    )
    
    # Results only include facts valid at query_time
    for edge in results.edges:
        assert edge.valid_at <= query_time
        assert edge.invalid_at is None or edge.invalid_at > query_time
```

### Tracking Changes Over Time

```python
# Implement change tracking
async def track_entity_changes(graphiti: Graphiti, entity_name: str):
    # Get all historical versions of an entity
    query = """
    MATCH (n:Entity {name: $name})
    RETURN n
    ORDER BY n.valid_at DESC
    """
    
    records = await graphiti.driver.execute_query(
        query, 
        {"name": entity_name}
    )
    
    changes = []
    for record in records:
        node = record['n']
        changes.append({
            'valid_from': node['valid_at'],
            'valid_to': node.get('invalid_at'),
            'attributes': node['attributes'],
            'summary': node['summary']
        })
    
    return changes

# Example usage
history = await track_entity_changes(graphiti, "John Smith")
for change in history:
    print(f"From {change['valid_from']} to {change['valid_to']}: {change['summary']}")
```

## 6. Community Management - Real Implementation

### Building Communities

```python
from graphiti_core.utils.maintenance.community_operations import (
    build_communities,
    update_community
)

# Build communities from scratch
async def create_communities(graphiti: Graphiti):
    # Get all entities in a group
    nodes = await EntityNode.get_by_group_id(
        graphiti.driver, 
        group_id='products'
    )
    
    # Build communities using Louvain algorithm
    communities = await build_communities(
        graphiti.clients,
        nodes,
        resolution=1.0  # Higher = more communities
    )
    
    print(f"Created {len(communities)} communities")
    
    for community in communities:
        print(f"Community: {community.name}")
        print(f"Summary: {community.summary}")
        print(f"Members: {len(community.members)}")
```

### Incremental Community Updates

```python
# Update communities when new nodes are added
async def update_communities_incremental(graphiti: Graphiti, new_nodes: list):
    for node in new_nodes:
        # Update only affected communities
        await update_community(
            graphiti.clients,
            node,
            update_threshold=0.3  # Update if > 30% membership change
        )
```

## 7. Error Handling and Recovery - Production Patterns

### Resilient Episode Processing

```python
async def process_episodes_with_recovery(graphiti: Graphiti, episodes: list):
    failed_episodes = []
    successful = 0
    
    for episode in episodes:
        try:
            # Add with timeout
            result = await asyncio.wait_for(
                graphiti.add_episode(
                    name=episode['name'],
                    episode_body=episode['content'],
                    source=EpisodeType.text,
                    reference_time=episode['timestamp']
                ),
                timeout=30.0  # 30 second timeout
            )
            successful += 1
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout processing episode {episode['name']}")
            failed_episodes.append(episode)
            
        except RateLimitError as e:
            # Handle rate limiting
            logger.warning(f"Rate limited, waiting {e.retry_after}s")
            await asyncio.sleep(e.retry_after)
            failed_episodes.append(episode)  # Retry later
            
        except Exception as e:
            logger.error(f"Failed to process episode: {e}")
            failed_episodes.append(episode)
    
    # Retry failed episodes with exponential backoff
    if failed_episodes:
        await retry_failed_episodes(graphiti, failed_episodes)
    
    return successful, failed_episodes
```

### Transaction Management

```python
async def atomic_graph_update(graphiti: Graphiti):
    """Perform atomic updates using transactions"""
    
    async with graphiti.driver.session() as session:
        async with session.begin_transaction() as tx:
            try:
                # Create entities
                await tx.run("""
                    CREATE (n:Entity {uuid: $uuid, name: $name})
                """, {"uuid": str(uuid4()), "name": "New Entity"})
                
                # Create relationships
                await tx.run("""
                    MATCH (a:Entity {name: $from})
                    MATCH (b:Entity {name: $to})
                    CREATE (a)-[r:RELATES_TO {fact: $fact}]->(b)
                """, {"from": "Entity A", "to": "New Entity", "fact": "connected"})
                
                # Commit if all successful
                await tx.commit()
                
            except Exception as e:
                # Rollback on any error
                await tx.rollback()
                raise e
```

## 8. Multi-Tenant Implementation

### Group-Based Partitioning

```python
async def multi_tenant_setup(graphiti: Graphiti):
    tenants = ['customer_a', 'customer_b', 'customer_c']
    
    for tenant_id in tenants:
        # Each tenant gets isolated data
        await graphiti.add_episode(
            name=f"Initial data for {tenant_id}",
            episode_body="Tenant-specific information",
            source=EpisodeType.text,
            reference_time=datetime.now(),
            group_id=tenant_id  # Partition by tenant
        )
    
    # Query only tenant-specific data
    results = await graphiti.search(
        "query",
        group_ids=['customer_a']  # Only searches customer_a's data
    )
```

### Dynamic Index Management

```python
# Graphiti automatically creates group-specific indices
async def optimize_for_tenant(graphiti: Graphiti, tenant_id: str):
    # Create optimized indices for specific tenant
    await graphiti.driver.execute_query(f"""
        CREATE INDEX tenant_{tenant_id}_entity_name 
        IF NOT EXISTS 
        FOR (n:Entity) 
        ON (n.name)
        WHERE n.group_id = '{tenant_id}'
    """)
```

## 9. Performance Monitoring - Production Insights

### Tracking Performance Metrics

```python
import time
from graphiti_core.telemetry import capture_event

async def monitored_episode_processing(graphiti: Graphiti, episode):
    start_time = time.time()
    
    # Process episode
    result = await graphiti.add_episode(
        name=episode['name'],
        episode_body=episode['content'],
        source=EpisodeType.text,
        reference_time=episode['timestamp']
    )
    
    # Capture metrics
    processing_time = time.time() - start_time
    
    capture_event('episode_processed', {
        'duration_ms': processing_time * 1000,
        'entities_extracted': len(result.nodes),
        'relationships_created': len(result.edges),
        'episode_length': len(episode['content']),
        'group_id': result.episode.group_id
    })
    
    # Log if processing is slow
    if processing_time > 5.0:
        logger.warning(f"Slow episode processing: {processing_time:.2f}s")
    
    return result
```

### Query Performance Analysis

```python
async def analyze_search_performance(graphiti: Graphiti):
    test_queries = [
        "simple entity lookup",
        "complex relationship query with multiple conditions",
        "temporal query for historical data"
    ]
    
    performance_results = []
    
    for query in test_queries:
        start = time.perf_counter()
        
        results = await graphiti.search(query)
        
        duration = time.perf_counter() - start
        
        performance_results.append({
            'query': query[:50],
            'duration_ms': duration * 1000,
            'results_count': len(results.edges),
            'query_complexity': len(query.split())
        })
    
    # Analyze results
    avg_latency = sum(r['duration_ms'] for r in performance_results) / len(performance_results)
    print(f"Average query latency: {avg_latency:.2f}ms")
    
    return performance_results
```

## 10. Integration with External Systems

### Webhook Integration

```python
async def setup_webhook_processing(graphiti: Graphiti):
    """Process incoming webhooks as episodes"""
    
    async def process_webhook(webhook_data: dict):
        # Transform webhook to episode
        episode_content = {
            'event_type': webhook_data['type'],
            'timestamp': webhook_data['timestamp'],
            'data': webhook_data['payload']
        }
        
        # Add as JSON episode
        result = await graphiti.add_episode(
            name=f"Webhook_{webhook_data['id']}",
            episode_body=json.dumps(episode_content),
            source=EpisodeType.json,
            reference_time=datetime.fromisoformat(webhook_data['timestamp']),
            source_description=f"Webhook from {webhook_data['source']}"
        )
        
        return result
```

### Streaming Data Integration

```python
async def process_stream(graphiti: Graphiti, stream_source):
    """Process streaming data in real-time"""
    
    buffer = []
    buffer_size = 10  # Process in batches
    
    async for message in stream_source:
        buffer.append(RawEpisode(
            name=f"Stream_{message.id}",
            content=message.content,
            reference_time=message.timestamp,
            source=EpisodeType.message,
            source_description="Live stream"
        ))
        
        if len(buffer) >= buffer_size:
            # Process batch
            await graphiti.add_episode_bulk(buffer)
            buffer.clear()
    
    # Process remaining
    if buffer:
        await graphiti.add_episode_bulk(buffer)
```

## Summary: Key Implementation Patterns

1. **Always initialize indices** - First step after setup
2. **Use bulk operations** for large datasets
3. **Configure search** based on your use case
4. **Leverage temporal features** for versioning
5. **Implement error handling** for production
6. **Monitor performance** with telemetry
7. **Use transactions** for atomic updates
8. **Partition by group_id** for multi-tenancy
9. **Cache when possible** for performance
10. **Process incrementally** rather than batch rebuilding

These patterns come from real production usage and the actual Graphiti codebase, giving you battle-tested approaches for building temporal knowledge graph applications.
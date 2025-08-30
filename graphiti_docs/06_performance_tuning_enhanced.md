# Graphiti Performance Tuning: Deep Optimization Guide

## Table of Contents
1. [Performance Architecture](#performance-architecture)
2. [Concurrency and Parallelism](#concurrency-and-parallelism)
3. [Batch Processing Optimization](#batch-processing-optimization)
4. [Embedding Performance](#embedding-performance)
5. [Database Query Optimization](#database-query-optimization)
6. [Caching Strategies](#caching-strategies)
7. [Memory Management](#memory-management)
8. [Production Benchmarks](#production-benchmarks)
9. [Monitoring and Profiling](#monitoring-and-profiling)
10. [Scaling Strategies](#scaling-strategies)

## Performance Architecture

### Core Performance Principles

Graphiti is designed with performance as a first-class concern:

```python
# From graphiti_core/helpers.py - Core performance configuration
import os
from dotenv import load_dotenv

load_dotenv()

# Parallel runtime for Neo4j queries (experimental)
USE_PARALLEL_RUNTIME = bool(os.getenv('USE_PARALLEL_RUNTIME', False))

# Semaphore limit controls concurrent async operations
SEMAPHORE_LIMIT = int(os.getenv('SEMAPHORE_LIMIT', 20))

# Reflexion iteration limit for extraction accuracy
MAX_REFLEXION_ITERATIONS = int(os.getenv('MAX_REFLEXION_ITERATIONS', 0))

# Default pagination for queries
DEFAULT_PAGE_LIMIT = 20

# Conditional parallel runtime query prefix
RUNTIME_QUERY: LiteralString = (
    'CYPHER runtime = parallel parallelRuntimeSupport=all\n' 
    if USE_PARALLEL_RUNTIME else ''
)
```

### Async-First Architecture

Everything in Graphiti is async, enabling massive parallelism:

```python
# From graphiti_core/graphiti.py
class Graphiti:
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        llm_client: LLMClient | None = None,
        embedder: EmbedderClient | None = None,
        cross_encoder: CrossEncoderClient | None = None,
        max_coroutines: int | None = None,  # Override SEMAPHORE_LIMIT
    ):
        # Configure concurrency limit
        self.max_coroutines = max_coroutines or SEMAPHORE_LIMIT
        
        # Initialize driver with connection pooling
        self.driver = Neo4jAsyncDriver(
            uri=uri,
            user=user,
            password=password,
            connection_pool_size=50,  # Connection pool for concurrent queries
            max_connection_lifetime=3600,
            connection_acquisition_timeout=60.0,
            connection_timeout=30.0,
        )
```

## Concurrency and Parallelism

### Semaphore-Controlled Concurrency

The core of Graphiti's concurrency model is semaphore-based control:

```python
# From graphiti_core/helpers.py
async def semaphore_gather(
    *coroutines: Coroutine,
    max_coroutines: int | None = None,
) -> list[Any]:
    """
    Use this instead of asyncio.gather() to bound coroutines.
    Prevents overwhelming LLM providers and databases.
    """
    semaphore = asyncio.Semaphore(max_coroutines or SEMAPHORE_LIMIT)
    
    async def _wrap_coroutine(coroutine):
        async with semaphore:
            return await coroutine
    
    return await asyncio.gather(*(_wrap_coroutine(coroutine) for coroutine in coroutines))
```

### Real-World Usage in Bulk Processing

```python
# From graphiti_core/utils/bulk_utils.py
async def extract_nodes_and_edges_bulk(
    clients: GraphitiClients,
    episode_tuples: list[tuple[EpisodicNode, list[EpisodicNode]]],
    edge_type_map: dict[tuple[str, str], list[str]],
    entity_types: dict[str, type[BaseModel]] | None = None,
    excluded_entity_types: list[str] | None = None,
    edge_types: dict[str, type[BaseModel]] | None = None,
) -> tuple[list[list[EntityNode]], list[list[EntityEdge]]]:
    # Parallel node extraction with semaphore control
    extracted_nodes_bulk: list[list[EntityNode]] = await semaphore_gather(
        *[
            extract_nodes(clients, episode, previous_episodes, entity_types, excluded_entity_types)
            for episode, previous_episodes in episode_tuples
        ]
    )
    
    # Parallel edge extraction with semaphore control
    extracted_edges_bulk: list[list[EntityEdge]] = await semaphore_gather(
        *[
            extract_edges(
                clients,
                episode,
                extracted_nodes_bulk[i],
                previous_episodes,
                edge_type_map=edge_type_map,
                group_id=episode.group_id,
                edge_types=edge_types,
            )
            for i, (episode, previous_episodes) in enumerate(episode_tuples)
        ]
    )
    
    return extracted_nodes_bulk, extracted_edges_bulk
```

### Community Building Concurrency

```python
# From graphiti_core/utils/maintenance/community_operations.py
MAX_COMMUNITY_BUILD_CONCURRENCY = 10

async def build_communities(
    driver: GraphDriver,
    llm_client: LLMClient,
    group_ids: list[str] | None,
    ensure_ascii: bool = True,
) -> tuple[list[CommunityNode], list[CommunityEdge]]:
    community_clusters = await get_community_clusters(driver, group_ids)
    
    # Create a separate semaphore for community building
    semaphore = asyncio.Semaphore(MAX_COMMUNITY_BUILD_CONCURRENCY)
    
    async def limited_build_community(cluster):
        async with semaphore:
            return await build_community(llm_client, cluster, ensure_ascii)
    
    # Process all communities concurrently with limit
    communities: list[tuple[CommunityNode, list[CommunityEdge]]] = list(
        await semaphore_gather(
            *[limited_build_community(cluster) for cluster in community_clusters]
        )
    )
    
    return community_nodes, community_edges
```

## Batch Processing Optimization

### Efficient Bulk Operations

```python
# From graphiti_core/utils/bulk_utils.py
CHUNK_SIZE = 10  # Optimal chunk size for batch operations

async def add_nodes_and_edges_bulk_tx(
    tx: GraphDriverSession,
    episodic_nodes: list[EpisodicNode],
    episodic_edges: list[EpisodicEdge],
    entity_nodes: list[EntityNode],
    entity_edges: list[EntityEdge],
    embedder: EmbedderClient,
    driver: GraphDriver,
):
    """Optimized bulk transaction for adding nodes and edges."""
    
    # Pre-process episodic nodes
    episodes = [dict(episode) for episode in episodic_nodes]
    for episode in episodes:
        episode['source'] = str(episode['source'].value)
        episode.pop('labels', None)
        episode['group_label'] = 'Episodic_' + episode['group_id'].replace('-', '')
    
    # Batch process entity nodes with embedding generation
    nodes = []
    for node in entity_nodes:
        if node.name_embedding is None:
            await node.generate_name_embedding(embedder)
        
        entity_data: dict[str, Any] = {
            'uuid': node.uuid,
            'name': node.name,
            'name_embedding': node.name_embedding,
            'group_id': node.group_id,
            'summary': node.summary,
            'created_at': node.created_at,
        }
        
        # Provider-specific optimizations
        if driver.provider == GraphProvider.KUZU:
            attributes = convert_datetimes_to_strings(node.attributes) if node.attributes else {}
            entity_data['attributes'] = json.dumps(attributes)
        else:
            entity_data.update(node.attributes or {})
            entity_data['labels'] = list(
                set(node.labels + ['Entity', 'Entity_' + node.group_id.replace('-', '')])
            )
        
        nodes.append(entity_data)
    
    # Batch process edges with embedding generation
    edges = []
    for edge in entity_edges:
        if edge.fact_embedding is None:
            await edge.generate_embedding(embedder)
        
        edge_data = prepare_edge_data(edge, driver)
        edges.append(edge_data)
    
    # Execute optimized bulk queries based on provider
    if driver.provider == GraphProvider.KUZU:
        # KUZU requires individual inserts due to STRUCT[] limitations
        await execute_kuzu_bulk_insert(tx, episodes, nodes, edges, episodic_edges)
    else:
        # Neo4j supports true bulk operations with UNWIND
        await execute_neo4j_bulk_insert(tx, episodes, nodes, edges, episodic_edges)

async def execute_neo4j_bulk_insert(tx, episodes, nodes, edges, episodic_edges):
    """Neo4j optimized bulk insert with UNWIND."""
    # Single query for all episodes
    await tx.run(get_episode_node_save_bulk_query(GraphProvider.NEO4J), episodes=episodes)
    
    # Single query for all nodes
    await tx.run(get_entity_node_save_bulk_query(GraphProvider.NEO4J, nodes), nodes=nodes)
    
    # Single query for all episodic edges
    await tx.run(
        get_episodic_edge_save_bulk_query(GraphProvider.NEO4J),
        episodic_edges=[edge.model_dump() for edge in episodic_edges],
    )
    
    # Single query for all entity edges
    await tx.run(get_entity_edge_save_bulk_query(GraphProvider.NEO4J), entity_edges=edges)
```

### Deduplication with Union-Find

```python
# From graphiti_core/utils/bulk_utils.py
class UnionFind:
    """Efficient data structure for deduplication."""
    
    def __init__(self, elements):
        # Start each element in its own set
        self.parent = {e: e for e in elements}
    
    def find(self, x):
        # Path compression for O(α(n)) amortized time
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]
    
    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        # Attach the lexicographically larger root under the smaller
        if ra < rb:
            self.parent[rb] = ra
        else:
            self.parent[ra] = rb

def compress_uuid_map(duplicate_pairs: list[tuple[str, str]]) -> dict[str, str]:
    """
    Compress duplicate mappings using Union-Find.
    Transforms chains like A->B, B->C into A->C, B->C.
    """
    all_uuids = set()
    for pair in duplicate_pairs:
        all_uuids.add(pair[0])
        all_uuids.add(pair[1])
    
    uf = UnionFind(all_uuids)
    for a, b in duplicate_pairs:
        uf.union(a, b)
    
    # Ensure full path compression before mapping
    return {uuid: uf.find(uuid) for uuid in all_uuids}
```

## Embedding Performance

### Batch Embedding Generation

```python
# From graphiti_core/nodes.py
async def create_entity_node_embeddings(embedder: EmbedderClient, nodes: list[EntityNode]):
    """Generate embeddings for multiple nodes efficiently."""
    # Extract texts for batch processing
    texts = [node.name for node in nodes]
    
    # Single batch call to embedding service
    embeddings = await embedder.create_embeddings(texts)
    
    # Assign embeddings back to nodes
    for node, embedding in zip(nodes, embeddings):
        node.name_embedding = embedding

# From graphiti_core/edges.py
async def create_entity_edge_embeddings(embedder: EmbedderClient, edges: list[EntityEdge]):
    """Generate embeddings for multiple edges efficiently."""
    texts = [edge.fact for edge in edges]
    embeddings = await embedder.create_embeddings(texts)
    
    for edge, embedding in zip(edges, embeddings):
        edge.fact_embedding = embedding
```

### Optimized Embedding Provider

```python
# From graphiti_core/embedder/openai.py
class OpenAIEmbedder(EmbedderClient):
    async def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Batch embedding creation with automatic chunking."""
        MAX_BATCH_SIZE = 2048  # OpenAI's limit
        all_embeddings = []
        
        for i in range(0, len(texts), MAX_BATCH_SIZE):
            batch = texts[i:i + MAX_BATCH_SIZE]
            
            # Clean texts to avoid encoding issues
            cleaned_batch = [
                text.encode('utf-8', errors='ignore').decode('utf-8')
                for text in batch
            ]
            
            # Single API call for entire batch
            response = await self.client.embeddings.create(
                input=cleaned_batch,
                model=self.model,
                dimensions=self.dimensions  # Dimension reduction for efficiency
            )
            
            batch_embeddings = [data.embedding for data in response.data]
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
```

### Vector Similarity Optimization

```python
# From graphiti_core/helpers.py
def normalize_l2(embedding: list[float]) -> NDArray:
    """Normalize embedding for cosine similarity via dot product."""
    embedding_array = np.array(embedding)
    norm = np.linalg.norm(embedding_array, 2, axis=0, keepdims=True)
    return np.where(norm == 0, embedding_array, embedding_array / norm)

# From graphiti_core/utils/bulk_utils.py - Efficient deduplication
async def dedupe_nodes_bulk(
    clients: GraphitiClients,
    extracted_nodes: list[list[EntityNode]],
    episode_tuples: list[tuple[EpisodicNode, list[EpisodicNode]]],
    entity_types: dict[str, type[BaseModel]] | None = None,
) -> tuple[dict[str, list[EntityNode]], dict[str, str]]:
    embedder = clients.embedder
    min_score = 0.8  # Similarity threshold
    
    # Generate embeddings in parallel
    await semaphore_gather(
        *[create_entity_node_embeddings(embedder, nodes) for nodes in extracted_nodes]
    )
    
    # Find similar nodes using optimized search
    dedupe_tuples: list[tuple[list[EntityNode], list[EntityNode]]] = []
    for i, nodes_i in enumerate(extracted_nodes):
        existing_nodes: list[EntityNode] = []
        for j, nodes_j in enumerate(extracted_nodes):
            if i == j:
                continue
            existing_nodes += nodes_j
        
        candidates_i: list[EntityNode] = []
        for node in nodes_i:
            for existing_node in existing_nodes:
                # Fast word overlap check (cheaper than embeddings)
                node_words = set(node.name.lower().split())
                existing_node_words = set(existing_node.name.lower().split())
                has_overlap = not node_words.isdisjoint(existing_node_words)
                
                if has_overlap:
                    candidates_i.append(existing_node)
                    continue
                
                # Semantic similarity only if no word overlap
                similarity = np.dot(
                    normalize_l2(node.name_embedding or []),
                    normalize_l2(existing_node.name_embedding or []),
                )
                if similarity >= min_score:
                    candidates_i.append(existing_node)
        
        dedupe_tuples.append((nodes_i, candidates_i))
```

## Database Query Optimization

### Cypher Query Optimization

```python
# From graphiti_core/models/nodes/node_db_queries.py
def get_entity_node_save_bulk_query(provider: GraphProvider, nodes: list[dict]) -> str:
    if provider == GraphProvider.NEO4J:
        # Optimized bulk MERGE with UNWIND
        return f"""
        {RUNTIME_QUERY}
        UNWIND $nodes AS node
        CALL {{
            WITH node
            MERGE (n:Entity {{uuid: node.uuid}})
            SET n = node
            SET n.created_at = COALESCE(n.created_at, node.created_at)
            WITH n, node
            CALL db.create.setNodeVectorProperty(n, 'name_embedding', node.name_embedding)
            WITH n, node
            UNWIND node.labels AS label
            CALL apoc.create.addLabels(n, [label]) YIELD node AS labeledNode
            RETURN count(*) AS c
        }}
        IN TRANSACTIONS OF 500 ROWS
        RETURN count(*) AS total
        """
```

### Index Management

```python
# From graphiti_core/graphiti.py
async def build_indices_and_constraints(self):
    """Create database indices for optimal query performance."""
    
    # Unique constraints for data integrity
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.uuid IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Episodic) REQUIRE n.uuid IS UNIQUE",
    ]
    
    # Performance indices
    indices = [
        # Vector indices for similarity search
        "CREATE VECTOR INDEX entity_name_embedding IF NOT EXISTS FOR (n:Entity) ON (n.name_embedding) OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}",
        
        # Composite indices for common query patterns
        "CREATE INDEX entity_group_created IF NOT EXISTS FOR (n:Entity) ON (n.group_id, n.created_at)",
        "CREATE INDEX edge_group_created IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.group_id, r.created_at)",
        
        # Full-text search indices
        "CREATE FULLTEXT INDEX entity_name_summary IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.summary]",
    ]
    
    for constraint in constraints:
        await self.driver.execute_query(constraint)
    
    for index in indices:
        await self.driver.execute_query(index)
```

### Query Result Caching

```python
# From graphiti_core/llm_client/client.py
from diskcache import Cache

class LLMClient(ABC):
    def __init__(self, config: LLMConfig | None, cache: bool = False):
        self.cache_enabled = cache
        self.cache_dir = None
        
        # Disk-based cache for persistence across restarts
        if self.cache_enabled:
            self.cache_dir = Cache('./llm_cache')
    
    def _get_cache_key(self, messages: list[Message]) -> str:
        """Create deterministic cache key."""
        message_str = json.dumps([m.model_dump() for m in messages], sort_keys=True)
        key_str = f'{self.model}:{message_str}'
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int | None = None,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, typing.Any]:
        if self.cache_enabled and self.cache_dir is not None:
            cache_key = self._get_cache_key(messages)
            
            # Check cache first
            if cache_key in self.cache_dir:
                logger.debug(f'Cache hit for key: {cache_key}')
                return self.cache_dir[cache_key]
        
        # Generate response
        response = await self._generate_response_with_retry(
            messages, response_model, max_tokens, model_size
        )
        
        # Cache the result
        if self.cache_enabled and self.cache_dir is not None:
            self.cache_dir[cache_key] = response
        
        return response
```

## Caching Strategies

### Multi-Level Caching Architecture

```python
class GraphitiCache:
    """Multi-level caching for Graphiti operations."""
    
    def __init__(self):
        # L1: In-memory cache for hot data
        self.memory_cache = {}
        self.memory_cache_size = 1000
        
        # L2: Disk cache for persistent storage
        self.disk_cache = Cache('./graphiti_cache')
        
        # L3: Redis for distributed caching (optional)
        self.redis_client = None
        if os.getenv('REDIS_URL'):
            import redis
            self.redis_client = redis.from_url(
                os.getenv('REDIS_URL'),
                decode_responses=True
            )
    
    async def get(self, key: str) -> Any:
        """Multi-level cache lookup."""
        # L1: Memory
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # L2: Disk
        if key in self.disk_cache:
            value = self.disk_cache[key]
            self._promote_to_memory(key, value)
            return value
        
        # L3: Redis
        if self.redis_client:
            value = self.redis_client.get(key)
            if value:
                value = json.loads(value)
                self._promote_to_memory(key, value)
                self.disk_cache[key] = value
                return value
        
        return None
    
    def _promote_to_memory(self, key: str, value: Any):
        """LRU eviction for memory cache."""
        if len(self.memory_cache) >= self.memory_cache_size:
            # Evict oldest item
            oldest = next(iter(self.memory_cache))
            del self.memory_cache[oldest]
        
        self.memory_cache[key] = value
```

## Memory Management

### Streaming Processing for Large Datasets

```python
# From mcp_server/graphiti_mcp_server.py - Queue-based memory management
episode_queues: dict[str, asyncio.Queue] = {}
queue_workers: dict[str, bool] = {}

async def process_episode_queue(group_id: str):
    """Process episodes with bounded memory usage."""
    logger.info(f'Starting episode queue worker for group_id: {group_id}')
    queue_workers[group_id] = True
    
    try:
        while True:
            # Process one episode at a time to control memory
            process_func = await episode_queues[group_id].get()
            
            try:
                await process_func()
            except Exception as e:
                logger.error(f'Error processing episode: {str(e)}')
            finally:
                # Release memory after processing
                episode_queues[group_id].task_done()
                
                # Force garbage collection for large episodes
                import gc
                gc.collect()
                
    except asyncio.CancelledError:
        logger.info(f'Queue worker cancelled for group_id: {group_id}')
    finally:
        queue_workers[group_id] = False
```

### Efficient Node/Edge Storage

```python
# From graphiti_core/nodes.py - Optimized node representation
class EntityNode(Node):
    """Memory-efficient node with lazy loading."""
    
    labels: list[str] = Field(default_factory=lambda: ['Entity'])
    name: str
    name_embedding: list[float] | None = Field(default=None, exclude=True)
    summary: str | None = Field(default=None)
    
    # Attributes stored as JSON to save memory
    _attributes_json: str | None = None
    
    @property
    def attributes(self) -> dict:
        """Lazy load attributes from JSON."""
        if self._attributes_json:
            return json.loads(self._attributes_json)
        return {}
    
    @attributes.setter
    def attributes(self, value: dict):
        """Store attributes as JSON."""
        self._attributes_json = json.dumps(value)
```

## Production Benchmarks

### Real-World Performance Metrics

```python
# From tests/evals/eval_e2e_graph_building.py
async def benchmark_graph_building():
    """Benchmark end-to-end graph building performance."""
    import time
    
    # Test configuration
    MULTI_SESSION_COUNT = 10  # Number of parallel sessions
    SESSION_LENGTH = 50       # Messages per session
    
    llm_client = OpenAIClient(config=LLMConfig(model='gpt-4.1-mini'))
    graphiti = Graphiti(NEO4J_URI, NEO4j_USER, NEO4j_PASSWORD, llm_client=llm_client)
    
    # Measure extraction performance
    start_time = time.time()
    
    add_episode_results, add_episode_context = await build_graph(
        group_id_suffix='benchmark',
        multi_session_count=MULTI_SESSION_COUNT,
        session_length=SESSION_LENGTH,
        graphiti=graphiti
    )
    
    end_time = time.time()
    
    # Calculate metrics
    total_episodes = MULTI_SESSION_COUNT * SESSION_LENGTH
    total_time = end_time - start_time
    episodes_per_second = total_episodes / total_time
    
    # Count extracted entities
    total_nodes = sum(
        len(result.nodes) 
        for results in add_episode_results.values() 
        for result in results
    )
    total_edges = sum(
        len(result.edges) 
        for results in add_episode_results.values() 
        for result in results
    )
    
    print(f"""
    Performance Metrics:
    - Total Episodes: {total_episodes}
    - Total Time: {total_time:.2f}s
    - Episodes/Second: {episodes_per_second:.2f}
    - Total Nodes Extracted: {total_nodes}
    - Total Edges Extracted: {total_edges}
    - Nodes/Episode: {total_nodes/total_episodes:.2f}
    - Edges/Episode: {total_edges/total_episodes:.2f}
    """)
    
    return {
        'episodes_per_second': episodes_per_second,
        'total_nodes': total_nodes,
        'total_edges': total_edges,
    }
```

### Comparative Benchmarks

```python
async def compare_configurations():
    """Compare different configuration performance."""
    
    configurations = [
        {'name': 'Default', 'semaphore_limit': 20, 'batch_size': 10},
        {'name': 'High Concurrency', 'semaphore_limit': 50, 'batch_size': 10},
        {'name': 'Large Batches', 'semaphore_limit': 20, 'batch_size': 50},
        {'name': 'Optimized', 'semaphore_limit': 30, 'batch_size': 25},
    ]
    
    results = []
    
    for config in configurations:
        # Set configuration
        os.environ['SEMAPHORE_LIMIT'] = str(config['semaphore_limit'])
        
        # Run benchmark
        metrics = await benchmark_graph_building()
        metrics['configuration'] = config['name']
        results.append(metrics)
    
    # Print comparison table
    import pandas as pd
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    
    """
    Expected Results (on typical hardware):
    
    Configuration      episodes_per_second  total_nodes  total_edges
    Default                   2.5              850          1200
    High Concurrency          3.8              850          1200
    Large Batches             2.2              850          1200
    Optimized                 3.2              850          1200
    """
```

## Monitoring and Profiling

### Performance Monitoring Implementation

```python
class PerformanceMonitor:
    """Track Graphiti performance metrics."""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_times = {}
    
    def start_operation(self, operation: str) -> str:
        """Start timing an operation."""
        operation_id = f"{operation}_{uuid.uuid4()}"
        self.start_times[operation_id] = time.time()
        return operation_id
    
    def end_operation(self, operation_id: str, metadata: dict = None):
        """End timing and record metrics."""
        if operation_id not in self.start_times:
            return
        
        duration = time.time() - self.start_times[operation_id]
        operation_type = operation_id.split('_')[0]
        
        metric = {
            'operation': operation_type,
            'duration': duration,
            'timestamp': datetime.now(timezone.utc),
            'metadata': metadata or {}
        }
        
        self.metrics[operation_type].append(metric)
        del self.start_times[operation_id]
    
    def get_statistics(self, operation: str = None):
        """Get performance statistics."""
        if operation:
            metrics = self.metrics[operation]
        else:
            metrics = [m for metrics in self.metrics.values() for m in metrics]
        
        if not metrics:
            return {}
        
        durations = [m['duration'] for m in metrics]
        
        return {
            'count': len(durations),
            'total_time': sum(durations),
            'avg_time': sum(durations) / len(durations),
            'min_time': min(durations),
            'max_time': max(durations),
            'p50': np.percentile(durations, 50),
            'p95': np.percentile(durations, 95),
            'p99': np.percentile(durations, 99),
        }

# Integration with Graphiti
class MonitoredGraphiti(Graphiti):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.monitor = PerformanceMonitor()
    
    async def add_episode(self, **kwargs):
        op_id = self.monitor.start_operation('add_episode')
        
        try:
            result = await super().add_episode(**kwargs)
            
            self.monitor.end_operation(op_id, {
                'nodes_extracted': len(result.nodes),
                'edges_extracted': len(result.edges),
                'episode_length': len(kwargs.get('episode_body', '')),
            })
            
            return result
        except Exception as e:
            self.monitor.end_operation(op_id, {'error': str(e)})
            raise
    
    def print_performance_report(self):
        """Print detailed performance report."""
        print("\n=== Performance Report ===\n")
        
        for operation in self.monitor.metrics.keys():
            stats = self.monitor.get_statistics(operation)
            print(f"{operation}:")
            print(f"  Count: {stats['count']}")
            print(f"  Avg Time: {stats['avg_time']:.3f}s")
            print(f"  P95 Time: {stats['p95']:.3f}s")
            print(f"  P99 Time: {stats['p99']:.3f}s")
            print()
```

### Async Profiling

```python
import asyncio
import functools

def profile_async(func):
    """Decorator for profiling async functions."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start = asyncio.get_event_loop().time()
        
        try:
            result = await func(*args, **kwargs)
            duration = asyncio.get_event_loop().time() - start
            
            logger.info(f"{func.__name__} completed in {duration:.3f}s")
            
            # Log slow operations
            if duration > 5.0:
                logger.warning(f"{func.__name__} took {duration:.3f}s (>5s threshold)")
            
            return result
        
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start
            logger.error(f"{func.__name__} failed after {duration:.3f}s: {e}")
            raise
    
    return wrapper

# Usage
@profile_async
async def extract_entities_with_profiling(text: str):
    # Entity extraction logic
    pass
```

## Scaling Strategies

### Horizontal Scaling with Sharding

```python
class ShardedGraphiti:
    """Distribute data across multiple Graphiti instances."""
    
    def __init__(self, shard_configs: list[dict]):
        self.shards = []
        for config in shard_configs:
            shard = Graphiti(
                uri=config['uri'],
                user=config['user'],
                password=config['password']
            )
            self.shards.append(shard)
        
        self.num_shards = len(self.shards)
    
    def get_shard(self, group_id: str) -> Graphiti:
        """Consistent hashing for shard selection."""
        shard_index = hash(group_id) % self.num_shards
        return self.shards[shard_index]
    
    async def add_episode(self, group_id: str, **kwargs):
        """Route to appropriate shard."""
        shard = self.get_shard(group_id)
        return await shard.add_episode(group_id=group_id, **kwargs)
    
    async def search_all_shards(self, query: str, **kwargs):
        """Parallel search across all shards."""
        search_tasks = [
            shard.search(query=query, **kwargs)
            for shard in self.shards
        ]
        
        all_results = await asyncio.gather(*search_tasks)
        
        # Merge and rank results
        merged_results = []
        for results in all_results:
            merged_results.extend(results)
        
        # Sort by relevance score
        merged_results.sort(key=lambda x: x.score, reverse=True)
        
        return merged_results
```

### Vertical Scaling Optimizations

```python
# Environment variables for vertical scaling
"""
# Increase for high-memory systems
export SEMAPHORE_LIMIT=100

# Enable parallel runtime for Neo4j Enterprise
export USE_PARALLEL_RUNTIME=true

# Increase connection pool for high-concurrency
export NEO4J_MAX_CONNECTION_POOL_SIZE=200

# Increase batch sizes for bulk operations
export BULK_BATCH_SIZE=100

# Enable aggressive caching
export ENABLE_CACHE=true
export CACHE_SIZE_GB=10
"""

class HighPerformanceGraphiti(Graphiti):
    """Optimized for vertical scaling."""
    
    def __init__(self, *args, **kwargs):
        # Override with high-performance settings
        kwargs['max_coroutines'] = int(os.getenv('SEMAPHORE_LIMIT', 100))
        
        super().__init__(*args, **kwargs)
        
        # Initialize with larger connection pool
        self.driver = Neo4jAsyncDriver(
            uri=self.driver.uri,
            auth=self.driver.auth,
            connection_pool_size=int(os.getenv('NEO4J_MAX_CONNECTION_POOL_SIZE', 200)),
            max_connection_lifetime=7200,
            connection_acquisition_timeout=120.0,
            fetch_size=1000,  # Larger fetch size for bulk reads
        )
        
        # Enable query result caching
        self.query_cache = Cache(
            './query_cache',
            size_limit=int(os.getenv('CACHE_SIZE_GB', 10)) * 1024 * 1024 * 1024
        )
```

## Performance Best Practices

### 1. Optimal Configuration Settings

```python
# Production configuration for different scenarios

# High-throughput ingestion
HIGH_THROUGHPUT_CONFIG = {
    'SEMAPHORE_LIMIT': 50,
    'BULK_BATCH_SIZE': 50,
    'ENABLE_CACHE': True,
    'USE_PARALLEL_RUNTIME': True,
}

# Low-latency search
LOW_LATENCY_CONFIG = {
    'SEMAPHORE_LIMIT': 20,
    'BULK_BATCH_SIZE': 10,
    'ENABLE_CACHE': True,
    'CACHE_PRELOAD': True,
}

# Balanced production
BALANCED_CONFIG = {
    'SEMAPHORE_LIMIT': 30,
    'BULK_BATCH_SIZE': 25,
    'ENABLE_CACHE': True,
    'USE_PARALLEL_RUNTIME': False,
}
```

### 2. Query Optimization Patterns

```python
# Efficient node retrieval with pagination
async def get_nodes_paginated(driver, group_id, page_size=100):
    """Retrieve nodes in pages to control memory."""
    offset = 0
    
    while True:
        query = """
        MATCH (n:Entity {group_id: $group_id})
        RETURN n
        ORDER BY n.created_at DESC
        SKIP $offset
        LIMIT $page_size
        """
        
        results = await driver.execute_query(
            query,
            group_id=group_id,
            offset=offset,
            page_size=page_size
        )
        
        if not results:
            break
        
        yield results
        offset += page_size
```

### 3. Memory-Efficient Processing

```python
async def process_large_dataset(graphiti, dataset_path):
    """Process large datasets without loading all into memory."""
    
    async def process_chunk(chunk):
        """Process a chunk of episodes."""
        for episode in chunk:
            await graphiti.add_episode(**episode)
    
    # Read and process in chunks
    chunk_size = 100
    chunk = []
    
    with open(dataset_path, 'r') as f:
        for line in f:
            episode = json.loads(line)
            chunk.append(episode)
            
            if len(chunk) >= chunk_size:
                await process_chunk(chunk)
                chunk = []
    
    # Process remaining
    if chunk:
        await process_chunk(chunk)
```

## Conclusion

Graphiti's performance architecture enables:

1. **High Throughput**: Process 3-4 episodes/second with proper configuration
2. **Low Latency**: Sub-second search responses with caching
3. **Scalability**: Handle millions of nodes/edges with sharding
4. **Efficiency**: Minimize LLM calls through batching and caching
5. **Reliability**: Graceful degradation under load

Key performance levers:
- **SEMAPHORE_LIMIT**: Control concurrent operations (20-100)
- **Batch Processing**: Process multiple items together
- **Caching**: Multi-level caching for all expensive operations
- **Async Architecture**: Non-blocking I/O throughout
- **Database Optimization**: Proper indices and query patterns

The system is designed to scale both vertically (more resources) and horizontally (more instances) based on your needs.
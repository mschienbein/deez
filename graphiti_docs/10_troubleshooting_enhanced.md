# Graphiti Troubleshooting Guide - Deep Debugging with Real Issues

## Table of Contents
1. [Common Error Classes and Their Resolution](#common-error-classes-and-their-resolution)
2. [LLM Integration Issues and Debugging](#llm-integration-issues-and-debugging)
3. [Database Connection Problems](#database-connection-problems)
4. [Entity Extraction Failures](#entity-extraction-failures)
5. [Memory and Performance Issues](#memory-and-performance-issues)
6. [Validation and Schema Errors](#validation-and-schema-errors)
7. [Temporal Data Conflicts](#temporal-data-conflicts)
8. [Search and Retrieval Problems](#search-and-retrieval-problems)
9. [Community Detection Failures](#community-detection-failures)
10. [Migration and Data Import Issues](#migration-and-data-import-issues)
11. [Debugging Tools and Techniques](#debugging-tools-and-techniques)
12. [Production Monitoring Strategies](#production-monitoring-strategies)

## Common Error Classes and Their Resolution

### Understanding Graphiti's Exception Hierarchy

Graphiti defines a comprehensive exception hierarchy in `graphiti_core/errors.py` that helps identify specific failure modes. Here's the complete error taxonomy and how to handle each:

```python
# From graphiti_core/errors.py
class GraphitiError(Exception):
    """Base exception class for Graphiti Core."""

class EdgeNotFoundError(GraphitiError):
    """Raised when an edge is not found."""
    def __init__(self, uuid: str):
        self.message = f'edge {uuid} not found'
        super().__init__(self.message)

class NodeNotFoundError(GraphitiError):
    """Raised when a node is not found."""
    def __init__(self, uuid: str):
        self.message = f'node {uuid} not found'
        super().__init__(self.message)

class GroupIdValidationError(GraphitiError):
    """Raised when a group_id contains invalid characters."""
    def __init__(self, group_id: str):
        self.message = f'group_id "{group_id}" must contain only alphanumeric characters, dashes, or underscores'
        super().__init__(self.message)

class EntityTypeValidationError(GraphitiError):
    """Raised when an entity type uses protected attribute names."""
    def __init__(self, entity_type: str, entity_type_attribute: str):
        self.message = f'{entity_type_attribute} cannot be used as an attribute for {entity_type} as it is a protected attribute name.'
        super().__init__(self.message)
```

### Real-World Error Handling Patterns

The MCP server implementation shows practical error handling patterns used in production:

```python
# From mcp_server/graphiti_mcp_server.py
async def process_episode_task(
    name: str,
    content: str,
    source_description: str,
    group_id_str: str
) -> EpisodeResponse | ErrorResponse:
    try:
        # Validate inputs
        if not group_id_str:
            return ErrorResponse(error='group_id is required')
        
        # Get or create graphiti instance
        async with graphiti_instances_lock:
            if group_id_str not in graphiti_instances:
                try:
                    graphiti_instances[group_id_str] = await initialize_graphiti(group_id_str)
                except Exception as e:
                    logger.error(f'Failed to initialize Graphiti for group_id {group_id_str}: {str(e)}')
                    return ErrorResponse(error=f'Failed to initialize Graphiti: {str(e)}')
        
        # Process the episode
        graphiti = graphiti_instances[group_id_str]
        result = await graphiti.add_episode(
            name=name,
            episode_body=content,
            source_description=source_description,
            reference_time=datetime.now(UTC)
        )
        
        logger.info(f"Episode '{name}' processed successfully")
        return EpisodeResponse(
            message=f"Episode '{name}' processed successfully",
            entity_count=result.entity_count if result else 0,
            relation_count=result.relation_count if result else 0
        )
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error processing episode '{name}' for group_id {group_id_str}: {error_msg}")
        return ErrorResponse(error=f"Error processing episode: {error_msg}")
```

## LLM Integration Issues and Debugging

### LLM-Specific Error Classes

Graphiti defines specific exceptions for LLM failures in `graphiti_core/llm_client/errors.py`:

```python
class RateLimitError(Exception):
    """Exception raised when the rate limit is exceeded."""
    def __init__(self, message='Rate limit exceeded. Please try again later.'):
        self.message = message
        super().__init__(self.message)

class RefusalError(Exception):
    """Exception raised when the LLM refuses to generate a response."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)

class EmptyResponseError(Exception):
    """Exception raised when the LLM returns an empty response."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
```

### Handling Rate Limits with Exponential Backoff

The OpenAI reranker client shows how to handle rate limits gracefully:

```python
# From graphiti_core/cross_encoder/openai_reranker_client.py
async def score_passages(
    self,
    query: str,
    passages: list[tuple[str, str]]
) -> list[tuple[str, float]]:
    try:
        # Prepare batch request
        tasks = []
        for uuid, passage in passages:
            prompt = self._format_prompt(query, passage)
            tasks.append(self._score_single_passage(prompt, uuid))
        
        # Execute with retry logic
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle failures
        scored_passages = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f'Error in generating LLM response: {result}')
                # Return low score for failed passages
                scored_passages.append((uuid, 0.0))
            else:
                scored_passages.append(result)
                
        return scored_passages
        
    except Exception as e:
        logger.error(f'Error in generating LLM response: {e}')
        raise
```

### Debugging Token Limit Issues

For Gemini models, Graphiti tracks token limits per model:

```python
# From graphiti_core/llm_client/gemini_client.py
# Maximum output tokens for different Gemini models
GEMINI_MODEL_MAX_TOKENS = {
    'gemini-1.5-flash': 8192,
    'gemini-1.5-flash-8b': 8192,
    'gemini-1.5-pro': 8192,
    'gemini-2.0-flash-exp': 8192,
    'gemini-exp-1206': 8192,
}

# Default max tokens for models not in the mapping
DEFAULT_MAX_TOKENS = 2000

def _resolve_max_tokens(self, requested_max_tokens: int | None, model: str) -> int:
    """
    Resolve the maximum output tokens to use based on precedence rules.
    
    Precedence order:
    1. Explicit max_tokens parameter passed to generate_response()
    2. Instance max_tokens set during client initialization
    3. Model-specific default from GEMINI_MODEL_MAX_TOKENS
    4. Global DEFAULT_MAX_TOKENS as fallback
    """
    if requested_max_tokens is not None:
        return requested_max_tokens
    
    if self.max_tokens is not None:
        return self.max_tokens
    
    return self._get_max_tokens_for_model(model)
```

### Debugging LLM Response Parsing

When LLM responses don't match expected formats:

```python
# From graphiti_core/cross_encoder/gemini_reranker_client.py
try:
    response = await self.client.generate_text_async(
        prompt=prompt,
        generation_config=genai.GenerationConfig(
            temperature=0.0,
            max_output_tokens=3,
        ),
    )
    
    if response and response.text:
        try:
            # Try to extract numeric score
            score_text = response.text.strip()
            score = float(score_text)
            return (uuid, score)
        except ValueError:
            logger.warning(f'Could not parse score from response: {score_text}')
            # Check for True/False response
            if score_text.lower() == 'true':
                return (uuid, 1.0)
            elif score_text.lower() == 'false':
                return (uuid, 0.0)
    else:
        logger.warning('Empty response from Gemini for passage scoring')
        
except Exception as e:
    logger.warning(f'Error parsing score from Gemini response: {e}')
    return (uuid, 0.0)  # Default to low score on error
```

## Database Connection Problems

### Neo4j Connection Validation

The MCP server shows comprehensive Neo4j configuration validation:

```python
# From mcp_server/graphiti_mcp_server.py
class Neo4jConfig(BaseModel):
    """Configuration for Neo4j database connection."""
    uri: str = 'bolt://localhost:7687'
    user: str = 'neo4j'
    password: str = 'password'
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables."""
        return cls(
            uri=os.environ.get('NEO4J_URI', 'bolt://localhost:7687'),
            user=os.environ.get('NEO4J_USER', 'neo4j'),
            password=os.environ.get('NEO4J_PASSWORD', 'password'),
        )

async def initialize_graphiti(group_id: str | None = None) -> Graphiti:
    """Initialize a Graphiti instance with comprehensive error handling."""
    try:
        # Load configuration
        config = GraphitiConfig.from_env()
        
        # Validate Neo4j configuration
        if not config.neo4j.uri or not config.neo4j.user or not config.neo4j.password:
            raise ValueError('NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set')
        
        # Create driver with connection testing
        driver = Neo4jDriver(
            uri=config.neo4j.uri,
            user=config.neo4j.user,
            password=config.neo4j.password
        )
        
        # Test connection
        await driver.verify_connection()
        
        # Initialize Graphiti
        graphiti = Graphiti(
            graph_driver=driver,
            llm_client=llm_client,
            embedder=embedder,
            entity_types=entity_types if config.use_custom_entities else None
        )
        
        await graphiti.build_indices()
        logger.info(f'Graphiti initialized successfully for group_id: {group_id}')
        return graphiti
        
    except Exception as e:
        logger.error(f'Failed to initialize Graphiti: {str(e)}')
        raise
```

### Connection Pool Management

For production environments, manage connection pools carefully:

```python
# Best practice for Neo4j connection management
from neo4j import AsyncGraphDatabase
from contextlib import asynccontextmanager

class Neo4jConnectionManager:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(
            uri,
            auth=(user, password),
            max_connection_pool_size=50,
            connection_timeout=30,
            max_transaction_retry_time=30
        )
    
    @asynccontextmanager
    async def get_session(self):
        async with self.driver.session() as session:
            yield session
    
    async def verify_connection(self):
        """Test database connectivity."""
        try:
            async with self.get_session() as session:
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                if record['test'] != 1:
                    raise ConnectionError("Database connection test failed")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise
    
    async def close(self):
        await self.driver.close()
```

## Entity Extraction Failures

### Debugging Entity Extraction Pipeline

The entity extraction process can fail at multiple points. Here's how to debug each stage:

```python
# From graphiti_core/utils/maintenance/node_operations.py
async def extract_new_nodes(
    context: str,
    episode_type: EpisodeType,
    llm_client: LLMClient,
    episode: EpisodicNode,
    custom_entity_types: list[EntityType] | None = None,
    excluded_entity_types: list[str] | None = None,
    episodes_context: dict[str, RawEpisode] | None = None,
) -> list[EntityNode]:
    """Extract new entity nodes with comprehensive error handling."""
    
    # Stage 1: LLM extraction
    start = time()
    try:
        llm_response = await llm_client.generate_response(
            messages=[
                {'role': 'system', 'content': entity_extract_system_prompt},
                {'role': 'user', 'content': entity_extract_prompt(
                    context,
                    episode.content,
                    episode.created_at,
                    custom_entity_types
                )}
            ]
        )
    except (RateLimitError, RefusalError, EmptyResponseError) as e:
        logger.error(f"LLM extraction failed: {e}")
        return []
    
    end = time()
    logger.debug(f'Extracted new nodes: {llm_response.response_data} in {(end - start) * 1000} ms')
    
    # Stage 2: Parse extracted entities
    try:
        extracted_entities = llm_response.response_data.get('extracted_entities', [])
    except AttributeError:
        logger.error("Invalid LLM response format")
        return []
    
    # Stage 3: Filter excluded entity types
    extracted_nodes = []
    for extracted_entity in extracted_entities:
        entity_type_name = extracted_entity.get('entity_type')
        
        if excluded_entity_types and entity_type_name in excluded_entity_types:
            logger.debug(f'Excluding entity "{extracted_entity.get("name")}" of type "{entity_type_name}"')
            continue
        
        # Stage 4: Create node with validation
        try:
            new_node = EntityNode(
                name=extracted_entity['name'],
                labels=[entity_type_name] if entity_type_name else [],
                episode_uuids=[episode.uuid],
                created_at=episode.created_at,
            )
            logger.debug(f'Created new node: {new_node.name} (UUID: {new_node.uuid})')
            extracted_nodes.append(new_node)
        except KeyError as e:
            logger.error(f"Missing required field in extracted entity: {e}")
            continue
    
    logger.debug(f'Extracted nodes: {[(n.name, n.uuid) for n in extracted_nodes]}')
    return extracted_nodes
```

### Entity Type Validation Errors

Graphiti validates entity types to prevent conflicts with reserved attributes:

```python
# From graphiti_core/helpers.py
def validate_excluded_entity_types(
    excluded_entity_types: list[str] | None,
    entity_types: list[EntityType] | None
) -> None:
    """
    Validate that excluded entity types are valid.
    
    Raises:
        ValueError: If any excluded type names are invalid
    """
    if not excluded_entity_types:
        return
    
    # Get available entity type names
    available_types = set()
    if entity_types:
        available_types = {et.name for et in entity_types}
    
    # Check for invalid exclusions
    invalid_types = set(excluded_entity_types) - available_types
    if invalid_types:
        raise ValueError(
            f'Invalid excluded entity types: {sorted(invalid_types)}. '
            f'Available types: {sorted(available_types)}'
        )
```

### Debugging Entity Resolution Failures

When entities aren't properly deduplicated:

```python
# From graphiti_core/utils/maintenance/node_operations.py
async def dedupe_extracted_nodes(
    llm_client: LLMClient,
    extracted_nodes: list[EntityNode],
    existing_nodes: list[EntityNode],
    episodes_context: dict[str, RawEpisode] | None = None,
) -> tuple[list[DuplicateNodeInfo], list[EntityNode]]:
    """Debug entity deduplication issues."""
    
    # Log input state
    logger.info(f"Deduplicating {len(extracted_nodes)} extracted nodes against {len(existing_nodes)} existing nodes")
    
    # Track deduplication decisions
    duplicate_pairs = []
    unique_nodes = []
    
    for extracted_node in extracted_nodes:
        # Find potential duplicates
        candidates = [
            existing for existing in existing_nodes
            if similar_entity_name(extracted_node.name, existing.name)
        ]
        
        if candidates:
            # Use LLM to resolve
            is_duplicate = await llm_client.dedupe_entities(
                extracted_node,
                candidates,
                episodes_context
            )
            
            if is_duplicate:
                duplicate_pairs.append(DuplicateNodeInfo(
                    original_node=candidates[0],
                    duplicate_node=extracted_node
                ))
                logger.debug(f"Node '{extracted_node.name}' is duplicate of '{candidates[0].name}'")
            else:
                unique_nodes.append(extracted_node)
                logger.debug(f"Node '{extracted_node.name}' is unique")
        else:
            unique_nodes.append(extracted_node)
    
    logger.info(f"Deduplication complete: {len(duplicate_pairs)} duplicates, {len(unique_nodes)} unique")
    return duplicate_pairs, unique_nodes
```

## Memory and Performance Issues

### Debugging Memory Leaks

Monitor memory usage in long-running processes:

```python
# Memory profiling for Graphiti operations
import tracemalloc
import asyncio
from graphiti_core import Graphiti

async def profile_memory_usage():
    """Profile memory usage during episode processing."""
    tracemalloc.start()
    
    # Baseline snapshot
    snapshot1 = tracemalloc.take_snapshot()
    
    # Process episodes
    graphiti = await initialize_graphiti()
    for i in range(100):
        await graphiti.add_episode(
            name=f"Episode {i}",
            episode_body=f"Content for episode {i}",
            source_description="Memory test"
        )
        
        if i % 10 == 0:
            # Take snapshot every 10 episodes
            snapshot2 = tracemalloc.take_snapshot()
            top_stats = snapshot2.compare_to(snapshot1, 'lineno')
            
            print(f"\n[ Top 10 memory allocations after {i} episodes ]")
            for stat in top_stats[:10]:
                print(stat)
    
    tracemalloc.stop()
```

### Optimizing Embedding Generation

The embedding process includes performance monitoring:

```python
# From graphiti_core/nodes.py
async def generate_embedding(self, embedder: EmbedderClient) -> list[float]:
    """Generate embedding with performance tracking."""
    text = self.name
    if self.summary != '':
        text = f'{self.name} {self.summary}'
    
    start = time()
    embedding = await embedder.create_embedding(text)
    end = time()
    
    logger.debug(f'embedded {text} in {end - start} ms')
    
    # Monitor slow embeddings
    if (end - start) > 1.0:  # More than 1 second
        logger.warning(f'Slow embedding generation for text of length {len(text)}: {end - start}s')
    
    return embedding
```

### Handling Large-Scale Batch Operations

For bulk operations, use semaphore-controlled concurrency:

```python
# From graphiti_core/graphiti.py
async def add_episode_bulk(
    self,
    episodes: list[RawEpisode],
    group_id: str,
    entity_types: list[EntityType] | None = None
) -> EpisodeProcessingResult:
    """Process episodes in bulk with memory management."""
    
    # Process in batches to avoid memory exhaustion
    BATCH_SIZE = 10
    all_results = []
    
    for i in range(0, len(episodes), BATCH_SIZE):
        batch = episodes[i:i + BATCH_SIZE]
        
        # Process batch with controlled concurrency
        async with asyncio.Semaphore(5):  # Limit concurrent operations
            tasks = [
                self._process_single_episode(episode, group_id, entity_types)
                for episode in batch
            ]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results and errors
        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Episode processing failed: {result}")
            else:
                all_results.append(result)
        
        # Force garbage collection between batches
        import gc
        gc.collect()
    
    return self._aggregate_results(all_results)
```

## Validation and Schema Errors

### Group ID Validation

Graphiti enforces strict group ID validation to prevent injection attacks:

```python
# From graphiti_core/helpers.py
def validate_group_id(group_id: str) -> bool:
    """
    Validate that a group_id contains only allowed characters.
    
    Args:
        group_id: The group_id to validate
        
    Returns:
        True if valid
        
    Raises:
        GroupIdValidationError: If group_id contains invalid characters
    """
    # Pattern matches: letters (a-z, A-Z), digits (0-9), hyphens (-), and underscores (_)
    if not re.match(r'^[a-zA-Z0-9_-]+$', group_id):
        raise GroupIdValidationError(group_id)
    
    return True

# Usage with error handling
try:
    validate_group_id(user_provided_group_id)
except GroupIdValidationError as e:
    logger.error(f"Invalid group_id: {e}")
    return {"error": "Group ID must contain only alphanumeric characters, dashes, or underscores"}
```

### Entity Type Schema Validation

Protect against schema conflicts:

```python
# From graphiti_core/utils/ontology_utils/entity_types_utils.py
def validate_entity_types(entity_types: list[EntityType]) -> None:
    """Validate entity types don't use protected attributes."""
    
    PROTECTED_ATTRIBUTES = {
        'uuid', 'name', 'summary', 'created_at', 'updated_at',
        'valid_from', 'valid_to', 'embedding', 'group_id'
    }
    
    for entity_type in entity_types:
        for attribute in entity_type.attributes:
            if attribute.name in PROTECTED_ATTRIBUTES:
                raise EntityTypeValidationError(
                    entity_type.name,
                    attribute.name
                )
```

## Temporal Data Conflicts

### Debugging Temporal Invalidation

When edges aren't properly invalidated:

```python
# From graphiti_core/utils/maintenance/temporal_operations.py
async def invalidate_edges(
    driver: GraphProvider,
    entity_edges: list[EntityEdge],
    group_id: str
) -> list[EntityEdge]:
    """Debug temporal edge invalidation."""
    
    invalidated_edges = []
    current_time = datetime.now(UTC)
    
    for edge in entity_edges:
        # Log invalidation decision
        logger.debug(
            f"Invalidating edge: {edge.name} (UUID: {edge.uuid}) at {current_time}"
        )
        
        # Set valid_to timestamp
        edge.valid_to = current_time
        
        # Persist to database
        await driver.update_edge(edge, group_id)
        invalidated_edges.append(edge)
        
        # Verify invalidation
        retrieved = await driver.get_edge(edge.uuid, group_id)
        if retrieved.valid_to != current_time:
            logger.error(f"Failed to invalidate edge {edge.uuid}")
    
    logger.info(f"Invalidated {len(invalidated_edges)} edges")
    return invalidated_edges
```

### Resolving Time-Based Query Issues

Debug point-in-time queries:

```python
# Debugging temporal queries
async def debug_temporal_query(
    driver: GraphProvider,
    group_id: str,
    reference_time: datetime
):
    """Debug what data is visible at a specific point in time."""
    
    # Query all nodes valid at reference_time
    nodes_query = """
    MATCH (n:Entity {group_id: $group_id})
    WHERE n.valid_from <= $reference_time 
      AND (n.valid_to IS NULL OR n.valid_to > $reference_time)
    RETURN n
    """
    
    nodes = await driver.query(nodes_query, {
        'group_id': group_id,
        'reference_time': reference_time
    })
    
    logger.info(f"Found {len(nodes)} valid nodes at {reference_time}")
    
    # Query all edges valid at reference_time
    edges_query = """
    MATCH ()-[r:RELATES_TO {group_id: $group_id}]->()
    WHERE r.valid_from <= $reference_time
      AND (r.valid_to IS NULL OR r.valid_to > $reference_time)
    RETURN r
    """
    
    edges = await driver.query(edges_query, {
        'group_id': group_id,
        'reference_time': reference_time
    })
    
    logger.info(f"Found {len(edges)} valid edges at {reference_time}")
    
    return nodes, edges
```

## Search and Retrieval Problems

### Debugging Search Relevance

When search results aren't relevant:

```python
# From graphiti_core/search/search_utils.py
async def get_relevant_nodes(
    query: str,
    driver: GraphProvider,
    embedder: EmbedderClient,
    group_ids: list[str],
    search_method: SearchMethod,
    reranker: RerankingProvider | None = None
) -> SearchResults:
    """Debug search relevance issues."""
    
    # Log search parameters
    logger.info(f"Searching for: '{query}'")
    logger.info(f"Method: {search_method}, Groups: {group_ids}")
    
    # Stage 1: Embedding generation
    start = time()
    query_embedding = await embedder.create_embedding(query)
    logger.debug(f"Generated embedding in {(time() - start) * 1000}ms")
    
    # Stage 2: Vector search
    vector_results = await driver.vector_search(
        query_embedding,
        group_ids,
        limit=100
    )
    logger.debug(f"Vector search returned {len(vector_results)} results")
    
    # Stage 3: BM25 search
    bm25_results = await driver.fulltext_search(
        query,
        group_ids,
        limit=100
    )
    logger.debug(f"BM25 search returned {len(bm25_results)} results")
    
    # Stage 4: Fusion
    if search_method == SearchMethod.HYBRID:
        fused_results = reciprocal_rank_fusion(
            vector_results,
            bm25_results,
            k=60
        )
        logger.debug(f"RRF fusion produced {len(fused_results)} results")
    
    # Stage 5: Reranking
    if reranker:
        reranked = await reranker.rerank(query, fused_results)
        logger.debug(f"Reranking complete, top score: {reranked[0][1] if reranked else 0}")
    
    end = time()
    logger.debug(f'Found relevant nodes: {[r.uuid for r in fused_results[:5]]} in {(end - start) * 1000} ms')
    
    return fused_results
```

### Search Reranker Errors

Handle reranking failures gracefully:

```python
# From graphiti_core/search/search.py
async def search_with_reranking(
    query: str,
    reranker: CrossEncoderClient
) -> list[SearchResult]:
    """Search with fallback when reranking fails."""
    
    try:
        # Get initial results
        initial_results = await get_relevant_nodes(query)
        
        # Attempt reranking
        try:
            reranked = await reranker.rerank(query, initial_results)
            return reranked
        except SearchRerankerError as e:
            logger.warning(f"Reranking failed: {e}, using original results")
            return initial_results
            
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise
```

## Community Detection Failures

### Debugging Label Propagation

When communities aren't forming correctly:

```python
# From graphiti_core/utils/maintenance/community_operations.py
async def build_community_nodes(
    driver: GraphProvider,
    nodes: list[EntityNode],
    edges: list[EntityEdge],
    group_id: str,
    llm_client: LLMClient | None = None
) -> tuple[list[CommunityNode], list[CommunityEdge]]:
    """Debug community detection failures."""
    
    logger.info(f"Building communities for {len(nodes)} nodes and {len(edges)} edges")
    
    # Stage 1: Build adjacency matrix
    node_ids = [node.uuid for node in nodes]
    adjacency_matrix = build_adjacency_matrix(nodes, edges)
    
    logger.debug(f"Adjacency matrix density: {adjacency_matrix.nnz / (len(nodes) ** 2):.4f}")
    
    # Stage 2: Run label propagation
    try:
        labels = label_propagation(adjacency_matrix)
        logger.debug(f"Label propagation found {len(set(labels))} communities")
    except Exception as e:
        logger.error(f"Label propagation failed: {e}")
        return [], []
    
    # Stage 3: Create community nodes
    communities = defaultdict(list)
    for i, label in enumerate(labels):
        communities[label].append(nodes[i])
    
    # Log community sizes
    for label, members in communities.items():
        logger.debug(f"Community {label}: {len(members)} members")
    
    # Stage 4: Generate summaries
    community_nodes = []
    for label, member_nodes in communities.items():
        if len(member_nodes) < 2:
            logger.debug(f"Skipping community {label} with only {len(member_nodes)} members")
            continue
        
        # Create community node
        community = CommunityNode(
            name=f"Community_{label}",
            labels=["COMMUNITY"],
            members=[n.uuid for n in member_nodes],
            created_at=datetime.now(UTC),
            group_id=group_id
        )
        
        # Generate summary if LLM available
        if llm_client:
            try:
                summary = await generate_community_summary(
                    llm_client,
                    member_nodes,
                    edges
                )
                community.summary = summary
            except Exception as e:
                logger.warning(f"Failed to generate summary for community {label}: {e}")
        
        community_nodes.append(community)
    
    logger.info(f"Created {len(community_nodes)} community nodes")
    return community_nodes, []
```

### Community Summary Generation Failures

Debug LLM-based community summarization:

```python
async def generate_community_summary(
    llm_client: LLMClient,
    nodes: list[EntityNode],
    edges: list[EntityEdge]
) -> str:
    """Generate community summary with error handling."""
    
    # Prepare context
    node_descriptions = [f"- {node.name}: {node.summary}" for node in nodes[:20]]
    edge_descriptions = [
        f"- {edge.source_name} {edge.name} {edge.target_name}"
        for edge in edges[:20]
    ]
    
    prompt = f"""
    Summarize this community of entities:
    
    Entities:
    {chr(10).join(node_descriptions)}
    
    Relationships:
    {chr(10).join(edge_descriptions)}
    
    Provide a concise summary of what this community represents.
    """
    
    try:
        response = await llm_client.generate_response(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        return response.content
    except Exception as e:
        logger.error(f"Community summary generation failed: {e}")
        # Fallback to basic summary
        return f"Community of {len(nodes)} related entities"
```

## Migration and Data Import Issues

### Handling Large Data Imports

When importing fails due to size:

```python
# Chunked import strategy
async def import_large_dataset(
    graphiti: Graphiti,
    data_file: str,
    chunk_size: int = 100
):
    """Import large dataset with progress tracking and error recovery."""
    
    import json
    from pathlib import Path
    
    # Load data
    data_path = Path(data_file)
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    with open(data_path) as f:
        all_episodes = json.load(f)
    
    total = len(all_episodes)
    logger.info(f"Starting import of {total} episodes")
    
    # Track progress
    successful = 0
    failed = []
    
    # Process in chunks
    for i in range(0, total, chunk_size):
        chunk = all_episodes[i:i + chunk_size]
        chunk_num = i // chunk_size + 1
        
        logger.info(f"Processing chunk {chunk_num} ({i}-{min(i + chunk_size, total)} of {total})")
        
        # Process chunk with retry
        for attempt in range(3):
            try:
                results = await graphiti.add_episode_bulk(
                    episodes=[
                        RawEpisode(
                            name=ep['name'],
                            content=ep['content'],
                            source_description=ep.get('source', 'Import'),
                            reference_time=datetime.fromisoformat(ep['timestamp'])
                        )
                        for ep in chunk
                    ],
                    group_id="import"
                )
                successful += len(chunk)
                break
            except Exception as e:
                logger.warning(f"Chunk {chunk_num} attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    failed.extend([(i + j, ep['name']) for j, ep in enumerate(chunk)])
                else:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    # Report results
    logger.info(f"Import complete: {successful} successful, {len(failed)} failed")
    if failed:
        logger.error(f"Failed episodes: {failed[:10]}...")  # Show first 10
    
    return successful, failed
```

### Schema Migration Errors

Handle schema evolution during migration:

```python
# Schema migration with validation
async def migrate_schema(
    source_driver: GraphProvider,
    target_driver: GraphProvider,
    group_id: str
):
    """Migrate schema with compatibility checking."""
    
    # Stage 1: Extract source schema
    source_schema = await source_driver.get_schema()
    logger.info(f"Source schema: {source_schema}")
    
    # Stage 2: Check target compatibility
    target_schema = await target_driver.get_schema()
    
    # Find incompatibilities
    missing_node_labels = set(source_schema['node_labels']) - set(target_schema['node_labels'])
    missing_edge_types = set(source_schema['edge_types']) - set(target_schema['edge_types'])
    
    if missing_node_labels or missing_edge_types:
        logger.warning(f"Schema differences detected:")
        logger.warning(f"Missing node labels: {missing_node_labels}")
        logger.warning(f"Missing edge types: {missing_edge_types}")
        
        # Create missing schema elements
        for label in missing_node_labels:
            await target_driver.create_constraint(f"CREATE CONSTRAINT FOR (n:{label}) REQUIRE n.uuid IS UNIQUE")
        
        for edge_type in missing_edge_types:
            await target_driver.create_index(f"CREATE INDEX FOR ()-[r:{edge_type}]->() ON (r.group_id)")
    
    # Stage 3: Migrate data with validation
    nodes = await source_driver.get_all_nodes(group_id)
    edges = await source_driver.get_all_edges(group_id)
    
    logger.info(f"Migrating {len(nodes)} nodes and {len(edges)} edges")
    
    # Validate and transform data
    for node in nodes:
        try:
            # Add any missing required fields
            if not hasattr(node, 'embedding'):
                node.embedding = [0.0] * 768  # Default embedding
            
            await target_driver.create_node(node)
        except Exception as e:
            logger.error(f"Failed to migrate node {node.uuid}: {e}")
    
    for edge in edges:
        try:
            await target_driver.create_edge(edge)
        except Exception as e:
            logger.error(f"Failed to migrate edge {edge.uuid}: {e}")
```

## Debugging Tools and Techniques

### Comprehensive Logging Strategy

Enable detailed logging for debugging:

```python
# Configure logging for debugging
import logging
import sys
from pathlib import Path

def setup_debug_logging(log_file: str = "graphiti_debug.log"):
    """Configure comprehensive logging for debugging."""
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter('%(levelname)s - %(message)s')
    
    # File handler for detailed logs
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Console handler for important messages
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    
    # Configure loggers
    loggers = [
        'graphiti_core',
        'graphiti_core.search',
        'graphiti_core.utils.maintenance',
        'graphiti_core.llm_client',
        'graphiti_core.driver'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    # Log configuration
    logger = logging.getLogger('graphiti_core')
    logger.info(f"Debug logging configured, writing to {log_file}")

# Use in debugging sessions
if __name__ == "__main__":
    setup_debug_logging()
    
    # Your debugging code here
    graphiti = await initialize_graphiti()
    # ... debug operations
```

### Query Performance Analysis

Analyze slow queries:

```python
# From graphiti_core/driver/neo4j_driver.py
async def analyze_query_performance(
    driver: Neo4jDriver,
    query: str,
    params: dict
):
    """Analyze query performance using EXPLAIN and PROFILE."""
    
    # Get query plan
    explain_query = f"EXPLAIN {query}"
    plan = await driver.query(explain_query, params)
    logger.info(f"Query plan: {plan}")
    
    # Profile query execution
    profile_query = f"PROFILE {query}"
    start = time()
    profile = await driver.query(profile_query, params)
    duration = time() - start
    
    # Extract metrics
    db_hits = profile.summary.counters.db_hits
    rows = profile.summary.counters.rows
    
    logger.info(f"Query execution: {duration:.3f}s, DB hits: {db_hits}, Rows: {rows}")
    
    # Check for common issues
    if db_hits > 10000:
        logger.warning("High DB hits - consider adding indexes")
    
    if duration > 1.0:
        logger.warning("Slow query - consider optimization")
    
    return {
        'duration': duration,
        'db_hits': db_hits,
        'rows': rows,
        'plan': plan
    }
```

### Memory Profiling

Track memory usage in production:

```python
# Memory monitoring utility
import psutil
import os

class MemoryMonitor:
    def __init__(self, threshold_mb: int = 1000):
        self.process = psutil.Process(os.getpid())
        self.threshold_bytes = threshold_mb * 1024 * 1024
        self.baseline = self.get_memory_usage()
    
    def get_memory_usage(self) -> int:
        """Get current memory usage in bytes."""
        return self.process.memory_info().rss
    
    def check_memory(self, operation: str):
        """Check memory usage and log if above threshold."""
        current = self.get_memory_usage()
        increase = current - self.baseline
        
        if increase > self.threshold_bytes:
            mb_increase = increase / (1024 * 1024)
            logger.warning(
                f"High memory usage after {operation}: "
                f"+{mb_increase:.2f}MB (total: {current / (1024 * 1024):.2f}MB)"
            )
    
    def reset_baseline(self):
        """Reset the baseline memory measurement."""
        self.baseline = self.get_memory_usage()

# Usage in Graphiti operations
monitor = MemoryMonitor(threshold_mb=500)

async def monitored_episode_processing(graphiti: Graphiti, episodes: list):
    """Process episodes with memory monitoring."""
    
    for i, episode in enumerate(episodes):
        await graphiti.add_episode(
            name=episode.name,
            episode_body=episode.content,
            source_description=episode.source
        )
        
        # Check memory every 10 episodes
        if i % 10 == 0:
            monitor.check_memory(f"episode_{i}")
```

## Production Monitoring Strategies

### Health Check Implementation

Implement comprehensive health checks:

```python
# Health check endpoint for production monitoring
from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta

app = FastAPI()

@app.get("/health")
async def health_check():
    """Comprehensive health check for Graphiti deployment."""
    
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": {}
    }
    
    # Check 1: Database connectivity
    try:
        await graphiti.driver.verify_connection()
        health_status["checks"]["database"] = "ok"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = f"failed: {str(e)}"
    
    # Check 2: LLM client
    try:
        test_response = await graphiti.llm_client.generate_response(
            messages=[{"role": "user", "content": "test"}],
            max_tokens=1
        )
        health_status["checks"]["llm"] = "ok"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["llm"] = f"failed: {str(e)}"
    
    # Check 3: Embedder
    try:
        test_embedding = await graphiti.embedder.create_embedding("test")
        health_status["checks"]["embedder"] = "ok"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["checks"]["embedder"] = f"failed: {str(e)}"
    
    # Check 4: Memory usage
    memory_mb = psutil.Process().memory_info().rss / (1024 * 1024)
    if memory_mb > 2000:  # 2GB threshold
        health_status["status"] = "degraded"
        health_status["checks"]["memory"] = f"high: {memory_mb:.2f}MB"
    else:
        health_status["checks"]["memory"] = f"ok: {memory_mb:.2f}MB"
    
    # Check 5: Recent processing success rate
    recent_errors = await get_recent_error_count()
    if recent_errors > 10:
        health_status["status"] = "degraded"
        health_status["checks"]["processing"] = f"high error rate: {recent_errors} errors"
    else:
        health_status["checks"]["processing"] = "ok"
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status
```

### Metrics Collection

Implement metrics for monitoring:

```python
# Prometheus metrics for Graphiti
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
episode_counter = Counter('graphiti_episodes_total', 'Total episodes processed')
episode_errors = Counter('graphiti_episode_errors_total', 'Total episode processing errors')
processing_time = Histogram('graphiti_processing_seconds', 'Episode processing time')
active_groups = Gauge('graphiti_active_groups', 'Number of active group IDs')
node_count = Gauge('graphiti_nodes_total', 'Total number of nodes', ['group_id'])
edge_count = Gauge('graphiti_edges_total', 'Total number of edges', ['group_id'])

# Instrumented episode processing
async def process_episode_with_metrics(
    graphiti: Graphiti,
    episode: RawEpisode,
    group_id: str
):
    """Process episode with metrics collection."""
    
    start_time = time.time()
    
    try:
        result = await graphiti.add_episode(
            name=episode.name,
            episode_body=episode.content,
            source_description=episode.source,
            reference_time=episode.reference_time
        )
        
        # Update metrics
        episode_counter.inc()
        processing_time.observe(time.time() - start_time)
        
        # Update graph size metrics
        nodes = await graphiti.driver.get_node_count(group_id)
        edges = await graphiti.driver.get_edge_count(group_id)
        node_count.labels(group_id=group_id).set(nodes)
        edge_count.labels(group_id=group_id).set(edges)
        
        return result
        
    except Exception as e:
        episode_errors.inc()
        processing_time.observe(time.time() - start_time)
        logger.error(f"Episode processing failed: {e}")
        raise
```

### Alert Configuration

Set up alerting for critical issues:

```python
# Alert manager configuration
class AlertManager:
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url
        self.alert_thresholds = {
            'error_rate': 0.1,  # 10% error rate
            'processing_time': 5.0,  # 5 seconds
            'memory_usage': 0.9,  # 90% of available memory
            'queue_size': 1000  # 1000 pending episodes
        }
    
    async def check_and_alert(self, metrics: dict):
        """Check metrics and send alerts if thresholds exceeded."""
        
        alerts = []
        
        # Check error rate
        if metrics['error_rate'] > self.alert_thresholds['error_rate']:
            alerts.append({
                'severity': 'critical',
                'message': f"High error rate: {metrics['error_rate']:.2%}",
                'metric': 'error_rate',
                'value': metrics['error_rate']
            })
        
        # Check processing time
        if metrics['p95_processing_time'] > self.alert_thresholds['processing_time']:
            alerts.append({
                'severity': 'warning',
                'message': f"Slow processing: P95={metrics['p95_processing_time']:.2f}s",
                'metric': 'processing_time',
                'value': metrics['p95_processing_time']
            })
        
        # Check memory usage
        if metrics['memory_usage_ratio'] > self.alert_thresholds['memory_usage']:
            alerts.append({
                'severity': 'critical',
                'message': f"High memory usage: {metrics['memory_usage_ratio']:.1%}",
                'metric': 'memory_usage',
                'value': metrics['memory_usage_ratio']
            })
        
        # Send alerts
        if alerts and self.webhook_url:
            await self.send_webhook(alerts)
        
        return alerts
    
    async def send_webhook(self, alerts: list):
        """Send alerts to webhook endpoint."""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            for alert in alerts:
                await session.post(
                    self.webhook_url,
                    json={
                        'text': f"[{alert['severity'].upper()}] {alert['message']}",
                        'severity': alert['severity'],
                        'metric': alert['metric'],
                        'value': alert['value'],
                        'timestamp': datetime.now(UTC).isoformat()
                    }
                )
```

This comprehensive troubleshooting guide provides real-world debugging strategies, error handling patterns, and monitoring solutions directly from the Graphiti codebase. Each section includes actual code from the repository demonstrating how to identify, debug, and resolve common issues in production deployments.
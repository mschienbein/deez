# Complete API Reference

## Table of Contents
1. [Graphiti Core API](#graphiti-core-api)
2. [Episode Management](#episode-management)
3. [Search and Retrieval](#search-and-retrieval)
4. [Node Operations](#node-operations)
5. [Edge Operations](#edge-operations)
6. [Community Operations](#community-operations)
7. [Configuration APIs](#configuration-apis)
8. [Driver APIs](#driver-apis)
9. [LLM Client APIs](#llm-client-apis)
10. [Utility Functions](#utility-functions)

---

## Graphiti Core API

### Class: `Graphiti`

The main entry point for interacting with the Graphiti knowledge graph system.

```python
class Graphiti:
    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
        llm_client: LLMClient | None = None,
        embedder: EmbedderClient | None = None,
        cross_encoder: CrossEncoderClient | None = None,
        store_raw_episode_content: bool = True,
        graph_driver: GraphDriver | None = None,
        max_coroutines: int | None = None,
        ensure_ascii: bool = False
    )
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `uri` | `str \| None` | `None` | URI of the graph database (e.g., `bolt://localhost:7687`) |
| `user` | `str \| None` | `None` | Database username |
| `password` | `str \| None` | `None` | Database password |
| `llm_client` | `LLMClient \| None` | `OpenAIClient()` | LLM client for entity extraction |
| `embedder` | `EmbedderClient \| None` | `OpenAIEmbedder()` | Embedding client for semantic search |
| `cross_encoder` | `CrossEncoderClient \| None` | `OpenAIRerankerClient()` | Cross-encoder for result reranking |
| `store_raw_episode_content` | `bool` | `True` | Whether to store raw episode content |
| `graph_driver` | `GraphDriver \| None` | `None` | Custom graph database driver |
| `max_coroutines` | `int \| None` | `None` | Maximum concurrent operations |
| `ensure_ascii` | `bool` | `False` | Escape non-ASCII in JSON for prompts |

#### Example

```python
from graphiti_core import Graphiti

# Basic initialization with Neo4j
graphiti = Graphiti(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)

# With custom LLM and embedder
from graphiti_core.llm_client import AnthropicClient
from graphiti_core.embedder import VoyageEmbedder

graphiti = Graphiti(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
    llm_client=AnthropicClient(api_key="..."),
    embedder=VoyageEmbedder(api_key="...")
)
```

### Method: `build_indices_and_constraints`

Initialize database indices and constraints.

```python
async def build_indices_and_constraints(self) -> None
```

#### Description
Creates necessary database indices and constraints for optimal performance. This should be called once when setting up a new database.

#### Example

```python
await graphiti.build_indices_and_constraints()
```

### Method: `close`

Close database connections and clean up resources.

```python
async def close(self) -> None
```

#### Example

```python
await graphiti.close()
```

---

## Episode Management

### Method: `add_episode`

Add a single episode to the knowledge graph.

```python
async def add_episode(
    self,
    name: str,
    episode_body: str | dict,
    source: EpisodeType,
    source_description: str | None = None,
    reference_time: datetime | None = None,
    group_id: str | None = None,
    entity_types: list[type[BaseModel]] | None = None,
    relationships: list[type[BaseModel]] | None = None
) -> AddEpisodeResults
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Unique name for the episode |
| `episode_body` | `str \| dict` | Required | Content of the episode (text or JSON) |
| `source` | `EpisodeType` | Required | Type of episode (text, json, message) |
| `source_description` | `str \| None` | `None` | Description of the episode source |
| `reference_time` | `datetime \| None` | `None` | When the episode occurred |
| `group_id` | `str \| None` | `None` | Group identifier for organizing episodes |
| `entity_types` | `list[type[BaseModel]] \| None` | `None` | Custom entity types to extract |
| `relationships` | `list[type[BaseModel]] \| None` | `None` | Custom relationship types |

#### Returns

`AddEpisodeResults` object containing:
- `episode`: The created `EpisodicNode`
- `episodic_edges`: List of `EpisodicEdge` objects
- `nodes`: List of extracted `EntityNode` objects
- `edges`: List of created `EntityEdge` objects
- `communities`: List of `CommunityNode` objects
- `community_edges`: List of `CommunityEdge` objects

#### Example

```python
from graphiti_core.nodes import EpisodeType
from datetime import datetime, timezone

result = await graphiti.add_episode(
    name="Meeting_2024_01_15",
    episode_body="Alice discussed the Q1 roadmap with Bob. They agreed to prioritize the API redesign.",
    source=EpisodeType.text,
    source_description="Team meeting notes",
    reference_time=datetime(2024, 1, 15, 14, 0, tzinfo=timezone.utc),
    group_id="team_meetings"
)

print(f"Created episode: {result.episode.uuid}")
print(f"Extracted {len(result.nodes)} entities")
print(f"Created {len(result.edges)} relationships")
```

### Method: `add_episodes_bulk`

Add multiple episodes in a single batch operation.

```python
async def add_episodes_bulk(
    self,
    episodes: list[RawEpisode],
    group_id: str | None = None,
    entity_types: list[type[BaseModel]] | None = None,
    relationships: list[type[BaseModel]] | None = None
) -> BulkAddResults
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `episodes` | `list[RawEpisode]` | Required | List of episodes to process |
| `group_id` | `str \| None` | `None` | Group identifier for all episodes |
| `entity_types` | `list[type[BaseModel]] \| None` | `None` | Custom entity types |
| `relationships` | `list[type[BaseModel]] \| None` | `None` | Custom relationship types |

#### Example

```python
from graphiti_core.utils.bulk_utils import RawEpisode

episodes = [
    RawEpisode(
        name="Episode_1",
        content="Content 1",
        source=EpisodeType.text,
        source_description="Source 1",
        reference_time=datetime.now(timezone.utc)
    ),
    RawEpisode(
        name="Episode_2",
        content="Content 2",
        source=EpisodeType.text,
        source_description="Source 2",
        reference_time=datetime.now(timezone.utc)
    )
]

results = await graphiti.add_episodes_bulk(episodes, group_id="batch_001")
```

### Method: `get_episode`

Retrieve a specific episode by UUID.

```python
async def get_episode(self, episode_uuid: str) -> EpisodicNode | None
```

#### Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `episode_uuid` | `str` | UUID of the episode to retrieve |

#### Returns

`EpisodicNode` object or `None` if not found.

---

## Search and Retrieval

### Method: `search`

Perform a hybrid search on the knowledge graph.

```python
async def search(
    self,
    query: str,
    center_node_uuid: str | None = None,
    group_ids: list[str] | None = None,
    limit: int = 10,
    time_filter: datetime | None = None
) -> list[EntityEdge]
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | Required | Search query text |
| `center_node_uuid` | `str \| None` | `None` | UUID of node to center search around |
| `group_ids` | `list[str] \| None` | `None` | Limit search to specific groups |
| `limit` | `int` | `10` | Maximum number of results |
| `time_filter` | `datetime \| None` | `None` | Point-in-time filter |

#### Returns

List of `EntityEdge` objects representing search results.

#### Example

```python
# Simple search
results = await graphiti.search("project deadlines")

# Search with center node for contextual ranking
results = await graphiti.search(
    query="recent updates",
    center_node_uuid="node-uuid-123",
    limit=20
)

# Search within specific groups
results = await graphiti.search(
    query="customer feedback",
    group_ids=["support_tickets", "user_interviews"],
    limit=15
)
```

### Method: `_search`

Advanced search with custom configuration.

```python
async def _search(
    self,
    query: str,
    config: SearchConfig,
    group_ids: list[str] | None = None,
    filters: SearchFilters | None = None
) -> SearchResults
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | Required | Search query |
| `config` | `SearchConfig` | Required | Search configuration object |
| `group_ids` | `list[str] \| None` | `None` | Group filters |
| `filters` | `SearchFilters \| None` | `None` | Additional search filters |

#### Example

```python
from graphiti_core.search import SearchConfig
from graphiti_core.search.search_config_recipes import EDGE_HYBRID_SEARCH_RRF

# Use predefined search recipe
results = await graphiti._search(
    query="technical documentation",
    config=EDGE_HYBRID_SEARCH_RRF
)

# Custom search configuration
custom_config = SearchConfig(
    search_methods=["semantic", "keyword"],
    fusion_method="reciprocal_rank",
    use_reranking=True,
    limit=25
)

results = await graphiti._search(
    query="API endpoints",
    config=custom_config
)
```

### Method: `search_communities`

Search for communities in the graph.

```python
async def search_communities(
    self,
    query: str,
    limit: int = 10
) -> list[CommunityNode]
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | Required | Search query |
| `limit` | `int` | `10` | Maximum results |

#### Returns

List of `CommunityNode` objects.

---

## Node Operations

### Class: `EntityNode`

Represents an entity in the knowledge graph.

```python
@dataclass
class EntityNode:
    uuid: str
    name: str
    labels: list[str]
    summary: str | None = None
    created_at: datetime = field(default_factory=utc_now)
    attributes: dict[str, Any] = field(default_factory=dict)
    embedding: np.ndarray | None = None
```

### Method: `get_node`

Retrieve a specific node by UUID.

```python
async def get_node(self, node_uuid: str) -> EntityNode | None
```

#### Example

```python
node = await graphiti.get_node("node-uuid-123")
if node:
    print(f"Node: {node.name}")
    print(f"Labels: {', '.join(node.labels)}")
```

### Method: `get_nodes_by_name`

Find nodes by name.

```python
async def get_nodes_by_name(
    self,
    name: str,
    fuzzy: bool = False
) -> list[EntityNode]
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | `str` | Required | Name to search for |
| `fuzzy` | `bool` | `False` | Enable fuzzy matching |

### Method: `update_node`

Update an existing node.

```python
async def update_node(
    self,
    node_uuid: str,
    name: str | None = None,
    summary: str | None = None,
    attributes: dict[str, Any] | None = None
) -> EntityNode
```

### Method: `delete_node`

Delete a node and its relationships.

```python
async def delete_node(
    self,
    node_uuid: str,
    cascade: bool = False
) -> bool
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `node_uuid` | `str` | Required | UUID of node to delete |
| `cascade` | `bool` | `False` | Delete connected edges |

---

## Edge Operations

### Class: `EntityEdge`

Represents a relationship between entities.

```python
@dataclass
class EntityEdge:
    uuid: str
    source_node_uuid: str
    target_node_uuid: str
    fact: str
    valid_at: datetime
    invalid_at: datetime | None = None
    created_at: datetime = field(default_factory=utc_now)
    confidence: float = 1.0
    provenance: str | None = None
```

### Method: `get_edge`

Retrieve a specific edge by UUID.

```python
async def get_edge(self, edge_uuid: str) -> EntityEdge | None
```

### Method: `get_edges_for_node`

Get all edges connected to a node.

```python
async def get_edges_for_node(
    self,
    node_uuid: str,
    direction: str = "both"
) -> list[EntityEdge]
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `node_uuid` | `str` | Required | UUID of the node |
| `direction` | `str` | `"both"` | Direction: "in", "out", or "both" |

### Method: `invalidate_edge`

Mark an edge as invalid at a specific time.

```python
async def invalidate_edge(
    self,
    edge_uuid: str,
    invalid_at: datetime | None = None
) -> EntityEdge
```

### Method: `create_edge`

Create a new edge between nodes.

```python
async def create_edge(
    self,
    source_node_uuid: str,
    target_node_uuid: str,
    fact: str,
    valid_at: datetime | None = None,
    confidence: float = 1.0
) -> EntityEdge
```

---

## Community Operations

### Method: `build_communities`

Detect and build communities in the graph.

```python
async def build_communities(
    self,
    algorithm: str = "louvain",
    resolution: float = 1.0,
    min_community_size: int = 3
) -> list[CommunityNode]
```

#### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `algorithm` | `str` | `"louvain"` | Algorithm: "louvain", "label_propagation" |
| `resolution` | `float` | `1.0` | Resolution parameter (higher = more communities) |
| `min_community_size` | `int` | `3` | Minimum nodes for a community |

### Method: `get_community`

Get a specific community by UUID.

```python
async def get_community(
    self,
    community_uuid: str
) -> CommunityNode | None
```

### Method: `get_community_members`

Get all members of a community.

```python
async def get_community_members(
    self,
    community_uuid: str
) -> list[EntityNode]
```

### Method: `update_communities`

Update communities incrementally.

```python
async def update_communities(
    self,
    incremental: bool = True,
    affected_nodes_only: bool = True
) -> list[CommunityNode]
```

---

## Configuration APIs

### Class: `SearchConfig`

Configuration for search operations.

```python
@dataclass
class SearchConfig:
    search_methods: list[str] = field(
        default_factory=lambda: ["semantic", "keyword", "graph"]
    )
    fusion_method: str = "reciprocal_rank"
    semantic_weight: float = 0.4
    keyword_weight: float = 0.3
    graph_weight: float = 0.3
    use_reranking: bool = True
    reranker_model: str | None = None
    limit: int = 20
    similarity_threshold: float = 0.7
    max_graph_depth: int = 2
```

### Predefined Search Recipes

```python
from graphiti_core.search.search_config_recipes import (
    EDGE_HYBRID_SEARCH_RRF,        # Balanced hybrid search
    EDGE_HYBRID_SEARCH_NODE_DISTANCE,  # Graph-distance weighted
    NODE_HYBRID_SEARCH_RRF,        # Node-focused search
    COMBINED_HYBRID_SEARCH_CROSS_ENCODER  # With cross-encoder reranking
)
```

### Class: `SearchFilters`

Filters for search operations.

```python
@dataclass
class SearchFilters:
    created_after: datetime | None = None
    created_before: datetime | None = None
    entity_types: list[str] | None = None
    edge_types: list[str] | None = None
    group_ids: list[str] | None = None
    min_confidence: float = 0.0
    has_embedding: bool | None = None
```

### Class: `LLMConfig`

Configuration for LLM clients.

```python
@dataclass
class LLMConfig:
    model: str = "gpt-4"
    small_model: str = "gpt-3.5-turbo"
    temperature: float = 0.0
    max_completion_tokens: int = 4000
    api_key: str | None = None
    base_url: str | None = None
    organization: str | None = None
```

---

## Driver APIs

### Class: `GraphDriver` (Abstract)

Base class for graph database drivers.

```python
class GraphDriver(ABC):
    @abstractmethod
    async def execute(
        self,
        query: str,
        parameters: dict | None = None
    ) -> list[dict]:
        """Execute a query on the graph database."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the database connection."""
        pass
```

### Class: `Neo4jDriver`

Neo4j-specific driver implementation.

```python
class Neo4jDriver(GraphDriver):
    def __init__(
        self,
        uri: str,
        user: str | None = None,
        password: str | None = None,
        database: str = "neo4j"
    )
```

### Class: `FalkorDriver`

FalkorDB driver implementation.

```python
class FalkorDriver(GraphDriver):
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        username: str | None = None,
        password: str | None = None,
        database: str = "default_db"
    )
```

### Class: `NeptuneDriver`

Amazon Neptune driver implementation.

```python
class NeptuneDriver(GraphDriver):
    def __init__(
        self,
        host: str,
        aoss_host: str,
        port: int = 8182,
        aoss_port: int = 443
    )
```

---

## LLM Client APIs

### Class: `LLMClient` (Abstract)

Base class for LLM clients.

```python
class LLMClient(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        **kwargs
    ) -> str:
        """Generate text completion."""
        pass
    
    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        response_model: type[BaseModel],
        **kwargs
    ) -> BaseModel:
        """Generate structured output."""
        pass
```

### Class: `OpenAIClient`

OpenAI API client.

```python
class OpenAIClient(LLMClient):
    def __init__(
        self,
        config: LLMConfig | None = None
    )
```

### Class: `AnthropicClient`

Anthropic Claude API client.

```python
class AnthropicClient(LLMClient):
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-opus-20240229"
    )
```

### Class: `GeminiClient`

Google Gemini API client.

```python
class GeminiClient(LLMClient):
    def __init__(
        self,
        config: LLMConfig
    )
```

---

## Utility Functions

### Function: `create_entity_node_embeddings`

Generate embeddings for entity nodes.

```python
async def create_entity_node_embeddings(
    nodes: list[EntityNode],
    embedder: EmbedderClient,
    batch_size: int = 100
) -> list[EntityNode]
```

### Function: `create_entity_edge_embeddings`

Generate embeddings for edges.

```python
async def create_entity_edge_embeddings(
    edges: list[EntityEdge],
    embedder: EmbedderClient,
    batch_size: int = 100
) -> list[EntityEdge]
```

### Function: `semaphore_gather`

Execute async tasks with concurrency control.

```python
async def semaphore_gather(
    tasks: list[Coroutine],
    max_concurrent: int | None = None
) -> list[Any]
```

#### Example

```python
tasks = [
    process_episode(ep) for ep in episodes
]

results = await semaphore_gather(tasks, max_concurrent=10)
```

### Function: `utc_now`

Get current UTC time.

```python
def utc_now() -> datetime:
    """Get current UTC time with timezone awareness."""
    return datetime.now(timezone.utc)
```

### Function: `validate_entity_types`

Validate custom entity type definitions.

```python
def validate_entity_types(
    entity_types: list[type[BaseModel]]
) -> bool
```

### Function: `validate_group_id`

Validate group ID format.

```python
def validate_group_id(group_id: str) -> bool:
    """
    Validate group ID format.
    Must be alphanumeric with underscores, hyphens.
    """
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, group_id))
```

---

## Data Classes

### Class: `RawEpisode`

Input format for bulk episode processing.

```python
@dataclass
class RawEpisode:
    name: str
    content: str | dict
    source: EpisodeType
    source_description: str
    reference_time: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
```

### Class: `ProcessedEpisode`

Result of episode processing.

```python
@dataclass
class ProcessedEpisode:
    episode: EpisodicNode
    nodes: list[EntityNode]
    edges: list[EntityEdge]
    processing_time: float
    errors: list[str] = field(default_factory=list)
```

### Class: `SearchResults`

Container for search results.

```python
@dataclass
class SearchResults:
    edges: list[EntityEdge] = field(default_factory=list)
    nodes: list[EntityNode] = field(default_factory=list)
    communities: list[CommunityNode] = field(default_factory=list)
    total_count: int = 0
    search_config: SearchConfig | None = None
    query_time: float = 0.0
```

---

## Enums

### Enum: `EpisodeType`

Types of episodes that can be added.

```python
class EpisodeType(str, Enum):
    text = "text"        # Plain text content
    json = "json"        # Structured JSON data
    message = "message"  # Chat/conversation message
```

### Enum: `ConflictStrategy`

Strategies for handling conflicting facts.

```python
class ConflictStrategy(str, Enum):
    TEMPORAL_OVERRIDE = "temporal_override"  # Newer facts override
    CONFIDENCE_BASED = "confidence_based"    # Higher confidence wins
    SOURCE_AUTHORITY = "source_authority"    # Based on source rank
    MANUAL_REVIEW = "manual_review"         # Flag for manual review
```

### Enum: `FusionMethod`

Methods for combining search results.

```python
class FusionMethod(str, Enum):
    RECIPROCAL_RANK = "reciprocal_rank"  # RRF fusion
    LINEAR_COMBINATION = "linear"        # Weighted linear
    MAX_SCORE = "max"                   # Take maximum score
    NONE = "none"                        # No fusion
```

---

## Error Handling

### Exception Classes

```python
class GraphitiError(Exception):
    """Base exception for Graphiti errors."""
    pass

class EntityExtractionError(GraphitiError):
    """Error during entity extraction."""
    pass

class DatabaseError(GraphitiError):
    """Database operation error."""
    pass

class SearchError(GraphitiError):
    """Search operation error."""
    pass

class ValidationError(GraphitiError):
    """Validation error."""
    pass
```

### Error Handling Example

```python
try:
    result = await graphiti.add_episode(
        name="test",
        episode_body="content",
        source=EpisodeType.text
    )
except EntityExtractionError as e:
    logger.error(f"Failed to extract entities: {e}")
except DatabaseError as e:
    logger.error(f"Database error: {e}")
except GraphitiError as e:
    logger.error(f"Graphiti error: {e}")
```

---

## Environment Variables

### Core Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required if using OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic API key | Optional |
| `GOOGLE_API_KEY` | Google API key | Optional |
| `VOYAGE_API_KEY` | Voyage API key | Optional |

### Performance Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `SEMAPHORE_LIMIT` | Max concurrent operations | `10` |
| `USE_PARALLEL_RUNTIME` | Enable Neo4j parallel runtime | `false` |
| `BATCH_SIZE` | Default batch size | `100` |
| `CACHE_TTL` | Cache time-to-live (seconds) | `300` |

### Database Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j connection URI | `bolt://localhost:7687` |
| `NEO4J_USER` | Neo4j username | `neo4j` |
| `NEO4J_PASSWORD` | Neo4j password | Required |
| `NEO4J_DATABASE` | Database name | `neo4j` |

---

## Migration from v0.x to v1.x

### Breaking Changes

1. **Driver Initialization**: Now pass `graph_driver` instead of separate URI/credentials
2. **Async by Default**: All operations are now async
3. **Custom Entity Types**: Use Pydantic models instead of dictionaries
4. **Search API**: Unified search interface with config objects

### Migration Example

```python
# Old (v0.x)
graphiti = Graphiti(uri, user, password)
result = graphiti.add_episode(...)

# New (v1.x)
graphiti = Graphiti(uri, user, password)
result = await graphiti.add_episode(...)
```

---

## Best Practices

### 1. Connection Management

Always close connections when done:

```python
try:
    graphiti = Graphiti(...)
    # Use graphiti
finally:
    await graphiti.close()
```

Or use context manager (if available):

```python
async with Graphiti(...) as graphiti:
    # Use graphiti
```

### 2. Batch Operations

Prefer bulk operations for better performance:

```python
# Good - single bulk operation
results = await graphiti.add_episodes_bulk(episodes)

# Less efficient - multiple individual calls
for episode in episodes:
    await graphiti.add_episode(...)
```

### 3. Error Handling

Always handle potential errors:

```python
try:
    result = await graphiti.search(query)
except SearchError as e:
    # Handle search errors
    logger.error(f"Search failed: {e}")
    result = []
```

### 4. Custom Entity Types

Define clear, focused entity types:

```python
class Person(BaseModel):
    """A person entity."""
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    email: str | None = Field(None, description="Email address")
```

### 5. Performance Optimization

Set appropriate concurrency limits:

```python
# For high-throughput scenarios
graphiti = Graphiti(
    ...,
    max_coroutines=50  # Increase parallelism
)

# For rate-limited APIs
graphiti = Graphiti(
    ...,
    max_coroutines=5  # Reduce parallelism
)
```

---

## Support and Resources

- **Documentation**: [https://help.getzep.com/graphiti](https://help.getzep.com/graphiti)
- **GitHub**: [https://github.com/getzep/graphiti](https://github.com/getzep/graphiti)
- **Discord**: [Zep Discord Server](https://discord.com/invite/W8Kw6bsgXQ)
- **Issues**: [GitHub Issues](https://github.com/getzep/graphiti/issues)
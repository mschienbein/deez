# Graphiti Integration Patterns: A Deep Technical Guide

## Table of Contents
1. [LLM Provider Integrations](#llm-provider-integrations)
2. [Embedding Provider Integrations](#embedding-provider-integrations)
3. [Agent Framework Integrations](#agent-framework-integrations)
4. [MCP Server Integration](#mcp-server-integration)
5. [FastAPI Service Integration](#fastapi-service-integration)
6. [Custom Entity Type Integration](#custom-entity-type-integration)
7. [Multi-Tenant Integration](#multi-tenant-integration)
8. [Streaming and Queue Integration](#streaming-and-queue-integration)

## LLM Provider Integrations

### Understanding the LLM Client Architecture

Graphiti uses an abstract LLM client interface that allows seamless switching between providers. Here's how the actual implementation works:

```python
# From graphiti_core/llm_client/client.py
class LLMClient(ABC):
    def __init__(self, config: LLMConfig | None, cache: bool = False):
        if config is None:
            config = LLMConfig()
        
        self.config = config
        self.model = config.model
        self.small_model = config.small_model  # For cost optimization
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.cache_enabled = cache
        self.cache_dir = None
        
        # Disk-based caching for repeated queries
        if self.cache_enabled:
            self.cache_dir = Cache(DEFAULT_CACHE_DIR)
    
    def _clean_input(self, input: str) -> str:
        """Clean input string of invalid unicode and control characters."""
        # Clean any invalid Unicode
        cleaned = input.encode('utf-8', errors='ignore').decode('utf-8')
        
        # Remove zero-width characters and other invisible unicode
        zero_width = '\u200b\u200c\u200d\ufeff\u2060'
        for char in zero_width:
            cleaned = cleaned.replace(char, '')
        
        # Remove control characters except newlines, returns, and tabs
        cleaned = ''.join(char for char in cleaned if ord(char) >= 32 or char in '\n\r\t')
        
        return cleaned
    
    @retry(
        stop=stop_after_attempt(4),
        wait=wait_random_exponential(multiplier=10, min=5, max=120),
        retry=retry_if_exception(is_server_or_retry_error),
        reraise=True,
    )
    async def _generate_response_with_retry(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, typing.Any]:
        # Exponential backoff with jitter for rate limiting
        try:
            return await self._generate_response(messages, response_model, max_tokens, model_size)
        except (httpx.HTTPStatusError, RateLimitError) as e:
            raise e
```

### OpenAI Integration

The OpenAI integration is the most comprehensive, supporting both direct API and Azure endpoints:

```python
# From graphiti_core/llm_client/openai_client.py
class OpenAIClient(BaseOpenAIClient):
    def __init__(
        self,
        config: LLMConfig | None = None,
        client: AsyncOpenAI | None = None,
        cache: bool = False,
    ):
        super().__init__(config=config, cache=cache)
        
        if client is not None:
            self.client = client
        else:
            # Support for custom base URLs (e.g., local LLMs)
            base_url = self.config.base_url or 'https://api.openai.com/v1'
            
            self.client = AsyncOpenAI(
                api_key=self.config.api_key,
                base_url=base_url,
                max_retries=self.config.max_retries,
                timeout=Timeout(self.config.timeout_seconds),
            )
    
    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, typing.Any]:
        # Model selection based on task size
        model = self.model if model_size == ModelSize.medium else self.small_model
        
        # Convert internal messages to OpenAI format
        openai_messages = [
            {'role': m.role, 'content': self._clean_input(m.content)}
            for m in messages
        ]
        
        if response_model is not None:
            # Structured output with JSON mode
            response = await self.client.beta.chat.completions.parse(
                model=model,
                messages=openai_messages,
                temperature=self.temperature,
                max_tokens=max_tokens,
                response_format=response_model,
            )
            
            # Handle refusal responses
            if response.choices[0].message.refusal:
                raise Exception(f"LLM refused to respond: {response.choices[0].message.refusal}")
            
            parsed = response.choices[0].message.parsed
            if parsed is None:
                raise Exception("Failed to parse response")
            
            return parsed.model_dump()
        else:
            # Regular text completion
            response = await self.client.chat.completions.create(
                model=model,
                messages=openai_messages,
                temperature=self.temperature,
                max_tokens=max_tokens,
            )
            
            return {'response': response.choices[0].message.content}
```

### Anthropic Claude Integration

The Anthropic integration shows how to adapt a different API structure:

```python
# From graphiti_core/llm_client/anthropic_client.py
class AnthropicClient(LLMClient):
    def __init__(self, config: LLMConfig | None = None, cache: bool = False):
        super().__init__(config=config, cache=cache)
        self.client = AsyncAnthropic(api_key=self.config.api_key)
        
        # Claude-specific model mapping
        self.model_map = {
            'claude-3-haiku': 'claude-3-haiku-20240307',
            'claude-3-sonnet': 'claude-3-5-sonnet-20241022',
            'claude-3-opus': 'claude-3-opus-20240229',
        }
    
    async def _generate_response(
        self,
        messages: list[Message],
        response_model: type[BaseModel] | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        model_size: ModelSize = ModelSize.medium,
    ) -> dict[str, typing.Any]:
        # Claude requires system message separately
        system_message = None
        user_messages = []
        
        for msg in messages:
            if msg.role == 'system':
                system_message = self._clean_input(msg.content)
            else:
                # Claude uses 'user' and 'assistant' roles
                role = 'user' if msg.role == 'user' else 'assistant'
                user_messages.append({
                    'role': role,
                    'content': self._clean_input(msg.content)
                })
        
        # Use small model for simple tasks
        model = self.model if model_size == ModelSize.medium else self.small_model
        model_name = self.model_map.get(model, model)
        
        if response_model is not None:
            # Claude's structured output via tool use
            tool_name = 'extract_info'
            tools = [{
                'name': tool_name,
                'description': 'Extract structured information',
                'input_schema': response_model.model_json_schema()
            }]
            
            response = await self.client.messages.create(
                model=model_name,
                messages=user_messages,
                system=system_message,
                max_tokens=max_tokens,
                temperature=self.temperature,
                tools=tools,
                tool_choice={'type': 'tool', 'name': tool_name}
            )
            
            # Extract structured data from tool use
            for content in response.content:
                if content.type == 'tool_use' and content.name == tool_name:
                    return content.input
            
            raise Exception("No tool use in response")
        else:
            response = await self.client.messages.create(
                model=model_name,
                messages=user_messages,
                system=system_message,
                max_tokens=max_tokens,
                temperature=self.temperature,
            )
            
            return {'response': response.content[0].text}
```

### Azure OpenAI Integration

Azure requires special authentication and deployment handling:

```python
# From graphiti_core/llm_client/azure_openai_client.py
class AzureOpenAILLMClient(BaseOpenAIClient):
    """Wrapper class for AsyncAzureOpenAI that implements the LLMClient interface."""
    
    def __init__(
        self,
        azure_client: AsyncAzureOpenAI,
        config: LLMConfig | None = None,
        cache: bool = False,
    ):
        super().__init__(config=config, cache=cache)
        self.client = azure_client
        
        # Azure uses deployment names instead of model names
        # The deployment name is configured in Azure portal
        
    # Inherits _generate_response from BaseOpenAIClient
    # The main difference is in initialization and authentication

# From mcp_server/graphiti_mcp_server.py - Azure setup with managed identity
def create_azure_credential_token_provider() -> Callable[[], str]:
    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential, 'https://cognitiveservices.azure.com/.default'
    )
    return token_provider

# Azure configuration with managed identity
if azure_openai_use_managed_identity:
    token_provider = create_azure_credential_token_provider()
    return AzureOpenAILLMClient(
        azure_client=AsyncAzureOpenAI(
            azure_endpoint=azure_endpoint,
            azure_deployment=deployment_name,
            api_version=api_version,
            azure_ad_token_provider=token_provider,  # Managed identity auth
        ),
        config=LLMConfig(
            model=model,
            small_model=small_model,
            temperature=temperature,
        ),
    )
```

## Embedding Provider Integrations

### Embedding Client Architecture

The embedding system is designed for high throughput with batching:

```python
# From graphiti_core/embedder/client.py
class EmbedderClient(ABC):
    @abstractmethod
    async def create_embedding(self, text: str) -> list[float]:
        """Create embedding for a single text."""
        pass
    
    @abstractmethod
    async def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings for multiple texts with batching."""
        pass
    
    @abstractmethod
    async def create_embedding_pooled(self, texts: list[str]) -> list[float]:
        """Create a single pooled embedding from multiple texts."""
        pass

# From graphiti_core/embedder/openai.py
class OpenAIEmbedder(EmbedderClient):
    def __init__(self, config: OpenAIEmbedderConfig | None = None):
        if config is None:
            config = OpenAIEmbedderConfig()
        
        self.client = AsyncOpenAI(api_key=config.api_key)
        self.model = config.embedding_model
        self.dimensions = config.embedding_dim
    
    async def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Batch embedding creation with automatic chunking."""
        # OpenAI has a limit on batch size
        MAX_BATCH_SIZE = 2048
        all_embeddings = []
        
        for i in range(0, len(texts), MAX_BATCH_SIZE):
            batch = texts[i:i + MAX_BATCH_SIZE]
            
            # Clean texts to avoid encoding issues
            cleaned_batch = [
                text.encode('utf-8', errors='ignore').decode('utf-8')
                for text in batch
            ]
            
            response = await self.client.embeddings.create(
                input=cleaned_batch,
                model=self.model,
                dimensions=self.dimensions  # Ada v3 supports dimension reduction
            )
            
            # Extract embeddings in order
            batch_embeddings = [data.embedding for data in response.data]
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    async def create_embedding_pooled(self, texts: list[str]) -> list[float]:
        """Create a single embedding from multiple texts using mean pooling."""
        if not texts:
            raise ValueError("No texts provided for pooling")
        
        embeddings = await self.create_embeddings(texts)
        
        # Mean pooling across all embeddings
        pooled = []
        embedding_dim = len(embeddings[0])
        
        for i in range(embedding_dim):
            mean_value = sum(emb[i] for emb in embeddings) / len(embeddings)
            pooled.append(mean_value)
        
        return pooled
```

### Azure OpenAI Embeddings

Azure embeddings with deployment management:

```python
# From graphiti_core/embedder/azure_openai.py
class AzureOpenAIEmbedderClient(EmbedderClient):
    """Wrapper for Azure OpenAI embeddings."""
    
    def __init__(
        self,
        azure_client: AsyncAzureOpenAI,
        model: str = 'text-embedding-3-small'
    ):
        self.client = azure_client
        self.model = model
    
    async def create_embedding(self, text: str) -> list[float]:
        # Azure uses deployment name configured in the client
        response = await self.client.embeddings.create(
            input=[text],
            model=self.model  # This is actually the deployment name in Azure
        )
        return response.data[0].embedding
    
    async def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        # Azure has same API as OpenAI but uses deployment names
        response = await self.client.embeddings.create(
            input=texts,
            model=self.model
        )
        return [data.embedding for data in response.data]
```

## Agent Framework Integrations

### LangGraph Agent Integration

The LangGraph integration shows how to build a stateful agent with Graphiti memory:

```python
# From examples/langgraph-agent/agent.ipynb
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode
from typing_extensions import TypedDict

class State(TypedDict):
    messages: Annotated[list, add_messages]
    user_name: str
    user_node_uuid: str

# Tool for searching Graphiti
@tool
async def get_shoe_data(query: str) -> str:
    """Search the graphiti graph for information about shoes"""
    edge_results = await client.search(
        query,
        center_node_uuid=manybirds_node_uuid,  # Center search on product node
        num_results=10,
    )
    return edges_to_facts_string(edge_results)

# Chatbot function with Graphiti context
async def chatbot(state: State):
    facts_string = None
    if len(state['messages']) > 0:
        last_message = state['messages'][-1]
        
        # Build query from conversation context
        graphiti_query = f'{state["user_name"] if isinstance(last_message, HumanMessage) else "SalesBot"}: {last_message.content}'
        
        # Search with user node as center for personalization
        edge_results = await client.search(
            graphiti_query, 
            center_node_uuid=state['user_node_uuid'], 
            num_results=5
        )
        facts_string = edges_to_facts_string(edge_results)
    
    # Build system message with Graphiti context
    system_message = SystemMessage(
        content=f"""You are a skillful shoe salesperson working for ManyBirds.
        
        Facts about the user and their conversation:
        {facts_string or 'No facts about the user and their conversation'}"""
    )
    
    messages = [system_message] + state['messages']
    response = await llm.ainvoke(messages)
    
    # Asynchronously persist conversation to Graphiti
    asyncio.create_task(
        client.add_episode(
            name='Chatbot Response',
            episode_body=f'{state["user_name"]}: {state["messages"][-1]}\nSalesBot: {response.content}',
            source=EpisodeType.message,
            reference_time=datetime.now(timezone.utc),
            source_description='Chatbot',
        )
    )
    
    return {'messages': [response]}

# Build the LangGraph agent
graph_builder = StateGraph(State)
memory = MemorySaver()

# Define conditional routing
async def should_continue(state, config):
    last_message = state['messages'][-1]
    if not last_message.tool_calls:
        return 'end'
    else:
        return 'continue'

# Wire up the graph
graph_builder.add_node('agent', chatbot)
graph_builder.add_node('tools', tool_node)
graph_builder.add_edge(START, 'agent')
graph_builder.add_conditional_edges(
    'agent', 
    should_continue, 
    {'continue': 'tools', 'end': END}
)
graph_builder.add_edge('tools', 'agent')

graph = graph_builder.compile(checkpointer=memory)

# Run the agent
await graph.ainvoke(
    {
        'messages': [{'role': 'user', 'content': 'What shoes do you have?'}],
        'user_name': user_name,
        'user_node_uuid': user_node_uuid,
    },
    config={'configurable': {'thread_id': uuid.uuid4().hex}},
)
```

## MCP Server Integration

### Model Context Protocol Server

The MCP server exposes Graphiti as a tool for AI assistants:

```python
# From mcp_server/graphiti_mcp_server.py
from mcp.server.fastmcp import FastMCP

# Custom entity types for domain-specific extraction
class Requirement(BaseModel):
    """A Requirement represents a specific need that must be fulfilled."""
    project_name: str = Field(
        description='The name of the project to which the requirement belongs.'
    )
    description: str = Field(
        description='Description of the requirement.'
    )

class Preference(BaseModel):
    """A Preference represents a user's expressed like or dislike."""
    category: str = Field(
        description="The category of the preference (e.g., 'Brands', 'Food', 'Music')"
    )
    description: str = Field(
        description='Brief description of the preference.'
    )

ENTITY_TYPES: dict[str, BaseModel] = {
    'Requirement': Requirement,
    'Preference': Preference,
    'Procedure': Procedure,
}

# Initialize MCP server
mcp = FastMCP(
    'Graphiti Agent Memory',
    instructions=GRAPHITI_MCP_INSTRUCTIONS,
)

# Episode queues for sequential processing per group
episode_queues: dict[str, asyncio.Queue] = {}
queue_workers: dict[str, bool] = {}

async def process_episode_queue(group_id: str):
    """Process episodes for a specific group_id sequentially."""
    logger.info(f'Starting episode queue worker for group_id: {group_id}')
    queue_workers[group_id] = True
    
    try:
        while True:
            # Get next episode processing function from queue
            process_func = await episode_queues[group_id].get()
            
            try:
                await process_func()
            except Exception as e:
                logger.error(f'Error processing queued episode for group_id {group_id}: {str(e)}')
            finally:
                episode_queues[group_id].task_done()
    except asyncio.CancelledError:
        logger.info(f'Episode queue worker for group_id {group_id} was cancelled')
    finally:
        queue_workers[group_id] = False

@mcp.tool()
async def add_memory(
    name: str,
    episode_body: str,
    group_id: str | None = None,
    source: str = 'text',
    source_description: str = '',
    uuid: str | None = None,
) -> SuccessResponse | ErrorResponse:
    """Add an episode to memory. Returns immediately and processes in background."""
    
    # Map string source to EpisodeType enum
    source_type = EpisodeType.text
    if source.lower() == 'message':
        source_type = EpisodeType.message
    elif source.lower() == 'json':
        source_type = EpisodeType.json
    
    effective_group_id = group_id if group_id is not None else config.group_id
    group_id_str = str(effective_group_id) if effective_group_id is not None else ''
    
    # Define the episode processing function
    async def process_episode():
        try:
            logger.info(f"Processing queued episode '{name}' for group_id: {group_id_str}")
            
            # Use custom entity types if enabled
            entity_types = ENTITY_TYPES if config.use_custom_entities else {}
            
            await client.add_episode(
                name=name,
                episode_body=episode_body,
                source=source_type,
                source_description=source_description,
                group_id=group_id_str,
                uuid=uuid,
                reference_time=datetime.now(timezone.utc),
                entity_types=entity_types,  # Custom extraction
            )
            logger.info(f"Episode '{name}' processed successfully")
        except Exception as e:
            logger.error(f"Error processing episode '{name}': {str(e)}")
    
    # Initialize queue for this group_id if it doesn't exist
    if group_id_str not in episode_queues:
        episode_queues[group_id_str] = asyncio.Queue()
    
    # Add to queue
    await episode_queues[group_id_str].put(process_episode)
    
    # Start worker if not running
    if not queue_workers.get(group_id_str, False):
        asyncio.create_task(process_episode_queue(group_id_str))
    
    return SuccessResponse(
        message=f"Episode '{name}' queued for processing (position: {episode_queues[group_id_str].qsize()})"
    )

@mcp.tool()
async def search_memory_nodes(
    query: str,
    group_ids: list[str] | None = None,
    max_nodes: int = 10,
    center_node_uuid: str | None = None,
    entity: str = '',  # Filter by entity type
) -> NodeSearchResponse | ErrorResponse:
    """Search the graph memory for relevant node summaries."""
    
    # Use appropriate search config based on center node
    if center_node_uuid is not None:
        search_config = NODE_HYBRID_SEARCH_NODE_DISTANCE.model_copy(deep=True)
    else:
        search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
    
    search_config.limit = max_nodes
    
    # Apply entity type filter
    filters = SearchFilters()
    if entity != '':
        filters.node_labels = [entity]
    
    # Perform search
    search_results = await client._search(
        query=query,
        config=search_config,
        group_ids=effective_group_ids,
        center_node_uuid=center_node_uuid,
        search_filter=filters,
    )
    
    # Format results
    formatted_nodes = [
        {
            'uuid': node.uuid,
            'name': node.name,
            'summary': node.summary,
            'labels': node.labels,
            'group_id': node.group_id,
            'created_at': node.created_at.isoformat(),
            'attributes': node.attributes,
        }
        for node in search_results.nodes
    ]
    
    return NodeSearchResponse(message='Nodes retrieved successfully', nodes=formatted_nodes)
```

## FastAPI Service Integration

### RESTful API Service

Building a production API with Graphiti:

```python
# From server/graph_service/zep_graphiti.py
from fastapi import Depends, HTTPException
from graphiti_core import Graphiti

class ZepGraphiti(Graphiti):
    """Extended Graphiti with additional management methods."""
    
    async def save_entity_node(self, name: str, uuid: str, group_id: str, summary: str = ''):
        new_node = EntityNode(
            name=name,
            uuid=uuid,
            group_id=group_id,
            summary=summary,
        )
        await new_node.generate_name_embedding(self.embedder)
        await new_node.save(self.driver)
        return new_node
    
    async def get_entity_edge(self, uuid: str):
        try:
            edge = await EntityEdge.get_by_uuid(self.driver, uuid)
            return edge
        except EdgeNotFoundError as e:
            raise HTTPException(status_code=404, detail=e.message) from e
    
    async def delete_group(self, group_id: str):
        """Delete all data for a specific group."""
        try:
            edges = await EntityEdge.get_by_group_ids(self.driver, [group_id])
        except GroupsEdgesNotFoundError:
            logger.warning(f'No edges found for group {group_id}')
            edges = []
        
        nodes = await EntityNode.get_by_group_ids(self.driver, [group_id])
        episodes = await EpisodicNode.get_by_group_ids(self.driver, [group_id])
        
        # Delete all components
        for edge in edges:
            await edge.delete(self.driver)
        for node in nodes:
            await node.delete(self.driver)
        for episode in episodes:
            await episode.delete(self.driver)

# Dependency injection for FastAPI
async def get_graphiti(settings: ZepEnvDep):
    client = ZepGraphiti(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    
    # Configure LLM client
    if settings.openai_base_url is not None:
        client.llm_client.config.base_url = settings.openai_base_url
    if settings.openai_api_key is not None:
        client.llm_client.config.api_key = settings.openai_api_key
    if settings.model_name is not None:
        client.llm_client.model = settings.model_name
    
    try:
        yield client
    finally:
        await client.close()

ZepGraphitiDep = Annotated[ZepGraphiti, Depends(get_graphiti)]

# FastAPI endpoints
@app.post("/episodes")
async def add_episode(
    episode: EpisodeRequest,
    graphiti: ZepGraphitiDep
):
    """Add a new episode to the graph."""
    await graphiti.add_episode(
        name=episode.name,
        episode_body=episode.body,
        source=episode.source,
        group_id=episode.group_id,
        reference_time=datetime.now(timezone.utc)
    )
    return {"status": "success"}

@app.get("/search/facts")
async def search_facts(
    query: str,
    group_id: str,
    limit: int = 10,
    graphiti: ZepGraphitiDep
):
    """Search for facts in the graph."""
    results = await graphiti.search(
        query=query,
        group_ids=[group_id],
        num_results=limit
    )
    
    return [get_fact_result_from_edge(edge) for edge in results]
```

## Custom Entity Type Integration

### Domain-Specific Entity Extraction

Define custom entities for your domain:

```python
# Custom entity definitions with extraction instructions
class Requirement(BaseModel):
    """A Requirement represents a specific need or feature.
    
    Instructions for identifying and extracting requirements:
    1. Look for explicit statements of needs ("We need X", "X is required")
    2. Identify functional specifications
    3. Pay attention to non-functional requirements (performance, security)
    4. Extract constraints or limitations
    5. Focus on clear, specific, measurable requirements
    6. Capture priority if mentioned ("critical", "high priority")
    7. Include dependencies between requirements
    8. Preserve original intent and scope
    """
    
    project_name: str = Field(
        description='The project this requirement belongs to'
    )
    description: str = Field(
        description='Clear description of the requirement'
    )
    priority: str = Field(
        default='medium',
        description='Priority level: low, medium, high, critical'
    )
    dependencies: list[str] = Field(
        default_factory=list,
        description='Other requirements this depends on'
    )

class TechnicalConcept(BaseModel):
    """A technical concept, pattern, or architectural element."""
    
    name: str = Field(description='Name of the concept')
    category: str = Field(description='Category: pattern, architecture, algorithm, etc.')
    description: str = Field(description='Technical description')
    related_concepts: list[str] = Field(
        default_factory=list,
        description='Related technical concepts'
    )

# Register entity types with Graphiti
ENTITY_TYPES = {
    'Requirement': Requirement,
    'TechnicalConcept': TechnicalConcept,
}

# Use in episode processing
await graphiti.add_episode(
    name='Architecture Discussion',
    episode_body=transcript,
    source=EpisodeType.message,
    entity_types=ENTITY_TYPES,  # Custom extraction
    reference_time=datetime.now(timezone.utc)
)

# The LLM will now extract these specific entity types
# and create appropriate nodes and relationships
```

## Multi-Tenant Integration

### Group-Based Data Isolation

Implement multi-tenancy with group_id partitioning:

```python
class MultiTenantGraphiti:
    """Multi-tenant wrapper for Graphiti."""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
        self.tenant_cache = {}
    
    def get_tenant_id(self, organization: str, project: str) -> str:
        """Generate consistent tenant ID."""
        return f"{organization}:{project}"
    
    async def add_tenant_episode(
        self,
        organization: str,
        project: str,
        episode_data: dict
    ):
        """Add episode with automatic tenant isolation."""
        tenant_id = self.get_tenant_id(organization, project)
        
        # Add tenant metadata
        enriched_body = {
            **episode_data,
            '_tenant': {
                'organization': organization,
                'project': project,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        }
        
        await self.graphiti.add_episode(
            name=episode_data.get('name', 'Episode'),
            episode_body=json.dumps(enriched_body),
            source=EpisodeType.json,
            group_id=tenant_id,  # Tenant isolation
            reference_time=datetime.now(timezone.utc)
        )
    
    async def search_tenant_data(
        self,
        organization: str,
        project: str,
        query: str,
        include_org_wide: bool = False
    ):
        """Search within tenant boundaries."""
        group_ids = []
        
        # Always include project-specific data
        project_tenant = self.get_tenant_id(organization, project)
        group_ids.append(project_tenant)
        
        # Optionally include organization-wide data
        if include_org_wide:
            org_tenant = f"{organization}:*"
            group_ids.append(org_tenant)
        
        return await self.graphiti.search(
            query=query,
            group_ids=group_ids,
            num_results=20
        )
    
    async def migrate_tenant_data(
        self,
        from_org: str,
        from_project: str,
        to_org: str,
        to_project: str
    ):
        """Migrate data between tenants."""
        from_tenant = self.get_tenant_id(from_org, from_project)
        to_tenant = self.get_tenant_id(to_org, to_project)
        
        # Get all nodes and edges for the source tenant
        nodes = await EntityNode.get_by_group_ids(
            self.graphiti.driver,
            [from_tenant]
        )
        edges = await EntityEdge.get_by_group_ids(
            self.graphiti.driver,
            [from_tenant]
        )
        episodes = await EpisodicNode.get_by_group_ids(
            self.graphiti.driver,
            [from_tenant]
        )
        
        # Update group_ids and save to new tenant
        for node in nodes:
            node.group_id = to_tenant
            await node.save(self.graphiti.driver)
        
        for edge in edges:
            edge.group_id = to_tenant
            await edge.save(self.graphiti.driver)
        
        for episode in episodes:
            episode.group_id = to_tenant
            await episode.save(self.graphiti.driver)
        
        logger.info(f"Migrated {len(nodes)} nodes, {len(edges)} edges, {len(episodes)} episodes")
```

## Streaming and Queue Integration

### Real-Time Event Processing

Process streaming data with buffering and batching:

```python
class StreamingGraphiti:
    """Process streaming data with Graphiti."""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
        self.buffer = []
        self.buffer_size = 100
        self.flush_interval = 60  # seconds
        self.last_flush = datetime.now(timezone.utc)
        self.processing_lock = asyncio.Lock()
    
    async def ingest_stream_event(self, event: dict):
        """Ingest a single streaming event."""
        async with self.processing_lock:
            self.buffer.append(event)
            
            # Check if we should flush
            should_flush = (
                len(self.buffer) >= self.buffer_size or
                (datetime.now(timezone.utc) - self.last_flush).seconds >= self.flush_interval
            )
            
            if should_flush:
                await self._flush_buffer()
    
    async def _flush_buffer(self):
        """Process buffered events as a batch."""
        if not self.buffer:
            return
        
        # Group events by type for efficient processing
        events_by_type = defaultdict(list)
        for event in self.buffer:
            events_by_type[event.get('type', 'unknown')].append(event)
        
        # Process each type
        for event_type, events in events_by_type.items():
            if event_type == 'user_action':
                await self._process_user_actions(events)
            elif event_type == 'system_log':
                await self._process_system_logs(events)
            else:
                await self._process_generic_events(events)
        
        # Clear buffer and update flush time
        self.buffer.clear()
        self.last_flush = datetime.now(timezone.utc)
    
    async def _process_user_actions(self, events: list[dict]):
        """Process user action events."""
        # Combine related actions into episodes
        sessions = defaultdict(list)
        for event in events:
            session_id = event.get('session_id', 'unknown')
            sessions[session_id].append(event)
        
        # Create episode for each session
        for session_id, session_events in sessions.items():
            episode_body = self._format_session_events(session_events)
            
            await self.graphiti.add_episode(
                name=f"User Session {session_id}",
                episode_body=episode_body,
                source=EpisodeType.message,
                group_id=session_events[0].get('user_id', 'anonymous'),
                reference_time=datetime.fromisoformat(session_events[0]['timestamp'])
            )
    
    def _format_session_events(self, events: list[dict]) -> str:
        """Format session events as conversation."""
        formatted = []
        for event in sorted(events, key=lambda e: e['timestamp']):
            action = event.get('action', 'unknown')
            details = event.get('details', {})
            formatted.append(f"User performed {action}: {json.dumps(details)}")
        
        return '\n'.join(formatted)

# Kafka integration example
from aiokafka import AIOKafkaConsumer

async def consume_kafka_to_graphiti(
    graphiti: Graphiti,
    kafka_config: dict
):
    """Consume Kafka messages and ingest into Graphiti."""
    consumer = AIOKafkaConsumer(
        'events-topic',
        bootstrap_servers=kafka_config['servers'],
        group_id='graphiti-consumer',
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )
    
    streaming_graphiti = StreamingGraphiti(graphiti)
    
    await consumer.start()
    try:
        async for msg in consumer:
            event = msg.value
            await streaming_graphiti.ingest_stream_event(event)
    finally:
        await consumer.stop()
```

## Best Practices for Integration

### 1. Error Handling and Resilience

```python
class ResilientGraphiti:
    """Graphiti wrapper with comprehensive error handling."""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
        self.error_count = 0
        self.circuit_breaker_threshold = 5
        self.circuit_open = False
    
    async def add_episode_safe(self, **kwargs):
        """Add episode with error handling and circuit breaker."""
        if self.circuit_open:
            raise Exception("Circuit breaker is open")
        
        try:
            result = await self.graphiti.add_episode(**kwargs)
            self.error_count = 0  # Reset on success
            return result
        
        except RateLimitError as e:
            # Handle rate limiting with backoff
            self.error_count += 1
            if self.error_count >= self.circuit_breaker_threshold:
                self.circuit_open = True
                asyncio.create_task(self._reset_circuit_breaker())
            
            # Exponential backoff
            wait_time = min(2 ** self.error_count, 60)
            await asyncio.sleep(wait_time)
            
            # Retry once
            return await self.graphiti.add_episode(**kwargs)
        
        except Exception as e:
            # Log and re-raise other errors
            logger.error(f"Error adding episode: {e}")
            raise
    
    async def _reset_circuit_breaker(self):
        """Reset circuit breaker after cooldown."""
        await asyncio.sleep(300)  # 5 minute cooldown
        self.circuit_open = False
        self.error_count = 0
        logger.info("Circuit breaker reset")
```

### 2. Performance Monitoring

```python
class MonitoredGraphiti:
    """Graphiti with performance monitoring."""
    
    def __init__(self, graphiti: Graphiti, metrics_client):
        self.graphiti = graphiti
        self.metrics = metrics_client
    
    async def add_episode(self, **kwargs):
        """Add episode with metrics tracking."""
        start_time = time.time()
        
        try:
            result = await self.graphiti.add_episode(**kwargs)
            
            # Track success metrics
            duration = time.time() - start_time
            self.metrics.histogram('graphiti.episode.duration', duration)
            self.metrics.increment('graphiti.episode.success')
            
            # Track entity extraction metrics
            if hasattr(result, 'entity_count'):
                self.metrics.gauge('graphiti.entities.extracted', result.entity_count)
            
            return result
        
        except Exception as e:
            # Track failure metrics
            self.metrics.increment('graphiti.episode.failure')
            self.metrics.increment(f'graphiti.error.{type(e).__name__}')
            raise
    
    async def search(self, **kwargs):
        """Search with performance tracking."""
        start_time = time.time()
        
        results = await self.graphiti.search(**kwargs)
        
        # Track search metrics
        duration = time.time() - start_time
        self.metrics.histogram('graphiti.search.duration', duration)
        self.metrics.gauge('graphiti.search.results', len(results))
        
        return results
```

### 3. Testing Integration

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
async def mock_graphiti():
    """Create a mock Graphiti instance for testing."""
    with patch('graphiti_core.Graphiti') as MockGraphiti:
        instance = MockGraphiti.return_value
        
        # Mock methods
        instance.add_episode = AsyncMock(return_value=None)
        instance.search = AsyncMock(return_value=[])
        instance.build_indices_and_constraints = AsyncMock()
        
        # Mock driver
        instance.driver = AsyncMock()
        instance.driver.client = AsyncMock()
        
        yield instance

async def test_integration_with_mock(mock_graphiti):
    """Test integration with mocked Graphiti."""
    # Test episode addition
    await mock_graphiti.add_episode(
        name="Test Episode",
        episode_body="Test content",
        source=EpisodeType.text
    )
    
    mock_graphiti.add_episode.assert_called_once()
    
    # Test search
    results = await mock_graphiti.search(query="test")
    assert results == []
    mock_graphiti.search.assert_called_once_with(query="test")
```

## Conclusion

These integration patterns demonstrate how Graphiti can be seamlessly integrated into various AI architectures and workflows. The key principles are:

1. **Abstraction**: Use abstract interfaces for providers to enable easy switching
2. **Resilience**: Implement retry logic, circuit breakers, and error handling
3. **Performance**: Use batching, caching, and async processing for scale
4. **Monitoring**: Track metrics for observability in production
5. **Testing**: Mock external dependencies for reliable tests

The modular design of Graphiti makes it adaptable to any AI system that needs temporal knowledge graph capabilities, from simple chatbots to complex multi-agent systems.
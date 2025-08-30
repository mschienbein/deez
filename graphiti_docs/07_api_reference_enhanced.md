# Graphiti API Reference: Complete Implementation Guide

## Table of Contents
1. [Core Graphiti Class](#core-graphiti-class)
2. [Episode Management APIs](#episode-management-apis)
3. [Search APIs](#search-apis)
4. [Node APIs](#node-apis)
5. [Edge APIs](#edge-apis)
6. [Community APIs](#community-apis)
7. [Database Management APIs](#database-management-apis)
8. [Utility APIs](#utility-apis)
9. [Return Types and Models](#return-types-and-models)
10. [Error Handling](#error-handling)

## Core Graphiti Class

### Initialization

```python
# From graphiti_core/graphiti.py
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
        ensure_ascii: bool = False,
    ):
        """
        Initialize a Graphiti instance with comprehensive configuration.
        
        Parameters
        ----------
        uri : str | None
            The URI of the Neo4j database (e.g., 'bolt://localhost:7687')
        user : str | None
            Username for database authentication
        password : str | None
            Password for database authentication
        llm_client : LLMClient | None
            Custom LLM client (defaults to OpenAIClient)
        embedder : EmbedderClient | None
            Custom embedder (defaults to OpenAIEmbedder)
        cross_encoder : CrossEncoderClient | None
            Custom cross-encoder for reranking (defaults to OpenAIRerankerClient)
        store_raw_episode_content : bool
            Whether to store raw episode content (default: True)
        graph_driver : GraphDriver | None
            Custom graph driver (defaults to Neo4jDriver)
        max_coroutines : int | None
            Override SEMAPHORE_LIMIT for concurrent operations
        ensure_ascii : bool
            Escape non-ASCII in JSON (False preserves Unicode)
        """
        
        # Initialize graph driver
        if graph_driver:
            self.driver = graph_driver
        else:
            if uri is None:
                raise ValueError('uri must be provided when graph_driver is None')
            self.driver = Neo4jDriver(uri, user, password)
        
        # Store configuration
        self.store_raw_episode_content = store_raw_episode_content
        self.max_coroutines = max_coroutines
        self.ensure_ascii = ensure_ascii
        
        # Initialize AI clients with defaults
        self.llm_client = llm_client or OpenAIClient()
        self.embedder = embedder or OpenAIEmbedder()
        self.cross_encoder = cross_encoder or OpenAIRerankerClient()
        
        # Create unified clients object
        self.clients = GraphitiClients(
            driver=self.driver,
            llm_client=self.llm_client,
            embedder=self.embedder,
            cross_encoder=self.cross_encoder,
            ensure_ascii=self.ensure_ascii,
        )
        
        # Capture initialization telemetry
        self._capture_initialization_telemetry()
```

### Resource Management

```python
async def close(self):
    """
    Close database connection and release resources.
    
    Usage:
        graphiti = Graphiti(uri, user, password)
        try:
            # Use graphiti...
        finally:
            await graphiti.close()
    """
    await self.driver.close()
```

## Episode Management APIs

### add_episode

```python
async def add_episode(
    self,
    name: str,
    episode_body: str,
    source_description: str,
    reference_time: datetime,
    source: EpisodeType = EpisodeType.message,
    group_id: str | None = None,
    uuid: str | None = None,
    update_communities: bool = False,
    entity_types: dict[str, type[BaseModel]] | None = None,
    excluded_entity_types: list[str] | None = None,
    previous_episode_uuids: list[str] | None = None,
    edge_types: dict[str, type[BaseModel]] | None = None,
    edge_type_map: dict[tuple[str, str], list[str]] | None = None,
) -> AddEpisodeResults:
    """
    Process an episode and update the graph with extracted entities and relationships.
    
    This is the primary method for adding information to Graphiti. It performs:
    1. Entity extraction from text
    2. Relationship extraction
    3. Node deduplication
    4. Edge resolution and invalidation
    5. Community updates (optional)
    
    Parameters
    ----------
    name : str
        Name/title of the episode
    episode_body : str
        Content to process (text, JSON, or message format)
    source_description : str
        Description of the source (e.g., "customer chat", "API call")
    reference_time : datetime
        Temporal reference point for the episode
    source : EpisodeType
        Type of content: text, message, or json
    group_id : str | None
        Partition ID for multi-tenancy
    uuid : str | None
        Optional UUID (auto-generated if not provided)
    update_communities : bool
        Whether to update community nodes
    entity_types : dict[str, type[BaseModel]] | None
        Custom entity types for extraction
    excluded_entity_types : list[str] | None
        Entity types to exclude from extraction
    previous_episode_uuids : list[str] | None
        Specific episodes to use as context
    edge_types : dict[str, type[BaseModel]] | None
        Custom edge types for extraction
    edge_type_map : dict[tuple[str, str], list[str]] | None
        Mapping of node pairs to allowed edge types
    
    Returns
    -------
    AddEpisodeResults
        Contains created episode, nodes, edges, and communities
    
    Implementation Details
    ----------------------
    """
    try:
        start = time()
        now = utc_now()
        
        # Validate inputs
        group_id = group_id or get_default_group_id(self.driver.provider)
        validate_entity_types(entity_types)
        validate_excluded_entity_types(excluded_entity_types, entity_types)
        validate_group_id(group_id)
        
        # Build dynamic indexes for the group
        await build_dynamic_indexes(self.driver, group_id)
        
        # Get previous episodes for context
        previous_episodes = (
            await self.retrieve_episodes(
                reference_time,
                last_n=RELEVANT_SCHEMA_LIMIT,
                group_ids=[group_id],
                source=source,
            )
            if previous_episode_uuids is None
            else await EpisodicNode.get_by_uuids(self.driver, previous_episode_uuids)
        )
        
        # Create or retrieve episode node
        episode = (
            await EpisodicNode.get_by_uuid(self.driver, uuid)
            if uuid is not None
            else EpisodicNode(
                name=name,
                group_id=group_id,
                labels=[],
                source=source,
                content=episode_body,
                source_description=source_description,
                created_at=now,
                valid_at=reference_time,
            )
        )
        
        # Extract entities as nodes
        extracted_nodes = await extract_nodes(
            self.clients, episode, previous_episodes, entity_types, excluded_entity_types
        )
        
        # Parallel extraction and resolution
        (nodes, uuid_map, node_duplicates), extracted_edges = await semaphore_gather(
            resolve_extracted_nodes(
                self.clients,
                extracted_nodes,
                episode,
                previous_episodes,
                entity_types,
            ),
            extract_edges(
                self.clients,
                episode,
                extracted_nodes,
                previous_episodes,
                edge_type_map or {('Entity', 'Entity'): []},
                group_id,
                edge_types,
            ),
            max_coroutines=self.max_coroutines,
        )
        
        # Resolve edge pointers after deduplication
        edges = resolve_edge_pointers(extracted_edges, uuid_map)
        
        # Resolve edges and extract attributes in parallel
        (resolved_edges, invalidated_edges), hydrated_nodes = await semaphore_gather(
            resolve_extracted_edges(
                self.clients,
                edges,
                episode,
                nodes,
                edge_types or {},
                edge_type_map or {('Entity', 'Entity'): []},
            ),
            extract_attributes_from_nodes(
                self.clients, nodes, episode, previous_episodes, entity_types
            ),
            max_coroutines=self.max_coroutines,
        )
        
        # Build all edge types
        duplicate_of_edges = build_duplicate_of_edges(episode, now, node_duplicates)
        entity_edges = resolved_edges + invalidated_edges + duplicate_of_edges
        episodic_edges = build_episodic_edges(nodes, episode.uuid, now)
        
        episode.entity_edges = [edge.uuid for edge in entity_edges]
        
        # Clear content if not storing raw
        if not self.store_raw_episode_content:
            episode.content = ''
        
        # Bulk save to database
        await add_nodes_and_edges_bulk(
            self.driver, [episode], episodic_edges, hydrated_nodes, entity_edges, self.embedder
        )
        
        # Update communities if requested
        communities = []
        community_edges = []
        if update_communities:
            community_results = await semaphore_gather(
                *[
                    update_community(
                        self.driver, self.llm_client, self.embedder, node, self.ensure_ascii
                    )
                    for node in nodes
                ],
                max_coroutines=self.max_coroutines,
            )
            # Flatten results
            for comm_nodes, comm_edges in community_results:
                communities.extend(comm_nodes)
                community_edges.extend(comm_edges)
        
        end = time()
        logger.info(f'Completed add_episode in {(end - start) * 1000} ms')
        
        return AddEpisodeResults(
            episode=episode,
            episodic_edges=episodic_edges,
            nodes=hydrated_nodes,
            edges=entity_edges,
            communities=communities,
            community_edges=community_edges,
        )
    
    except Exception as e:
        capture_event('add_episode_failed', {'error': str(e)})
        raise
```

### add_episode_bulk

```python
async def add_episode_bulk(
    self,
    episodes: list[RawEpisode],
    group_id: str | None = None,
    update_communities: bool = False,
    entity_types: dict[str, type[BaseModel]] | None = None,
    excluded_entity_types: list[str] | None = None,
    edge_types: dict[str, type[BaseModel]] | None = None,
    edge_type_map: dict[tuple[str, str], list[str]] | None = None,
):
    """
    Efficiently process multiple episodes in bulk.
    
    Optimizations:
    - Batch entity/edge extraction
    - Shared deduplication across episodes
    - Single database transaction
    - Parallel processing with semaphore control
    
    Parameters
    ----------
    episodes : list[RawEpisode]
        List of episodes to process
    group_id : str | None
        Partition for all episodes
    update_communities : bool
        Update communities after processing
    entity_types : dict[str, type[BaseModel]] | None
        Custom entity types
    excluded_entity_types : list[str] | None
        Entity types to exclude
    edge_types : dict[str, type[BaseModel]] | None
        Custom edge types
    edge_type_map : dict[tuple[str, str], list[str]] | None
        Node pair to edge type mapping
    """
    start = time()
    now = utc_now()
    
    # Validate inputs
    group_id = group_id or get_default_group_id(self.driver.provider)
    validate_entity_types(entity_types)
    validate_excluded_entity_types(excluded_entity_types, entity_types)
    validate_group_id(group_id)
    
    # Build indexes once for the group
    await build_dynamic_indexes(self.driver, group_id)
    
    # Create episode nodes
    episodic_nodes = []
    for raw_episode in episodes:
        episodic_node = EpisodicNode(
            name=raw_episode.name,
            group_id=group_id,
            labels=[],
            source=raw_episode.source,
            content=raw_episode.content,
            source_description=raw_episode.source_description,
            created_at=now,
            valid_at=raw_episode.reference_time,
        )
        if raw_episode.uuid is not None:
            episodic_node.uuid = raw_episode.uuid
        episodic_nodes.append(episodic_node)
    
    # Get previous episodes for each new episode
    episode_tuples = await retrieve_previous_episodes_bulk(self.driver, episodic_nodes)
    
    # Extract nodes and edges in bulk
    extracted_nodes_bulk, extracted_edges_bulk = await extract_nodes_and_edges_bulk(
        self.clients,
        episode_tuples,
        edge_type_map or {('Entity', 'Entity'): []},
        entity_types,
        excluded_entity_types,
        edge_types,
    )
    
    # Deduplicate nodes across all episodes
    nodes_by_episode, node_uuid_map = await dedupe_nodes_bulk(
        self.clients, extracted_nodes_bulk, episode_tuples, entity_types
    )
    
    # Deduplicate edges across all episodes
    edges_by_episode = await dedupe_edges_bulk(
        self.clients,
        extracted_edges_bulk,
        episode_tuples,
        [],  # entities placeholder
        edge_types or {},
        edge_type_map or {('Entity', 'Entity'): []},
    )
    
    # Collect all unique nodes and edges
    all_nodes = []
    all_edges = []
    seen_node_uuids = set()
    seen_edge_uuids = set()
    
    for episode in episodic_nodes:
        episode_nodes = nodes_by_episode.get(episode.uuid, [])
        episode_edges = edges_by_episode.get(episode.uuid, [])
        
        for node in episode_nodes:
            if node.uuid not in seen_node_uuids:
                all_nodes.append(node)
                seen_node_uuids.add(node.uuid)
        
        for edge in episode_edges:
            if edge.uuid not in seen_edge_uuids:
                all_edges.append(edge)
                seen_edge_uuids.add(edge.uuid)
        
        # Build episodic edges
        episodic_edges.extend(build_episodic_edges(episode_nodes, episode.uuid, now))
        
        # Store edge references in episode
        episode.entity_edges = [edge.uuid for edge in episode_edges]
        
        # Clear content if configured
        if not self.store_raw_episode_content:
            episode.content = ''
    
    # Bulk save everything
    await add_nodes_and_edges_bulk(
        self.driver, episodic_nodes, episodic_edges, all_nodes, all_edges, self.embedder
    )
    
    # Update communities if requested
    if update_communities:
        await build_communities(self.driver, self.llm_client, [group_id], self.ensure_ascii)
    
    end = time()
    logger.info(f'Completed add_episode_bulk for {len(episodes)} episodes in {(end - start) * 1000} ms')
```

### retrieve_episodes

```python
async def retrieve_episodes(
    self,
    reference_time: datetime,
    last_n: int = EPISODE_WINDOW_LEN,
    source: EpisodeType | None = None,
    group_ids: list[str] | None = None,
) -> list[EpisodicNode]:
    """
    Retrieve recent episodes for context.
    
    Parameters
    ----------
    reference_time : datetime
        Point in time to retrieve episodes before
    last_n : int
        Maximum number of episodes to retrieve
    source : EpisodeType | None
        Filter by episode source type
    group_ids : list[str] | None
        Filter by group IDs
    
    Returns
    -------
    list[EpisodicNode]
        List of episodes ordered by recency
    """
    return await retrieve_episodes(self.driver, reference_time, last_n, group_ids, source)
```

### remove_episode

```python
async def remove_episode(self, episode_uuid: str):
    """
    Remove an episode and its associated data.
    
    Logic:
    1. Find edges created by this episode
    2. Delete edges where this episode is the creator
    3. Find nodes only mentioned by this episode
    4. Delete orphaned nodes
    5. Delete the episode itself
    
    Parameters
    ----------
    episode_uuid : str
        UUID of episode to remove
    """
    # Find the episode
    episode = await EpisodicNode.get_by_uuid(self.driver, episode_uuid)
    
    # Find edges mentioned by the episode
    edges = await EntityEdge.get_by_uuids(self.driver, episode.entity_edges)
    
    # Delete edges created by this episode
    edges_to_delete: list[EntityEdge] = []
    for edge in edges:
        if edge.episodes and edge.episodes[0] == episode.uuid:
            edges_to_delete.append(edge)
    
    # Find nodes mentioned by the episode
    nodes = await get_mentioned_nodes(self.driver, [episode])
    
    # Delete nodes only mentioned in this episode
    nodes_to_delete: list[EntityNode] = []
    for node in nodes:
        query: LiteralString = '''
            MATCH (e:Episodic)-[:MENTIONS]->(n:Entity {uuid: $uuid}) 
            RETURN count(*) AS episode_count
        '''
        records, _, _ = await self.driver.execute_query(
            query, uuid=node.uuid, routing_='r'
        )
        
        for record in records:
            if record['episode_count'] == 1:
                nodes_to_delete.append(node)
    
    # Execute deletions
    await Edge.delete_by_uuids(self.driver, [edge.uuid for edge in edges_to_delete])
    await Node.delete_by_uuids(self.driver, [node.uuid for node in nodes_to_delete])
    await episode.delete(self.driver)
```

## Search APIs

### search (Basic)

```python
async def search(
    self,
    query: str,
    center_node_uuid: str | None = None,
    group_ids: list[str] | None = None,
    num_results=DEFAULT_SEARCH_LIMIT,
    search_filter: SearchFilters | None = None,
) -> list[EntityEdge]:
    """
    Basic hybrid search returning facts as edges.
    
    Uses RRF (Reciprocal Rank Fusion) by default, or node distance
    reranking when a center node is provided.
    
    Parameters
    ----------
    query : str
        Search query
    center_node_uuid : str | None
        Center node for proximity reranking
    group_ids : list[str] | None
        Filter by groups
    num_results : int
        Maximum results (default: 10)
    search_filter : SearchFilters | None
        Additional filters
    
    Returns
    -------
    list[EntityEdge]
        Relevant facts as edges
    """
    search_config = (
        EDGE_HYBRID_SEARCH_RRF 
        if center_node_uuid is None 
        else EDGE_HYBRID_SEARCH_NODE_DISTANCE
    )
    search_config.limit = num_results
    
    edges = (
        await search(
            self.clients,
            query,
            group_ids,
            search_config,
            search_filter if search_filter is not None else SearchFilters(),
            center_node_uuid,
        )
    ).edges
    
    return edges
```

### search_ (Advanced)

```python
async def search_(
    self,
    query: str,
    config: SearchConfig = COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
    group_ids: list[str] | None = None,
    center_node_uuid: str | None = None,
    bfs_origin_node_uuids: list[str] | None = None,
    search_filter: SearchFilters | None = None,
) -> SearchResults:
    """
    Advanced search with full control over search strategy.
    
    Returns complete graph structures (nodes and edges) with
    configurable search algorithms and reranking.
    
    Parameters
    ----------
    query : str
        Search query
    config : SearchConfig
        Search configuration (see search_config_recipes)
    group_ids : list[str] | None
        Filter by groups
    center_node_uuid : str | None
        Center for proximity ranking
    bfs_origin_node_uuids : list[str] | None
        Starting nodes for BFS traversal
    search_filter : SearchFilters | None
        Advanced filters
    
    Returns
    -------
    SearchResults
        Complete results with nodes, edges, and episodes
    
    Available Configurations
    ------------------------
    - COMBINED_HYBRID_SEARCH_CROSS_ENCODER: Best quality with cross-encoder reranking
    - EDGE_HYBRID_SEARCH_RRF: Fast hybrid search with RRF fusion
    - EDGE_HYBRID_SEARCH_NODE_DISTANCE: Proximity-based reranking
    - NODE_HYBRID_SEARCH_RRF: Node-focused search
    - BFS_SEARCH: Graph traversal from origin nodes
    """
    return await search(
        self.clients,
        query,
        group_ids,
        config,
        search_filter if search_filter is not None else SearchFilters(),
        center_node_uuid,
        bfs_origin_node_uuids,
    )
```

### get_nodes_and_edges_by_episode

```python
async def get_nodes_and_edges_by_episode(
    self, 
    episode_uuids: list[str]
) -> SearchResults:
    """
    Retrieve all nodes and edges associated with specific episodes.
    
    Parameters
    ----------
    episode_uuids : list[str]
        List of episode UUIDs
    
    Returns
    -------
    SearchResults
        All nodes and edges from the episodes
    """
    episodes = await EpisodicNode.get_by_uuids(self.driver, episode_uuids)
    
    # Get edges in parallel
    edges_list = await semaphore_gather(
        *[EntityEdge.get_by_uuids(self.driver, episode.entity_edges) 
          for episode in episodes],
        max_coroutines=self.max_coroutines,
    )
    
    # Flatten edge lists
    edges: list[EntityEdge] = [edge for lst in edges_list for edge in lst]
    
    # Get all mentioned nodes
    nodes = await get_mentioned_nodes(self.driver, episodes)
    
    return SearchResults(edges=edges, nodes=nodes)
```

## Node APIs

### EntityNode Operations

```python
# From graphiti_core/nodes.py
class EntityNode(Node):
    """Entity node representing a concept, person, place, or thing."""
    
    @classmethod
    async def get_by_uuid(cls, driver: GraphDriver, uuid: str) -> 'EntityNode':
        """Retrieve entity node by UUID."""
        query = """
        MATCH (n:Entity {uuid: $uuid})
        RETURN n
        """
        records, _, _ = await driver.execute_query(query, uuid=uuid)
        if not records:
            raise NodeNotFoundError(uuid)
        return cls(**records[0]['n'])
    
    @classmethod
    async def get_by_group_ids(
        cls, 
        driver: GraphDriver, 
        group_ids: list[str]
    ) -> list['EntityNode']:
        """Retrieve all entity nodes in specified groups."""
        query = """
        MATCH (n:Entity)
        WHERE n.group_id IN $group_ids
        RETURN n
        ORDER BY n.created_at DESC
        """
        records, _, _ = await driver.execute_query(query, group_ids=group_ids)
        return [cls(**record['n']) for record in records]
    
    async def generate_name_embedding(self, embedder: EmbedderClient):
        """Generate embedding for node name."""
        self.name_embedding = await embedder.create_embedding(self.name)
    
    async def save(self, driver: GraphDriver):
        """Save or update node in database."""
        query = """
        MERGE (n:Entity {uuid: $uuid})
        SET n = $properties
        SET n.created_at = COALESCE(n.created_at, $created_at)
        WITH n
        CALL db.create.setNodeVectorProperty(n, 'name_embedding', $name_embedding)
        RETURN n
        """
        properties = self.model_dump(exclude={'name_embedding'})
        await driver.execute_query(
            query,
            uuid=self.uuid,
            properties=properties,
            created_at=self.created_at,
            name_embedding=self.name_embedding
        )
```

### CommunityNode Operations

```python
# From graphiti_core/nodes.py
class CommunityNode(Node):
    """Community node representing a cluster of related entities."""
    
    summary: str | None = Field(default=None)
    
    async def build_from_entities(
        self,
        llm_client: LLMClient,
        entities: list[EntityNode],
        ensure_ascii: bool = False
    ):
        """Build community summary from member entities."""
        # Hierarchical summarization
        summaries = [entity.summary for entity in entities]
        
        while len(summaries) > 1:
            # Pairwise summarization
            new_summaries = []
            for i in range(0, len(summaries), 2):
                if i + 1 < len(summaries):
                    pair_summary = await summarize_pair(
                        llm_client,
                        (summaries[i], summaries[i + 1]),
                        ensure_ascii
                    )
                    new_summaries.append(pair_summary)
                else:
                    new_summaries.append(summaries[i])
            summaries = new_summaries
        
        self.summary = summaries[0]
        self.name = await generate_summary_description(
            llm_client, self.summary, ensure_ascii
        )
```

## Edge APIs

### EntityEdge Operations

```python
# From graphiti_core/edges.py
class EntityEdge(Edge):
    """Edge representing a relationship between entities."""
    
    fact: str
    fact_embedding: list[float] | None = Field(default=None, exclude=True)
    episodes: list[str] = Field(default_factory=list)
    expired_at: datetime | None = Field(default=None)
    valid_at: datetime | None = Field(default=None)
    invalid_at: datetime | None = Field(default=None)
    
    @classmethod
    async def get_by_uuid(cls, driver: GraphDriver, uuid: str) -> 'EntityEdge':
        """Retrieve edge by UUID."""
        if driver.provider == GraphProvider.KUZU:
            query = """
            MATCH (s:Entity)-[r:RELATES_TO {uuid: $uuid}]-(re:RelatesToNode_)-[r2:RELATES_TO]-(t:Entity)
            RETURN r, re, r2, s.uuid AS source_uuid, t.uuid AS target_uuid
            """
        else:
            query = """
            MATCH (s:Entity)-[r:RELATES_TO {uuid: $uuid}]->(t:Entity)
            RETURN r, s.uuid AS source_uuid, t.uuid AS target_uuid
            """
        
        records, _, _ = await driver.execute_query(query, uuid=uuid)
        if not records:
            raise EdgeNotFoundError(uuid)
        
        return cls.from_record(records[0], driver.provider)
    
    async def generate_embedding(self, embedder: EmbedderClient):
        """Generate embedding for fact text."""
        self.fact_embedding = await embedder.create_embedding(self.fact)
    
    async def invalidate(self, invalidated_at: datetime):
        """Mark edge as invalidated at specific time."""
        self.invalid_at = invalidated_at
        self.expired_at = invalidated_at
```

### add_triplet

```python
async def add_triplet(
    self, 
    source_node: EntityNode, 
    edge: EntityEdge, 
    target_node: EntityNode
):
    """
    Add a single triplet (source, edge, target) to the graph.
    
    Handles:
    - Node deduplication
    - Edge resolution
    - Embedding generation
    - Database persistence
    
    Parameters
    ----------
    source_node : EntityNode
        Source entity
    edge : EntityEdge
        Relationship
    target_node : EntityNode
        Target entity
    """
    # Generate embeddings if needed
    if source_node.name_embedding is None:
        await source_node.generate_name_embedding(self.embedder)
    if target_node.name_embedding is None:
        await target_node.generate_name_embedding(self.embedder)
    if edge.fact_embedding is None:
        await edge.generate_embedding(self.embedder)
    
    # Resolve nodes (deduplication)
    nodes, uuid_map, _ = await resolve_extracted_nodes(
        self.clients,
        [source_node, target_node],
    )
    
    # Update edge pointers after deduplication
    updated_edge = resolve_edge_pointers([edge], uuid_map)[0]
    
    # Find related edges for context
    related_edges = (await get_relevant_edges(
        self.driver, [updated_edge], SearchFilters()
    ))[0]
    
    # Find edges to potentially invalidate
    existing_edges = (await get_edge_invalidation_candidates(
        self.driver, [updated_edge], SearchFilters()
    ))[0]
    
    # Resolve edge (may invalidate existing edges)
    resolved_edge, invalidated_edges, _ = await resolve_extracted_edge(
        self.llm_client,
        updated_edge,
        related_edges,
        existing_edges,
        EpisodicNode(  # Dummy episode for context
            name='',
            source=EpisodeType.text,
            source_description='',
            content='',
            valid_at=edge.valid_at or utc_now(),
            entity_edges=[],
            group_id=edge.group_id,
        ),
        None,
        self.ensure_ascii,
    )
    
    edges: list[EntityEdge] = [resolved_edge] + invalidated_edges
    
    # Generate embeddings for all edges
    await create_entity_edge_embeddings(self.embedder, edges)
    await create_entity_node_embeddings(self.embedder, nodes)
    
    # Save to database
    await add_nodes_and_edges_bulk(
        self.driver, [], [], nodes, edges, self.embedder
    )
```

## Community APIs

### build_communities

```python
async def build_communities(self, group_ids: list[str] | None = None):
    """
    Build community nodes from entity clusters.
    
    Process:
    1. Detect communities using label propagation
    2. Hierarchically summarize each community
    3. Create community nodes and edges
    
    Parameters
    ----------
    group_ids : list[str] | None
        Groups to build communities for
    """
    await remove_communities(self.driver)  # Clear existing
    
    community_nodes, community_edges = await build_communities(
        self.driver,
        self.llm_client,
        group_ids,
        self.ensure_ascii
    )
    
    # Save communities
    for node in community_nodes:
        await node.save(self.driver)
    for edge in community_edges:
        await edge.save(self.driver)
```

## Database Management APIs

### build_indices_and_constraints

```python
async def build_indices_and_constraints(self, delete_existing: bool = False):
    """
    Create database indices and constraints for optimal performance.
    
    Creates:
    - Unique constraints on UUIDs
    - Vector indices for similarity search
    - Composite indices for common queries
    - Full-text search indices
    
    Parameters
    ----------
    delete_existing : bool
        Whether to drop existing indices first
    """
    if delete_existing:
        await self.driver.execute_query("DROP INDEX IF EXISTS *")
    
    # Unique constraints
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Entity) REQUIRE n.uuid IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Episodic) REQUIRE n.uuid IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Community) REQUIRE n.uuid IS UNIQUE",
    ]
    
    # Vector indices for embeddings
    vector_indices = [
        """CREATE VECTOR INDEX entity_name_embedding IF NOT EXISTS 
           FOR (n:Entity) ON (n.name_embedding) 
           OPTIONS {indexConfig: {
               `vector.dimensions`: 1536, 
               `vector.similarity_function`: 'cosine'
           }}""",
        """CREATE VECTOR INDEX entity_fact_embedding IF NOT EXISTS 
           FOR ()-[r:RELATES_TO]-() ON (r.fact_embedding) 
           OPTIONS {indexConfig: {
               `vector.dimensions`: 1536, 
               `vector.similarity_function`: 'cosine'
           }}""",
    ]
    
    # Composite indices for queries
    composite_indices = [
        "CREATE INDEX entity_group_created IF NOT EXISTS FOR (n:Entity) ON (n.group_id, n.created_at)",
        "CREATE INDEX edge_group_created IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.group_id, r.created_at)",
        "CREATE INDEX episode_group_valid IF NOT EXISTS FOR (n:Episodic) ON (n.group_id, n.valid_at)",
    ]
    
    # Full-text search indices
    fulltext_indices = [
        "CREATE FULLTEXT INDEX entity_name_summary IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.summary]",
        "CREATE FULLTEXT INDEX edge_fact IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON EACH [r.fact]",
    ]
    
    # Execute all index creation
    for constraint in constraints:
        await self.driver.execute_query(constraint)
    
    for index in vector_indices + composite_indices + fulltext_indices:
        await self.driver.execute_query(index)
    
    await build_indices_and_constraints(self.driver)
```

## Return Types and Models

### AddEpisodeResults

```python
class AddEpisodeResults(BaseModel):
    """Results from adding an episode."""
    episode: EpisodicNode
    episodic_edges: list[EpisodicEdge]
    nodes: list[EntityNode]
    edges: list[EntityEdge]
    communities: list[CommunityNode]
    community_edges: list[CommunityEdge]
```

### SearchResults

```python
# From graphiti_core/search/search_config.py
class SearchResults(BaseModel):
    """Complete search results."""
    nodes: list[EntityNode] = Field(default_factory=list)
    edges: list[EntityEdge] = Field(default_factory=list)
    episodes: list[EpisodicNode] = Field(default_factory=list)
```

### SearchConfig

```python
# From graphiti_core/search/search.py
class SearchConfig(BaseModel):
    """Configuration for search behavior."""
    # Search methods
    semantics: SearchMethod
    semantics_weight: float = 1.0
    bm25: SearchMethod | None = None
    bm25_weight: float = 1.0
    graph_traversal: SearchMethod | None = None
    graph_traversal_weight: float = 1.0
    
    # Reranking
    reranker: RerankMethod | None = None
    reranker_weight: float = 1.0
    
    # Limits
    limit: int = DEFAULT_SEARCH_LIMIT
    
    # Fusion method
    fusion_method: FusionMethod = FusionMethod.reciprocal_rank_fusion
```

## Error Handling

### Custom Exceptions

```python
# From graphiti_core/errors.py
class GraphitiError(Exception):
    """Base exception for Graphiti."""
    pass

class NodeNotFoundError(GraphitiError):
    """Raised when a node is not found."""
    def __init__(self, uuid: str):
        self.uuid = uuid
        self.message = f"Node with UUID {uuid} not found"
        super().__init__(self.message)

class EdgeNotFoundError(GraphitiError):
    """Raised when an edge is not found."""
    def __init__(self, uuid: str):
        self.uuid = uuid
        self.message = f"Edge with UUID {uuid} not found"
        super().__init__(self.message)

class GroupIdValidationError(GraphitiError):
    """Raised when group_id contains invalid characters."""
    def __init__(self, group_id: str):
        self.group_id = group_id
        self.message = f"Invalid group_id '{group_id}': must contain only alphanumeric characters, dashes, and underscores"
        super().__init__(self.message)

class EntityTypeValidationError(GraphitiError):
    """Raised when entity types are invalid."""
    pass
```

### Error Handling Patterns

```python
# Retry with exponential backoff
@retry(
    stop=stop_after_attempt(4),
    wait=wait_random_exponential(multiplier=10, min=5, max=120),
    retry=retry_if_exception(is_server_or_retry_error),
    reraise=True,
)
async def robust_api_call():
    """API call with automatic retry."""
    pass

# Graceful degradation
try:
    result = await graphiti.add_episode(...)
except RateLimitError:
    # Queue for later processing
    await queue_episode_for_retry(...)
except NodeNotFoundError as e:
    # Handle missing node
    logger.warning(f"Node {e.uuid} not found, creating new")
    await create_node(...)
except Exception as e:
    # Capture telemetry and re-raise
    capture_event('unexpected_error', {'error': str(e)})
    raise
```

## Usage Examples

### Basic Usage

```python
# Initialize
graphiti = Graphiti(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)

# Add episode
result = await graphiti.add_episode(
    name="Customer Feedback",
    episode_body="The customer loves the new feature but wants dark mode",
    source_description="support ticket",
    reference_time=datetime.now(timezone.utc),
    group_id="customer_123"
)

# Search
facts = await graphiti.search(
    query="What does the customer want?",
    group_ids=["customer_123"],
    num_results=5
)

# Advanced search
results = await graphiti.search_(
    query="customer preferences",
    config=COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
    group_ids=["customer_123"]
)

# Clean up
await graphiti.close()
```

### Custom Entity Types

```python
from pydantic import BaseModel, Field

class ProductEntity(BaseModel):
    """Custom product entity."""
    product_id: str = Field(description="Product identifier")
    category: str = Field(description="Product category")
    price: float = Field(description="Product price")

# Use custom entities
result = await graphiti.add_episode(
    name="Product Catalog Update",
    episode_body=product_data_json,
    source=EpisodeType.json,
    source_description="product API",
    reference_time=datetime.now(timezone.utc),
    entity_types={
        "Product": ProductEntity
    }
)
```

### Bulk Processing

```python
episodes = [
    RawEpisode(
        name=f"Message {i}",
        content=message,
        source_description="chat",
        source=EpisodeType.message,
        reference_time=timestamp
    )
    for i, (message, timestamp) in enumerate(messages_with_timestamps)
]

await graphiti.add_episode_bulk(
    episodes=episodes,
    group_id="conversation_456",
    update_communities=True
)
```

## Conclusion

The Graphiti API provides a comprehensive interface for building and querying temporal knowledge graphs. Key design principles:

1. **Async-First**: All operations are async for maximum performance
2. **Flexible**: Supports custom entity/edge types and search configurations
3. **Scalable**: Bulk operations and semaphore-controlled concurrency
4. **Robust**: Comprehensive error handling and retry logic
5. **Extensible**: Plugin architecture for LLMs, embedders, and databases

The API balances ease of use (simple search() method) with power (advanced search_() with full configuration), making it suitable for both simple applications and complex AI systems.
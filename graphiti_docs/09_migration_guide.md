# Migration Guide to Graphiti

## Table of Contents
1. [Migration from Traditional RAG](#migration-from-traditional-rag)
2. [Migration from GraphRAG](#migration-from-graphrag)
3. [Migration from Vector Databases](#migration-from-vector-databases)
4. [Migration from MemGPT](#migration-from-memgpt)
5. [Migration from Raw Neo4j](#migration-from-raw-neo4j)
6. [Migration from Document Stores](#migration-from-document-stores)
7. [Migration from Chat Memory Systems](#migration-from-chat-memory-systems)
8. [Data Migration Strategies](#data-migration-strategies)
9. [API Migration Patterns](#api-migration-patterns)
10. [Post-Migration Validation](#post-migration-validation)

---

## Migration from Traditional RAG

### Understanding the Differences

Traditional RAG systems typically consist of:
- Document chunking and indexing
- Vector embeddings stored in a database
- Similarity search for retrieval
- Static document stores

Graphiti provides:
- Dynamic knowledge graph construction
- Temporal awareness of facts
- Relationship-based retrieval
- Continuous learning from interactions

### Migration Strategy

#### Step 1: Assess Current RAG System

```python
class RAGSystemAnalyzer:
    """Analyze existing RAG system for migration."""
    
    def __init__(self, existing_system):
        self.system = existing_system
        self.analysis = {}
    
    async def analyze(self):
        """Analyze the existing RAG system."""
        self.analysis = {
            "document_count": await self._count_documents(),
            "chunk_count": await self._count_chunks(),
            "average_chunk_size": await self._get_avg_chunk_size(),
            "embedding_dimensions": await self._get_embedding_dims(),
            "index_type": await self._get_index_type(),
            "metadata_schema": await self._get_metadata_schema()
        }
        
        return self.analysis
    
    async def _count_documents(self):
        """Count total documents in the system."""
        # Implementation depends on your RAG system
        return self.system.get_document_count()
    
    async def estimate_migration_time(self):
        """Estimate time required for migration."""
        doc_count = self.analysis["document_count"]
        chunk_count = self.analysis["chunk_count"]
        
        # Rough estimates (adjust based on your hardware)
        time_per_chunk = 0.1  # seconds
        estimated_seconds = chunk_count * time_per_chunk
        
        return {
            "estimated_hours": estimated_seconds / 3600,
            "recommended_batch_size": 100,
            "parallel_workers": 10
        }
```

#### Step 2: Export RAG Data

```python
class RAGExporter:
    """Export data from traditional RAG system."""
    
    def __init__(self, rag_system):
        self.rag_system = rag_system
    
    async def export_documents(
        self,
        output_dir: str,
        batch_size: int = 100
    ):
        """Export documents from RAG system."""
        os.makedirs(output_dir, exist_ok=True)
        
        documents = []
        async for doc_batch in self.rag_system.iterate_documents(batch_size):
            for doc in doc_batch:
                exported_doc = {
                    "id": doc.id,
                    "content": doc.content,
                    "metadata": doc.metadata,
                    "chunks": await self._export_chunks(doc.id),
                    "embeddings": await self._export_embeddings(doc.id)
                }
                documents.append(exported_doc)
            
            # Save batch
            batch_file = f"{output_dir}/batch_{len(documents)}.json"
            with open(batch_file, 'w') as f:
                json.dump(documents[-batch_size:], f)
        
        return len(documents)
    
    async def _export_chunks(self, doc_id: str):
        """Export chunks for a document."""
        chunks = await self.rag_system.get_chunks(doc_id)
        return [
            {
                "id": chunk.id,
                "text": chunk.text,
                "start": chunk.start,
                "end": chunk.end,
                "metadata": chunk.metadata
            }
            for chunk in chunks
        ]
```

#### Step 3: Transform to Graphiti Format

```python
class RAGToGraphitiTransformer:
    """Transform RAG data to Graphiti episodes."""
    
    def __init__(self, graphiti):
        self.graphiti = graphiti
    
    async def transform_documents(
        self,
        documents: List[Dict],
        preserve_chunks: bool = False
    ) -> List[RawEpisode]:
        """Transform RAG documents to Graphiti episodes."""
        episodes = []
        
        for doc in documents:
            if preserve_chunks:
                # Create episode for each chunk
                for chunk in doc.get("chunks", []):
                    episode = RawEpisode(
                        name=f"doc_{doc['id']}_chunk_{chunk['id']}",
                        content=chunk["text"],
                        source=EpisodeType.text,
                        source_description=f"RAG migration: {doc.get('metadata', {}).get('source', 'unknown')}",
                        reference_time=self._get_timestamp(doc),
                        metadata={
                            "original_doc_id": doc["id"],
                            "chunk_id": chunk["id"],
                            **doc.get("metadata", {})
                        }
                    )
                    episodes.append(episode)
            else:
                # Create single episode per document
                episode = RawEpisode(
                    name=f"doc_{doc['id']}",
                    content=doc["content"],
                    source=EpisodeType.text,
                    source_description=f"RAG migration: {doc.get('metadata', {}).get('source', 'unknown')}",
                    reference_time=self._get_timestamp(doc),
                    metadata=doc.get("metadata", {})
                )
                episodes.append(episode)
        
        return episodes
    
    def _get_timestamp(self, doc: Dict) -> datetime:
        """Extract or generate timestamp for document."""
        if "timestamp" in doc.get("metadata", {}):
            return datetime.fromisoformat(doc["metadata"]["timestamp"])
        elif "created_at" in doc:
            return datetime.fromisoformat(doc["created_at"])
        else:
            # Use current time if no timestamp available
            return datetime.now(timezone.utc)
```

#### Step 4: Import into Graphiti

```python
class RAGMigrator:
    """Complete RAG to Graphiti migration."""
    
    def __init__(self, rag_system, graphiti):
        self.rag_system = rag_system
        self.graphiti = graphiti
        self.exporter = RAGExporter(rag_system)
        self.transformer = RAGToGraphitiTransformer(graphiti)
    
    async def migrate(
        self,
        batch_size: int = 100,
        parallel_workers: int = 10,
        preserve_embeddings: bool = False
    ):
        """Execute complete migration."""
        logger.info("Starting RAG to Graphiti migration")
        
        # Step 1: Export from RAG
        logger.info("Exporting documents from RAG system...")
        export_dir = "/tmp/rag_export"
        doc_count = await self.exporter.export_documents(
            export_dir,
            batch_size
        )
        logger.info(f"Exported {doc_count} documents")
        
        # Step 2: Process in batches
        logger.info("Transforming and importing to Graphiti...")
        
        for batch_file in os.listdir(export_dir):
            if batch_file.endswith('.json'):
                with open(f"{export_dir}/{batch_file}", 'r') as f:
                    documents = json.load(f)
                
                # Transform to episodes
                episodes = await self.transformer.transform_documents(
                    documents,
                    preserve_chunks=True
                )
                
                # Import to Graphiti
                results = await self.graphiti.add_episodes_bulk(
                    episodes,
                    group_id="rag_migration"
                )
                
                logger.info(f"Imported batch: {len(results.episodes)} episodes")
        
        # Step 3: Verify migration
        verification = await self._verify_migration(doc_count)
        
        return {
            "documents_migrated": doc_count,
            "episodes_created": verification["episode_count"],
            "entities_extracted": verification["entity_count"],
            "relationships_created": verification["edge_count"]
        }
    
    async def _verify_migration(self, expected_count: int) -> Dict:
        """Verify migration success."""
        # Count episodes in migration group
        query = """
        MATCH (e:Episode {group_id: 'rag_migration'})
        RETURN count(e) as episode_count
        """
        result = await self.graphiti.driver.execute(query)
        
        return {
            "episode_count": result[0]["episode_count"],
            "entity_count": await self._count_entities(),
            "edge_count": await self._count_edges()
        }
```

### Migration Code Example

```python
# Complete RAG migration example
async def migrate_rag_to_graphiti():
    # Initialize systems
    rag_system = ExistingRAGSystem(
        vector_db_url="http://localhost:8000",
        api_key="..."
    )
    
    graphiti = Graphiti(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )
    
    # Analyze existing system
    analyzer = RAGSystemAnalyzer(rag_system)
    analysis = await analyzer.analyze()
    print(f"RAG System Analysis: {json.dumps(analysis, indent=2)}")
    
    # Estimate migration time
    time_estimate = await analyzer.estimate_migration_time()
    print(f"Estimated migration time: {time_estimate['estimated_hours']} hours")
    
    # Execute migration
    migrator = RAGMigrator(rag_system, graphiti)
    results = await migrator.migrate(
        batch_size=100,
        parallel_workers=10,
        preserve_embeddings=False
    )
    
    print(f"Migration complete: {results}")
    
    # Test new system
    test_query = "test search query"
    
    # Old RAG search
    rag_results = await rag_system.search(test_query)
    
    # New Graphiti search
    graphiti_results = await graphiti.search(test_query)
    
    print(f"RAG returned {len(rag_results)} results")
    print(f"Graphiti returned {len(graphiti_results)} results")
```

---

## Migration from GraphRAG

### Key Differences

GraphRAG (Microsoft) vs Graphiti:
- **GraphRAG**: Batch processing, community summarization, hierarchical structure
- **Graphiti**: Real-time updates, temporal awareness, dynamic relationships

### Migration Strategy

#### Step 1: Export GraphRAG Data

```python
class GraphRAGExporter:
    """Export data from GraphRAG system."""
    
    def __init__(self, graphrag_path: str):
        self.graphrag_path = graphrag_path
        self.entities = []
        self.relationships = []
        self.communities = []
    
    async def export_graph(self):
        """Export GraphRAG graph structure."""
        # Load GraphRAG parquet files
        import pandas as pd
        
        # Load entities
        entities_df = pd.read_parquet(
            f"{self.graphrag_path}/output/entities.parquet"
        )
        self.entities = entities_df.to_dict('records')
        
        # Load relationships
        relationships_df = pd.read_parquet(
            f"{self.graphrag_path}/output/relationships.parquet"
        )
        self.relationships = relationships_df.to_dict('records')
        
        # Load communities
        communities_df = pd.read_parquet(
            f"{self.graphrag_path}/output/communities.parquet"
        )
        self.communities = communities_df.to_dict('records')
        
        return {
            "entities": len(self.entities),
            "relationships": len(self.relationships),
            "communities": len(self.communities)
        }
    
    def get_entity_by_id(self, entity_id: str):
        """Get entity by ID."""
        for entity in self.entities:
            if entity.get("id") == entity_id:
                return entity
        return None
```

#### Step 2: Transform GraphRAG to Graphiti

```python
class GraphRAGToGraphitiTransformer:
    """Transform GraphRAG data to Graphiti format."""
    
    def __init__(self, graphiti):
        self.graphiti = graphiti
        self.entity_mapping = {}  # GraphRAG ID -> Graphiti UUID
    
    async def transform_entities(
        self,
        graphrag_entities: List[Dict]
    ) -> List[EntityNode]:
        """Transform GraphRAG entities to Graphiti nodes."""
        nodes = []
        
        for entity in graphrag_entities:
            # Create Graphiti node
            node = EntityNode(
                uuid=str(uuid4()),
                name=entity.get("name", "Unknown"),
                labels=[entity.get("type", "Entity")],
                summary=entity.get("description", ""),
                attributes={
                    "graphrag_id": entity.get("id"),
                    "graphrag_type": entity.get("type"),
                    **entity.get("attributes", {})
                }
            )
            
            # Store mapping
            self.entity_mapping[entity["id"]] = node.uuid
            nodes.append(node)
        
        return nodes
    
    async def transform_relationships(
        self,
        graphrag_relationships: List[Dict]
    ) -> List[EntityEdge]:
        """Transform GraphRAG relationships to Graphiti edges."""
        edges = []
        
        for rel in graphrag_relationships:
            source_id = rel.get("source")
            target_id = rel.get("target")
            
            # Map to Graphiti UUIDs
            source_uuid = self.entity_mapping.get(source_id)
            target_uuid = self.entity_mapping.get(target_id)
            
            if source_uuid and target_uuid:
                edge = EntityEdge(
                    uuid=str(uuid4()),
                    source_node_uuid=source_uuid,
                    target_node_uuid=target_uuid,
                    fact=rel.get("description", f"{rel.get('type', 'RELATES_TO')}"),
                    valid_at=datetime.now(timezone.utc),
                    confidence=rel.get("weight", 1.0),
                    attributes={
                        "graphrag_source": source_id,
                        "graphrag_target": target_id,
                        "graphrag_type": rel.get("type")
                    }
                )
                edges.append(edge)
        
        return edges
    
    async def transform_communities(
        self,
        graphrag_communities: List[Dict]
    ) -> List[CommunityNode]:
        """Transform GraphRAG communities to Graphiti communities."""
        communities = []
        
        for comm in graphrag_communities:
            # Create community node
            community = CommunityNode(
                uuid=str(uuid4()),
                name=f"Community_{comm.get('id', 'unknown')}",
                summary=comm.get("summary", ""),
                member_uuids=[
                    self.entity_mapping.get(member_id)
                    for member_id in comm.get("members", [])
                    if member_id in self.entity_mapping
                ],
                attributes={
                    "graphrag_id": comm.get("id"),
                    "level": comm.get("level", 0),
                    "size": len(comm.get("members", []))
                }
            )
            communities.append(community)
        
        return communities
```

#### Step 3: Import to Graphiti

```python
class GraphRAGMigrator:
    """Migrate from GraphRAG to Graphiti."""
    
    def __init__(self, graphrag_path: str, graphiti):
        self.exporter = GraphRAGExporter(graphrag_path)
        self.transformer = GraphRAGToGraphitiTransformer(graphiti)
        self.graphiti = graphiti
    
    async def migrate(self):
        """Execute complete migration."""
        logger.info("Starting GraphRAG to Graphiti migration")
        
        # Step 1: Export GraphRAG data
        export_stats = await self.exporter.export_graph()
        logger.info(f"Exported GraphRAG data: {export_stats}")
        
        # Step 2: Transform entities
        nodes = await self.transformer.transform_entities(
            self.exporter.entities
        )
        logger.info(f"Transformed {len(nodes)} entities")
        
        # Step 3: Transform relationships
        edges = await self.transformer.transform_relationships(
            self.exporter.relationships
        )
        logger.info(f"Transformed {len(edges)} relationships")
        
        # Step 4: Transform communities
        communities = await self.transformer.transform_communities(
            self.exporter.communities
        )
        logger.info(f"Transformed {len(communities)} communities")
        
        # Step 5: Import to Graphiti
        await self._import_to_graphiti(nodes, edges, communities)
        
        # Step 6: Recreate summaries as episodes
        await self._import_summaries()
        
        return {
            "entities_migrated": len(nodes),
            "relationships_migrated": len(edges),
            "communities_migrated": len(communities)
        }
    
    async def _import_to_graphiti(
        self,
        nodes: List[EntityNode],
        edges: List[EntityEdge],
        communities: List[CommunityNode]
    ):
        """Import transformed data to Graphiti."""
        # Batch import nodes
        for i in range(0, len(nodes), 100):
            batch = nodes[i:i+100]
            for node in batch:
                await self.graphiti.driver.execute(
                    """
                    CREATE (n:Entity {
                        uuid: $uuid,
                        name: $name,
                        summary: $summary,
                        created_at: $created_at
                    })
                    """,
                    {
                        "uuid": node.uuid,
                        "name": node.name,
                        "summary": node.summary,
                        "created_at": node.created_at.isoformat()
                    }
                )
        
        # Batch import edges
        for i in range(0, len(edges), 100):
            batch = edges[i:i+100]
            for edge in batch:
                await self.graphiti.driver.execute(
                    """
                    MATCH (s:Entity {uuid: $source_uuid})
                    MATCH (t:Entity {uuid: $target_uuid})
                    CREATE (s)-[r:RELATES_TO {
                        uuid: $uuid,
                        fact: $fact,
                        valid_at: $valid_at,
                        confidence: $confidence
                    }]->(t)
                    """,
                    {
                        "source_uuid": edge.source_node_uuid,
                        "target_uuid": edge.target_node_uuid,
                        "uuid": edge.uuid,
                        "fact": edge.fact,
                        "valid_at": edge.valid_at.isoformat(),
                        "confidence": edge.confidence
                    }
                )
    
    async def _import_summaries(self):
        """Import GraphRAG summaries as episodes."""
        for comm in self.exporter.communities:
            if comm.get("summary"):
                await self.graphiti.add_episode(
                    name=f"GraphRAG_Summary_{comm.get('id')}",
                    episode_body=comm["summary"],
                    source=EpisodeType.text,
                    source_description="GraphRAG community summary",
                    reference_time=datetime.now(timezone.utc),
                    group_id="graphrag_migration"
                )
```

---

## Migration from Vector Databases

### Common Vector Database Sources

- Pinecone
- Weaviate
- Qdrant
- Milvus
- ChromaDB
- FAISS

### Universal Vector DB Migration

```python
class VectorDBMigrator:
    """Universal vector database migrator."""
    
    def __init__(self, vector_db_type: str, graphiti):
        self.db_type = vector_db_type
        self.graphiti = graphiti
        self.client = self._get_client()
    
    def _get_client(self):
        """Get appropriate vector DB client."""
        if self.db_type == "pinecone":
            import pinecone
            return pinecone.Index("your-index")
        elif self.db_type == "weaviate":
            import weaviate
            return weaviate.Client("http://localhost:8080")
        elif self.db_type == "qdrant":
            from qdrant_client import QdrantClient
            return QdrantClient("localhost", port=6333)
        # Add more as needed
    
    async def migrate_collection(
        self,
        collection_name: str,
        batch_size: int = 100
    ):
        """Migrate a vector collection to Graphiti."""
        if self.db_type == "pinecone":
            await self._migrate_pinecone(collection_name, batch_size)
        elif self.db_type == "weaviate":
            await self._migrate_weaviate(collection_name, batch_size)
        elif self.db_type == "qdrant":
            await self._migrate_qdrant(collection_name, batch_size)
    
    async def _migrate_pinecone(
        self,
        index_name: str,
        batch_size: int
    ):
        """Migrate from Pinecone."""
        # Fetch all vectors with metadata
        index = self.client
        
        # Query all vectors (pagination required for large indexes)
        all_ids = []
        for ids in index.list(namespace=""):
            all_ids.extend(ids)
        
        # Process in batches
        for i in range(0, len(all_ids), batch_size):
            batch_ids = all_ids[i:i+batch_size]
            
            # Fetch vectors and metadata
            vectors = index.fetch(batch_ids)
            
            # Convert to episodes
            episodes = []
            for vec_id, vec_data in vectors.items():
                metadata = vec_data.get("metadata", {})
                
                episode = RawEpisode(
                    name=f"vector_{vec_id}",
                    content=metadata.get("text", ""),
                    source=EpisodeType.text,
                    source_description=f"Pinecone migration: {index_name}",
                    reference_time=self._parse_timestamp(metadata),
                    metadata={
                        "vector_id": vec_id,
                        "original_metadata": metadata
                    }
                )
                episodes.append(episode)
            
            # Import to Graphiti
            await self.graphiti.add_episodes_bulk(episodes)
    
    async def _migrate_weaviate(
        self,
        class_name: str,
        batch_size: int
    ):
        """Migrate from Weaviate."""
        offset = 0
        
        while True:
            # Query Weaviate
            result = (
                self.client.query
                .get(class_name)
                .with_additional(["id", "vector"])
                .with_limit(batch_size)
                .with_offset(offset)
                .do()
            )
            
            objects = result.get("data", {}).get("Get", {}).get(class_name, [])
            
            if not objects:
                break
            
            # Convert to episodes
            episodes = []
            for obj in objects:
                episode = RawEpisode(
                    name=f"weaviate_{obj['_additional']['id']}",
                    content=json.dumps(obj),
                    source=EpisodeType.json,
                    source_description=f"Weaviate migration: {class_name}",
                    reference_time=datetime.now(timezone.utc),
                    metadata=obj
                )
                episodes.append(episode)
            
            # Import to Graphiti
            await self.graphiti.add_episodes_bulk(episodes)
            
            offset += batch_size
    
    def _parse_timestamp(self, metadata: Dict) -> datetime:
        """Parse timestamp from metadata."""
        for key in ["timestamp", "created_at", "date"]:
            if key in metadata:
                try:
                    return datetime.fromisoformat(metadata[key])
                except:
                    pass
        return datetime.now(timezone.utc)
```

---

## Migration from MemGPT

### MemGPT to Graphiti Migration

```python
class MemGPTMigrator:
    """Migrate from MemGPT to Graphiti."""
    
    def __init__(self, memgpt_config: Dict, graphiti):
        self.memgpt = self._init_memgpt(memgpt_config)
        self.graphiti = graphiti
    
    def _init_memgpt(self, config: Dict):
        """Initialize MemGPT connection."""
        # MemGPT specific initialization
        from memgpt import MemGPT
        return MemGPT(**config)
    
    async def migrate_agent_memory(
        self,
        agent_id: str
    ):
        """Migrate a MemGPT agent's memory to Graphiti."""
        # Get agent memory
        memory = self.memgpt.get_agent_memory(agent_id)
        
        # Extract core memory
        core_memory = memory.get("core_memory", {})
        await self._migrate_core_memory(core_memory, agent_id)
        
        # Extract recall memory (conversation history)
        recall_memory = memory.get("recall_memory", [])
        await self._migrate_recall_memory(recall_memory, agent_id)
        
        # Extract archival memory
        archival_memory = memory.get("archival_memory", [])
        await self._migrate_archival_memory(archival_memory, agent_id)
    
    async def _migrate_core_memory(
        self,
        core_memory: Dict,
        agent_id: str
    ):
        """Migrate core memory as structured episodes."""
        # Core memory contains user and system information
        user_info = core_memory.get("human", {})
        system_info = core_memory.get("persona", {})
        
        # Create user profile episode
        if user_info:
            await self.graphiti.add_episode(
                name=f"MemGPT_User_Profile_{agent_id}",
                episode_body=json.dumps(user_info),
                source=EpisodeType.json,
                source_description="MemGPT core memory - user",
                reference_time=datetime.now(timezone.utc),
                group_id=f"memgpt_agent_{agent_id}"
            )
        
        # Create system profile episode
        if system_info:
            await self.graphiti.add_episode(
                name=f"MemGPT_System_Profile_{agent_id}",
                episode_body=json.dumps(system_info),
                source=EpisodeType.json,
                source_description="MemGPT core memory - system",
                reference_time=datetime.now(timezone.utc),
                group_id=f"memgpt_agent_{agent_id}"
            )
    
    async def _migrate_recall_memory(
        self,
        recall_memory: List[Dict],
        agent_id: str
    ):
        """Migrate conversation history."""
        episodes = []
        
        for i, message in enumerate(recall_memory):
            episode = RawEpisode(
                name=f"MemGPT_Message_{agent_id}_{i}",
                content=message.get("content", ""),
                source=EpisodeType.message,
                source_description=f"MemGPT recall - {message.get('role', 'unknown')}",
                reference_time=self._parse_message_timestamp(message),
                metadata={
                    "role": message.get("role"),
                    "message_id": message.get("id"),
                    "agent_id": agent_id
                }
            )
            episodes.append(episode)
        
        # Bulk import conversations
        if episodes:
            await self.graphiti.add_episodes_bulk(
                episodes,
                group_id=f"memgpt_agent_{agent_id}"
            )
    
    async def _migrate_archival_memory(
        self,
        archival_memory: List[Dict],
        agent_id: str
    ):
        """Migrate archival memory (long-term storage)."""
        episodes = []
        
        for entry in archival_memory:
            episode = RawEpisode(
                name=f"MemGPT_Archive_{agent_id}_{entry.get('id', uuid4())}",
                content=entry.get("content", ""),
                source=EpisodeType.text,
                source_description="MemGPT archival memory",
                reference_time=self._parse_timestamp(entry),
                metadata={
                    "importance": entry.get("importance", 0),
                    "agent_id": agent_id,
                    **entry.get("metadata", {})
                }
            )
            episodes.append(episode)
        
        if episodes:
            await self.graphiti.add_episodes_bulk(
                episodes,
                group_id=f"memgpt_agent_{agent_id}"
            )
```

---

## Migration from Raw Neo4j

### Neo4j to Graphiti Enhancement

If you already have a Neo4j graph but want Graphiti's features:

```python
class Neo4jEnhancer:
    """Enhance existing Neo4j graph with Graphiti features."""
    
    def __init__(self, existing_neo4j_driver, graphiti):
        self.existing = existing_neo4j_driver
        self.graphiti = graphiti
    
    async def enhance_with_temporal_model(self):
        """Add temporal properties to existing relationships."""
        # Add temporal properties to all relationships
        query = """
        MATCH ()-[r]->()
        WHERE r.valid_at IS NULL
        SET r.valid_at = datetime(),
            r.invalid_at = null,
            r.created_at = COALESCE(r.created_at, datetime())
        RETURN count(r) as updated_count
        """
        
        result = await self.existing.execute(query)
        logger.info(f"Added temporal properties to {result[0]['updated_count']} relationships")
    
    async def extract_episodes_from_nodes(self):
        """Convert existing nodes to episodes for reprocessing."""
        # Query existing nodes
        query = """
        MATCH (n)
        WHERE NOT n:Episode
        RETURN n
        LIMIT 1000
        """
        
        nodes = await self.existing.execute(query)
        
        episodes = []
        for record in nodes:
            node = record['n']
            
            # Create episode from node content
            content = self._node_to_text(node)
            
            episode = RawEpisode(
                name=f"neo4j_node_{node.get('id', uuid4())}",
                content=content,
                source=EpisodeType.text,
                source_description="Neo4j node migration",
                reference_time=self._get_node_timestamp(node)
            )
            episodes.append(episode)
        
        # Process through Graphiti for enrichment
        if episodes:
            results = await self.graphiti.add_episodes_bulk(episodes)
            logger.info(f"Enriched {len(results.episodes)} nodes with Graphiti features")
    
    def _node_to_text(self, node: Dict) -> str:
        """Convert node properties to text."""
        parts = []
        
        # Add name/title
        if "name" in node:
            parts.append(f"Name: {node['name']}")
        elif "title" in node:
            parts.append(f"Title: {node['title']}")
        
        # Add description/summary
        if "description" in node:
            parts.append(f"Description: {node['description']}")
        elif "summary" in node:
            parts.append(f"Summary: {node['summary']}")
        
        # Add other properties
        skip_props = {"name", "title", "description", "summary", "id", "uuid"}
        for key, value in node.items():
            if key not in skip_props:
                parts.append(f"{key}: {value}")
        
        return ". ".join(parts)
    
    async def add_graphiti_indexes(self):
        """Add Graphiti-specific indexes to existing Neo4j."""
        await self.graphiti.build_indices_and_constraints()
    
    async def enable_vector_search(self):
        """Add vector embeddings to existing nodes."""
        # Query nodes without embeddings
        query = """
        MATCH (n)
        WHERE n.embedding IS NULL
        RETURN n
        LIMIT 100
        """
        
        nodes = await self.existing.execute(query)
        
        # Generate embeddings
        for record in nodes:
            node = record['n']
            text = self._node_to_text(node)
            
            # Generate embedding
            embedding = await self.graphiti.embedder.embed(text)
            
            # Update node with embedding
            update_query = """
            MATCH (n)
            WHERE id(n) = $node_id
            SET n.embedding = $embedding
            """
            
            await self.existing.execute(update_query, {
                "node_id": node.id,
                "embedding": embedding.tolist()
            })
```

---

## Migration from Document Stores

### Elasticsearch/OpenSearch Migration

```python
class ElasticsearchMigrator:
    """Migrate from Elasticsearch to Graphiti."""
    
    def __init__(self, es_host: str, graphiti):
        from elasticsearch import AsyncElasticsearch
        self.es = AsyncElasticsearch([es_host])
        self.graphiti = graphiti
    
    async def migrate_index(
        self,
        index_name: str,
        doc_type: str = "_doc"
    ):
        """Migrate an Elasticsearch index to Graphiti."""
        # Scroll through all documents
        scroll_size = 100
        scroll_time = "2m"
        
        # Initial search
        response = await self.es.search(
            index=index_name,
            doc_type=doc_type,
            scroll=scroll_time,
            size=scroll_size,
            body={"query": {"match_all": {}}}
        )
        
        scroll_id = response['_scroll_id']
        hits = response['hits']['hits']
        
        while hits:
            # Process current batch
            episodes = []
            for hit in hits:
                episode = self._doc_to_episode(hit, index_name)
                episodes.append(episode)
            
            # Import to Graphiti
            if episodes:
                await self.graphiti.add_episodes_bulk(episodes)
            
            # Get next batch
            response = await self.es.scroll(
                scroll_id=scroll_id,
                scroll=scroll_time
            )
            hits = response['hits']['hits']
        
        # Clean up scroll
        await self.es.clear_scroll(scroll_id=scroll_id)
    
    def _doc_to_episode(self, hit: Dict, index_name: str) -> RawEpisode:
        """Convert Elasticsearch document to episode."""
        doc = hit['_source']
        
        # Determine content field
        content = doc.get('content') or doc.get('text') or json.dumps(doc)
        
        return RawEpisode(
            name=f"es_{index_name}_{hit['_id']}",
            content=content,
            source=EpisodeType.text if isinstance(content, str) else EpisodeType.json,
            source_description=f"Elasticsearch: {index_name}",
            reference_time=self._parse_es_timestamp(doc),
            metadata={
                "es_id": hit['_id'],
                "es_index": index_name,
                "es_score": hit.get('_score'),
                **doc
            }
        )
```

---

## Migration from Chat Memory Systems

### LangChain Memory Migration

```python
class LangChainMemoryMigrator:
    """Migrate from LangChain memory to Graphiti."""
    
    def __init__(self, langchain_memory, graphiti):
        self.memory = langchain_memory
        self.graphiti = graphiti
    
    async def migrate_conversation_memory(self):
        """Migrate conversation buffer memory."""
        # Get all messages from memory
        messages = self.memory.chat_memory.messages
        
        episodes = []
        for i, message in enumerate(messages):
            episode = RawEpisode(
                name=f"langchain_msg_{i}",
                content=message.content,
                source=EpisodeType.message,
                source_description=f"LangChain {message.type}",
                reference_time=datetime.now(timezone.utc),
                metadata={
                    "role": message.type,
                    "additional_kwargs": message.additional_kwargs
                }
            )
            episodes.append(episode)
        
        # Import to Graphiti
        if episodes:
            await self.graphiti.add_episodes_bulk(
                episodes,
                group_id="langchain_migration"
            )
    
    async def migrate_summary_memory(self):
        """Migrate conversation summary memory."""
        if hasattr(self.memory, 'moving_summary_buffer'):
            summary = self.memory.moving_summary_buffer
            
            await self.graphiti.add_episode(
                name="langchain_summary",
                episode_body=summary,
                source=EpisodeType.text,
                source_description="LangChain conversation summary",
                reference_time=datetime.now(timezone.utc),
                group_id="langchain_migration"
            )
```

---

## Data Migration Strategies

### Incremental Migration

```python
class IncrementalMigrator:
    """Incremental migration strategy for large datasets."""
    
    def __init__(self, source_system, graphiti):
        self.source = source_system
        self.graphiti = graphiti
        self.checkpoint_file = "migration_checkpoint.json"
    
    async def migrate_incremental(
        self,
        batch_size: int = 100,
        checkpoint_interval: int = 1000
    ):
        """Migrate data incrementally with checkpoints."""
        # Load checkpoint
        checkpoint = self._load_checkpoint()
        start_offset = checkpoint.get("offset", 0)
        
        offset = start_offset
        total_migrated = checkpoint.get("total", 0)
        
        try:
            while True:
                # Fetch batch from source
                batch = await self.source.fetch_batch(
                    offset=offset,
                    limit=batch_size
                )
                
                if not batch:
                    break
                
                # Transform and import
                episodes = self._transform_batch(batch)
                await self.graphiti.add_episodes_bulk(episodes)
                
                # Update progress
                offset += len(batch)
                total_migrated += len(batch)
                
                # Save checkpoint
                if total_migrated % checkpoint_interval == 0:
                    self._save_checkpoint({
                        "offset": offset,
                        "total": total_migrated,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    logger.info(f"Checkpoint saved: {total_migrated} items migrated")
                
        except Exception as e:
            logger.error(f"Migration failed at offset {offset}: {e}")
            self._save_checkpoint({
                "offset": offset,
                "total": total_migrated,
                "error": str(e)
            })
            raise
        
        return total_migrated
    
    def _load_checkpoint(self) -> Dict:
        """Load migration checkpoint."""
        if os.path.exists(self.checkpoint_file):
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_checkpoint(self, checkpoint: Dict):
        """Save migration checkpoint."""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
```

### Parallel Migration

```python
class ParallelMigrator:
    """Parallel migration for high-performance."""
    
    def __init__(self, source_system, graphiti, num_workers: int = 10):
        self.source = source_system
        self.graphiti = graphiti
        self.num_workers = num_workers
    
    async def migrate_parallel(self):
        """Migrate data using parallel workers."""
        # Get total count
        total_count = await self.source.get_total_count()
        
        # Calculate work distribution
        chunk_size = total_count // self.num_workers
        
        # Create worker tasks
        tasks = []
        for i in range(self.num_workers):
            start_offset = i * chunk_size
            end_offset = start_offset + chunk_size if i < self.num_workers - 1 else total_count
            
            task = self._worker(
                worker_id=i,
                start_offset=start_offset,
                end_offset=end_offset
            )
            tasks.append(task)
        
        # Run workers in parallel
        results = await asyncio.gather(*tasks)
        
        # Aggregate results
        total_migrated = sum(results)
        logger.info(f"Parallel migration complete: {total_migrated} items")
        
        return total_migrated
    
    async def _worker(
        self,
        worker_id: int,
        start_offset: int,
        end_offset: int
    ):
        """Worker function for parallel migration."""
        logger.info(f"Worker {worker_id} starting: {start_offset} to {end_offset}")
        
        migrated = 0
        offset = start_offset
        
        while offset < end_offset:
            batch_size = min(100, end_offset - offset)
            
            # Fetch batch
            batch = await self.source.fetch_batch(
                offset=offset,
                limit=batch_size
            )
            
            if not batch:
                break
            
            # Transform and import
            episodes = self._transform_batch(batch)
            await self.graphiti.add_episodes_bulk(episodes)
            
            offset += len(batch)
            migrated += len(batch)
            
            if migrated % 1000 == 0:
                logger.info(f"Worker {worker_id}: {migrated} items migrated")
        
        logger.info(f"Worker {worker_id} complete: {migrated} items")
        return migrated
```

---

## API Migration Patterns

### REST API to Graphiti

```python
class RESTAPIWrapper:
    """Wrap Graphiti as REST API for compatibility."""
    
    def __init__(self, graphiti):
        self.graphiti = graphiti
        self.app = FastAPI()
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup REST API routes matching old system."""
        
        @self.app.post("/documents")
        async def add_document(doc: DocumentRequest):
            """Compatibility endpoint for document addition."""
            # Transform to Graphiti episode
            result = await self.graphiti.add_episode(
                name=doc.id,
                episode_body=doc.content,
                source=EpisodeType.text,
                source_description=doc.source,
                reference_time=doc.timestamp
            )
            
            return {
                "id": result.episode.uuid,
                "status": "success"
            }
        
        @self.app.get("/search")
        async def search(q: str, limit: int = 10):
            """Compatibility endpoint for search."""
            results = await self.graphiti.search(q, limit=limit)
            
            # Transform to old format
            return {
                "query": q,
                "results": [
                    {
                        "id": r.uuid,
                        "content": r.fact,
                        "score": getattr(r, 'score', 1.0)
                    }
                    for r in results
                ]
            }
```

---

## Post-Migration Validation

### Validation Framework

```python
class MigrationValidator:
    """Validate migration success."""
    
    def __init__(self, source_system, graphiti):
        self.source = source_system
        self.graphiti = graphiti
        self.validation_results = {}
    
    async def validate_migration(self) -> Dict:
        """Run complete validation suite."""
        self.validation_results = {
            "count_validation": await self._validate_counts(),
            "search_validation": await self._validate_search(),
            "data_integrity": await self._validate_integrity(),
            "performance": await self._validate_performance(),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return self.validation_results
    
    async def _validate_counts(self) -> Dict:
        """Validate record counts."""
        source_count = await self.source.get_total_count()
        
        # Count episodes in Graphiti
        query = "MATCH (e:Episode) RETURN count(e) as count"
        result = await self.graphiti.driver.execute(query)
        graphiti_count = result[0]['count']
        
        return {
            "source_count": source_count,
            "graphiti_count": graphiti_count,
            "match": source_count == graphiti_count,
            "difference": abs(source_count - graphiti_count)
        }
    
    async def _validate_search(self) -> Dict:
        """Validate search functionality."""
        test_queries = [
            "test query 1",
            "sample search",
            "specific term"
        ]
        
        results = {}
        for query in test_queries:
            # Search both systems
            source_results = await self.source.search(query)
            graphiti_results = await self.graphiti.search(query)
            
            results[query] = {
                "source_count": len(source_results),
                "graphiti_count": len(graphiti_results),
                "overlap": self._calculate_overlap(source_results, graphiti_results)
            }
        
        return results
    
    async def _validate_integrity(self) -> Dict:
        """Validate data integrity."""
        # Sample random records
        sample_size = 100
        samples = await self.source.get_random_samples(sample_size)
        
        integrity_checks = []
        for sample in samples:
            # Try to find in Graphiti
            found = await self._find_in_graphiti(sample)
            integrity_checks.append({
                "source_id": sample.get("id"),
                "found": found is not None,
                "content_match": self._compare_content(sample, found) if found else False
            })
        
        success_rate = sum(1 for c in integrity_checks if c["found"]) / len(integrity_checks)
        
        return {
            "sample_size": sample_size,
            "success_rate": success_rate,
            "failures": [c for c in integrity_checks if not c["found"]][:10]
        }
    
    async def _validate_performance(self) -> Dict:
        """Compare performance metrics."""
        import time
        
        test_queries = ["test", "search", "query", "data", "information"]
        
        source_times = []
        graphiti_times = []
        
        for query in test_queries:
            # Time source system
            start = time.perf_counter()
            await self.source.search(query)
            source_times.append(time.perf_counter() - start)
            
            # Time Graphiti
            start = time.perf_counter()
            await self.graphiti.search(query)
            graphiti_times.append(time.perf_counter() - start)
        
        return {
            "source_avg_ms": sum(source_times) / len(source_times) * 1000,
            "graphiti_avg_ms": sum(graphiti_times) / len(graphiti_times) * 1000,
            "improvement": (sum(source_times) - sum(graphiti_times)) / sum(source_times) * 100
        }
    
    def generate_report(self) -> str:
        """Generate validation report."""
        report = "MIGRATION VALIDATION REPORT\n"
        report += "=" * 50 + "\n\n"
        
        # Count validation
        counts = self.validation_results.get("count_validation", {})
        report += f"RECORD COUNTS:\n"
        report += f"  Source: {counts.get('source_count', 'N/A')}\n"
        report += f"  Graphiti: {counts.get('graphiti_count', 'N/A')}\n"
        report += f"  Match: {'✓' if counts.get('match') else '✗'}\n\n"
        
        # Integrity validation
        integrity = self.validation_results.get("data_integrity", {})
        report += f"DATA INTEGRITY:\n"
        report += f"  Success Rate: {integrity.get('success_rate', 0) * 100:.1f}%\n\n"
        
        # Performance
        perf = self.validation_results.get("performance", {})
        report += f"PERFORMANCE:\n"
        report += f"  Source Avg: {perf.get('source_avg_ms', 0):.2f}ms\n"
        report += f"  Graphiti Avg: {perf.get('graphiti_avg_ms', 0):.2f}ms\n"
        report += f"  Improvement: {perf.get('improvement', 0):.1f}%\n"
        
        return report
```

---

## Migration Checklist

### Pre-Migration
- [ ] Backup source system
- [ ] Analyze source data volume and structure
- [ ] Estimate migration time and resources
- [ ] Set up Graphiti environment
- [ ] Test migration with small sample
- [ ] Plan downtime if needed

### During Migration
- [ ] Monitor progress with checkpoints
- [ ] Log all errors and warnings
- [ ] Validate data integrity periodically
- [ ] Monitor system resources
- [ ] Keep stakeholders informed

### Post-Migration
- [ ] Run validation suite
- [ ] Compare search results
- [ ] Performance benchmarking
- [ ] Update documentation
- [ ] Train users on new system
- [ ] Plan old system decommission

---

## Next Steps

After migrating to Graphiti:

1. **Optimize Performance**: Review performance tuning guide
2. **Set Up Monitoring**: Implement observability
3. **Integrate with Agents**: Connect AI agents to Graphiti
4. **Enable Advanced Features**: Communities, temporal queries
5. **Plan Continuous Migration**: For ongoing data sources
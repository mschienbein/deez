# Graphiti Migration Guide: Complete Implementation Strategies

## Table of Contents
1. [Migration Overview](#migration-overview)
2. [Migrating from Vector Databases](#migrating-from-vector-databases)
3. [Migrating from Traditional Graph Databases](#migrating-from-traditional-graph-databases)
4. [Migrating from GraphRAG](#migrating-from-graphrag)
5. [Data Import Strategies](#data-import-strategies)
6. [Schema Migration](#schema-migration)
7. [Zero-Downtime Migration](#zero-downtime-migration)
8. [Validation and Testing](#validation-and-testing)
9. [Rollback Strategies](#rollback-strategies)
10. [Post-Migration Optimization](#post-migration-optimization)

## Migration Overview

### Migration Planning Framework

```python
class MigrationPlan:
    """Comprehensive migration planning and execution framework."""
    
    def __init__(self, source_system: str, target_graphiti: Graphiti):
        self.source_system = source_system
        self.target = target_graphiti
        self.migration_stats = {
            'total_records': 0,
            'migrated_records': 0,
            'failed_records': 0,
            'start_time': None,
            'end_time': None,
            'errors': []
        }
    
    async def analyze_source_data(self) -> dict:
        """Analyze source data for migration planning."""
        analysis = {
            'total_size': 0,
            'record_count': 0,
            'data_types': set(),
            'estimated_migration_time': 0,
            'required_transformations': [],
            'potential_issues': []
        }
        
        # Analyze based on source system type
        if self.source_system == 'pinecone':
            analysis = await self._analyze_pinecone()
        elif self.source_system == 'neo4j':
            analysis = await self._analyze_neo4j()
        elif self.source_system == 'graphrag':
            analysis = await self._analyze_graphrag()
        
        # Estimate migration time
        records_per_second = 2.5  # Based on benchmarks
        analysis['estimated_migration_time'] = analysis['record_count'] / records_per_second
        
        return analysis
    
    async def create_migration_strategy(self, analysis: dict) -> dict:
        """Create optimal migration strategy based on analysis."""
        strategy = {
            'approach': 'batch',  # or 'streaming', 'parallel'
            'batch_size': 100,
            'parallelism': 10,
            'checkpointing': True,
            'validation': True
        }
        
        # Optimize based on data size
        if analysis['record_count'] < 1000:
            strategy['approach'] = 'batch'
            strategy['batch_size'] = 100
        elif analysis['record_count'] < 100000:
            strategy['approach'] = 'parallel'
            strategy['parallelism'] = 20
        else:
            strategy['approach'] = 'streaming'
            strategy['checkpointing'] = True
        
        return strategy
```

## Migrating from Vector Databases

### Pinecone to Graphiti Migration

```python
import pinecone
from datetime import datetime, timezone
import json

class PineconeToGraphitiMigrator:
    """Migrate from Pinecone vector database to Graphiti."""
    
    def __init__(self, pinecone_config: dict, graphiti: Graphiti):
        self.pinecone_index = pinecone.Index(pinecone_config['index_name'])
        self.graphiti = graphiti
        self.namespace_to_group_id = {}
    
    async def migrate_vectors_to_episodes(
        self, 
        namespace: str = None,
        batch_size: int = 100,
        preserve_metadata: bool = True
    ):
        """
        Migrate Pinecone vectors to Graphiti episodes.
        
        Conversion Strategy:
        - Each vector becomes an episode
        - Metadata becomes episode attributes
        - Text content is extracted and processed
        - Relationships are inferred from metadata
        """
        # Query all vectors from namespace
        query_response = self.pinecone_index.query(
            vector=[0] * 1536,  # Dummy vector for metadata query
            top_k=10000,
            include_metadata=True,
            namespace=namespace
        )
        
        migrated_count = 0
        failed_count = 0
        
        # Process in batches
        for i in range(0, len(query_response.matches), batch_size):
            batch = query_response.matches[i:i+batch_size]
            
            episodes = []
            for match in batch:
                try:
                    # Extract content and metadata
                    vector_id = match.id
                    metadata = match.metadata or {}
                    
                    # Convert to episode
                    episode = {
                        'name': metadata.get('title', f'Vector {vector_id}'),
                        'episode_body': metadata.get('text', ''),
                        'source_description': f'Migrated from Pinecone: {namespace or "default"}',
                        'reference_time': self._parse_timestamp(metadata.get('timestamp')),
                        'source': EpisodeType.text,
                        'group_id': self._get_group_id(namespace, metadata),
                        'uuid': f'pinecone_{vector_id}'
                    }
                    
                    episodes.append(episode)
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Failed to convert vector {vector_id}: {e}")
            
            # Bulk add episodes to Graphiti
            if episodes:
                try:
                    await self.graphiti.add_episode_bulk(
                        episodes=[
                            RawEpisode(
                                name=ep['name'],
                                content=ep['episode_body'],
                                source_description=ep['source_description'],
                                source=ep['source'],
                                reference_time=ep['reference_time'],
                                uuid=ep['uuid']
                            )
                            for ep in episodes
                        ],
                        group_id=episodes[0]['group_id']
                    )
                    migrated_count += len(episodes)
                except Exception as e:
                    failed_count += len(episodes)
                    logger.error(f"Failed to add batch: {e}")
        
        return {
            'migrated': migrated_count,
            'failed': failed_count,
            'success_rate': migrated_count / (migrated_count + failed_count)
        }
    
    def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp from various formats."""
        if not timestamp_str:
            return datetime.now(timezone.utc)
        
        try:
            # Try ISO format
            return datetime.fromisoformat(timestamp_str)
        except:
            try:
                # Try Unix timestamp
                return datetime.fromtimestamp(float(timestamp_str), timezone.utc)
            except:
                return datetime.now(timezone.utc)
    
    def _get_group_id(self, namespace: str, metadata: dict) -> str:
        """Map Pinecone namespace to Graphiti group_id."""
        if namespace:
            return f"pinecone_{namespace}"
        elif 'user_id' in metadata:
            return f"user_{metadata['user_id']}"
        else:
            return "pinecone_default"
    
    async def migrate_with_relationship_inference(self):
        """
        Advanced migration with relationship inference.
        
        Infers relationships based on:
        - Semantic similarity between vectors
        - Shared metadata attributes
        - Temporal proximity
        """
        # First, migrate all vectors as episodes
        migration_result = await self.migrate_vectors_to_episodes()
        
        # Then, infer relationships
        print("Inferring relationships from vector similarities...")
        
        # Get all migrated episodes
        episodes = await self.graphiti.retrieve_episodes(
            reference_time=datetime.now(timezone.utc),
            last_n=migration_result['migrated']
        )
        
        # Build similarity graph
        for i, episode1 in enumerate(episodes):
            for episode2 in episodes[i+1:]:
                # Check for shared metadata
                if self._have_shared_context(episode1, episode2):
                    # Create relationship edge
                    await self._create_inferred_edge(episode1, episode2)
        
        return migration_result
    
    def _have_shared_context(self, ep1: EpisodicNode, ep2: EpisodicNode) -> bool:
        """Check if episodes share context."""
        # Implementation depends on metadata structure
        # Example: Check for shared tags, categories, or entities
        return False  # Placeholder
    
    async def _create_inferred_edge(self, ep1: EpisodicNode, ep2: EpisodicNode):
        """Create inferred relationship between episodes."""
        # Extract entities from episodes and create edges
        pass  # Implementation needed
```

### Weaviate to Graphiti Migration

```python
import weaviate

class WeaviateToGraphitiMigrator:
    """Migrate from Weaviate to Graphiti."""
    
    def __init__(self, weaviate_url: str, graphiti: Graphiti):
        self.weaviate_client = weaviate.Client(weaviate_url)
        self.graphiti = graphiti
    
    async def migrate_class_to_episodes(
        self,
        class_name: str,
        text_properties: list[str],
        relationship_properties: list[str] = None
    ):
        """
        Migrate a Weaviate class to Graphiti episodes.
        
        Parameters
        ----------
        class_name : str
            Weaviate class to migrate
        text_properties : list[str]
            Properties to combine as episode body
        relationship_properties : list[str]
            Properties that indicate relationships
        """
        # Query all objects from class
        query = self.weaviate_client.query.get(
            class_name,
            properties=text_properties + (relationship_properties or [])
        )
        
        results = query.do()
        objects = results['data']['Get'][class_name]
        
        # Convert to episodes with relationship extraction
        for obj in objects:
            # Combine text properties
            episode_body = '\n'.join([
                f"{prop}: {obj.get(prop, '')}"
                for prop in text_properties
            ])
            
            # Add episode
            result = await self.graphiti.add_episode(
                name=f"{class_name} {obj.get('_id', '')}",
                episode_body=episode_body,
                source_description=f"Migrated from Weaviate class {class_name}",
                reference_time=datetime.now(timezone.utc),
                source=EpisodeType.json if relationship_properties else EpisodeType.text,
                group_id=f"weaviate_{class_name.lower()}"
            )
            
            # Handle relationships
            if relationship_properties:
                await self._migrate_relationships(obj, relationship_properties, result)
    
    async def _migrate_relationships(
        self,
        obj: dict,
        relationship_properties: list[str],
        episode_result: AddEpisodeResults
    ):
        """Extract and create relationships from object properties."""
        for prop in relationship_properties:
            if prop in obj and obj[prop]:
                # Create edges for relationships
                # Implementation depends on Weaviate schema
                pass
```

## Migrating from Traditional Graph Databases

### Neo4j to Graphiti Migration

```python
from neo4j import AsyncGraphDatabase

class Neo4jToGraphitiMigrator:
    """Migrate from existing Neo4j database to Graphiti structure."""
    
    def __init__(self, source_neo4j_config: dict, target_graphiti: Graphiti):
        self.source_driver = AsyncGraphDatabase.driver(
            source_neo4j_config['uri'],
            auth=(source_neo4j_config['user'], source_neo4j_config['password'])
        )
        self.target = target_graphiti
    
    async def migrate_with_schema_mapping(
        self,
        node_mappings: dict[str, dict],
        edge_mappings: dict[str, dict]
    ):
        """
        Migrate with explicit schema mapping.
        
        Example mappings:
        node_mappings = {
            'Person': {
                'target_type': 'Entity',
                'name_field': 'name',
                'summary_field': 'bio',
                'group_id': 'people'
            }
        }
        """
        migration_stats = {
            'nodes': {'migrated': 0, 'failed': 0},
            'edges': {'migrated': 0, 'failed': 0}
        }
        
        # Migrate nodes
        for source_label, mapping in node_mappings.items():
            stats = await self._migrate_nodes(source_label, mapping)
            migration_stats['nodes']['migrated'] += stats['migrated']
            migration_stats['nodes']['failed'] += stats['failed']
        
        # Migrate relationships
        for source_type, mapping in edge_mappings.items():
            stats = await self._migrate_edges(source_type, mapping)
            migration_stats['edges']['migrated'] += stats['migrated']
            migration_stats['edges']['failed'] += stats['failed']
        
        return migration_stats
    
    async def _migrate_nodes(self, source_label: str, mapping: dict) -> dict:
        """Migrate nodes of a specific label."""
        async with self.source_driver.session() as session:
            # Query source nodes
            query = f"""
            MATCH (n:{source_label})
            RETURN n
            LIMIT 1000
            """
            
            result = await session.run(query)
            records = await result.data()
            
            migrated = 0
            failed = 0
            
            for record in records:
                node_data = record['n']
                
                try:
                    # Transform to Graphiti entity
                    entity = EntityNode(
                        name=node_data.get(mapping['name_field'], 'Unknown'),
                        summary=node_data.get(mapping.get('summary_field'), ''),
                        group_id=mapping['group_id'],
                        labels=[mapping['target_type']],
                        attributes={
                            k: v for k, v in node_data.items()
                            if k not in [mapping['name_field'], mapping.get('summary_field')]
                        }
                    )
                    
                    # Generate embedding
                    await entity.generate_name_embedding(self.target.embedder)
                    
                    # Save to target
                    await entity.save(self.target.driver)
                    migrated += 1
                    
                except Exception as e:
                    failed += 1
                    logger.error(f"Failed to migrate node: {e}")
            
            return {'migrated': migrated, 'failed': failed}
    
    async def _migrate_edges(self, source_type: str, mapping: dict) -> dict:
        """Migrate relationships of a specific type."""
        async with self.source_driver.session() as session:
            query = f"""
            MATCH (s)-[r:{source_type}]->(t)
            RETURN s, r, t
            LIMIT 1000
            """
            
            result = await session.run(query)
            records = await result.data()
            
            migrated = 0
            failed = 0
            
            for record in records:
                try:
                    source_node = record['s']
                    rel = record['r']
                    target_node = record['t']
                    
                    # Create entity edge
                    edge = EntityEdge(
                        source_node_uuid=self._get_node_uuid(source_node),
                        target_node_uuid=self._get_node_uuid(target_node),
                        name=mapping.get('name', source_type),
                        fact=self._build_fact(source_node, rel, target_node, mapping),
                        group_id=mapping['group_id'],
                        valid_at=datetime.now(timezone.utc),
                        attributes=dict(rel)
                    )
                    
                    # Generate embedding
                    await edge.generate_embedding(self.target.embedder)
                    
                    # Save to target
                    await edge.save(self.target.driver)
                    migrated += 1
                    
                except Exception as e:
                    failed += 1
                    logger.error(f"Failed to migrate edge: {e}")
            
            return {'migrated': migrated, 'failed': failed}
    
    def _get_node_uuid(self, node: dict) -> str:
        """Get or generate UUID for node."""
        if 'uuid' in node:
            return node['uuid']
        elif 'id' in node:
            return f"neo4j_{node['id']}"
        else:
            return str(uuid.uuid4())
    
    def _build_fact(
        self,
        source: dict,
        rel: dict,
        target: dict,
        mapping: dict
    ) -> str:
        """Build fact string from relationship."""
        if 'fact_template' in mapping:
            return mapping['fact_template'].format(
                source=source.get('name', 'entity'),
                relationship=rel.get('type', 'relates to'),
                target=target.get('name', 'entity')
            )
        else:
            return f"{source.get('name')} {rel.get('type', 'relates to')} {target.get('name')}"
```

## Migrating from GraphRAG

### GraphRAG to Graphiti Migration

```python
class GraphRAGToGraphitiMigrator:
    """Migrate from Microsoft GraphRAG to Graphiti."""
    
    def __init__(self, graphrag_data_path: str, graphiti: Graphiti):
        self.data_path = graphrag_data_path
        self.graphiti = graphiti
    
    async def migrate_graphrag_output(self):
        """
        Migrate GraphRAG output files to Graphiti.
        
        GraphRAG produces:
        - entities.parquet
        - relationships.parquet
        - communities.parquet
        - documents.parquet
        """
        import pandas as pd
        
        migration_results = {}
        
        # Load GraphRAG data
        entities_df = pd.read_parquet(f"{self.data_path}/entities.parquet")
        relationships_df = pd.read_parquet(f"{self.data_path}/relationships.parquet")
        communities_df = pd.read_parquet(f"{self.data_path}/communities.parquet")
        documents_df = pd.read_parquet(f"{self.data_path}/documents.parquet")
        
        # Migrate documents as episodes
        print("Migrating documents...")
        migration_results['documents'] = await self._migrate_documents(documents_df)
        
        # Migrate entities
        print("Migrating entities...")
        migration_results['entities'] = await self._migrate_entities(entities_df)
        
        # Migrate relationships
        print("Migrating relationships...")
        migration_results['relationships'] = await self._migrate_relationships_graphrag(
            relationships_df
        )
        
        # Migrate communities
        print("Migrating communities...")
        migration_results['communities'] = await self._migrate_communities(communities_df)
        
        return migration_results
    
    async def _migrate_documents(self, documents_df: pd.DataFrame) -> dict:
        """Migrate GraphRAG documents to episodes."""
        episodes = []
        
        for _, doc in documents_df.iterrows():
            episode = RawEpisode(
                name=doc.get('title', f"Document {doc['id']}"),
                content=doc['text'],
                source_description="GraphRAG document",
                source=EpisodeType.text,
                reference_time=self._parse_graphrag_timestamp(doc.get('timestamp')),
                uuid=f"graphrag_doc_{doc['id']}"
            )
            episodes.append(episode)
        
        # Add episodes in bulk
        await self.graphiti.add_episode_bulk(
            episodes=episodes,
            group_id="graphrag_migration"
        )
        
        return {'migrated': len(episodes), 'failed': 0}
    
    async def _migrate_entities(self, entities_df: pd.DataFrame) -> dict:
        """Migrate GraphRAG entities to Graphiti nodes."""
        nodes = []
        
        for _, entity in entities_df.iterrows():
            node = EntityNode(
                name=entity['name'],
                summary=entity.get('description', ''),
                group_id="graphrag_migration",
                labels=[entity.get('type', 'Entity')],
                attributes={
                    'graphrag_id': entity['id'],
                    'degree': entity.get('degree', 0),
                    'community_id': entity.get('community_id')
                }
            )
            nodes.append(node)
        
        # Generate embeddings in batch
        await create_entity_node_embeddings(self.graphiti.embedder, nodes)
        
        # Save nodes
        for node in nodes:
            await node.save(self.graphiti.driver)
        
        return {'migrated': len(nodes), 'failed': 0}
    
    async def _migrate_relationships_graphrag(
        self,
        relationships_df: pd.DataFrame
    ) -> dict:
        """Migrate GraphRAG relationships to edges."""
        edges = []
        
        for _, rel in relationships_df.iterrows():
            edge = EntityEdge(
                source_node_uuid=f"graphrag_entity_{rel['source']}",
                target_node_uuid=f"graphrag_entity_{rel['target']}",
                name=rel.get('type', 'relates_to'),
                fact=rel.get('description', ''),
                group_id="graphrag_migration",
                valid_at=datetime.now(timezone.utc),
                attributes={
                    'weight': rel.get('weight', 1.0),
                    'graphrag_id': rel['id']
                }
            )
            edges.append(edge)
        
        # Generate embeddings in batch
        await create_entity_edge_embeddings(self.graphiti.embedder, edges)
        
        # Save edges
        for edge in edges:
            await edge.save(self.graphiti.driver)
        
        return {'migrated': len(edges), 'failed': 0}
    
    async def _migrate_communities(self, communities_df: pd.DataFrame) -> dict:
        """Migrate GraphRAG communities to Graphiti community nodes."""
        communities = []
        
        for _, comm in communities_df.iterrows():
            community = CommunityNode(
                name=comm.get('title', f"Community {comm['id']}"),
                summary=comm.get('summary', ''),
                group_id="graphrag_migration",
                labels=['Community'],
                attributes={
                    'level': comm.get('level', 0),
                    'graphrag_id': comm['id']
                }
            )
            communities.append(community)
        
        # Generate embeddings
        for community in communities:
            await community.generate_name_embedding(self.graphiti.embedder)
        
        # Save communities
        for community in communities:
            await community.save(self.graphiti.driver)
        
        return {'migrated': len(communities), 'failed': 0}
    
    def _parse_graphrag_timestamp(self, timestamp) -> datetime:
        """Parse GraphRAG timestamp format."""
        if pd.isna(timestamp):
            return datetime.now(timezone.utc)
        try:
            return pd.to_datetime(timestamp).to_pydatetime()
        except:
            return datetime.now(timezone.utc)
```

## Data Import Strategies

### Streaming Import for Large Datasets

```python
class StreamingImporter:
    """Stream large datasets into Graphiti."""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
        self.checkpoint_file = "migration_checkpoint.json"
    
    async def stream_jsonl_file(
        self,
        file_path: str,
        batch_size: int = 100,
        resume_from_checkpoint: bool = True
    ):
        """
        Stream JSONL file with checkpointing.
        
        Handles:
        - Large files that don't fit in memory
        - Crash recovery with checkpoints
        - Progress tracking
        """
        import ijson
        
        # Load checkpoint if resuming
        checkpoint = self._load_checkpoint() if resume_from_checkpoint else {'line': 0}
        
        processed_lines = checkpoint['line']
        batch = []
        
        with open(file_path, 'rb') as file:
            # Skip to checkpoint
            for _ in range(processed_lines):
                file.readline()
            
            # Process remaining lines
            parser = ijson.items(file, 'item')
            
            for line_num, item in enumerate(parser, start=processed_lines):
                try:
                    # Convert to episode
                    episode = self._convert_to_episode(item)
                    batch.append(episode)
                    
                    # Process batch
                    if len(batch) >= batch_size:
                        await self._process_batch(batch)
                        batch = []
                        
                        # Update checkpoint
                        self._save_checkpoint({'line': processed_lines + line_num})
                        
                        # Progress update
                        if (processed_lines + line_num) % 1000 == 0:
                            print(f"Processed {processed_lines + line_num} lines")
                
                except Exception as e:
                    logger.error(f"Error processing line {line_num}: {e}")
            
            # Process remaining batch
            if batch:
                await self._process_batch(batch)
        
        # Clear checkpoint on completion
        self._clear_checkpoint()
    
    def _convert_to_episode(self, item: dict) -> RawEpisode:
        """Convert JSON item to episode."""
        return RawEpisode(
            name=item.get('title', 'Untitled'),
            content=item.get('content', ''),
            source_description=item.get('source', 'import'),
            source=EpisodeType.json if 'metadata' in item else EpisodeType.text,
            reference_time=datetime.fromisoformat(
                item.get('timestamp', datetime.now(timezone.utc).isoformat())
            )
        )
    
    async def _process_batch(self, batch: list[RawEpisode]):
        """Process a batch of episodes."""
        await self.graphiti.add_episode_bulk(
            episodes=batch,
            group_id="import"
        )
    
    def _load_checkpoint(self) -> dict:
        """Load checkpoint from file."""
        try:
            with open(self.checkpoint_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {'line': 0}
    
    def _save_checkpoint(self, checkpoint: dict):
        """Save checkpoint to file."""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint, f)
    
    def _clear_checkpoint(self):
        """Clear checkpoint file."""
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
```

### Parallel Import for Performance

```python
class ParallelImporter:
    """Parallel import for maximum throughput."""
    
    def __init__(self, graphiti: Graphiti, num_workers: int = 10):
        self.graphiti = graphiti
        self.num_workers = num_workers
        self.import_queue = asyncio.Queue()
        self.error_queue = asyncio.Queue()
    
    async def import_from_source(
        self,
        data_source: callable,
        total_records: int = None
    ):
        """
        Import data using parallel workers.
        
        Parameters
        ----------
        data_source : callable
            Async generator that yields data items
        total_records : int
            Total number of records for progress tracking
        """
        # Start workers
        workers = [
            asyncio.create_task(self._worker(f"worker_{i}"))
            for i in range(self.num_workers)
        ]
        
        # Start progress tracker
        progress_task = asyncio.create_task(
            self._track_progress(total_records)
        )
        
        # Feed data to queue
        async for item in data_source():
            await self.import_queue.put(item)
        
        # Signal workers to stop
        for _ in range(self.num_workers):
            await self.import_queue.put(None)
        
        # Wait for workers to complete
        await asyncio.gather(*workers)
        
        # Stop progress tracker
        progress_task.cancel()
        
        # Handle errors
        errors = []
        while not self.error_queue.empty():
            errors.append(await self.error_queue.get())
        
        return {
            'total_processed': self.processed_count,
            'errors': errors,
            'success_rate': 1 - (len(errors) / self.processed_count)
        }
    
    async def _worker(self, worker_id: str):
        """Worker to process import items."""
        while True:
            item = await self.import_queue.get()
            
            if item is None:  # Shutdown signal
                break
            
            try:
                # Process item
                await self._process_item(item)
                self.processed_count += 1
            except Exception as e:
                await self.error_queue.put({
                    'worker': worker_id,
                    'item': item,
                    'error': str(e)
                })
    
    async def _process_item(self, item: dict):
        """Process a single import item."""
        # Convert and add to Graphiti
        await self.graphiti.add_episode(
            name=item['name'],
            episode_body=item['content'],
            source_description=item.get('source', 'import'),
            reference_time=datetime.now(timezone.utc),
            group_id=item.get('group_id', 'import')
        )
    
    async def _track_progress(self, total: int = None):
        """Track and report import progress."""
        while True:
            await asyncio.sleep(10)
            if total:
                progress = (self.processed_count / total) * 100
                print(f"Progress: {progress:.1f}% ({self.processed_count}/{total})")
            else:
                print(f"Processed: {self.processed_count} items")
```

## Schema Migration

### Schema Evolution Management

```python
class SchemaEvolution:
    """Manage schema changes during migration."""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
        self.schema_versions = []
    
    async def apply_schema_migration(
        self,
        version: str,
        migration_func: callable,
        rollback_func: callable = None
    ):
        """
        Apply schema migration with versioning.
        
        Parameters
        ----------
        version : str
            Schema version identifier
        migration_func : callable
            Function to apply migration
        rollback_func : callable
            Function to rollback migration
        """
        # Check if already applied
        if await self._is_version_applied(version):
            print(f"Schema version {version} already applied")
            return
        
        try:
            # Apply migration
            print(f"Applying schema migration {version}")
            await migration_func(self.graphiti)
            
            # Record version
            await self._record_version(version)
            
            print(f"Schema migration {version} completed")
            
        except Exception as e:
            print(f"Schema migration {version} failed: {e}")
            
            if rollback_func:
                print(f"Rolling back {version}")
                await rollback_func(self.graphiti)
            
            raise
    
    async def _is_version_applied(self, version: str) -> bool:
        """Check if schema version is already applied."""
        query = """
        MATCH (v:SchemaVersion {version: $version})
        RETURN v
        """
        records, _, _ = await self.graphiti.driver.execute_query(
            query, version=version
        )
        return len(records) > 0
    
    async def _record_version(self, version: str):
        """Record applied schema version."""
        query = """
        CREATE (v:SchemaVersion {
            version: $version,
            applied_at: $timestamp
        })
        """
        await self.graphiti.driver.execute_query(
            query,
            version=version,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

# Example schema migrations
async def migration_v1_add_custom_entities(graphiti: Graphiti):
    """Add custom entity types."""
    # Add constraints for new entity types
    await graphiti.driver.execute_query(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Product) REQUIRE n.uuid IS UNIQUE"
    )
    await graphiti.driver.execute_query(
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Customer) REQUIRE n.uuid IS UNIQUE"
    )

async def migration_v2_add_temporal_indices(graphiti: Graphiti):
    """Add temporal indices for better query performance."""
    await graphiti.driver.execute_query(
        "CREATE INDEX temporal_validity IF NOT EXISTS FOR (n:Entity) ON (n.valid_at)"
    )
    await graphiti.driver.execute_query(
        "CREATE INDEX temporal_invalidity IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.invalid_at)"
    )
```

## Zero-Downtime Migration

### Blue-Green Migration Strategy

```python
class BlueGreenMigration:
    """Zero-downtime migration using blue-green deployment."""
    
    def __init__(
        self,
        blue_graphiti: Graphiti,  # Current production
        green_graphiti: Graphiti  # New instance
    ):
        self.blue = blue_graphiti
        self.green = green_graphiti
        self.sync_enabled = False
    
    async def execute_migration(self):
        """Execute blue-green migration."""
        # Phase 1: Initial sync
        print("Phase 1: Initial data sync")
        await self._initial_sync()
        
        # Phase 2: Enable dual writes
        print("Phase 2: Enabling dual writes")
        await self._enable_dual_writes()
        
        # Phase 3: Continuous sync
        print("Phase 3: Continuous synchronization")
        await self._continuous_sync()
        
        # Phase 4: Validation
        print("Phase 4: Validation")
        validation_passed = await self._validate_migration()
        
        if not validation_passed:
            print("Validation failed, rolling back")
            await self._rollback()
            return False
        
        # Phase 5: Switch traffic
        print("Phase 5: Switching traffic")
        await self._switch_traffic()
        
        # Phase 6: Cleanup
        print("Phase 6: Cleanup")
        await self._cleanup()
        
        return True
    
    async def _initial_sync(self):
        """Sync existing data from blue to green."""
        # Get all episodes from blue
        episodes = await self.blue.retrieve_episodes(
            reference_time=datetime.now(timezone.utc),
            last_n=10000
        )
        
        # Migrate to green
        for episode in episodes:
            await self.green.add_episode(
                name=episode.name,
                episode_body=episode.content,
                source_description=episode.source_description,
                reference_time=episode.valid_at,
                source=episode.source,
                group_id=episode.group_id,
                uuid=episode.uuid
            )
    
    async def _enable_dual_writes(self):
        """Enable writing to both instances."""
        self.sync_enabled = True
        
        # Monkey-patch add_episode to write to both
        original_add_episode = self.blue.add_episode
        
        async def dual_write_episode(*args, **kwargs):
            # Write to blue
            blue_result = await original_add_episode(*args, **kwargs)
            
            # Write to green
            try:
                await self.green.add_episode(*args, **kwargs)
            except Exception as e:
                logger.error(f"Failed to write to green: {e}")
            
            return blue_result
        
        self.blue.add_episode = dual_write_episode
    
    async def _continuous_sync(self):
        """Keep instances in sync during migration."""
        # Run for a defined period
        sync_duration = 3600  # 1 hour
        start_time = time.time()
        
        while time.time() - start_time < sync_duration:
            # Check for drift
            drift = await self._check_drift()
            
            if drift > 0:
                print(f"Detected drift of {drift} records, resyncing")
                await self._resync_drift()
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _check_drift(self) -> int:
        """Check for data drift between instances."""
        blue_count_query = "MATCH (n:Entity) RETURN count(n) as count"
        green_count_query = "MATCH (n:Entity) RETURN count(n) as count"
        
        blue_result, _, _ = await self.blue.driver.execute_query(blue_count_query)
        green_result, _, _ = await self.green.driver.execute_query(green_count_query)
        
        return abs(blue_result[0]['count'] - green_result[0]['count'])
    
    async def _validate_migration(self) -> bool:
        """Validate migration completeness and accuracy."""
        validations = []
        
        # Check record counts
        validations.append(await self._validate_counts())
        
        # Check data integrity
        validations.append(await self._validate_integrity())
        
        # Check search quality
        validations.append(await self._validate_search_quality())
        
        return all(validations)
    
    async def _switch_traffic(self):
        """Switch application traffic to green instance."""
        # This would typically involve updating load balancer
        # or service discovery configuration
        print("Traffic switched to green instance")
    
    async def _rollback(self):
        """Rollback migration if validation fails."""
        self.sync_enabled = False
        # Clear green instance
        await clear_data(self.green.driver)
        print("Migration rolled back")
    
    async def _cleanup(self):
        """Clean up after successful migration."""
        # Blue instance can be decommissioned
        print("Migration completed successfully")
```

## Validation and Testing

### Migration Validation Framework

```python
class MigrationValidator:
    """Comprehensive validation for migrations."""
    
    def __init__(self, source_system, target_graphiti: Graphiti):
        self.source = source_system
        self.target = target_graphiti
        self.validation_results = []
    
    async def validate_migration(self) -> dict:
        """Run complete validation suite."""
        results = {
            'data_completeness': await self._validate_completeness(),
            'data_integrity': await self._validate_integrity(),
            'search_quality': await self._validate_search(),
            'performance': await self._validate_performance(),
            'relationships': await self._validate_relationships()
        }
        
        # Calculate overall score
        scores = [r['score'] for r in results.values()]
        results['overall_score'] = sum(scores) / len(scores)
        
        return results
    
    async def _validate_completeness(self) -> dict:
        """Validate all data was migrated."""
        source_count = await self._get_source_count()
        target_count = await self._get_target_count()
        
        completeness = target_count / source_count if source_count > 0 else 0
        
        return {
            'score': completeness,
            'source_count': source_count,
            'target_count': target_count,
            'missing': source_count - target_count
        }
    
    async def _validate_integrity(self) -> dict:
        """Validate data integrity after migration."""
        # Sample records for validation
        sample_size = 100
        issues = []
        
        sample_records = await self._get_sample_records(sample_size)
        
        for record in sample_records:
            # Check for data corruption
            if not self._validate_record(record):
                issues.append(record)
        
        integrity_score = 1 - (len(issues) / sample_size)
        
        return {
            'score': integrity_score,
            'sample_size': sample_size,
            'issues': issues
        }
    
    async def _validate_search(self) -> dict:
        """Validate search functionality."""
        test_queries = [
            "recent updates",
            "user preferences",
            "product information",
            "system configuration"
        ]
        
        search_scores = []
        
        for query in test_queries:
            results = await self.target.search(query=query, num_results=10)
            
            # Score based on result relevance
            score = self._score_search_results(query, results)
            search_scores.append(score)
        
        return {
            'score': sum(search_scores) / len(search_scores),
            'queries_tested': len(test_queries),
            'avg_result_count': sum(len(r) for r in search_scores) / len(search_scores)
        }
    
    async def _validate_performance(self) -> dict:
        """Validate performance metrics."""
        import time
        
        # Test ingestion speed
        start = time.time()
        await self.target.add_episode(
            name="Performance test",
            episode_body="Test content for performance validation",
            source_description="validation",
            reference_time=datetime.now(timezone.utc)
        )
        ingestion_time = time.time() - start
        
        # Test search speed
        start = time.time()
        await self.target.search(query="test", num_results=10)
        search_time = time.time() - start
        
        # Score based on thresholds
        ingestion_score = 1.0 if ingestion_time < 1.0 else 0.5
        search_score = 1.0 if search_time < 0.1 else 0.5
        
        return {
            'score': (ingestion_score + search_score) / 2,
            'ingestion_time_ms': ingestion_time * 1000,
            'search_time_ms': search_time * 1000
        }
    
    async def _validate_relationships(self) -> dict:
        """Validate relationship preservation."""
        # Check if relationships are preserved
        query = """
        MATCH (n:Entity)-[r:RELATES_TO]->(m:Entity)
        RETURN count(r) as relationship_count
        """
        
        result, _, _ = await self.target.driver.execute_query(query)
        relationship_count = result[0]['relationship_count']
        
        # Compare with expected relationships
        expected_relationships = await self._get_expected_relationships()
        
        preservation_rate = (
            relationship_count / expected_relationships 
            if expected_relationships > 0 else 1.0
        )
        
        return {
            'score': preservation_rate,
            'found_relationships': relationship_count,
            'expected_relationships': expected_relationships
        }
```

## Rollback Strategies

### Automated Rollback System

```python
class RollbackManager:
    """Manage rollback operations for failed migrations."""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
        self.backup_path = "migration_backup"
    
    async def create_backup(self) -> str:
        """Create backup before migration."""
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Export data
        await self._export_nodes(backup_id)
        await self._export_edges(backup_id)
        await self._export_episodes(backup_id)
        
        return backup_id
    
    async def rollback_to_backup(self, backup_id: str):
        """Rollback to a specific backup."""
        # Clear current data
        await clear_data(self.graphiti.driver)
        
        # Restore from backup
        await self._restore_nodes(backup_id)
        await self._restore_edges(backup_id)
        await self._restore_episodes(backup_id)
        
        # Rebuild indices
        await self.graphiti.build_indices_and_constraints()
    
    async def _export_nodes(self, backup_id: str):
        """Export nodes to backup."""
        query = """
        MATCH (n:Entity)
        RETURN n
        """
        
        records, _, _ = await self.graphiti.driver.execute_query(query)
        
        with open(f"{self.backup_path}/{backup_id}_nodes.json", 'w') as f:
            json.dump([dict(r['n']) for r in records], f)
    
    async def _restore_nodes(self, backup_id: str):
        """Restore nodes from backup."""
        with open(f"{self.backup_path}/{backup_id}_nodes.json", 'r') as f:
            nodes = json.load(f)
        
        for node_data in nodes:
            node = EntityNode(**node_data)
            await node.save(self.graphiti.driver)
```

## Post-Migration Optimization

### Optimization Tasks

```python
async def post_migration_optimization(graphiti: Graphiti):
    """Run optimization tasks after migration."""
    
    print("Running post-migration optimizations...")
    
    # 1. Rebuild indices
    print("Rebuilding indices...")
    await graphiti.build_indices_and_constraints(delete_existing=True)
    
    # 2. Generate missing embeddings
    print("Generating missing embeddings...")
    await generate_missing_embeddings(graphiti)
    
    # 3. Build communities
    print("Building communities...")
    await graphiti.build_communities()
    
    # 4. Optimize graph structure
    print("Optimizing graph structure...")
    await optimize_graph_structure(graphiti)
    
    # 5. Cache warming
    print("Warming caches...")
    await warm_caches(graphiti)
    
    print("Post-migration optimization complete")

async def generate_missing_embeddings(graphiti: Graphiti):
    """Generate embeddings for nodes/edges without them."""
    # Find nodes without embeddings
    query = """
    MATCH (n:Entity)
    WHERE n.name_embedding IS NULL
    RETURN n
    """
    
    records, _, _ = await graphiti.driver.execute_query(query)
    
    nodes = [EntityNode(**dict(r['n'])) for r in records]
    
    # Generate embeddings in batches
    for i in range(0, len(nodes), 100):
        batch = nodes[i:i+100]
        await create_entity_node_embeddings(graphiti.embedder, batch)
        
        # Save updated nodes
        for node in batch:
            await node.save(graphiti.driver)

async def optimize_graph_structure(graphiti: Graphiti):
    """Optimize graph structure for better query performance."""
    # Remove orphaned nodes
    await graphiti.driver.execute_query("""
        MATCH (n:Entity)
        WHERE NOT (n)-[:RELATES_TO]-()
        AND NOT (n)<-[:MENTIONS]-()
        DELETE n
    """)
    
    # Merge duplicate edges
    await graphiti.driver.execute_query("""
        MATCH (n:Entity)-[r1:RELATES_TO]->(m:Entity)
        MATCH (n)-[r2:RELATES_TO]->(m)
        WHERE id(r1) < id(r2) AND r1.fact = r2.fact
        DELETE r2
    """)

async def warm_caches(graphiti: Graphiti):
    """Warm up caches with common queries."""
    common_queries = [
        "recent activity",
        "user information",
        "system status",
        "configuration settings"
    ]
    
    for query in common_queries:
        await graphiti.search(query=query, num_results=10)
```

## Conclusion

This migration guide provides comprehensive strategies for moving to Graphiti from various systems:

1. **Vector Databases**: Preserve embeddings while adding graph structure
2. **Graph Databases**: Map schemas and maintain relationships
3. **GraphRAG**: Leverage existing extractions with dynamic updates
4. **Large Datasets**: Stream with checkpointing and parallel processing
5. **Zero-Downtime**: Blue-green deployment with validation
6. **Validation**: Comprehensive testing framework
7. **Rollback**: Automated backup and restore capabilities
8. **Optimization**: Post-migration performance tuning

Key principles:
- **Incremental Migration**: Process in batches with checkpoints
- **Validation First**: Test thoroughly before switching
- **Preserve Context**: Maintain relationships and metadata
- **Performance Focus**: Optimize for production workloads
- **Safety Net**: Always have rollback strategy ready
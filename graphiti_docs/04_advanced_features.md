# Advanced Features and Techniques

## Table of Contents
1. [Community Detection and Management](#community-detection-and-management)
2. [Custom Ontologies](#custom-ontologies)
3. [Temporal Reasoning](#temporal-reasoning)
4. [Graph Analytics](#graph-analytics)
5. [Multi-Model Integration](#multi-model-integration)
6. [Advanced Search Strategies](#advanced-search-strategies)
7. [Production Patterns](#production-patterns)

---

## Community Detection and Management

### Understanding Communities in Graphiti

Communities are clusters of highly interconnected nodes that represent groups of related entities. Graphiti automatically detects and maintains these communities to improve search relevance and provide context.

```python
from graphiti_core.nodes import CommunityNode
from graphiti_core.edges import CommunityEdge

class CommunityManager:
    def __init__(self, graphiti):
        self.graphiti = graphiti
    
    async def build_communities(self, algorithm: str = "louvain"):
        """
        Build communities using specified algorithm.
        """
        # Graphiti provides built-in community detection
        communities = await self.graphiti.build_communities(
            algorithm=algorithm,
            resolution=1.0,  # Higher = more communities
            min_community_size=3
        )
        
        print(f"Detected {len(communities)} communities")
        
        for community in communities:
            print(f"Community {community.uuid}:")
            print(f"  Name: {community.name}")
            print(f"  Size: {community.member_count}")
            print(f"  Summary: {community.summary}")
    
    async def get_community_members(
        self,
        community_uuid: str
    ) -> List[EntityNode]:
        """
        Get all members of a community.
        """
        query = """
        MATCH (c:Community {uuid: $community_uuid})-[:HAS_MEMBER]->(n:Entity)
        RETURN n
        """
        
        results = await self.graphiti.driver.execute(query, {
            'community_uuid': community_uuid
        })
        
        return [EntityNode(**record['n']) for record in results]
    
    async def find_entity_communities(
        self,
        entity_name: str
    ) -> List[CommunityNode]:
        """
        Find all communities an entity belongs to.
        """
        results = await self.graphiti.search(
            f"communities containing {entity_name}"
        )
        
        communities = []
        for result in results:
            if isinstance(result, CommunityNode):
                communities.append(result)
        
        return communities
```

### Dynamic Community Updates

```python
async def update_communities_incrementally(graphiti):
    """
    Update communities as new data arrives.
    """
    # Add new episode
    await graphiti.add_episode(
        name="New Team Formation",
        episode_body="""
        Alice, Bob, and Charlie are forming a new AI research team.
        They will focus on large language models and knowledge graphs.
        """,
        source=EpisodeType.text,
        reference_time=datetime.now(timezone.utc)
    )
    
    # Update communities based on new information
    await graphiti.update_communities(
        incremental=True,  # Don't rebuild from scratch
        affected_nodes_only=True  # Only update affected communities
    )
```

### Community-Based Search

```python
async def community_aware_search(graphiti):
    """
    Search within specific communities for focused results.
    """
    # Find relevant community first
    communities = await graphiti.search_communities("engineering team")
    
    if communities:
        target_community = communities[0]
        
        # Search within community context
        results = await graphiti.search(
            query="recent decisions",
            community_uuid=target_community.uuid,
            expand_to_neighbors=True  # Include related communities
        )
        
        return results
```

---

## Custom Ontologies

### Building Domain-Specific Ontologies

```python
from typing import Dict, List, Type
from pydantic import BaseModel, Field

class OntologyBuilder:
    """
    Build and manage custom ontologies for specific domains.
    """
    def __init__(self):
        self.entity_types: Dict[str, Type[BaseModel]] = {}
        self.relationship_types: Dict[str, Type[BaseModel]] = {}
        self.constraints: List[Dict] = []
    
    def define_healthcare_ontology(self):
        """
        Define ontology for healthcare domain.
        """
        # Entity types
        class Patient(BaseModel):
            """A patient in the healthcare system."""
            patient_id: str = Field(..., description="Unique patient identifier")
            age: int = Field(..., description="Patient age")
            gender: str = Field(..., description="Patient gender")
            medical_history: List[str] = Field(default_factory=list)
        
        class Doctor(BaseModel):
            """A medical practitioner."""
            license_number: str = Field(..., description="Medical license number")
            specialization: str = Field(..., description="Medical specialization")
            hospital: str = Field(..., description="Affiliated hospital")
        
        class Diagnosis(BaseModel):
            """A medical diagnosis."""
            icd_code: str = Field(..., description="ICD-10 code")
            description: str = Field(..., description="Diagnosis description")
            severity: str = Field(..., description="Severity level")
        
        class Medication(BaseModel):
            """A prescribed medication."""
            drug_name: str = Field(..., description="Generic drug name")
            dosage: str = Field(..., description="Dosage information")
            frequency: str = Field(..., description="Dosing frequency")
        
        # Relationship types
        class Treats(BaseModel):
            """Doctor treats Patient."""
            start_date: str = Field(..., description="Treatment start date")
            primary_physician: bool = Field(default=False)
        
        class DiagnosedWith(BaseModel):
            """Patient diagnosed with Diagnosis."""
            diagnosis_date: str = Field(..., description="Date of diagnosis")
            confirmed: bool = Field(default=True)
        
        class Prescribes(BaseModel):
            """Doctor prescribes Medication to Patient."""
            prescription_date: str = Field(..., description="Prescription date")
            duration_days: int = Field(..., description="Duration in days")
        
        # Register types
        self.entity_types = {
            "Patient": Patient,
            "Doctor": Doctor,
            "Diagnosis": Diagnosis,
            "Medication": Medication
        }
        
        self.relationship_types = {
            "TREATS": Treats,
            "DIAGNOSED_WITH": DiagnosedWith,
            "PRESCRIBES": Prescribes
        }
        
        # Define constraints
        self.constraints = [
            {
                "type": "cardinality",
                "relationship": "TREATS",
                "min": 0,
                "max": None,  # A doctor can treat many patients
                "from": "Doctor",
                "to": "Patient"
            },
            {
                "type": "required",
                "entity": "Patient",
                "fields": ["patient_id", "age", "gender"]
            }
        ]
        
        return self
    
    def define_financial_ontology(self):
        """
        Define ontology for financial domain.
        """
        class Account(BaseModel):
            """A financial account."""
            account_number: str
            account_type: str
            balance: float
            currency: str = "USD"
        
        class Transaction(BaseModel):
            """A financial transaction."""
            transaction_id: str
            amount: float
            transaction_type: str
            timestamp: str
        
        class Customer(BaseModel):
            """A bank customer."""
            customer_id: str
            risk_score: float
            kyc_verified: bool
        
        # Relationships
        class Owns(BaseModel):
            """Customer owns Account."""
            since: str
            is_primary: bool
        
        class Transfers(BaseModel):
            """Transaction transfers between Accounts."""
            from_account: str
            to_account: str
            status: str
        
        self.entity_types.update({
            "Account": Account,
            "Transaction": Transaction,
            "Customer": Customer
        })
        
        self.relationship_types.update({
            "OWNS": Owns,
            "TRANSFERS": Transfers
        })
        
        return self
```

### Applying Custom Ontologies

```python
async def apply_custom_ontology(graphiti: Graphiti):
    """
    Apply custom ontology to Graphiti instance.
    """
    # Build ontology
    ontology_builder = OntologyBuilder()
    ontology_builder.define_healthcare_ontology()
    
    # Register entity types with Graphiti
    for entity_type in ontology_builder.entity_types.values():
        graphiti.register_entity_type(entity_type)
    
    # Register relationship types
    for rel_type in ontology_builder.relationship_types.values():
        graphiti.register_relationship_type(rel_type)
    
    # Apply constraints
    for constraint in ontology_builder.constraints:
        await graphiti.add_constraint(constraint)
    
    # Now Graphiti will use these types for extraction
    medical_record = """
    Patient John Doe (ID: P12345, 45 years old, male) was treated by 
    Dr. Sarah Smith (License: MD98765, Cardiologist at City Hospital).
    He was diagnosed with hypertension (ICD: I10) on January 15, 2024.
    Dr. Smith prescribed Lisinopril 10mg once daily for 90 days.
    """
    
    result = await graphiti.add_episode(
        name="Medical Record",
        episode_body=medical_record,
        source=EpisodeType.text,
        reference_time=datetime(2024, 1, 15)
    )
    
    # Entities will be extracted according to the ontology
    print(f"Extracted {len(result.nodes)} typed entities")
```

---

## Temporal Reasoning

### Advanced Temporal Queries

```python
class TemporalReasoner:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
    
    async def get_timeline(
        self,
        entity_name: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        Get complete timeline of events for an entity.
        """
        query = """
        MATCH (n:Entity {name: $entity_name})-[r]-(m:Entity)
        WHERE r.valid_at >= $start_date AND r.valid_at <= $end_date
        RETURN r.valid_at as timestamp,
               r.fact as fact,
               m.name as related_entity,
               r.invalid_at as ended_at
        ORDER BY r.valid_at
        """
        
        results = await self.graphiti.driver.execute(query, {
            'entity_name': entity_name,
            'start_date': start_date,
            'end_date': end_date
        })
        
        timeline = []
        for record in results:
            timeline.append({
                'timestamp': record['timestamp'],
                'fact': record['fact'],
                'related_entity': record['related_entity'],
                'ended_at': record['ended_at'],
                'duration': self._calculate_duration(
                    record['timestamp'],
                    record['ended_at']
                )
            })
        
        return timeline
    
    async def find_concurrent_facts(
        self,
        reference_time: datetime,
        entity_name: str = None
    ) -> List[Dict]:
        """
        Find all facts that were valid at a specific time.
        """
        query = """
        MATCH (n:Entity)-[r]-(m:Entity)
        WHERE r.valid_at <= $reference_time 
        AND (r.invalid_at IS NULL OR r.invalid_at > $reference_time)
        """
        
        if entity_name:
            query += " AND (n.name = $entity_name OR m.name = $entity_name)"
        
        query += " RETURN n.name as source, r.fact as fact, m.name as target"
        
        params = {'reference_time': reference_time}
        if entity_name:
            params['entity_name'] = entity_name
        
        results = await self.graphiti.driver.execute(query, params)
        
        return [
            {
                'source': r['source'],
                'fact': r['fact'],
                'target': r['target']
            }
            for r in results
        ]
    
    async def detect_temporal_patterns(
        self,
        pattern_type: str = "periodic"
    ) -> List[Dict]:
        """
        Detect temporal patterns in the data.
        """
        if pattern_type == "periodic":
            # Find facts that repeat periodically
            query = """
            MATCH (n:Entity)-[r1]-(m:Entity)
            MATCH (n)-[r2]-(m)
            WHERE r1.uuid <> r2.uuid
            AND r1.fact = r2.fact
            AND r1.invalid_at IS NOT NULL
            AND r2.valid_at > r1.invalid_at
            RETURN n.name as entity,
                   r1.fact as fact,
                   r1.valid_at as first_occurrence,
                   r2.valid_at as second_occurrence,
                   duration.between(r1.invalid_at, r2.valid_at) as gap
            """
        
        elif pattern_type == "cascading":
            # Find cascading changes
            query = """
            MATCH (n:Entity)-[r1]-(m:Entity)-[r2]-(o:Entity)
            WHERE r2.valid_at > r1.valid_at
            AND r2.valid_at < r1.valid_at + duration('P1D')
            RETURN n.name as trigger_entity,
                   r1.fact as trigger_fact,
                   m.name as intermediate,
                   r2.fact as cascade_fact,
                   o.name as affected_entity
            """
        
        results = await self.graphiti.driver.execute(query)
        return list(results)
```

### Temporal Conflict Detection

```python
async def detect_temporal_conflicts(graphiti: Graphiti):
    """
    Detect conflicting temporal facts.
    """
    query = """
    MATCH (n:Entity)-[r1]-(m:Entity)
    MATCH (n)-[r2]-(m)
    WHERE r1.uuid <> r2.uuid
    AND r1.valid_at < r2.invalid_at
    AND r2.valid_at < r1.invalid_at
    AND r1.fact <> r2.fact
    RETURN n.name as entity1,
           m.name as entity2,
           r1.fact as fact1,
           r2.fact as fact2,
           r1.valid_at as fact1_start,
           r1.invalid_at as fact1_end,
           r2.valid_at as fact2_start,
           r2.invalid_at as fact2_end
    """
    
    conflicts = await graphiti.driver.execute(query)
    
    for conflict in conflicts:
        print(f"Temporal conflict detected:")
        print(f"  Entities: {conflict['entity1']} - {conflict['entity2']}")
        print(f"  Fact 1: {conflict['fact1']} ({conflict['fact1_start']} to {conflict['fact1_end']})")
        print(f"  Fact 2: {conflict['fact2']} ({conflict['fact2_start']} to {conflict['fact2_end']})")
```

---

## Graph Analytics

### Network Analysis Metrics

```python
class GraphAnalyzer:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
    
    async def calculate_centrality_metrics(self):
        """
        Calculate various centrality metrics for nodes.
        """
        metrics = {}
        
        # Degree centrality
        degree_query = """
        MATCH (n:Entity)
        RETURN n.name as name,
               size((n)--()) as degree
        ORDER BY degree DESC
        LIMIT 10
        """
        
        degree_results = await self.graphiti.driver.execute(degree_query)
        metrics['top_degree_nodes'] = list(degree_results)
        
        # Betweenness centrality (simplified)
        betweenness_query = """
        MATCH p = allShortestPaths((a:Entity)-[*]-(b:Entity))
        WHERE a <> b
        UNWIND nodes(p)[1..-1] as n
        RETURN n.name as name,
               count(*) as betweenness
        ORDER BY betweenness DESC
        LIMIT 10
        """
        
        betweenness_results = await self.graphiti.driver.execute(betweenness_query)
        metrics['top_betweenness_nodes'] = list(betweenness_results)
        
        # Clustering coefficient
        clustering_query = """
        MATCH (n:Entity)--(neighbor)
        WITH n, collect(distinct neighbor) as neighbors
        MATCH (n1)--(n2)
        WHERE n1 IN neighbors AND n2 IN neighbors AND n1 <> n2
        WITH n, neighbors, count(DISTINCT [n1, n2]) as connections
        WITH n, size(neighbors) as k, connections
        WHERE k > 1
        RETURN n.name as name,
               2.0 * connections / (k * (k - 1)) as clustering_coefficient
        ORDER BY clustering_coefficient DESC
        """
        
        clustering_results = await self.graphiti.driver.execute(clustering_query)
        metrics['clustering_coefficients'] = list(clustering_results)
        
        return metrics
    
    async def find_knowledge_gaps(self):
        """
        Identify potential missing relationships in the graph.
        """
        query = """
        // Find entities that should be connected but aren't
        MATCH (a:Entity)-[:RELATES_TO]-(common:Entity)-[:RELATES_TO]-(b:Entity)
        WHERE NOT (a)-[:RELATES_TO]-(b)
        AND a <> b
        WITH a, b, count(distinct common) as common_neighbors
        WHERE common_neighbors >= 3
        RETURN a.name as entity1,
               b.name as entity2,
               common_neighbors,
               collect(common.name)[..5] as examples
        ORDER BY common_neighbors DESC
        LIMIT 20
        """
        
        gaps = await self.graphiti.driver.execute(query)
        
        suggestions = []
        for gap in gaps:
            suggestions.append({
                'entity1': gap['entity1'],
                'entity2': gap['entity2'],
                'confidence': gap['common_neighbors'] / 10.0,  # Normalize
                'evidence': gap['examples']
            })
        
        return suggestions
```

### Graph Evolution Analysis

```python
async def analyze_graph_evolution(graphiti: Graphiti):
    """
    Analyze how the graph has evolved over time.
    """
    # Growth rate analysis
    growth_query = """
    MATCH (n:Entity)
    WITH date(n.created_at) as creation_date, count(*) as daily_nodes
    ORDER BY creation_date
    RETURN creation_date,
           daily_nodes,
           sum(daily_nodes) OVER (ORDER BY creation_date) as cumulative_nodes
    """
    
    growth_data = await graphiti.driver.execute(growth_query)
    
    # Relationship dynamics
    relationship_query = """
    MATCH ()-[r:RELATES_TO]->()
    WITH date(r.created_at) as creation_date,
         CASE WHEN r.invalid_at IS NOT NULL THEN 1 ELSE 0 END as is_invalidated,
         count(*) as count
    RETURN creation_date,
           sum(CASE WHEN is_invalidated = 1 THEN count ELSE 0 END) as invalidated,
           sum(CASE WHEN is_invalidated = 0 THEN count ELSE 0 END) as active
    ORDER BY creation_date
    """
    
    relationship_data = await graphiti.driver.execute(relationship_query)
    
    return {
        'node_growth': list(growth_data),
        'relationship_dynamics': list(relationship_data)
    }
```

---

## Multi-Model Integration

### Using Different LLM Providers

```python
from graphiti_core.llm_client import AnthropicClient, GeminiClient
from graphiti_core.embedder import VoyageEmbedder
from graphiti_core.cross_encoder import BGERerankerClient

async def setup_multi_model_graphiti():
    """
    Configure Graphiti with multiple model providers.
    """
    # Use Anthropic for extraction (better structured output)
    llm_client = AnthropicClient(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-opus-20240229"
    )
    
    # Use Voyage for embeddings (specialized for retrieval)
    embedder = VoyageEmbedder(
        api_key=os.getenv("VOYAGE_API_KEY"),
        model="voyage-2"
    )
    
    # Use BGE for reranking (open-source, fast)
    reranker = BGERerankerClient(
        model_name="BAAI/bge-reranker-large"
    )
    
    graphiti = Graphiti(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password",
        llm_client=llm_client,
        embedder=embedder,
        cross_encoder=reranker
    )
    
    return graphiti
```

### Model Fallback Strategy

```python
class ModelFallbackManager:
    def __init__(self):
        self.primary_client = OpenAIClient()
        self.fallback_clients = [
            AnthropicClient(),
            GeminiClient(),
            GroqClient()
        ]
    
    async def extract_with_fallback(
        self,
        text: str,
        max_retries: int = 3
    ):
        """
        Try extraction with fallback models.
        """
        clients = [self.primary_client] + self.fallback_clients
        
        for i, client in enumerate(clients):
            try:
                result = await client.extract_entities(text)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Model {i} failed: {e}")
                if i == len(clients) - 1:
                    raise
                continue
        
        raise Exception("All models failed")
```

---

## Advanced Search Strategies

### Semantic Search with Context Windows

```python
class ContextualSearch:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
    
    async def search_with_context(
        self,
        query: str,
        context_size: int = 3,
        context_type: str = "temporal"
    ):
        """
        Search with expanded context windows.
        """
        # Initial search
        initial_results = await self.graphiti.search(query, limit=10)
        
        if not initial_results:
            return []
        
        expanded_results = []
        
        for result in initial_results:
            if context_type == "temporal":
                # Get temporally adjacent facts
                context = await self._get_temporal_context(
                    result,
                    window_size=context_size
                )
            elif context_type == "graph":
                # Get graph-adjacent facts
                context = await self._get_graph_context(
                    result,
                    hop_distance=context_size
                )
            
            expanded_results.append({
                'main_result': result,
                'context': context
            })
        
        return expanded_results
    
    async def _get_temporal_context(
        self,
        result,
        window_size: int
    ):
        """
        Get facts within temporal window.
        """
        query = """
        MATCH (n:Entity {uuid: $node_uuid})-[r]-()
        WHERE abs(duration.between(r.valid_at, $reference_time).days) <= $window_days
        RETURN r.fact as fact,
               r.valid_at as timestamp
        ORDER BY abs(duration.between(r.valid_at, $reference_time).days)
        LIMIT 10
        """
        
        context = await self.graphiti.driver.execute(query, {
            'node_uuid': result.source_node_uuid,
            'reference_time': result.valid_at,
            'window_days': window_size
        })
        
        return list(context)
```

### Query Expansion and Refinement

```python
class QueryExpander:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
        self.llm_client = graphiti.llm_client
    
    async def expand_query(
        self,
        original_query: str
    ) -> List[str]:
        """
        Expand query with synonyms and related terms.
        """
        prompt = f"""
        Generate search query variations for: "{original_query}"
        
        Include:
        1. Synonyms
        2. Related concepts
        3. Different phrasings
        4. Broader and narrower terms
        
        Return as a list of queries.
        """
        
        expansions = await self.llm_client.generate(prompt)
        return self._parse_expansions(expansions)
    
    async def iterative_refinement(
        self,
        query: str,
        max_iterations: int = 3
    ):
        """
        Iteratively refine search based on results.
        """
        results_history = []
        current_query = query
        
        for i in range(max_iterations):
            # Search with current query
            results = await self.graphiti.search(current_query)
            results_history.append(results)
            
            if not results or i == max_iterations - 1:
                break
            
            # Refine query based on results
            current_query = await self._refine_query(
                original_query=query,
                current_query=current_query,
                results=results
            )
        
        # Merge and deduplicate all results
        all_results = []
        seen_uuids = set()
        
        for iteration_results in results_history:
            for result in iteration_results:
                if result.uuid not in seen_uuids:
                    all_results.append(result)
                    seen_uuids.add(result.uuid)
        
        return all_results
```

---

## Production Patterns

### Error Handling and Resilience

```python
class ResilientGraphiti:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
        self.retry_config = {
            'max_retries': 3,
            'backoff_factor': 2,
            'max_backoff': 60
        }
    
    async def add_episode_with_retry(
        self,
        **kwargs
    ):
        """
        Add episode with exponential backoff retry.
        """
        retries = 0
        backoff = 1
        
        while retries < self.retry_config['max_retries']:
            try:
                result = await self.graphiti.add_episode(**kwargs)
                return result
            
            except Exception as e:
                retries += 1
                if retries == self.retry_config['max_retries']:
                    logger.error(f"Failed after {retries} retries: {e}")
                    raise
                
                wait_time = min(
                    backoff * self.retry_config['backoff_factor'],
                    self.retry_config['max_backoff']
                )
                
                logger.warning(f"Retry {retries} after {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
                backoff *= self.retry_config['backoff_factor']
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check.
        """
        health_status = {
            'database': 'unknown',
            'llm': 'unknown',
            'embedder': 'unknown',
            'indices': 'unknown',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Check database connection
        try:
            await self.graphiti.driver.execute("MATCH (n) RETURN count(n) LIMIT 1")
            health_status['database'] = 'healthy'
        except Exception as e:
            health_status['database'] = f'unhealthy: {str(e)}'
        
        # Check LLM
        try:
            test_response = await self.graphiti.llm_client.generate("test")
            health_status['llm'] = 'healthy' if test_response else 'degraded'
        except Exception as e:
            health_status['llm'] = f'unhealthy: {str(e)}'
        
        # Check embedder
        try:
            test_embedding = await self.graphiti.embedder.embed("test")
            health_status['embedder'] = 'healthy' if test_embedding else 'degraded'
        except Exception as e:
            health_status['embedder'] = f'unhealthy: {str(e)}'
        
        # Check indices
        try:
            index_check = await self.graphiti.driver.execute(
                "SHOW INDEXES YIELD name RETURN count(name) as count"
            )
            health_status['indices'] = f"healthy: {index_check[0]['count']} indices"
        except Exception as e:
            health_status['indices'] = f'unhealthy: {str(e)}'
        
        return health_status
```

### Monitoring and Observability

```python
import prometheus_client
from prometheus_client import Counter, Histogram, Gauge

class GraphitiMetrics:
    def __init__(self):
        # Define metrics
        self.episode_counter = Counter(
            'graphiti_episodes_total',
            'Total number of episodes processed',
            ['source_type', 'status']
        )
        
        self.extraction_duration = Histogram(
            'graphiti_extraction_duration_seconds',
            'Time spent extracting entities and relationships',
            ['entity_type']
        )
        
        self.graph_size = Gauge(
            'graphiti_graph_size',
            'Current size of the graph',
            ['element_type']
        )
        
        self.search_latency = Histogram(
            'graphiti_search_latency_seconds',
            'Search query latency',
            ['search_type']
        )
    
    def record_episode(self, source_type: str, status: str):
        """Record episode processing."""
        self.episode_counter.labels(
            source_type=source_type,
            status=status
        ).inc()
    
    def record_extraction(self, entity_type: str, duration: float):
        """Record extraction duration."""
        self.extraction_duration.labels(
            entity_type=entity_type
        ).observe(duration)
    
    async def update_graph_metrics(self, graphiti: Graphiti):
        """Update graph size metrics."""
        # Count nodes
        node_count = await graphiti.driver.execute(
            "MATCH (n) RETURN count(n) as count"
        )
        self.graph_size.labels(element_type='nodes').set(
            node_count[0]['count']
        )
        
        # Count edges
        edge_count = await graphiti.driver.execute(
            "MATCH ()-[r]->() RETURN count(r) as count"
        )
        self.graph_size.labels(element_type='edges').set(
            edge_count[0]['count']
        )
```

### Data Privacy and Security

```python
class SecureGraphiti:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
        self.pii_patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'
        }
    
    async def add_episode_with_pii_check(
        self,
        episode_body: str,
        **kwargs
    ):
        """
        Add episode after PII detection and optional redaction.
        """
        # Detect PII
        pii_found = self._detect_pii(episode_body)
        
        if pii_found:
            # Option 1: Reject
            # raise ValueError(f"PII detected: {pii_found}")
            
            # Option 2: Redact
            episode_body = self._redact_pii(episode_body, pii_found)
        
        # Add metadata about PII handling
        kwargs['source_description'] = kwargs.get('source_description', '') + \
            f" [PII_REDACTED: {','.join(pii_found.keys())}]" if pii_found else ""
        
        return await self.graphiti.add_episode(
            episode_body=episode_body,
            **kwargs
        )
    
    def _detect_pii(self, text: str) -> Dict[str, List[str]]:
        """Detect PII in text."""
        import re
        
        found_pii = {}
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                found_pii[pii_type] = matches
        
        return found_pii
    
    def _redact_pii(self, text: str, pii_found: Dict) -> str:
        """Redact PII from text."""
        import re
        
        for pii_type, pattern in self.pii_patterns.items():
            if pii_type in pii_found:
                text = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", text)
        
        return text
```

---

## Next Steps

This advanced features guide covers sophisticated capabilities of Graphiti. Continue with:

- **[05_integration_patterns.md](./05_integration_patterns.md)** - Integration with AI frameworks
- **[06_performance_tuning.md](./06_performance_tuning.md)** - Optimization for production
- **[07_api_reference.md](./07_api_reference.md)** - Complete API documentation
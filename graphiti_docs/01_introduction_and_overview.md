# Graphiti: A Comprehensive Guide to Temporal Knowledge Graphs for AI Agents

## Table of Contents
1. [Introduction and Overview](#introduction-and-overview)
2. [Why Graphiti?](#why-graphiti)
3. [Core Concepts](#core-concepts)
4. [Architecture Deep Dive](#architecture-deep-dive)
5. [Comparison with Traditional Approaches](#comparison-with-traditional-approaches)

---

## Introduction and Overview

Graphiti is a groundbreaking open-source framework developed by Zep AI for building and querying **temporally-aware knowledge graphs** specifically designed for AI agents operating in dynamic environments. Unlike traditional RAG (Retrieval-Augmented Generation) approaches that rely on static document stores and batch processing, Graphiti provides a living, breathing memory system that evolves in real-time.

### What is Graphiti?

At its core, Graphiti is a Python framework that:
- **Builds knowledge graphs incrementally** from both structured and unstructured data
- **Tracks temporal changes** in facts and relationships over time
- **Provides sub-second retrieval** through hybrid search mechanisms
- **Maintains historical context** without requiring full graph recomputation
- **Powers production AI systems** at scale

### The Knowledge Graph Paradigm

A knowledge graph represents information as a network of interconnected facts. Each fact is a "triplet" consisting of:
- **Two entities (nodes)**: e.g., "Kendra", "Adidas shoes"
- **Their relationship (edge)**: e.g., "loves"
- **Temporal metadata**: When this fact was true and when it was recorded

Example: "Kendra loves Adidas shoes" becomes:
```
[Kendra] ---(loves)---> [Adidas shoes]
         valid_from: 2024-01-01
         recorded_at: 2024-01-15
```

### Real-World Impact

Graphiti powers Zep, a turn-key context engineering platform that has demonstrated:
- **94.8% accuracy** on the Deep Memory Retrieval (DMR) benchmark (vs. 93.4% for MemGPT)
- **18.5% accuracy improvements** on the LongMemEval benchmark
- **90% reduction in response latency** (from ~30 seconds to ~3 seconds)
- **98% reduction in token usage** while maintaining high accuracy

---

## Why Graphiti?

### The Problem with Traditional RAG

Traditional RAG systems face several critical limitations:

1. **Static Knowledge Representation**
   - Documents are indexed once and rarely updated
   - No mechanism to track how information changes over time
   - Contradictions are handled poorly or not at all

2. **Batch Processing Overhead**
   - Entire document stores must be re-indexed for updates
   - Costly recomputation for every change
   - Latency measured in tens of seconds for complex queries

3. **Limited Contextual Understanding**
   - Cannot reason about temporal relationships
   - No way to query historical states
   - Loses context between related facts

### Graphiti's Solution

Graphiti addresses these challenges through several key innovations:

#### 1. Real-Time Incremental Updates
```python
# Traditional RAG: Re-index entire corpus
rag_system.rebuild_index(all_documents)  # Minutes to hours

# Graphiti: Add new information instantly
await graphiti.add_episode(
    name="Meeting Notes",
    episode_body="Alice is now the VP of Engineering",
    reference_time=datetime.now()
)  # Milliseconds
```

#### 2. Bi-Temporal Data Model
Graphiti tracks two critical time dimensions:
- **Valid Time (t_valid/t_invalid)**: When a fact was true in the real world
- **Transaction Time (t_created)**: When the fact was recorded in the system

This enables queries like:
- "What was Alice's role last month?"
- "When did we learn about the reorganization?"
- "Show me all changes to the product roadmap"

#### 3. Intelligent Conflict Resolution
When new information contradicts existing facts:
```python
# Existing fact: "Bob is the CEO" (valid_from: 2020-01-01)
# New information: "Alice is now the CEO"

# Graphiti automatically:
# 1. Marks the old fact as invalid (t_invalid: 2024-01-01)
# 2. Creates new fact with validity period
# 3. Preserves historical record for temporal queries
```

#### 4. Hybrid Search with Sub-Second Latency
Graphiti combines three search methods:
- **Semantic Search**: Vector embeddings for conceptual similarity
- **Keyword Search**: BM25 for exact term matching
- **Graph Traversal**: Relationship-based exploration

Results are merged and reranked in ~300ms at the 95th percentile.

### Use Cases Where Graphiti Excels

1. **Autonomous AI Agents**
   - Maintain conversation context across sessions
   - Track evolving user preferences
   - Remember task history and outcomes

2. **Enterprise Knowledge Management**
   - Integrate CRM, support tickets, and documentation
   - Track organizational changes
   - Maintain audit trails

3. **Dynamic Research Systems**
   - Monitor changing scientific data
   - Track hypothesis evolution
   - Link related findings across time

4. **Real-Time Monitoring**
   - Build temporal graphs from system logs
   - Track configuration changes
   - Identify patterns in event sequences

---

## Core Concepts

### Episodes: The Building Blocks

Episodes are the primary units of information in Graphiti. Each episode represents:
- A piece of text (conversation, document, note)
- Structured data (JSON, database records)
- An event with temporal context

```python
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

# Text Episode
await graphiti.add_episode(
    name="Customer Call",
    episode_body="John Smith called about billing issues with account #1234",
    source=EpisodeType.text,
    reference_time=datetime(2024, 1, 15, 10, 30)
)

# JSON Episode
await graphiti.add_episode(
    name="Account Update",
    episode_body=json.dumps({
        "account_id": "1234",
        "status": "resolved",
        "resolution": "Billing error corrected"
    }),
    source=EpisodeType.json,
    reference_time=datetime(2024, 1, 15, 14, 0)
)
```

### Nodes: Entities in the Graph

Nodes represent entities extracted from episodes:
- **EntityNode**: People, places, concepts, etc.
- **EpisodicNode**: The episode itself as a node
- **CommunityNode**: Clusters of related entities

Each node contains:
```python
{
    "uuid": "unique-identifier",
    "name": "John Smith",
    "labels": ["Person", "Customer"],
    "summary": "Customer with account #1234, experienced billing issues",
    "created_at": "2024-01-15T10:30:00Z",
    "attributes": {
        "account_id": "1234",
        "priority": "high"
    }
}
```

### Edges: Relationships with History

Edges connect nodes and carry temporal metadata:
- **EntityEdge**: Relationships between entities
- **EpisodicEdge**: Links episodes to entities
- **CommunityEdge**: Connects entities to communities

Edge structure:
```python
{
    "uuid": "edge-uuid",
    "source_node_uuid": "john-uuid",
    "target_node_uuid": "account-uuid",
    "fact": "John Smith owns account #1234",
    "valid_at": "2024-01-01T00:00:00Z",
    "invalid_at": null,  # Still valid
    "created_at": "2024-01-15T10:30:00Z"
}
```

### Custom Entity Types

Define domain-specific entities using Pydantic models:

```python
from pydantic import BaseModel, Field

class Customer(BaseModel):
    """A customer entity with business-specific attributes"""
    first_name: str = Field(..., description="Customer's first name")
    last_name: str = Field(..., description="Customer's last name")
    account_id: str = Field(..., description="Unique account identifier")
    subscription_tier: str = Field(..., description="Service level")

class Product(BaseModel):
    """A product in the catalog"""
    sku: str = Field(..., description="Stock keeping unit")
    name: str = Field(..., description="Product name")
    category: str = Field(..., description="Product category")
    price: float = Field(..., description="Current price")

# Register with Graphiti
graphiti.register_entity_type(Customer)
graphiti.register_entity_type(Product)
```

### Groups and Namespaces

Organize data into logical groups:
```python
# Create isolated graphs for different contexts
user_session_1 = "session-123"
user_session_2 = "session-456"

# Add episodes to specific groups
await graphiti.add_episode(
    name="User Query",
    episode_body="Show me my recent orders",
    group_id=user_session_1
)

# Search within a specific group
results = await graphiti.search(
    query="recent orders",
    group_ids=[user_session_1]
)
```

---

## Architecture Deep Dive

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Application Layer                      │
│  (Your AI Agent, Chatbot, or Application)                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                         Graphiti Core                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  Episode Processor                   │   │
│  │  • LLM extraction  • Entity resolution              │   │
│  │  • Relationship identification                      │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                   Search Engine                      │   │
│  │  • Hybrid retrieval  • Reranking                    │   │
│  │  • Graph traversal                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 Temporal Manager                     │   │
│  │  • Conflict resolution  • Validity tracking         │   │
│  │  • Historical queries                               │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                      Storage Layer                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │    Graph Database (Neo4j/FalkorDB/Neptune/Kuzu)     │   │
│  │  • Nodes and edges  • Indexes                       │   │
│  │  • Constraints      • Full-text search              │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Embedding Store                         │   │
│  │  • Vector indexes  • Semantic search                │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
```

### Episode Ingestion Pipeline

1. **Input Processing**
   ```python
   episode = {
       "content": "Alice promoted Bob to Senior Engineer",
       "timestamp": "2024-01-15T10:00:00Z"
   }
   ```

2. **LLM Extraction**
   - Entities: [Alice (Person), Bob (Person), Senior Engineer (Role)]
   - Relationships: [Alice PROMOTED Bob, Bob HAS_ROLE Senior Engineer]

3. **Entity Resolution**
   - Check if Alice/Bob already exist in graph
   - Merge or create new nodes as needed
   - Preserve entity attributes

4. **Temporal Processing**
   - Mark old relationships as invalid
   - Create new relationships with validity periods
   - Maintain audit trail

5. **Indexing**
   - Update vector embeddings
   - Refresh full-text indexes
   - Rebuild graph statistics

### Search Architecture

#### Hybrid Search Strategy

```python
# 1. Semantic Search (Vector Similarity)
semantic_results = embedding_search(
    query_embedding,
    similarity_threshold=0.7
)

# 2. Keyword Search (BM25)
keyword_results = fulltext_search(
    query_terms,
    boost_exact_matches=True
)

# 3. Graph Traversal
graph_results = traverse_relationships(
    start_nodes=semantic_results[:5],
    max_depth=2
)

# 4. Fusion and Reranking
final_results = reciprocal_rank_fusion(
    [semantic_results, keyword_results, graph_results],
    weights=[0.4, 0.3, 0.3]
)
```

#### Center Node Reranking

Focus search results around a specific entity:
```python
# Find information related to a specific person
center_node = get_node_by_name("Alice Johnson")
results = await graphiti.search(
    query="recent projects",
    center_node_uuid=center_node.uuid,
    max_distance=2  # Within 2 hops of Alice
)
```

### Performance Optimizations

1. **Parallel Processing**
   ```python
   # Set concurrency limit based on your LLM tier
   os.environ['SEMAPHORE_LIMIT'] = '50'
   
   # Graphiti automatically parallelizes:
   # - Entity extraction
   # - Embedding generation  
   # - Database writes
   ```

2. **Batch Operations**
   ```python
   # Bulk episode ingestion
   episodes = [episode1, episode2, ..., episode100]
   await graphiti.add_episodes_bulk(episodes)
   ```

3. **Lazy Loading**
   - Embeddings generated only when needed
   - Graph statistics cached and refreshed periodically
   - Incremental index updates

4. **Query Optimization**
   - Pre-computed graph projections
   - Materialized views for common patterns
   - Index hints for complex traversals

---

## Comparison with Traditional Approaches

### Graphiti vs. GraphRAG

| Aspect | GraphRAG | Graphiti |
|--------|----------|----------|
| **Architecture** | Batch-oriented, static clusters | Real-time, dynamic graph |
| **Update Model** | Full recomputation required | Incremental updates |
| **Query Latency** | 10-30+ seconds | <1 second (p95: 300ms) |
| **Temporal Support** | Basic timestamps | Full bi-temporal model |
| **Conflict Resolution** | LLM summarization | Temporal invalidation |
| **Memory Efficiency** | High token usage | 98% token reduction |
| **Custom Entities** | Not supported | Fully customizable |
| **Scale** | Moderate | High (parallel processing) |

### Graphiti vs. Vector Databases

| Aspect | Vector DB (Pinecone, Weaviate) | Graphiti |
|--------|--------------------------------|----------|
| **Data Model** | Flat documents with embeddings | Rich graph with relationships |
| **Relationships** | Not represented | First-class citizens |
| **Temporal Queries** | Not supported | Native support |
| **Search** | Semantic only | Hybrid (semantic + keyword + graph) |
| **Context** | Limited to k-nearest | Full graph context |
| **Updates** | Replace documents | Evolve relationships |

### Graphiti vs. Traditional Graph Databases

| Aspect | Neo4j/Neptune (alone) | Graphiti |
|--------|----------------------|----------|
| **Setup Complexity** | Manual schema design | Automatic extraction |
| **LLM Integration** | Custom implementation | Built-in |
| **Temporal Model** | Manual implementation | Native bi-temporal |
| **Search** | Cypher/Gremlin only | Hybrid with embeddings |
| **Entity Extraction** | Manual ETL | Automatic via LLM |
| **Conflict Resolution** | Custom logic | Built-in strategies |

### When to Choose Graphiti

✅ **Choose Graphiti when you need:**
- Real-time knowledge updates
- Temporal reasoning capabilities
- Complex relationship tracking
- Sub-second query performance
- Audit trails and historical queries
- Integration with AI agents

❌ **Consider alternatives when:**
- Data is truly static (e.g., historical archives)
- Simple keyword search suffices
- No relationship modeling needed
- Batch processing is acceptable
- Cost is the primary concern (Graphiti requires LLM calls)

---

## Next Steps

This document provides the foundational understanding of Graphiti. Continue to the following guides for deeper exploration:

1. **[02_technical_architecture.md](./02_technical_architecture.md)** - Detailed technical implementation
2. **[03_practical_implementation.md](./03_practical_implementation.md)** - Hands-on coding examples
3. **[04_advanced_features.md](./04_advanced_features.md)** - Custom entities, communities, and optimization
4. **[05_integration_patterns.md](./05_integration_patterns.md)** - Building agents with Graphiti
5. **[06_performance_tuning.md](./06_performance_tuning.md)** - Optimization and scaling strategies
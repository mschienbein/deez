# Comprehensive Glossary of AI Engineering, Embedding, and Graph Terms

## Table of Contents
- [AI/ML Fundamentals](#aiml-fundamentals)
- [Embeddings and Vector Operations](#embeddings-and-vector-operations)
- [Graph Database Concepts](#graph-database-concepts)
- [Natural Language Processing (NLP)](#natural-language-processing-nlp)
- [Retrieval and Search](#retrieval-and-search)
- [LLM and Generation](#llm-and-generation)
- [Temporal and State Management](#temporal-and-state-management)
- [System Architecture](#system-architecture)
- [Performance and Optimization](#performance-and-optimization)

---

## AI/ML Fundamentals

### **Agent**
An autonomous software entity that can perceive its environment, make decisions, and take actions to achieve specific goals. In AI context, agents use LLMs or other models to reason about tasks and execute them. Modern agents maintain memory (like Graphiti), use tools, and can operate independently over extended periods.

**Example**: A customer support agent that reads emails, searches documentation, and responds to queries without human intervention.

### **Few-Shot Learning**
A machine learning technique where a model learns to perform a task from only a few examples (typically 2-10). This is contrasted with zero-shot (no examples) and many-shot learning (hundreds or thousands of examples).

**In Practice**: When extracting entities with Graphiti, you might provide 3 examples of how to identify a "Person" entity, and the LLM learns the pattern from just those examples.

### **Inference**
The process of using a trained model to make predictions on new, unseen data. This is the "runtime" phase where the model applies what it learned during training.

**Context**: When Graphiti sends text to an LLM to extract entities, that's inference - the model is applying its training to new text.

### **Fine-tuning**
The process of taking a pre-trained model and training it further on a specific dataset to specialize it for a particular task or domain. This is different from training from scratch.

**Example**: Taking GPT-4 and fine-tuning it on medical literature to create a specialized medical assistant.

### **Hallucination**
When an AI model generates information that is plausible-sounding but factually incorrect or not present in its training data. This is a major challenge in LLMs.

**Mitigation in Graphiti**: Uses structured output and validation to reduce hallucinations during entity extraction.

### **Supervised vs Unsupervised Learning**
- **Supervised**: Learning from labeled data where correct answers are provided
- **Unsupervised**: Finding patterns in unlabeled data without explicit correct answers

**Relevance**: Community detection in Graphiti uses unsupervised learning to find clusters of related entities.

---

## Embeddings and Vector Operations

### **Embedding**
A dense numerical representation of data (usually text) in a high-dimensional vector space where similar items are close together. Embeddings capture semantic meaning in a format computers can process efficiently.

**Technical Details**: 
- Text "dog" might become a 1536-dimensional vector like [0.012, -0.34, 0.67, ...]
- Similar words like "puppy" would have similar vectors
- Typical dimensions: 384 (small), 768 (medium), 1536 (large), 3072 (very large)

### **Vector Database**
A specialized database optimized for storing and searching high-dimensional vectors (embeddings). Uses specialized indexes like HNSW or IVF for efficient similarity search.

**Examples**: Pinecone, Weaviate, Qdrant, Milvus, or vector indexes in Neo4j

### **Cosine Similarity**
A measure of similarity between two vectors based on the cosine of the angle between them. Ranges from -1 (opposite) to 1 (identical), with 0 meaning orthogonal (unrelated).

**Formula**: `similarity = (A·B) / (||A|| × ||B||)`

**Usage**: Graphiti uses cosine similarity to find semantically similar facts in the knowledge graph.

### **Euclidean Distance**
The straight-line distance between two points in vector space. Unlike cosine similarity, it considers magnitude.

**When to Use**: Better for embeddings where magnitude matters (e.g., intensity or strength of a feature).

### **Dimension Reduction**
Techniques to reduce the number of dimensions in embeddings while preserving important information. Common methods include PCA, t-SNE, and UMAP.

**Purpose**: Visualization (reducing to 2-3D), storage optimization, or noise reduction.

### **Embedding Model**
A neural network specifically trained to convert input (text, images, etc.) into embeddings. Different models optimize for different qualities.

**Examples**:
- **OpenAI text-embedding-3**: General purpose, high quality
- **Voyage-2**: Optimized for retrieval tasks
- **BGE**: Open-source, multilingual support
- **Sentence-BERT**: Fast, good for sentence similarity

### **Quantization**
Reducing the precision of embeddings (e.g., from float32 to int8) to save storage and improve speed, with minimal loss in accuracy.

**Trade-off**: 4x storage reduction for ~2% accuracy loss typically.

---

## Graph Database Concepts

### **Node (Vertex)**
A fundamental unit in a graph representing an entity. In knowledge graphs, nodes typically represent people, places, concepts, or events.

**In Graphiti**: 
```python
{
    "uuid": "unique-id",
    "name": "Alice Johnson",
    "labels": ["Person", "Employee"],
    "properties": {"age": 30, "department": "Engineering"}
}
```

### **Edge (Relationship)**
A connection between two nodes that represents how they relate. Edges can be directed (one-way) or undirected (bidirectional).

**In Graphiti**:
```python
{
    "source": "Alice",
    "relationship": "MANAGES",
    "target": "Bob",
    "properties": {"since": "2023-01-01"}
}
```

### **Property Graph**
A graph model where both nodes and edges can have properties (key-value pairs). Neo4j uses this model.

**Contrast with**: RDF graphs (triple stores) which use subject-predicate-object without properties.

### **Cypher Query Language**
Neo4j's declarative query language for pattern matching in graphs. Similar to SQL but designed for graph traversal.

**Example**:
```cypher
MATCH (p:Person)-[:WORKS_FOR]->(c:Company)
WHERE c.name = "TechCorp"
RETURN p.name, p.role
```

### **Graph Traversal**
The process of exploring a graph by following edges from node to node. Can be depth-first (DFS) or breadth-first (BFS).

**Application**: Finding all employees within 2 reporting levels of a CEO.

### **Degree Centrality**
The number of edges connected to a node. In directed graphs, there's in-degree (incoming) and out-degree (outgoing).

**Significance**: High-degree nodes are often important hubs in the network.

### **Betweenness Centrality**
Measures how often a node appears on shortest paths between other nodes. High betweenness indicates a node is a "bridge" in the network.

**Use Case**: Identifying key connectors or potential bottlenecks in information flow.

### **Community Detection**
Algorithms that identify clusters of densely connected nodes. Common algorithms include:
- **Louvain**: Fast, good for large graphs
- **Label Propagation**: Simple, scalable
- **Girvan-Newman**: Accurate but slower

**In Graphiti**: Automatically groups related entities for better context.

### **Subgraph**
A portion of a graph containing a subset of nodes and edges. Can be induced (all edges between selected nodes) or not.

### **Knowledge Graph**
A graph representation of real-world entities and their relationships, often enriched with semantic meaning and used for reasoning.

**Components**: Entities (nodes), relationships (edges), and often an ontology defining valid types and rules.

### **Triple Store**
A database designed to store and retrieve RDF triples (subject-predicate-object). Different from property graphs.

**Examples**: Apache Jena, Blazegraph, Amazon Neptune (supports both models).

---

## Natural Language Processing (NLP)

### **Tokenization**
Breaking text into smaller units (tokens) that can be processed. Tokens can be words, subwords, or characters.

**Example**: 
- Word: "Hello world" → ["Hello", "world"]
- Subword: "unhappy" → ["un", "happy"]
- BPE: "running" → ["run", "ning"]

### **Token Limit**
Maximum number of tokens a model can process in one request. Includes both input and output.

**Common Limits**:
- GPT-4: 128k tokens
- Claude: 200k tokens
- Most open models: 4k-32k tokens

### **Context Window**
The amount of text an LLM can "see" and consider when generating responses. Measured in tokens.

**Challenge**: Long documents must be chunked to fit within context windows.

### **Named Entity Recognition (NER)**
Identifying and classifying named entities (people, organizations, locations, etc.) in text.

**In Graphiti**: Core function for extracting nodes from unstructured text.

### **Relationship Extraction**
Identifying and classifying relationships between entities in text. More complex than NER as it requires understanding connections.

**Example**: From "Microsoft acquired GitHub in 2018" extract: Microsoft --[ACQUIRED]--> GitHub

### **Coreference Resolution**
Determining when different words refer to the same entity. Critical for accurate knowledge extraction.

**Example**: "John went to the store. He bought milk." - Understanding "He" refers to "John".

### **Lemmatization**
Reducing words to their base or dictionary form (lemma). More sophisticated than stemming.

**Examples**: 
- "running", "ran", "runs" → "run"
- "better" → "good"
- "was" → "be"

### **Stop Words**
Common words often filtered out in text processing because they carry little semantic meaning.

**Examples**: "the", "is", "at", "which", "on"

**Note**: Modern embeddings often keep stop words as they can affect meaning.

---

## Retrieval and Search

### **RAG (Retrieval-Augmented Generation)**
A technique combining information retrieval with text generation. The system retrieves relevant documents and uses them as context for generating responses.

**Traditional RAG Pipeline**:
1. Query → Embedding
2. Search vector database
3. Retrieve top-k documents
4. Insert into LLM prompt
5. Generate response

**Graphiti Improvement**: Replaces static document retrieval with dynamic knowledge graph queries.

### **Semantic Search**
Search based on meaning rather than exact keyword matches. Uses embeddings to find conceptually similar content.

**Example**: Searching for "car" might also find documents about "automobile", "vehicle", or "Tesla".

### **BM25 (Best Matching 25)**
A probabilistic ranking function used for keyword-based search. Considers term frequency and document length.

**Formula Components**:
- TF (term frequency): How often the term appears
- IDF (inverse document frequency): How rare the term is
- Document length normalization

**When It's Better**: Exact term matching, rare technical terms, ID lookups.

### **Hybrid Search**
Combining multiple search methods (typically semantic + keyword) for better results.

**Graphiti's Approach**:
1. Semantic search (embedding similarity)
2. BM25 keyword search
3. Graph traversal
4. Fusion and reranking

### **Reciprocal Rank Fusion (RRF)**
A method for combining rankings from multiple search methods. Robust and parameter-free.

**Formula**: `RRF_score(d) = Σ(1 / (k + rank(d)))` where k is typically 60.

### **Cross-Encoder Reranking**
Using a specialized model to score query-document pairs for relevance. More accurate but slower than bi-encoders.

**Process**:
1. Initial retrieval gets top-100 candidates
2. Cross-encoder scores each candidate
3. Re-sort by cross-encoder scores
4. Return top-k

**Trade-off**: 10x slower but 20-30% more accurate typically.

### **Dense vs Sparse Retrieval**
- **Dense**: Using embeddings (continuous vectors)
- **Sparse**: Using term-based methods like BM25 (sparse vectors with mostly zeros)

**Best Practice**: Combine both (hybrid) for optimal results.

### **k-Nearest Neighbors (k-NN)**
Finding the k most similar items to a query in vector space. Foundation of semantic search.

**Approximate versions** (ANN): Trade small accuracy loss for huge speed gains.

### **HNSW (Hierarchical Navigable Small World)**
An algorithm for approximate nearest neighbor search. Very fast and accurate.

**How it Works**: Builds a multi-layer graph where each layer is a "small world" network, enabling logarithmic search time.

---

## LLM and Generation

### **Large Language Model (LLM)**
Neural networks with billions of parameters trained on vast text corpora to understand and generate human-like text.

**Scales**:
- Small: <1B parameters (runs on phone)
- Medium: 1-10B (runs on laptop)
- Large: 10-100B (needs GPU)
- Very Large: >100B (needs multiple GPUs)

### **Structured Output**
Constraining LLM output to follow a specific schema or format, typically JSON. Prevents formatting errors and ensures parseability.

**In Graphiti**: Used for reliable entity and relationship extraction.

**Methods**:
- Grammar constraints (GBNF)
- JSON schema validation
- Function calling
- Guided generation

### **Temperature**
A parameter controlling randomness in generation. 0 = deterministic, 1 = balanced, 2 = very random.

**Use Cases**:
- 0: Extraction, classification
- 0.7: General conversation
- 1+: Creative writing

### **Top-k and Top-p Sampling**
Methods for selecting the next token during generation:
- **Top-k**: Consider only k most likely tokens
- **Top-p (nucleus)**: Consider tokens until cumulative probability exceeds p

**Example**: Top-p=0.9 means consider tokens that together have 90% probability.

### **Prompt Engineering**
The practice of designing effective prompts to get desired outputs from LLMs.

**Techniques**:
- Zero-shot: Direct instruction
- Few-shot: Provide examples
- Chain-of-thought: Step-by-step reasoning
- System prompts: Set behavior/role

### **Context Injection**
Inserting relevant information into a prompt to ground the LLM's response in facts.

**Graphiti's Approach**: Injects graph search results as context for accurate responses.

### **Token Probability/Logits**
The raw scores (logits) or probabilities assigned to each possible next token. Used for:
- Confidence estimation
- Constrained generation
- Debugging

### **Beam Search**
A search algorithm that explores multiple generation paths simultaneously, keeping the k best partial sequences at each step.

**Trade-off**: Better quality but slower than greedy decoding.

---

## Temporal and State Management

### **Bi-Temporal Model**
Tracking two time dimensions for each fact:
1. **Valid Time**: When the fact was true in the real world
2. **Transaction Time**: When the fact was recorded in the system

**Example**: "Bob was CEO from 2020-2023" (valid time) recorded on "2024-01-15" (transaction time).

### **Temporal Validity**
The time period during which a fact is considered true.

**In Graphiti**:
```python
{
    "valid_at": "2020-01-01",  # Start of validity
    "invalid_at": "2023-12-31"  # End of validity (null if still valid)
}
```

### **Point-in-Time Query**
Retrieving the state of the graph as it was at a specific moment in history.

**Use Case**: "What was the org structure on June 1, 2023?"

### **Temporal Conflict Resolution**
Handling contradictory facts with overlapping validity periods.

**Strategies**:
- Last-write-wins
- Highest confidence
- Source authority ranking
- Manual resolution

### **Event Sourcing**
Storing all changes as a sequence of events rather than just current state. Enables full history reconstruction.

**Benefit**: Complete audit trail and ability to replay history.

### **Snapshot**
A complete copy of state at a specific point in time. Used for:
- Backup/recovery
- Historical analysis
- Performance optimization

### **Tombstone**
A marker indicating that data has been deleted but preserving the deletion record for history.

**In Temporal Graphs**: Marks when facts become invalid rather than deleting them.

---

## System Architecture

### **Microservices**
Architecture pattern where applications are built as a suite of small, independent services.

**Graphiti Context**: Can run as a microservice providing knowledge graph capabilities to other services.

### **Event-Driven Architecture**
System design where components communicate through events rather than direct calls.

**Application**: Episodes in Graphiti can be triggered by events from other systems.

### **Asyncio/Asynchronous Programming**
Programming paradigm allowing concurrent execution without threads. Uses async/await syntax in Python.

**Why It Matters**: Graphiti uses async for parallel processing of embeddings and LLM calls.

### **Semaphore**
A synchronization primitive that limits the number of concurrent operations.

**In Graphiti**: `SEMAPHORE_LIMIT` controls parallel LLM calls to avoid rate limits.

### **Circuit Breaker Pattern**
Prevents cascading failures by stopping calls to a failing service after a threshold.

**States**: Closed (normal), Open (failing), Half-Open (testing recovery).

### **Message Queue**
System for asynchronous communication between services. Messages are stored until processed.

**Examples**: RabbitMQ, Kafka, AWS SQS.

**Use Case**: Queue episodes for batch processing in Graphiti.

### **CDC (Change Data Capture)**
Technique for identifying and capturing changes in a database to trigger downstream processing.

**Application**: Automatically update Graphiti when source databases change.

### **ETL vs ELT**
- **ETL**: Extract, Transform, Load - transform before storing
- **ELT**: Extract, Load, Transform - transform after storing

**Graphiti**: More like ETL - extracts and transforms text into graph structure before storing.

---

## Performance and Optimization

### **Latency**
Time delay between request and response. Different types:
- **P50**: Median latency (50th percentile)
- **P95**: 95th percentile (95% of requests are faster)
- **P99**: 99th percentile (worst-case for most users)

**Graphiti Target**: P95 < 300ms for search queries.

### **Throughput**
Number of operations processed per unit time (requests/second, episodes/hour).

**Factors**: Model size, batch size, parallelism, hardware.

### **Batch Processing**
Processing multiple items together rather than individually.

**Benefits**: 
- Amortized overhead
- Better GPU utilization
- Fewer API calls

**In Graphiti**: `add_episodes_bulk()` for batch ingestion.

### **Caching**
Storing frequently accessed data in fast storage to reduce computation or retrieval time.

**Levels**:
- Application cache (in-memory)
- Redis/Memcached (distributed)
- CDN (geographic)

### **Index**
Data structure that improves the speed of data retrieval operations.

**Types in Graph Databases**:
- B-tree: Range queries
- Hash: Exact match
- Full-text: Text search
- Vector: Similarity search
- Composite: Multiple properties

### **Sharding**
Distributing data across multiple machines for scalability.

**Strategies**:
- Hash-based: Distribute by hash of key
- Range-based: Distribute by value ranges
- Geographic: Distribute by location

### **Lazy Loading**
Deferring initialization or computation until actually needed.

**Example**: Computing embeddings only when search is performed, not during ingestion.

### **Connection Pooling**
Reusing database connections rather than creating new ones for each request.

**Benefits**: Reduces connection overhead, improves response time.

### **Backpressure**
Mechanism to prevent overwhelming a system by slowing down input when processing can't keep up.

**Implementation**: Queue limits, rate limiting, flow control.

### **Denormalization**
Storing redundant data to reduce the need for expensive joins or traversals.

**Trade-off**: More storage for better read performance.

### **Materialized View**
Pre-computed query results stored for fast retrieval.

**In Graphs**: Pre-computed communities, aggregations, or common traversal patterns.

---

## Additional Important Terms

### **ACID Properties**
Database transaction guarantees:
- **Atomicity**: All or nothing
- **Consistency**: Valid state transitions
- **Isolation**: Concurrent transaction separation
- **Durability**: Committed data persists

### **BASE Properties**
Alternative to ACID for distributed systems:
- **Basically Available**: System remains operational
- **Soft state**: State may change over time
- **Eventual consistency**: Consistency achieved eventually

### **CAP Theorem**
States that distributed systems can only guarantee 2 of:
- **Consistency**: All nodes see same data
- **Availability**: System remains operational
- **Partition tolerance**: Continues despite network failures

### **Idempotency**
Property where an operation can be applied multiple times without changing the result beyond the initial application.

**Important for**: Retry logic, distributed systems.

### **Schema-on-Read vs Schema-on-Write**
- **Schema-on-Write**: Enforce structure when storing (traditional databases)
- **Schema-on-Read**: Apply structure when querying (data lakes)

**Graphiti**: Hybrid - extracts structure during ingestion but flexible schema.

### **Precision and Recall**
Metrics for evaluating retrieval systems:
- **Precision**: Of retrieved items, how many are relevant?
- **Recall**: Of relevant items, how many were retrieved?

**F1 Score**: Harmonic mean of precision and recall.

### **UMAP (Uniform Manifold Approximation and Projection)**
Dimension reduction technique that preserves both local and global structure. Often used to visualize embeddings.

### **Attention Mechanism**
Neural network component that allows models to focus on relevant parts of input. Foundation of transformers and modern LLMs.

### **Transformer Architecture**
Neural network architecture using self-attention. Basis for GPT, BERT, and most modern LLMs.

**Key Innovation**: Processes all positions in parallel rather than sequentially.

### **Zero-Shot vs Few-Shot vs Fine-Tuning**
- **Zero-Shot**: Use model without examples
- **Few-Shot**: Provide a few examples in prompt
- **Fine-Tuning**: Retrain model on specific data

**Graphiti Default**: Few-shot extraction with examples in prompts.

### **Chunking**
Breaking large documents into smaller pieces for processing.

**Strategies**:
- Fixed size (e.g., 512 tokens)
- Semantic (paragraph/section boundaries)
- Sliding window (overlapping chunks)

### **GraphRAG**
Microsoft's approach using LLM-generated summaries of graph communities. Batch-oriented and expensive.

**Graphiti Advantage**: Real-time updates without regenerating summaries.

### **FAISS (Facebook AI Similarity Search)**
Library for efficient similarity search and clustering of dense vectors.

**Alternative to**: Purpose-built vector databases.

### **Pydantic**
Python library for data validation using Python type annotations. Used in Graphiti for defining entity schemas.

### **MCP (Model Context Protocol)**
Open protocol for connecting AI assistants to external data sources and tools.

**Graphiti Integration**: MCP server provides knowledge graph access to AI assistants.

---

## Acronyms Quick Reference

- **API**: Application Programming Interface
- **BERT**: Bidirectional Encoder Representations from Transformers
- **CRUD**: Create, Read, Update, Delete
- **DFS/BFS**: Depth-First Search / Breadth-First Search
- **DL**: Deep Learning
- **ETL**: Extract, Transform, Load
- **GPU**: Graphics Processing Unit
- **HNSW**: Hierarchical Navigable Small World
- **IDF**: Inverse Document Frequency
- **JSON**: JavaScript Object Notation
- **KG**: Knowledge Graph
- **KV**: Key-Value
- **LLM**: Large Language Model
- **ML**: Machine Learning
- **NER**: Named Entity Recognition
- **NLP**: Natural Language Processing
- **ORM**: Object-Relational Mapping
- **PCA**: Principal Component Analysis
- **RAG**: Retrieval-Augmented Generation
- **RDF**: Resource Description Framework
- **REST**: Representational State Transfer
- **RL**: Reinforcement Learning
- **RPC**: Remote Procedure Call
- **SLA**: Service Level Agreement
- **SPARQL**: SPARQL Protocol and RDF Query Language
- **SQL**: Structured Query Language
- **TF**: Term Frequency
- **TF-IDF**: Term Frequency-Inverse Document Frequency
- **TPU**: Tensor Processing Unit
- **t-SNE**: t-Distributed Stochastic Neighbor Embedding
- **UUID**: Universally Unique Identifier
- **WebSocket**: Protocol for persistent connections

---

This glossary should help fill in knowledge gaps as you explore Graphiti and modern AI engineering. Each term includes practical context for how it relates to knowledge graphs and agent systems.
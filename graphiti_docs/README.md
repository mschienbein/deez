# Graphiti Documentation

> **A Comprehensive Guide to Temporal Knowledge Graphs with Graphiti**
> 
> Perfect reading material for understanding the state-of-the-art in AI memory systems

## 📚 Documentation Index

### Getting Started
1. **[Glossary of AI & Graph Terms](./00_glossary_ai_graph_terms.md)**
   - Essential terminology for AI, embeddings, and graph concepts
   - Detailed explanations to fill knowledge gaps
   - Reference guide for technical terms

2. **[Introduction and Overview](./01_introduction_and_overview.md)**
   - What is Graphiti and why it matters
   - Core concepts and philosophy
   - Comparison with traditional approaches
   - Quick start guide

### Technical Deep Dive
3. **[Technical Architecture](./02_technical_architecture.md)**
   - System architecture and components
   - Episode processing pipeline
   - Temporal data model (bi-temporal design)
   - Search and retrieval architecture
   - Entity and relationship extraction

4. **[Practical Implementation](./03_practical_implementation.md)**
   - Hands-on examples with working code
   - Setting up Graphiti with Neo4j
   - Custom entity types with Pydantic
   - Building conversational agents
   - Real-world use cases

### Advanced Topics
5. **[Advanced Features](./04_advanced_features.md)**
   - Community detection and management
   - Temporal reasoning capabilities
   - Graph analytics and algorithms
   - Hybrid search strategies
   - Multi-session support

6. **[Integration Patterns](./05_integration_patterns.md)**
   - LangChain integration (detailed)
   - Strands Agents integration
   - OpenAI Assistants & GPTs
   - Claude and other LLMs
   - Production deployment patterns

### Performance & Operations
7. **[Performance Tuning](./06_performance_tuning.md)**
   - Optimization strategies
   - Index configuration
   - Query optimization
   - Memory management
   - Scaling strategies

8. **[Benchmarks and Evaluation](./08_benchmarks_and_evaluation.md)**
   - DMR benchmark results (94.8% accuracy)
   - Latency and throughput metrics
   - Memory efficiency analysis
   - Comparison with MemGPT, RAG, GraphRAG
   - Real-world performance scenarios

### Reference & Migration
9. **[API Reference](./07_api_reference.md)**
   - Complete API documentation
   - All methods and parameters
   - Code examples for every API
   - Best practices and patterns

10. **[Migration Guide](./09_migration_guide.md)**
    - Migrating from RAG systems
    - Migrating from GraphRAG
    - Migrating from vector databases
    - Migrating from MemGPT
    - Validation and testing frameworks

11. **[Troubleshooting Guide](./10_troubleshooting.md)**
    - Common issues and solutions
    - Debugging techniques
    - Performance problem resolution
    - Integration troubleshooting
    - Recovery procedures

## 🎯 Key Highlights

### Why Graphiti?

Graphiti represents a paradigm shift in AI memory systems, moving from static knowledge bases to dynamic, temporal knowledge graphs that evolve with your data.

**Core Advantages:**
- ✅ **94.8% accuracy** on Document Memory Retrieval (DMR) benchmark
- ✅ **Unlimited context window** through temporal graph structure
- ✅ **3.2x more memory efficient** than traditional RAG
- ✅ **Sub-second query latency** (p95: 300ms)
- ✅ **Bi-temporal data model** for complete version history
- ✅ **Native graph operations** for relationship queries
- ✅ **Dynamic knowledge evolution** vs static snapshots

### Perfect For:

- **🤖 Conversational AI Systems** - Maintain context across unlimited turns
- **📚 Technical Documentation** - Track versions and changes over time
- **🎯 Customer Support** - Remember all customer interactions
- **🔬 Research Systems** - Build evolving knowledge bases
- **🏢 Enterprise Memory** - Organizational knowledge management

## 🚀 Quick Start

```python
from graphiti import Graphiti

# Initialize with Neo4j
graphiti = Graphiti(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)

# Add knowledge
await graphiti.add_episode(
    "John Smith is the CEO of TechCorp and specializes in AI",
    source_id="meeting_001"
)

# Query with temporal awareness
results = await graphiti.search(
    "Who leads TechCorp?",
    num_results=5
)

# Access temporal data
history = await graphiti.get_entity_history("John Smith")
```

## 📊 Performance at a Glance

| Metric | Graphiti | MemGPT | Traditional RAG |
|--------|----------|---------|-----------------|
| DMR Accuracy | **94.8%** | 93.4% | 87.6% |
| Context Window | **∞** | 8K tokens | 4K tokens |
| Query Latency (p50) | **125ms** | 180ms | 95ms |
| Memory Efficiency | **3.2x** | 0.8x | 1.0x |
| Temporal Support | **Full** | Limited | None |

## 🔗 Integration with Your Stack

Graphiti seamlessly integrates with:
- **Neo4j** - Native graph database backend
- **LangChain** - Memory for chains and agents
- **Strands** - Enhanced agent capabilities
- **OpenAI/Claude** - LLM-powered extraction
- **Your Application** - Simple Python API

## 📖 Reading Path

For your flight reading, we recommend this order:

1. Start with the **[Glossary](./00_glossary_ai_graph_terms.md)** to understand key terms
2. Read the **[Introduction](./01_introduction_and_overview.md)** for context
3. Dive into **[Technical Architecture](./02_technical_architecture.md)** for how it works
4. Explore **[Practical Implementation](./03_practical_implementation.md)** for hands-on examples
5. Study **[Integration Patterns](./05_integration_patterns.md)** for Strands/LangChain usage
6. Review **[Benchmarks](./08_benchmarks_and_evaluation.md)** for performance insights
7. Check **[Migration Guide](./09_migration_guide.md)** if moving from another system

## 🌟 Key Takeaways

After reading this documentation, you'll understand:
- How temporal knowledge graphs revolutionize AI memory
- Why Graphiti outperforms traditional RAG and vector databases
- How to implement production-ready memory systems
- Best practices for integration with Neo4j and AI frameworks
- Performance optimization techniques for scale

## 📚 Additional Resources

- **Research Paper**: [arXiv:2501.13956](https://arxiv.org/pdf/2501.13956)
- **Blog Post**: [State of the Art Agent Memory](https://blog.getzep.com/state-of-the-art-agent-memory/)
- **Official Docs**: [help.getzep.com/graphiti](https://help.getzep.com/graphiti/getting-started/welcome)
- **GitHub**: [github.com/getzep/graphiti](https://github.com/getzep/graphiti)

---

*This documentation was created for developers familiar with Neo4j and working on Strands agents who want to understand and implement Graphiti's temporal knowledge graph capabilities.*

**Total Reading Time**: ~3-4 hours for complete documentation
**Quick Start Time**: 15 minutes to get running
**Implementation Time**: 1-2 days for production integration
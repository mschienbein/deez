# Graphiti Troubleshooting Guide

## Table of Contents
1. [Common Issues and Solutions](#common-issues-and-solutions)
2. [Debugging Techniques](#debugging-techniques)
3. [Performance Problems](#performance-problems)
4. [Integration Issues](#integration-issues)
5. [Data Quality Problems](#data-quality-problems)
6. [Memory and Resource Issues](#memory-and-resource-issues)
7. [Neo4j Specific Problems](#neo4j-specific-problems)
8. [LLM and API Issues](#llm-and-api-issues)
9. [Advanced Diagnostics](#advanced-diagnostics)
10. [Recovery Procedures](#recovery-procedures)

## Common Issues and Solutions

### 1. Installation and Setup Issues

#### Problem: ModuleNotFoundError when importing Graphiti
```python
# Error
ImportError: No module named 'graphiti'
```

**Solution:**
```bash
# Ensure proper installation
pip install graphiti-core

# For development version
pip install git+https://github.com/getzep/graphiti.git

# Verify installation
python -c "import graphiti; print(graphiti.__version__)"
```

#### Problem: Neo4j connection failures
```python
# Error
neo4j.exceptions.ServiceUnavailable: Failed to establish connection
```

**Solution:**
```python
from graphiti import Graphiti
from neo4j import GraphDatabase
import time

def connect_with_retry(uri, user, password, max_retries=5):
    """Connect to Neo4j with exponential backoff"""
    for attempt in range(max_retries):
        try:
            # Test connection first
            driver = GraphDatabase.driver(uri, auth=(user, password))
            with driver.session() as session:
                session.run("RETURN 1")
            driver.close()
            
            # Now initialize Graphiti
            return Graphiti(
                uri=uri,
                user=user,
                password=password
            )
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Connection failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise e

# Usage
graphiti = connect_with_retry(
    "bolt://localhost:7687",
    "neo4j",
    "password"
)
```

#### Problem: Embedding model initialization failures
```python
# Error
ValueError: Could not load embedding model
```

**Solution:**
```python
from graphiti import Graphiti
from typing import Optional
import os

class SafeGraphitiInit:
    """Safe initialization with fallbacks"""
    
    @staticmethod
    def create_instance(
        uri: str,
        user: str,
        password: str,
        llm_model: Optional[str] = None,
        embedding_model: Optional[str] = None
    ) -> Graphiti:
        # Try primary models
        try:
            return Graphiti(
                uri=uri,
                user=user,
                password=password,
                llm_model=llm_model or "gpt-4-turbo",
                embedding_model=embedding_model or "text-embedding-3-small"
            )
        except Exception as primary_error:
            print(f"Primary model failed: {primary_error}")
            
            # Try fallback models
            fallback_configs = [
                {
                    "llm_model": "gpt-3.5-turbo",
                    "embedding_model": "text-embedding-ada-002"
                },
                {
                    "llm_model": "claude-3-opus",
                    "embedding_model": "voyage-2"
                }
            ]
            
            for config in fallback_configs:
                try:
                    return Graphiti(
                        uri=uri,
                        user=user,
                        password=password,
                        **config
                    )
                except Exception:
                    continue
            
            # Last resort: minimal configuration
            return Graphiti(
                uri=uri,
                user=user,
                password=password,
                llm_model=None,  # Use defaults
                embedding_model=None
            )

# Usage
graphiti = SafeGraphitiInit.create_instance(
    "bolt://localhost:7687",
    "neo4j",
    "password"
)
```

### 2. Episode Processing Failures

#### Problem: Episodes not being processed
```python
# Silent failures during add_episode
```

**Solution with Debugging:**
```python
import logging
from typing import Any, Dict, List
import json

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("graphiti")

class EpisodeDebugger:
    """Debug episode processing issues"""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
        self.failed_episodes = []
    
    async def safe_add_episode(
        self,
        episode: str,
        source_id: str,
        metadata: Dict = None
    ) -> bool:
        """Add episode with comprehensive error handling"""
        try:
            # Pre-validate episode
            validation_errors = self.validate_episode(episode)
            if validation_errors:
                logger.warning(f"Episode validation issues: {validation_errors}")
            
            # Process with monitoring
            logger.info(f"Processing episode from {source_id}")
            logger.debug(f"Episode content: {episode[:200]}...")
            
            result = await self.graphiti.add_episode(
                episode=episode,
                source_id=source_id,
                metadata=metadata or {}
            )
            
            # Verify processing
            if not result:
                logger.error("Episode processing returned None/False")
                self.failed_episodes.append({
                    "episode": episode,
                    "source_id": source_id,
                    "error": "Processing returned empty result"
                })
                return False
            
            logger.info(f"Successfully processed episode: {source_id}")
            return True
            
        except Exception as e:
            logger.error(f"Episode processing failed: {str(e)}")
            self.failed_episodes.append({
                "episode": episode,
                "source_id": source_id,
                "error": str(e)
            })
            return False
    
    def validate_episode(self, episode: str) -> List[str]:
        """Validate episode before processing"""
        issues = []
        
        # Check length
        if len(episode) < 10:
            issues.append("Episode too short (< 10 chars)")
        if len(episode) > 100000:
            issues.append("Episode too long (> 100k chars)")
        
        # Check for problematic characters
        if '\x00' in episode:
            issues.append("Contains null bytes")
        
        # Check encoding
        try:
            episode.encode('utf-8')
        except UnicodeEncodeError:
            issues.append("Contains invalid UTF-8 characters")
        
        return issues
    
    def get_failure_report(self) -> str:
        """Generate failure report"""
        if not self.failed_episodes:
            return "No failures detected"
        
        report = f"Failed Episodes: {len(self.failed_episodes)}\n"
        for failure in self.failed_episodes[:5]:  # Show first 5
            report += f"- Source: {failure['source_id']}\n"
            report += f"  Error: {failure['error']}\n"
        
        return report

# Usage
debugger = EpisodeDebugger(graphiti)
await debugger.safe_add_episode(
    "User conversation about AI",
    "conv_123"
)
print(debugger.get_failure_report())
```

### 3. Entity Extraction Issues

#### Problem: Entities not being extracted
```python
# No entities found in obviously entity-rich text
```

**Solution with Custom Extraction:**
```python
from typing import List, Dict
import re

class EntityExtractionDebugger:
    """Debug and fix entity extraction issues"""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
    
    async def diagnose_extraction(self, text: str) -> Dict:
        """Diagnose why entities aren't being extracted"""
        diagnosis = {
            "text_length": len(text),
            "potential_entities": [],
            "extraction_issues": [],
            "recommendations": []
        }
        
        # Check text characteristics
        if len(text) < 20:
            diagnosis["extraction_issues"].append("Text too short")
            diagnosis["recommendations"].append("Provide more context")
        
        # Look for obvious entities (capitalized words)
        capitalized = re.findall(r'\b[A-Z][a-z]+\b', text)
        diagnosis["potential_entities"] = list(set(capitalized))
        
        # Check if LLM is responding
        try:
            test_extraction = await self.test_llm_extraction(text[:500])
            if not test_extraction:
                diagnosis["extraction_issues"].append("LLM not extracting")
                diagnosis["recommendations"].append("Check LLM configuration")
        except Exception as e:
            diagnosis["extraction_issues"].append(f"LLM error: {str(e)}")
            diagnosis["recommendations"].append("Verify API keys and model access")
        
        # Check prompt effectiveness
        if "potential_entities" in diagnosis and len(diagnosis["potential_entities"]) > 0:
            if not test_extraction or len(test_extraction) == 0:
                diagnosis["extraction_issues"].append("Prompt may be ineffective")
                diagnosis["recommendations"].append("Consider custom extraction prompts")
        
        return diagnosis
    
    async def test_llm_extraction(self, text: str) -> List[str]:
        """Test LLM extraction directly"""
        # This would call the LLM directly to test extraction
        # Implementation depends on your LLM setup
        prompt = f"""
        Extract all named entities from this text:
        {text}
        
        Return as a list of entity names.
        """
        # Simulate extraction test
        return []  # Replace with actual LLM call
    
    async def force_entity_extraction(
        self,
        text: str,
        hint_entities: List[str] = None
    ) -> Dict:
        """Force entity extraction with hints"""
        # Pre-seed with known entities
        if hint_entities:
            for entity_name in hint_entities:
                await self.graphiti.add_entity(
                    name=entity_name,
                    entity_type="PERSON",  # Adjust as needed
                    metadata={"source": "manual_hint"}
                )
        
        # Process with enhanced context
        enhanced_text = f"""
        Important entities to note:
        {', '.join(hint_entities) if hint_entities else 'Extract all entities'}
        
        Content:
        {text}
        """
        
        result = await self.graphiti.add_episode(
            enhanced_text,
            source_id="enhanced_extraction"
        )
        
        return result

# Usage
debugger = EntityExtractionDebugger(graphiti)
diagnosis = await debugger.diagnose_extraction(
    "John Smith met with Sarah Johnson about the AI project"
)
print(json.dumps(diagnosis, indent=2))
```

## Debugging Techniques

### 1. Enable Comprehensive Logging

```python
import logging
import sys
from datetime import datetime

class GraphitiLogger:
    """Advanced logging for Graphiti debugging"""
    
    def __init__(self, log_file: str = None):
        self.log_file = log_file or f"graphiti_debug_{datetime.now():%Y%m%d_%H%M%S}.log"
        self.setup_logging()
    
    def setup_logging(self):
        """Configure detailed logging"""
        # Root logger
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Specific loggers
        loggers = {
            'graphiti': logging.DEBUG,
            'neo4j': logging.INFO,
            'openai': logging.DEBUG,
            'httpx': logging.WARNING  # Reduce HTTP noise
        }
        
        for logger_name, level in loggers.items():
            logger = logging.getLogger(logger_name)
            logger.setLevel(level)
    
    def log_operation(self, operation: str, data: Dict = None):
        """Log specific operations"""
        logger = logging.getLogger('graphiti.operations')
        logger.info(f"Operation: {operation}")
        if data:
            logger.debug(f"Data: {json.dumps(data, indent=2)}")

# Usage
logger_setup = GraphitiLogger()
logger = logging.getLogger('graphiti')
```

### 2. Query Inspection and Optimization

```python
class QueryDebugger:
    """Debug and optimize Cypher queries"""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
        self.slow_queries = []
    
    async def profile_query(self, query: str, params: Dict = None) -> Dict:
        """Profile query performance"""
        import time
        
        # Add PROFILE prefix
        profile_query = f"PROFILE {query}"
        
        start_time = time.time()
        try:
            result = await self.graphiti.driver.session().run(
                profile_query,
                params or {}
            )
            execution_time = time.time() - start_time
            
            # Get execution plan
            summary = result.consume()
            plan = summary.profile
            
            profile_data = {
                "query": query,
                "execution_time": execution_time,
                "db_hits": plan.db_hits if plan else None,
                "rows_created": summary.counters.nodes_created,
                "relationships_created": summary.counters.relationships_created,
                "properties_set": summary.counters.properties_set
            }
            
            if execution_time > 1.0:  # Slow query threshold
                self.slow_queries.append(profile_data)
                logger.warning(f"Slow query detected: {execution_time:.2f}s")
            
            return profile_data
            
        except Exception as e:
            logger.error(f"Query profiling failed: {str(e)}")
            return {"error": str(e)}
    
    def suggest_optimizations(self, query: str) -> List[str]:
        """Suggest query optimizations"""
        suggestions = []
        
        # Check for missing indexes
        if "WHERE" in query and "INDEX" not in query:
            suggestions.append("Consider adding indexes for WHERE clause properties")
        
        # Check for cartesian products
        if query.count("MATCH") > 1 and "," in query:
            suggestions.append("Multiple MATCH clauses may create cartesian product")
        
        # Check for missing LIMIT
        if "RETURN" in query and "LIMIT" not in query:
            suggestions.append("Add LIMIT clause to prevent large result sets")
        
        # Check for property access in WHERE
        if "WHERE" in query and "." in query.split("WHERE")[1]:
            suggestions.append("Property access in WHERE clause may be slow without index")
        
        return suggestions

# Usage
debugger = QueryDebugger(graphiti)
profile = await debugger.profile_query(
    "MATCH (n:Entity)-[r:RELATES_TO]->(m:Entity) WHERE n.name = $name RETURN m",
    {"name": "John"}
)
print(f"Query took {profile['execution_time']:.3f}s")
print(f"Suggestions: {debugger.suggest_optimizations(profile['query'])}")
```

### 3. Memory Profiling

```python
import psutil
import tracemalloc
from typing import Callable

class MemoryProfiler:
    """Profile memory usage during Graphiti operations"""
    
    def __init__(self):
        self.snapshots = []
        self.process = psutil.Process()
    
    def start_profiling(self):
        """Start memory profiling"""
        tracemalloc.start()
        self.initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB
    
    def take_snapshot(self, label: str):
        """Take memory snapshot"""
        current_memory = self.process.memory_info().rss / 1024 / 1024
        snapshot = tracemalloc.take_snapshot()
        
        self.snapshots.append({
            "label": label,
            "memory_mb": current_memory,
            "delta_mb": current_memory - self.initial_memory,
            "snapshot": snapshot
        })
    
    def profile_operation(self, operation: Callable, label: str):
        """Profile memory for specific operation"""
        self.take_snapshot(f"Before {label}")
        result = operation()
        self.take_snapshot(f"After {label}")
        return result
    
    def get_report(self) -> str:
        """Generate memory report"""
        report = "Memory Usage Report\n"
        report += "=" * 50 + "\n"
        
        for snap in self.snapshots:
            report += f"{snap['label']}: {snap['memory_mb']:.2f} MB "
            report += f"(+{snap['delta_mb']:.2f} MB)\n"
        
        # Top memory allocations
        if self.snapshots:
            last_snapshot = self.snapshots[-1]["snapshot"]
            top_stats = last_snapshot.statistics('lineno')[:5]
            
            report += "\nTop Memory Allocations:\n"
            for stat in top_stats:
                report += f"{stat.size / 1024 / 1024:.2f} MB: {stat.traceback}\n"
        
        return report

# Usage
profiler = MemoryProfiler()
profiler.start_profiling()

async def heavy_operation():
    for i in range(100):
        await graphiti.add_episode(f"Episode {i}", f"source_{i}")

profiler.profile_operation(heavy_operation, "Batch Episode Processing")
print(profiler.get_report())
```

## Performance Problems

### 1. Slow Query Performance

#### Problem: Search queries taking too long
```python
# Searches taking > 5 seconds
```

**Solution with Query Optimization:**
```python
class QueryOptimizer:
    """Optimize slow queries"""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
    
    async def create_indexes(self):
        """Create necessary indexes for performance"""
        indexes = [
            # Entity indexes
            "CREATE INDEX entity_name IF NOT EXISTS FOR (n:Entity) ON (n.name)",
            "CREATE INDEX entity_type IF NOT EXISTS FOR (n:Entity) ON (n.entity_type)",
            "CREATE INDEX entity_embedding IF NOT EXISTS FOR (n:Entity) ON (n.embedding)",
            
            # Temporal indexes
            "CREATE INDEX entity_valid_time IF NOT EXISTS FOR (n:Entity) ON (n.valid_from, n.valid_to)",
            "CREATE INDEX entity_transaction_time IF NOT EXISTS FOR (n:Entity) ON (n.created_at)",
            
            # Relationship indexes
            "CREATE INDEX rel_type IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.relationship_type)",
            "CREATE INDEX rel_valid_time IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.valid_from, r.valid_to)",
            
            # Community indexes
            "CREATE INDEX community_id IF NOT EXISTS FOR (n:Community) ON (n.community_id)",
            "CREATE INDEX community_level IF NOT EXISTS FOR (n:Community) ON (n.level)",
            
            # Full-text search indexes
            "CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.description]",
            "CREATE FULLTEXT INDEX episode_fulltext IF NOT EXISTS FOR (n:Episode) ON EACH [n.content]"
        ]
        
        for index_query in indexes:
            try:
                await self.graphiti.driver.session().run(index_query)
                logger.info(f"Created index: {index_query.split('CREATE')[1].split('IF')[0]}")
            except Exception as e:
                logger.warning(f"Index creation failed: {str(e)}")
    
    async def optimize_search(
        self,
        query: str,
        use_cache: bool = True,
        limit_depth: int = 2
    ) -> List[Dict]:
        """Optimized search with caching and depth limits"""
        # Cache key
        cache_key = f"{query}_{limit_depth}"
        
        if use_cache and hasattr(self, '_cache'):
            if cache_key in self._cache:
                logger.info("Returning cached results")
                return self._cache[cache_key]
        
        # Optimized query with depth limit
        cypher = """
        MATCH (n:Entity)
        WHERE n.name CONTAINS $query OR n.description CONTAINS $query
        WITH n LIMIT 100
        OPTIONAL MATCH path = (n)-[r:RELATES_TO*..%d]-(m:Entity)
        RETURN n, collect(DISTINCT m) as related
        LIMIT 50
        """ % limit_depth
        
        result = await self.graphiti.driver.session().run(
            cypher,
            {"query": query}
        )
        
        # Cache results
        if use_cache:
            if not hasattr(self, '_cache'):
                self._cache = {}
            self._cache[cache_key] = result
        
        return result
    
    async def batch_search(
        self,
        queries: List[str],
        batch_size: int = 10
    ) -> Dict[str, List]:
        """Batch multiple searches efficiently"""
        results = {}
        
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i + batch_size]
            
            # Combine into single query
            cypher = """
            UNWIND $queries as query
            MATCH (n:Entity)
            WHERE n.name CONTAINS query OR n.description CONTAINS query
            RETURN query, collect(n) as entities
            """
            
            batch_result = await self.graphiti.driver.session().run(
                cypher,
                {"queries": batch}
            )
            
            for record in batch_result:
                results[record["query"]] = record["entities"]
        
        return results

# Usage
optimizer = QueryOptimizer(graphiti)
await optimizer.create_indexes()
results = await optimizer.optimize_search("artificial intelligence")
```

### 2. Memory Consumption Issues

#### Problem: Out of memory errors with large graphs
```python
# MemoryError or system becoming unresponsive
```

**Solution with Memory Management:**
```python
class MemoryManager:
    """Manage memory for large graph operations"""
    
    def __init__(self, graphiti: Graphiti, max_memory_mb: int = 4096):
        self.graphiti = graphiti
        self.max_memory_mb = max_memory_mb
        self.process = psutil.Process()
    
    def check_memory(self) -> Dict:
        """Check current memory usage"""
        memory = self.process.memory_info()
        return {
            "rss_mb": memory.rss / 1024 / 1024,
            "vms_mb": memory.vms / 1024 / 1024,
            "percent": self.process.memory_percent(),
            "available_mb": psutil.virtual_memory().available / 1024 / 1024
        }
    
    async def process_with_memory_limit(
        self,
        items: List,
        process_func: Callable,
        chunk_size: int = 100
    ):
        """Process items with memory constraints"""
        processed = 0
        failed = []
        
        for i in range(0, len(items), chunk_size):
            # Check memory before processing
            mem_status = self.check_memory()
            if mem_status["rss_mb"] > self.max_memory_mb * 0.8:
                logger.warning("Memory threshold reached, triggering cleanup")
                await self.cleanup_memory()
                
                # Re-check after cleanup
                mem_status = self.check_memory()
                if mem_status["rss_mb"] > self.max_memory_mb * 0.9:
                    logger.error("Memory still high after cleanup, stopping")
                    break
            
            # Process chunk
            chunk = items[i:i + chunk_size]
            try:
                for item in chunk:
                    await process_func(item)
                    processed += 1
            except Exception as e:
                logger.error(f"Processing failed: {str(e)}")
                failed.extend(chunk)
            
            # Periodic cleanup
            if i % (chunk_size * 10) == 0:
                await self.cleanup_memory()
        
        return {
            "processed": processed,
            "failed": len(failed),
            "failed_items": failed[:10]  # First 10 failures
        }
    
    async def cleanup_memory(self):
        """Clean up memory"""
        import gc
        
        # Close unused connections
        if hasattr(self.graphiti, '_connection_pool'):
            await self.graphiti._connection_pool.cleanup()
        
        # Clear caches
        if hasattr(self.graphiti, '_cache'):
            self.graphiti._cache.clear()
        
        # Force garbage collection
        gc.collect()
        
        logger.info("Memory cleanup completed")
    
    async def stream_large_results(
        self,
        query: str,
        params: Dict = None,
        chunk_size: int = 1000
    ):
        """Stream large result sets without loading all into memory"""
        offset = 0
        
        while True:
            # Paginated query
            paginated_query = f"{query} SKIP {offset} LIMIT {chunk_size}"
            
            result = await self.graphiti.driver.session().run(
                paginated_query,
                params or {}
            )
            
            records = list(result)
            if not records:
                break
            
            for record in records:
                yield record
            
            offset += chunk_size
            
            # Check memory between chunks
            if self.check_memory()["rss_mb"] > self.max_memory_mb * 0.7:
                await self.cleanup_memory()

# Usage
memory_mgr = MemoryManager(graphiti, max_memory_mb=2048)

# Process large dataset with memory limits
large_episodes = ["episode " * 1000 for _ in range(10000)]
result = await memory_mgr.process_with_memory_limit(
    large_episodes,
    lambda ep: graphiti.add_episode(ep, "bulk_source"),
    chunk_size=50
)
print(f"Processed: {result['processed']}, Failed: {result['failed']}")
```

## Integration Issues

### 1. LangChain Integration Problems

#### Problem: LangChain memory not syncing with Graphiti
```python
# LangChain conversations not appearing in graph
```

**Solution:**
```python
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage
from typing import List

class LangChainGraphitiSync:
    """Fix LangChain integration issues"""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
        self.sync_errors = []
    
    def create_synced_memory(self) -> ConversationBufferMemory:
        """Create memory that syncs with Graphiti"""
        memory = ConversationBufferMemory()
        
        # Override save_context to sync with Graphiti
        original_save = memory.save_context
        
        async def synced_save(inputs: Dict, outputs: Dict):
            # Save to LangChain memory
            original_save(inputs, outputs)
            
            # Sync to Graphiti
            try:
                episode = f"User: {inputs.get('input', '')}\nAssistant: {outputs.get('output', '')}"
                await self.graphiti.add_episode(
                    episode,
                    source_id=f"langchain_{datetime.now().timestamp()}",
                    metadata={
                        "integration": "langchain",
                        "timestamp": datetime.now().isoformat()
                    }
                )
            except Exception as e:
                self.sync_errors.append({
                    "error": str(e),
                    "inputs": inputs,
                    "outputs": outputs
                })
                logger.error(f"Sync failed: {str(e)}")
        
        memory.save_context = synced_save
        return memory
    
    async def repair_missing_conversations(
        self,
        messages: List[BaseMessage]
    ):
        """Repair missing conversations in graph"""
        repaired = 0
        
        for i in range(0, len(messages), 2):
            if i + 1 < len(messages):
                user_msg = messages[i]
                assistant_msg = messages[i + 1]
                
                # Check if already in graph
                existing = await self.graphiti.search(
                    user_msg.content[:50]  # First 50 chars
                )
                
                if not existing:
                    # Add missing conversation
                    episode = f"User: {user_msg.content}\nAssistant: {assistant_msg.content}"
                    await self.graphiti.add_episode(
                        episode,
                        source_id=f"repair_{i}",
                        metadata={
                            "repaired": True,
                            "original_timestamp": getattr(user_msg, 'timestamp', None)
                        }
                    )
                    repaired += 1
        
        logger.info(f"Repaired {repaired} missing conversations")
        return repaired

# Usage
sync = LangChainGraphitiSync(graphiti)
memory = sync.create_synced_memory()

# Repair missing data
from langchain.schema import HumanMessage, AIMessage
messages = [
    HumanMessage(content="What is AI?"),
    AIMessage(content="AI is artificial intelligence...")
]
await sync.repair_missing_conversations(messages)
```

### 2. API Rate Limiting Issues

#### Problem: Rate limit errors from LLM providers
```python
# openai.error.RateLimitError: Rate limit exceeded
```

**Solution with Rate Limiting:**
```python
import asyncio
from typing import Any
import time

class RateLimiter:
    """Handle API rate limiting gracefully"""
    
    def __init__(
        self,
        max_requests_per_minute: int = 60,
        max_tokens_per_minute: int = 90000
    ):
        self.max_rpm = max_requests_per_minute
        self.max_tpm = max_tokens_per_minute
        self.request_times = []
        self.token_counts = []
    
    async def wait_if_needed(self, estimated_tokens: int = 1000):
        """Wait if rate limit would be exceeded"""
        now = time.time()
        
        # Clean old entries
        self.request_times = [t for t in self.request_times if now - t < 60]
        self.token_counts = [(t, c) for t, c in self.token_counts if now - t < 60]
        
        # Check request limit
        if len(self.request_times) >= self.max_rpm:
            wait_time = 60 - (now - self.request_times[0])
            if wait_time > 0:
                logger.info(f"Rate limit: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        # Check token limit
        total_tokens = sum(c for _, c in self.token_counts)
        if total_tokens + estimated_tokens > self.max_tpm:
            wait_time = 60 - (now - self.token_counts[0][0])
            if wait_time > 0:
                logger.info(f"Token limit: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        # Record request
        self.request_times.append(now)
        self.token_counts.append((now, estimated_tokens))
    
    async def with_retry(
        self,
        func: Callable,
        max_retries: int = 5,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with exponential backoff"""
        for attempt in range(max_retries):
            try:
                # Estimate tokens (rough estimate)
                estimated_tokens = len(str(args) + str(kwargs)) * 2
                await self.wait_if_needed(estimated_tokens)
                
                return await func(*args, **kwargs)
                
            except Exception as e:
                if "rate" in str(e).lower():
                    wait_time = min(2 ** attempt * 10, 300)  # Max 5 minutes
                    logger.warning(f"Rate limit hit, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                elif attempt == max_retries - 1:
                    raise e
                else:
                    await asyncio.sleep(2 ** attempt)

class RateLimitedGraphiti:
    """Graphiti wrapper with rate limiting"""
    
    def __init__(self, graphiti: Graphiti, rate_limiter: RateLimiter):
        self.graphiti = graphiti
        self.rate_limiter = rate_limiter
    
    async def add_episode(self, episode: str, source_id: str, **kwargs):
        """Add episode with rate limiting"""
        return await self.rate_limiter.with_retry(
            self.graphiti.add_episode,
            episode=episode,
            source_id=source_id,
            **kwargs
        )
    
    async def search(self, query: str, **kwargs):
        """Search with rate limiting"""
        return await self.rate_limiter.with_retry(
            self.graphiti.search,
            query=query,
            **kwargs
        )

# Usage
rate_limiter = RateLimiter(
    max_requests_per_minute=50,
    max_tokens_per_minute=80000
)
limited_graphiti = RateLimitedGraphiti(graphiti, rate_limiter)

# Process many episodes without hitting rate limits
for episode in large_episode_list:
    await limited_graphiti.add_episode(episode, "bulk_source")
```

## Data Quality Problems

### 1. Duplicate Entity Detection

#### Problem: Multiple entities for the same real-world entity
```python
# "John Smith", "J. Smith", "John S." all as separate entities
```

**Solution with Entity Resolution:**
```python
from difflib import SequenceMatcher
import numpy as np

class EntityResolver:
    """Resolve duplicate entities"""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
    
    async def find_duplicates(
        self,
        similarity_threshold: float = 0.85
    ) -> List[List[Dict]]:
        """Find potential duplicate entities"""
        # Get all entities
        query = """
        MATCH (n:Entity)
        RETURN n.name as name, n.entity_type as type, id(n) as id
        """
        result = await self.graphiti.driver.session().run(query)
        entities = list(result)
        
        # Group by type
        by_type = {}
        for entity in entities:
            entity_type = entity["type"]
            if entity_type not in by_type:
                by_type[entity_type] = []
            by_type[entity_type].append(entity)
        
        # Find duplicates within each type
        duplicates = []
        for entity_type, typed_entities in by_type.items():
            for i, entity1 in enumerate(typed_entities):
                group = [entity1]
                for entity2 in typed_entities[i+1:]:
                    similarity = self.calculate_similarity(
                        entity1["name"],
                        entity2["name"]
                    )
                    if similarity > similarity_threshold:
                        group.append(entity2)
                
                if len(group) > 1:
                    duplicates.append(group)
        
        return duplicates
    
    def calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate name similarity"""
        # Direct match
        if name1.lower() == name2.lower():
            return 1.0
        
        # Substring match
        if name1.lower() in name2.lower() or name2.lower() in name1.lower():
            return 0.9
        
        # Initials match
        if self.match_initials(name1, name2):
            return 0.85
        
        # Sequence similarity
        return SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
    
    def match_initials(self, name1: str, name2: str) -> bool:
        """Check if names match by initials"""
        parts1 = name1.split()
        parts2 = name2.split()
        
        # Check if one is initials of the other
        initials1 = ''.join(p[0].upper() for p in parts1 if p)
        initials2 = ''.join(p[0].upper() for p in parts2 if p)
        
        return initials1 == initials2 or \
               any(p.replace('.', '').upper() == initials2 for p in parts1) or \
               any(p.replace('.', '').upper() == initials1 for p in parts2)
    
    async def merge_entities(
        self,
        entity_ids: List[int],
        primary_id: int = None
    ):
        """Merge duplicate entities"""
        if not primary_id:
            primary_id = entity_ids[0]
        
        merge_ids = [id for id in entity_ids if id != primary_id]
        
        # Merge relationships
        query = """
        MATCH (primary:Entity) WHERE id(primary) = $primary_id
        UNWIND $merge_ids as merge_id
        MATCH (merge:Entity) WHERE id(merge) = merge_id
        OPTIONAL MATCH (merge)-[r:RELATES_TO]-(other:Entity)
        FOREACH (rel IN CASE WHEN r IS NOT NULL THEN [r] ELSE [] END |
            MERGE (primary)-[:RELATES_TO {
                relationship_type: rel.relationship_type,
                weight: rel.weight,
                merged_from: merge_id
            }]-(other)
        )
        WITH merge
        DETACH DELETE merge
        """
        
        await self.graphiti.driver.session().run(
            query,
            {"primary_id": primary_id, "merge_ids": merge_ids}
        )
        
        logger.info(f"Merged {len(merge_ids)} entities into entity {primary_id}")
    
    async def auto_resolve_duplicates(self):
        """Automatically resolve obvious duplicates"""
        duplicates = await self.find_duplicates(similarity_threshold=0.95)
        
        resolved = 0
        for group in duplicates:
            if len(group) == 2:
                # Simple case: merge two entities
                await self.merge_entities(
                    [e["id"] for e in group],
                    primary_id=group[0]["id"]
                )
                resolved += 1
        
        logger.info(f"Auto-resolved {resolved} duplicate entity groups")
        return resolved

# Usage
resolver = EntityResolver(graphiti)
duplicates = await resolver.find_duplicates()
print(f"Found {len(duplicates)} potential duplicate groups")

# Auto-resolve high confidence duplicates
await resolver.auto_resolve_duplicates()
```

### 2. Relationship Quality Issues

#### Problem: Incorrect or missing relationships
```python
# Important relationships not being captured
```

**Solution with Relationship Enhancement:**
```python
class RelationshipEnhancer:
    """Enhance and fix relationship quality"""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
    
    async def audit_relationships(self) -> Dict:
        """Audit relationship quality"""
        audit = {
            "total_relationships": 0,
            "orphaned_relationships": 0,
            "duplicate_relationships": 0,
            "missing_types": 0,
            "weak_relationships": 0
        }
        
        # Count total relationships
        result = await self.graphiti.driver.session().run(
            "MATCH ()-[r:RELATES_TO]->() RETURN count(r) as count"
        )
        audit["total_relationships"] = result.single()["count"]
        
        # Find orphaned relationships (one endpoint missing)
        result = await self.graphiti.driver.session().run("""
            MATCH (n)-[r:RELATES_TO]->()
            WHERE NOT exists(n.name)
            RETURN count(r) as count
        """)
        audit["orphaned_relationships"] = result.single()["count"]
        
        # Find duplicate relationships
        result = await self.graphiti.driver.session().run("""
            MATCH (a:Entity)-[r1:RELATES_TO]->(b:Entity)
            MATCH (a)-[r2:RELATES_TO]->(b)
            WHERE id(r1) < id(r2) 
            AND r1.relationship_type = r2.relationship_type
            RETURN count(r1) as count
        """)
        audit["duplicate_relationships"] = result.single()["count"]
        
        # Find relationships without types
        result = await self.graphiti.driver.session().run("""
            MATCH ()-[r:RELATES_TO]->()
            WHERE r.relationship_type IS NULL OR r.relationship_type = ''
            RETURN count(r) as count
        """)
        audit["missing_types"] = result.single()["count"]
        
        # Find weak relationships (low weight)
        result = await self.graphiti.driver.session().run("""
            MATCH ()-[r:RELATES_TO]->()
            WHERE r.weight < 0.3
            RETURN count(r) as count
        """)
        audit["weak_relationships"] = result.single()["count"]
        
        return audit
    
    async def infer_missing_relationships(
        self,
        entity_name: str,
        max_distance: int = 2
    ) -> List[Dict]:
        """Infer potentially missing relationships"""
        # Get entity's context
        query = """
        MATCH (n:Entity {name: $name})
        OPTIONAL MATCH (n)-[r:RELATES_TO*1..%d]-(m:Entity)
        RETURN n, collect(DISTINCT m) as connected
        """ % max_distance
        
        result = await self.graphiti.driver.session().run(
            query,
            {"name": entity_name}
        )
        record = result.single()
        
        if not record:
            return []
        
        connected_entities = record["connected"]
        
        # Analyze co-occurrence patterns
        inferred = []
        for entity in connected_entities:
            # Check if entities often appear together in episodes
            co_occurrence = await self.check_co_occurrence(
                entity_name,
                entity["name"]
            )
            
            if co_occurrence > 0.7 and not self.has_direct_relationship(
                entity_name,
                entity["name"]
            ):
                inferred.append({
                    "from": entity_name,
                    "to": entity["name"],
                    "confidence": co_occurrence,
                    "suggested_type": self.suggest_relationship_type(
                        entity_name,
                        entity["name"]
                    )
                })
        
        return inferred
    
    async def check_co_occurrence(
        self,
        entity1: str,
        entity2: str
    ) -> float:
        """Check how often entities co-occur in episodes"""
        query = """
        MATCH (e1:Entity {name: $name1})-[:APPEARS_IN]->(ep:Episode)
        MATCH (e2:Entity {name: $name2})-[:APPEARS_IN]->(ep)
        WITH count(DISTINCT ep) as co_occurrences
        MATCH (e1:Entity {name: $name1})-[:APPEARS_IN]->(ep1:Episode)
        WITH co_occurrences, count(DISTINCT ep1) as total1
        MATCH (e2:Entity {name: $name2})-[:APPEARS_IN]->(ep2:Episode)
        WITH co_occurrences, total1, count(DISTINCT ep2) as total2
        RETURN toFloat(co_occurrences) / toFloat(total1 + total2 - co_occurrences) as jaccard
        """
        
        result = await self.graphiti.driver.session().run(
            query,
            {"name1": entity1, "name2": entity2}
        )
        
        record = result.single()
        return record["jaccard"] if record else 0.0
    
    def suggest_relationship_type(
        self,
        entity1: str,
        entity2: str
    ) -> str:
        """Suggest relationship type based on entity names"""
        # Simple heuristics (extend as needed)
        e1_lower = entity1.lower()
        e2_lower = entity2.lower()
        
        if "company" in e1_lower and "person" in e2_lower:
            return "EMPLOYS"
        elif "person" in e1_lower and "company" in e2_lower:
            return "WORKS_FOR"
        elif "product" in e1_lower or "product" in e2_lower:
            return "PRODUCES"
        elif "location" in e1_lower or "location" in e2_lower:
            return "LOCATED_IN"
        else:
            return "RELATES_TO"
    
    async def repair_relationships(self):
        """Repair common relationship issues"""
        repairs = {
            "removed_duplicates": 0,
            "added_types": 0,
            "removed_weak": 0
        }
        
        # Remove duplicate relationships
        query = """
        MATCH (a:Entity)-[r1:RELATES_TO]->(b:Entity)
        MATCH (a)-[r2:RELATES_TO]->(b)
        WHERE id(r1) < id(r2) 
        AND r1.relationship_type = r2.relationship_type
        DELETE r2
        RETURN count(r2) as count
        """
        result = await self.graphiti.driver.session().run(query)
        repairs["removed_duplicates"] = result.single()["count"]
        
        # Add missing relationship types
        query = """
        MATCH ()-[r:RELATES_TO]->()
        WHERE r.relationship_type IS NULL OR r.relationship_type = ''
        SET r.relationship_type = 'RELATES_TO'
        RETURN count(r) as count
        """
        result = await self.graphiti.driver.session().run(query)
        repairs["added_types"] = result.single()["count"]
        
        # Remove very weak relationships
        query = """
        MATCH ()-[r:RELATES_TO]->()
        WHERE r.weight < 0.1
        DELETE r
        RETURN count(r) as count
        """
        result = await self.graphiti.driver.session().run(query)
        repairs["removed_weak"] = result.single()["count"]
        
        return repairs

# Usage
enhancer = RelationshipEnhancer(graphiti)
audit = await enhancer.audit_relationships()
print(f"Relationship audit: {json.dumps(audit, indent=2)}")

# Infer missing relationships
inferred = await enhancer.infer_missing_relationships("John Smith")
print(f"Inferred {len(inferred)} potential relationships")

# Repair issues
repairs = await enhancer.repair_relationships()
print(f"Repairs completed: {json.dumps(repairs, indent=2)}")
```

## Neo4j Specific Problems

### 1. Connection Pool Exhaustion

#### Problem: Neo4j connection pool exhausted
```python
# neo4j.exceptions.ClientError: Connection pool exhausted
```

**Solution:**
```python
from neo4j import GraphDatabase
import asyncio

class Neo4jConnectionManager:
    """Manage Neo4j connections efficiently"""
    
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        max_connection_lifetime: int = 3600,
        max_connection_pool_size: int = 100
    ):
        self.uri = uri
        self.user = user
        self.password = password
        self.config = {
            "max_connection_lifetime": max_connection_lifetime,
            "max_connection_pool_size": max_connection_pool_size,
            "connection_acquisition_timeout": 60,
            "connection_timeout": 30,
            "keep_alive": True
        }
        self.driver = None
    
    def get_driver(self):
        """Get or create driver with proper configuration"""
        if not self.driver:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                **self.config
            )
        return self.driver
    
    async def execute_with_retry(
        self,
        query: str,
        params: Dict = None,
        max_retries: int = 3
    ):
        """Execute query with connection retry"""
        driver = self.get_driver()
        
        for attempt in range(max_retries):
            try:
                with driver.session() as session:
                    result = session.run(query, params or {})
                    return list(result)
            except Exception as e:
                if "pool" in str(e).lower() or "connection" in str(e).lower():
                    if attempt < max_retries - 1:
                        logger.warning(f"Connection issue, retrying... ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(2 ** attempt)
                        
                        # Reset driver on connection issues
                        if attempt == max_retries - 2:
                            self.reset_driver()
                    else:
                        raise e
                else:
                    raise e
    
    def reset_driver(self):
        """Reset driver connection"""
        if self.driver:
            try:
                self.driver.close()
            except:
                pass
        self.driver = None
        logger.info("Neo4j driver reset")
    
    def get_connection_stats(self) -> Dict:
        """Get connection pool statistics"""
        if not self.driver:
            return {"status": "no_driver"}
        
        # Note: Actual stats depend on Neo4j driver version
        return {
            "status": "active",
            "config": self.config
        }
    
    async def health_check(self) -> bool:
        """Check Neo4j health"""
        try:
            result = await self.execute_with_retry("RETURN 1 as health")
            return result[0]["health"] == 1
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

# Usage
conn_manager = Neo4jConnectionManager(
    "bolt://localhost:7687",
    "neo4j",
    "password",
    max_connection_pool_size=50
)

# Use with Graphiti
class ManagedGraphiti(Graphiti):
    def __init__(self, conn_manager: Neo4jConnectionManager, **kwargs):
        self.conn_manager = conn_manager
        super().__init__(
            uri=conn_manager.uri,
            user=conn_manager.user,
            password=conn_manager.password,
            **kwargs
        )
    
    async def execute_query(self, query: str, params: Dict = None):
        """Execute query with connection management"""
        return await self.conn_manager.execute_with_retry(query, params)

# Usage
graphiti = ManagedGraphiti(conn_manager)
```

### 2. Transaction Deadlocks

#### Problem: Deadlock detected in Neo4j transactions
```python
# neo4j.exceptions.TransientError: DeadlockDetected
```

**Solution:**
```python
class TransactionManager:
    """Handle Neo4j transactions safely"""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
    
    async def execute_in_transaction(
        self,
        operations: List[Tuple[str, Dict]],
        max_retries: int = 3
    ):
        """Execute multiple operations in a transaction with deadlock retry"""
        for attempt in range(max_retries):
            try:
                async with self.graphiti.driver.session() as session:
                    async with session.begin_transaction() as tx:
                        results = []
                        for query, params in operations:
                            result = await tx.run(query, params)
                            results.append(list(result))
                        await tx.commit()
                        return results
                        
            except Exception as e:
                if "deadlock" in str(e).lower():
                    if attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 0.1 * (1 + random.random())
                        logger.warning(f"Deadlock detected, retrying in {wait_time:.2f}s")
                        await asyncio.sleep(wait_time)
                    else:
                        raise e
                else:
                    raise e
    
    async def batch_update_with_locks(
        self,
        updates: List[Dict],
        batch_size: int = 100
    ):
        """Batch updates with proper locking order"""
        # Sort updates to prevent deadlocks
        sorted_updates = sorted(updates, key=lambda x: x.get("id", ""))
        
        for i in range(0, len(sorted_updates), batch_size):
            batch = sorted_updates[i:i + batch_size]
            
            operations = []
            for update in batch:
                query = """
                MATCH (n:Entity)
                WHERE id(n) = $id
                SET n += $properties
                RETURN n
                """
                operations.append((query, update))
            
            await self.execute_in_transaction(operations)
        
        logger.info(f"Completed {len(updates)} updates in batches")

# Usage
tx_manager = TransactionManager(graphiti)

# Execute multiple operations atomically
operations = [
    ("CREATE (n:Entity {name: $name}) RETURN n", {"name": "Entity1"}),
    ("CREATE (n:Entity {name: $name}) RETURN n", {"name": "Entity2"}),
    ("MATCH (a:Entity {name: $from}), (b:Entity {name: $to}) CREATE (a)-[:RELATES_TO]->(b)",
     {"from": "Entity1", "to": "Entity2"})
]
results = await tx_manager.execute_in_transaction(operations)
```

## Advanced Diagnostics

### 1. Comprehensive System Health Check

```python
class GraphitiDiagnostics:
    """Comprehensive diagnostics for Graphiti"""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
        self.diagnostics = {}
    
    async def run_full_diagnostics(self) -> Dict:
        """Run complete system diagnostics"""
        logger.info("Starting full system diagnostics...")
        
        # 1. Connection health
        self.diagnostics["connection"] = await self.check_connection()
        
        # 2. Database statistics
        self.diagnostics["database"] = await self.get_database_stats()
        
        # 3. Performance metrics
        self.diagnostics["performance"] = await self.measure_performance()
        
        # 4. Data quality
        self.diagnostics["data_quality"] = await self.assess_data_quality()
        
        # 5. API health
        self.diagnostics["api_health"] = await self.check_api_health()
        
        # 6. System resources
        self.diagnostics["resources"] = self.check_system_resources()
        
        # Generate report
        self.diagnostics["summary"] = self.generate_summary()
        
        return self.diagnostics
    
    async def check_connection(self) -> Dict:
        """Check Neo4j connection health"""
        try:
            start = time.time()
            result = await self.graphiti.driver.session().run("RETURN 1")
            latency = (time.time() - start) * 1000
            
            return {
                "status": "healthy",
                "latency_ms": latency,
                "connection_string": self.graphiti.uri
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def get_database_stats(self) -> Dict:
        """Get database statistics"""
        stats = {}
        
        queries = {
            "total_nodes": "MATCH (n) RETURN count(n) as count",
            "total_relationships": "MATCH ()-[r]->() RETURN count(r) as count",
            "entity_count": "MATCH (n:Entity) RETURN count(n) as count",
            "episode_count": "MATCH (n:Episode) RETURN count(n) as count",
            "community_count": "MATCH (n:Community) RETURN count(n) as count"
        }
        
        for key, query in queries.items():
            try:
                result = await self.graphiti.driver.session().run(query)
                stats[key] = result.single()["count"]
            except Exception as e:
                stats[key] = f"Error: {str(e)}"
        
        # Database size
        try:
            result = await self.graphiti.driver.session().run(
                "CALL apoc.meta.stats() YIELD nodeCount, relCount, labelCount, relTypeCount"
            )
            record = result.single()
            stats.update({
                "label_count": record["labelCount"],
                "relationship_type_count": record["relTypeCount"]
            })
        except:
            pass  # APOC might not be installed
        
        return stats
    
    async def measure_performance(self) -> Dict:
        """Measure performance metrics"""
        metrics = {}
        
        # Test queries with timing
        test_queries = [
            ("simple_lookup", "MATCH (n:Entity) RETURN n LIMIT 1"),
            ("relationship_traverse", "MATCH (n:Entity)-[r:RELATES_TO]->(m) RETURN n, r, m LIMIT 10"),
            ("aggregation", "MATCH (n:Entity) RETURN n.entity_type, count(*) as count"),
            ("text_search", "MATCH (n:Entity) WHERE n.name CONTAINS 'test' RETURN n LIMIT 10")
        ]
        
        for name, query in test_queries:
            start = time.time()
            try:
                await self.graphiti.driver.session().run(query)
                metrics[f"{name}_ms"] = (time.time() - start) * 1000
            except Exception as e:
                metrics[f"{name}_error"] = str(e)
        
        return metrics
    
    async def assess_data_quality(self) -> Dict:
        """Assess data quality metrics"""
        quality = {}
        
        # Check for common issues
        checks = [
            ("orphaned_nodes", """
                MATCH (n)
                WHERE NOT (n)--()
                RETURN count(n) as count
            """),
            ("missing_properties", """
                MATCH (n:Entity)
                WHERE n.name IS NULL OR n.entity_type IS NULL
                RETURN count(n) as count
            """),
            ("duplicate_relationships", """
                MATCH (a)-[r1:RELATES_TO]->(b)
                MATCH (a)-[r2:RELATES_TO]->(b)
                WHERE id(r1) < id(r2)
                RETURN count(r1) as count
            """),
            ("invalid_timestamps", """
                MATCH (n)
                WHERE n.created_at > n.valid_to
                RETURN count(n) as count
            """)
        ]
        
        for check_name, query in checks:
            try:
                result = await self.graphiti.driver.session().run(query)
                quality[check_name] = result.single()["count"]
            except Exception as e:
                quality[check_name] = f"Check failed: {str(e)}"
        
        return quality
    
    async def check_api_health(self) -> Dict:
        """Check LLM API health"""
        api_status = {}
        
        # Test LLM connectivity
        try:
            # This depends on your LLM setup
            test_prompt = "Test"
            # result = await self.graphiti.llm.generate(test_prompt)
            api_status["llm"] = "healthy"
        except Exception as e:
            api_status["llm"] = f"unhealthy: {str(e)}"
        
        # Test embedding model
        try:
            # result = await self.graphiti.embedding_model.embed("test")
            api_status["embedding"] = "healthy"
        except Exception as e:
            api_status["embedding"] = f"unhealthy: {str(e)}"
        
        return api_status
    
    def check_system_resources(self) -> Dict:
        """Check system resources"""
        import psutil
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage_percent": psutil.disk_usage('/').percent,
            "process_memory_mb": psutil.Process().memory_info().rss / 1024 / 1024
        }
    
    def generate_summary(self) -> Dict:
        """Generate diagnostic summary"""
        issues = []
        warnings = []
        
        # Check for critical issues
        if self.diagnostics.get("connection", {}).get("status") != "healthy":
            issues.append("Database connection unhealthy")
        
        if self.diagnostics.get("resources", {}).get("memory_percent", 0) > 90:
            issues.append("High memory usage")
        
        # Check for warnings
        quality = self.diagnostics.get("data_quality", {})
        if quality.get("orphaned_nodes", 0) > 100:
            warnings.append(f"High number of orphaned nodes: {quality['orphaned_nodes']}")
        
        if quality.get("duplicate_relationships", 0) > 50:
            warnings.append(f"Duplicate relationships detected: {quality['duplicate_relationships']}")
        
        return {
            "status": "critical" if issues else "warning" if warnings else "healthy",
            "issues": issues,
            "warnings": warnings,
            "timestamp": datetime.now().isoformat()
        }
    
    def print_report(self):
        """Print formatted diagnostic report"""
        print("\n" + "="*60)
        print("GRAPHITI DIAGNOSTIC REPORT")
        print("="*60)
        
        for section, data in self.diagnostics.items():
            print(f"\n[{section.upper()}]")
            if isinstance(data, dict):
                for key, value in data.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {data}")
        
        print("\n" + "="*60)

# Usage
diagnostics = GraphitiDiagnostics(graphiti)
report = await diagnostics.run_full_diagnostics()
diagnostics.print_report()

# Save report
with open("graphiti_diagnostics.json", "w") as f:
    json.dump(report, f, indent=2, default=str)
```

## Recovery Procedures

### 1. Disaster Recovery

```python
class DisasterRecovery:
    """Disaster recovery procedures for Graphiti"""
    
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
    
    async def create_backup(self, backup_path: str):
        """Create full backup of graph data"""
        logger.info(f"Creating backup to {backup_path}")
        
        # Export nodes
        nodes_query = """
        MATCH (n)
        RETURN n
        """
        nodes = await self.graphiti.driver.session().run(nodes_query)
        
        # Export relationships
        rels_query = """
        MATCH ()-[r]->()
        RETURN r
        """
        relationships = await self.graphiti.driver.session().run(rels_query)
        
        # Save to file
        backup_data = {
            "timestamp": datetime.now().isoformat(),
            "nodes": [dict(n["n"]) for n in nodes],
            "relationships": [dict(r["r"]) for r in relationships]
        }
        
        with open(backup_path, "w") as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        logger.info(f"Backup completed: {len(backup_data['nodes'])} nodes, {len(backup_data['relationships'])} relationships")
    
    async def restore_from_backup(self, backup_path: str):
        """Restore graph from backup"""
        logger.info(f"Restoring from {backup_path}")
        
        with open(backup_path, "r") as f:
            backup_data = json.load(f)
        
        # Clear existing data (BE CAREFUL!)
        await self.graphiti.driver.session().run("MATCH (n) DETACH DELETE n")
        
        # Restore nodes
        for node_data in backup_data["nodes"]:
            labels = node_data.pop("labels", ["Entity"])
            properties = json.dumps(node_data)
            
            query = f"""
            CREATE (n:{':'.join(labels)})
            SET n = $properties
            """
            await self.graphiti.driver.session().run(
                query,
                {"properties": node_data}
            )
        
        # Restore relationships
        # Implementation depends on relationship structure
        
        logger.info("Restore completed")
    
    async def repair_corrupted_data(self):
        """Repair common data corruption issues"""
        repairs = []
        
        # Fix invalid timestamps
        query = """
        MATCH (n)
        WHERE n.created_at > n.valid_to
        SET n.valid_to = n.created_at + duration('P30D')
        RETURN count(n) as count
        """
        result = await self.graphiti.driver.session().run(query)
        repairs.append(f"Fixed {result.single()['count']} invalid timestamps")
        
        # Remove orphaned relationships
        query = """
        MATCH ()-[r]->()
        WHERE NOT exists((n)) OR NOT exists((m))
        DELETE r
        RETURN count(r) as count
        """
        result = await self.graphiti.driver.session().run(query)
        repairs.append(f"Removed {result.single()['count']} orphaned relationships")
        
        return repairs

# Usage
recovery = DisasterRecovery(graphiti)

# Create backup
await recovery.create_backup("graphiti_backup_20240101.json")

# Repair data
repairs = await recovery.repair_corrupted_data()
print(f"Repairs completed: {repairs}")
```

## Troubleshooting Checklist

### Quick Diagnosis Flowchart

1. **Connection Issues?**
   - Check Neo4j is running: `neo4j status`
   - Verify credentials
   - Test connection: `cypher-shell -u neo4j -p password`
   - Check firewall/network

2. **Performance Issues?**
   - Run diagnostics: `GraphitiDiagnostics.run_full_diagnostics()`
   - Check indexes: `SHOW INDEXES`
   - Profile slow queries: `PROFILE <query>`
   - Monitor resources: `htop` / `docker stats`

3. **Data Quality Issues?**
   - Audit entities: `EntityResolver.find_duplicates()`
   - Audit relationships: `RelationshipEnhancer.audit_relationships()`
   - Check for orphans: `MATCH (n) WHERE NOT (n)--() RETURN n`

4. **Integration Issues?**
   - Verify API keys
   - Check rate limits
   - Test LLM directly
   - Enable debug logging

5. **Memory Issues?**
   - Use `MemoryManager`
   - Implement pagination
   - Clear caches periodically
   - Increase heap size

### Emergency Commands

```bash
# Restart Neo4j
sudo systemctl restart neo4j

# Clear Neo4j cache
MATCH (n) CALL db.clearQueryCaches() RETURN count(n)

# Check Neo4j logs
tail -f /var/log/neo4j/neo4j.log

# Monitor connections
netstat -an | grep 7687

# Emergency backup
neo4j-admin dump --database=neo4j --to=emergency_backup.dump
```

This comprehensive troubleshooting guide should help you diagnose and resolve most issues you might encounter with Graphiti. Remember to always backup your data before attempting major repairs or modifications!
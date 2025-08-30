# Performance Tuning and Optimization Guide

## Table of Contents
1. [Performance Baselines](#performance-baselines)
2. [LLM Optimization](#llm-optimization)
3. [Database Optimization](#database-optimization)
4. [Embedding and Vector Search](#embedding-and-vector-search)
5. [Concurrency and Parallelism](#concurrency-and-parallelism)
6. [Memory Management](#memory-management)
7. [Caching Strategies](#caching-strategies)
8. [Batch Processing](#batch-processing)
9. [Network Optimization](#network-optimization)
10. [Monitoring and Profiling](#monitoring-and-profiling)

---

## Performance Baselines

### Expected Performance Metrics

```python
class PerformanceBaselines:
    """Expected performance baselines for Graphiti operations."""
    
    # Episode Ingestion (per episode)
    INGESTION_BASELINES = {
        "text_episode_small": {  # <500 tokens
            "p50": 0.5,  # seconds
            "p95": 1.2,
            "p99": 2.0
        },
        "text_episode_large": {  # 500-2000 tokens
            "p50": 1.5,
            "p95": 3.0,
            "p99": 5.0
        },
        "json_episode": {
            "p50": 0.3,
            "p95": 0.8,
            "p99": 1.5
        },
        "bulk_ingestion_per_item": {  # With parallelism
            "p50": 0.2,
            "p95": 0.5,
            "p99": 1.0
        }
    }
    
    # Search Operations
    SEARCH_BASELINES = {
        "hybrid_search": {
            "p50": 0.15,  # seconds
            "p95": 0.3,
            "p99": 0.5
        },
        "semantic_only": {
            "p50": 0.1,
            "p95": 0.2,
            "p99": 0.35
        },
        "graph_traversal": {
            "p50": 0.05,
            "p95": 0.15,
            "p99": 0.3
        },
        "with_reranking": {
            "p50": 0.3,
            "p95": 0.6,
            "p99": 1.0
        }
    }
    
    # Graph Operations
    GRAPH_BASELINES = {
        "node_creation": {
            "p50": 0.01,
            "p95": 0.03,
            "p99": 0.05
        },
        "edge_creation": {
            "p50": 0.015,
            "p95": 0.04,
            "p99": 0.07
        },
        "community_detection": {
            "small_graph": 1.0,  # <1000 nodes
            "medium_graph": 5.0,  # 1000-10000 nodes
            "large_graph": 30.0  # >10000 nodes
        }
    }
```

### Performance Testing Framework

```python
import time
import asyncio
from contextlib import asynccontextmanager
from typing import Dict, List, Any
import statistics

class PerformanceTester:
    """Framework for testing Graphiti performance."""
    
    def __init__(self, graphiti):
        self.graphiti = graphiti
        self.results = []
    
    @asynccontextmanager
    async def measure(self, operation_name: str):
        """Context manager to measure operation time."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.results.append({
                "operation": operation_name,
                "duration": duration,
                "timestamp": datetime.now(timezone.utc)
            })
    
    async def test_ingestion_performance(
        self,
        num_episodes: int = 100
    ) -> Dict[str, float]:
        """Test episode ingestion performance."""
        durations = []
        
        for i in range(num_episodes):
            episode_content = f"Test episode {i}. " * 50  # ~100 tokens
            
            async with self.measure("ingestion"):
                await self.graphiti.add_episode(
                    name=f"Test_{i}",
                    episode_body=episode_content,
                    source=EpisodeType.text,
                    source_description="Performance test",
                    reference_time=datetime.now(timezone.utc)
                )
            
            durations.append(self.results[-1]["duration"])
        
        return {
            "mean": statistics.mean(durations),
            "median": statistics.median(durations),
            "p95": statistics.quantiles(durations, n=20)[18],  # 95th percentile
            "p99": statistics.quantiles(durations, n=100)[98],  # 99th percentile
            "min": min(durations),
            "max": max(durations)
        }
    
    async def test_search_performance(
        self,
        queries: List[str],
        search_configs: List[SearchConfig]
    ) -> Dict[str, Dict]:
        """Test search performance with different configurations."""
        results = {}
        
        for config_name, config in search_configs:
            config_durations = []
            
            for query in queries:
                async with self.measure(f"search_{config_name}"):
                    await self.graphiti._search(query, config=config)
                
                config_durations.append(self.results[-1]["duration"])
            
            results[config_name] = {
                "mean": statistics.mean(config_durations),
                "median": statistics.median(config_durations),
                "p95": statistics.quantiles(config_durations, n=20)[18],
                "p99": statistics.quantiles(config_durations, n=100)[98]
            }
        
        return results
    
    async def test_concurrent_operations(
        self,
        num_concurrent: int = 10
    ) -> Dict[str, Any]:
        """Test performance under concurrent load."""
        async def concurrent_operation(i: int):
            # Mix of operations
            if i % 3 == 0:
                # Search
                await self.graphiti.search(f"test query {i}")
            elif i % 3 == 1:
                # Ingestion
                await self.graphiti.add_episode(
                    name=f"Concurrent_{i}",
                    episode_body=f"Concurrent test {i}",
                    source=EpisodeType.text,
                    source_description="Concurrent test",
                    reference_time=datetime.now(timezone.utc)
                )
            else:
                # Graph query
                await self.graphiti.driver.execute(
                    "MATCH (n) RETURN n LIMIT 1"
                )
        
        start = time.perf_counter()
        
        # Run concurrent operations
        tasks = [concurrent_operation(i) for i in range(num_concurrent)]
        await asyncio.gather(*tasks)
        
        total_duration = time.perf_counter() - start
        
        return {
            "total_duration": total_duration,
            "operations_per_second": num_concurrent / total_duration,
            "average_latency": total_duration / num_concurrent
        }
```

---

## LLM Optimization

### Optimizing LLM Calls

```python
class LLMOptimizer:
    """Strategies for optimizing LLM usage in Graphiti."""
    
    def __init__(self, graphiti):
        self.graphiti = graphiti
        self.cache = {}  # Simple in-memory cache
    
    async def optimize_extraction(
        self,
        text: str,
        use_cache: bool = True,
        use_smaller_model: bool = False
    ) -> Dict:
        """Optimize entity extraction with various strategies."""
        
        # 1. Check cache first
        if use_cache:
            cache_key = hashlib.md5(text.encode()).hexdigest()
            if cache_key in self.cache:
                return self.cache[cache_key]
        
        # 2. Use smaller model for simple extractions
        if use_smaller_model and self._is_simple_text(text):
            result = await self._extract_with_small_model(text)
        else:
            result = await self._extract_with_main_model(text)
        
        # 3. Cache result
        if use_cache:
            self.cache[cache_key] = result
        
        return result
    
    def _is_simple_text(self, text: str) -> bool:
        """Determine if text is simple enough for smaller model."""
        # Simple heuristics
        return (
            len(text) < 500 and
            text.count('.') < 5 and
            not any(complex_term in text.lower() 
                   for complex_term in ['therefore', 'however', 'moreover'])
        )
    
    async def batch_llm_calls(
        self,
        texts: List[str],
        batch_size: int = 5
    ) -> List[Dict]:
        """Batch multiple texts into single LLM calls."""
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Combine into single prompt
            combined_prompt = self._create_batch_prompt(batch)
            
            # Single LLM call for batch
            batch_result = await self.graphiti.llm_client.generate_structured(
                combined_prompt,
                response_model=BatchExtractionResponse
            )
            
            results.extend(batch_result.extractions)
        
        return results
    
    def _create_batch_prompt(self, texts: List[str]) -> str:
        """Create a single prompt for batch extraction."""
        prompt = "Extract entities from the following texts:\n\n"
        
        for i, text in enumerate(texts, 1):
            prompt += f"Text {i}:\n{text}\n\n"
        
        prompt += "Return entities for each text separately."
        return prompt
    
    async def optimize_with_fallback(
        self,
        text: str,
        primary_model: str = "gpt-4",
        fallback_model: str = "gpt-3.5-turbo"
    ) -> Dict:
        """Use fallback model if primary fails or is slow."""
        try:
            # Try primary model with timeout
            result = await asyncio.wait_for(
                self._extract_with_model(text, primary_model),
                timeout=5.0  # 5 second timeout
            )
            return result
        
        except (asyncio.TimeoutError, Exception) as e:
            logger.warning(f"Primary model failed: {e}, using fallback")
            
            # Use fallback model
            return await self._extract_with_model(text, fallback_model)
```

### Token Optimization

```python
class TokenOptimizer:
    """Optimize token usage for cost and performance."""
    
    @staticmethod
    def truncate_smartly(
        text: str,
        max_tokens: int = 2000,
        preserve_structure: bool = True
    ) -> str:
        """Truncate text intelligently to fit token limits."""
        # Rough token estimation (1 token ≈ 4 characters)
        estimated_tokens = len(text) / 4
        
        if estimated_tokens <= max_tokens:
            return text
        
        if preserve_structure:
            # Try to preserve sentence boundaries
            sentences = text.split('. ')
            truncated = []
            token_count = 0
            
            for sentence in sentences:
                sentence_tokens = len(sentence) / 4
                if token_count + sentence_tokens > max_tokens:
                    break
                truncated.append(sentence)
                token_count += sentence_tokens
            
            return '. '.join(truncated) + '.'
        else:
            # Simple truncation
            max_chars = max_tokens * 4
            return text[:max_chars]
    
    @staticmethod
    def compress_prompt(
        prompt: str,
        compression_level: str = "medium"
    ) -> str:
        """Compress prompt to use fewer tokens."""
        if compression_level == "low":
            # Remove extra whitespace
            prompt = ' '.join(prompt.split())
        
        elif compression_level == "medium":
            # Remove unnecessary words
            unnecessary = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at']
            words = prompt.split()
            compressed = [w for w in words if w.lower() not in unnecessary or words.index(w) == 0]
            prompt = ' '.join(compressed)
        
        elif compression_level == "high":
            # Aggressive compression - abbreviations, etc.
            replacements = {
                'information': 'info',
                'configuration': 'config',
                'administrator': 'admin',
                'documentation': 'docs',
                'repository': 'repo'
            }
            for long, short in replacements.items():
                prompt = prompt.replace(long, short)
        
        return prompt
```

### Model Selection Strategy

```python
class ModelSelector:
    """Select optimal model based on task requirements."""
    
    def __init__(self):
        self.model_configs = {
            "fast": {
                "model": "gpt-3.5-turbo",
                "max_tokens": 500,
                "temperature": 0
            },
            "balanced": {
                "model": "gpt-4-turbo",
                "max_tokens": 1500,
                "temperature": 0.3
            },
            "accurate": {
                "model": "gpt-4",
                "max_tokens": 4000,
                "temperature": 0
            },
            "creative": {
                "model": "gpt-4",
                "max_tokens": 2000,
                "temperature": 0.8
            }
        }
    
    def select_model(
        self,
        task_type: str,
        text_length: int,
        complexity: str = "medium"
    ) -> Dict:
        """Select model based on task requirements."""
        if task_type == "extraction":
            if text_length < 500 and complexity == "low":
                return self.model_configs["fast"]
            elif text_length < 2000 and complexity == "medium":
                return self.model_configs["balanced"]
            else:
                return self.model_configs["accurate"]
        
        elif task_type == "generation":
            return self.model_configs["creative"]
        
        elif task_type == "classification":
            return self.model_configs["fast"]
        
        else:
            return self.model_configs["balanced"]
```

---

## Database Optimization

### Neo4j Performance Tuning

```python
class Neo4jOptimizer:
    """Neo4j-specific optimizations."""
    
    def __init__(self, driver):
        self.driver = driver
    
    async def optimize_indexes(self):
        """Create and optimize indexes for better performance."""
        indexes = [
            # Node indexes
            "CREATE INDEX node_name IF NOT EXISTS FOR (n:Entity) ON (n.name)",
            "CREATE INDEX node_created IF NOT EXISTS FOR (n:Entity) ON (n.created_at)",
            "CREATE INDEX node_type IF NOT EXISTS FOR (n:Entity) ON (n.type)",
            
            # Composite indexes
            "CREATE INDEX composite_project_date IF NOT EXISTS FOR (n:Entity) ON (n.project_id, n.created_at)",
            
            # Relationship indexes
            "CREATE INDEX rel_valid IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.valid_at)",
            "CREATE INDEX rel_invalid IF NOT EXISTS FOR ()-[r:RELATES_TO]-() ON (r.invalid_at)",
            
            # Full-text indexes
            "CREATE FULLTEXT INDEX entity_text IF NOT EXISTS FOR (n:Entity) ON EACH [n.name, n.summary, n.content]",
            
            # Vector indexes (Neo4j 5.x)
            "CREATE VECTOR INDEX entity_embedding IF NOT EXISTS FOR (n:Entity) ON n.embedding OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}"
        ]
        
        for index_query in indexes:
            try:
                await self.driver.execute(index_query)
                logger.info(f"Created index: {index_query[:50]}...")
            except Exception as e:
                logger.warning(f"Index creation failed: {e}")
    
    async def analyze_query_performance(self, query: str) -> Dict:
        """Analyze query performance using EXPLAIN/PROFILE."""
        # Get query plan
        explain_query = f"EXPLAIN {query}"
        plan = await self.driver.execute(explain_query)
        
        # Get actual execution profile
        profile_query = f"PROFILE {query}"
        profile = await self.driver.execute(profile_query)
        
        # Extract metrics
        metrics = {
            "estimated_rows": plan[0].get("estimatedRows", 0),
            "db_hits": profile[0].get("dbHits", 0),
            "rows_created": profile[0].get("rowsCreated", 0),
            "properties_set": profile[0].get("propertiesSet", 0)
        }
        
        return metrics
    
    async def optimize_memory_settings(self):
        """Configure Neo4j memory settings."""
        settings = {
            # Page cache (50% of available RAM)
            "dbms.memory.pagecache.size": "4g",
            
            # Heap size (25% of available RAM)
            "dbms.memory.heap.initial_size": "2g",
            "dbms.memory.heap.max_size": "2g",
            
            # Query cache
            "dbms.query_cache_size": "100",
            
            # Transaction settings
            "dbms.transaction.timeout": "30s",
            "dbms.transaction.concurrent.maximum": "100"
        }
        
        # These would be set in neo4j.conf
        return settings
    
    async def batch_write_optimization(
        self,
        nodes: List[Dict],
        edges: List[Dict],
        batch_size: int = 1000
    ):
        """Optimize batch writes with UNWIND."""
        # Batch nodes
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i:i + batch_size]
            
            query = """
            UNWIND $batch as node
            CREATE (n:Entity {
                uuid: node.uuid,
                name: node.name,
                created_at: node.created_at
            })
            """
            
            await self.driver.execute(query, {"batch": batch})
        
        # Batch edges
        for i in range(0, len(edges), batch_size):
            batch = edges[i:i + batch_size]
            
            query = """
            UNWIND $batch as edge
            MATCH (s:Entity {uuid: edge.source})
            MATCH (t:Entity {uuid: edge.target})
            CREATE (s)-[r:RELATES_TO {
                uuid: edge.uuid,
                fact: edge.fact,
                valid_at: edge.valid_at
            }]->(t)
            """
            
            await self.driver.execute(query, {"batch": batch})
```

### Query Optimization Patterns

```python
class QueryOptimizer:
    """Optimize Cypher queries for performance."""
    
    @staticmethod
    def optimize_path_queries(original_query: str) -> str:
        """Optimize path-finding queries."""
        # Use allShortestPaths instead of all paths
        optimized = original_query.replace(
            "MATCH p = (a)-[*]-(b)",
            "MATCH p = allShortestPaths((a)-[*..5]-(b))"
        )
        
        # Add relationship type hints
        optimized = optimized.replace(
            "-[*]-",
            "-[:RELATES_TO*]-"
        )
        
        # Use LIMIT early
        if "RETURN" in optimized and "LIMIT" not in optimized:
            optimized += " LIMIT 100"
        
        return optimized
    
    @staticmethod
    def use_index_hints(query: str, indexed_properties: List[str]) -> str:
        """Add index hints to queries."""
        for prop in indexed_properties:
            if f".{prop}" in query:
                # Add index hint
                query = query.replace(
                    f"MATCH (n",
                    f"MATCH (n:Entity"
                )
                query = query.replace(
                    f"WHERE n.{prop}",
                    f"USING INDEX n:Entity({prop}) WHERE n.{prop}"
                )
        
        return query
    
    @staticmethod
    def optimize_aggregations(query: str) -> str:
        """Optimize aggregation queries."""
        # Use WITH for intermediate aggregations
        if "COUNT(" in query and "GROUP BY" not in query:
            query = query.replace(
                "RETURN",
                "WITH n, COUNT(*) as cnt RETURN"
            )
        
        # Limit before aggregation when possible
        if "ORDER BY" in query and "LIMIT" in query:
            parts = query.split("RETURN")
            if len(parts) == 2:
                query = f"{parts[0]} WITH * LIMIT 1000 RETURN {parts[1]}"
        
        return query
```

---

## Embedding and Vector Search

### Embedding Optimization

```python
class EmbeddingOptimizer:
    """Optimize embedding generation and storage."""
    
    def __init__(self, embedder):
        self.embedder = embedder
        self.cache = {}
    
    async def batch_embed(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[np.ndarray]:
        """Batch embedding generation for efficiency."""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Check cache
            batch_embeddings = []
            texts_to_embed = []
            cache_indices = []
            
            for j, text in enumerate(batch):
                cache_key = hashlib.md5(text.encode()).hexdigest()
                if cache_key in self.cache:
                    batch_embeddings.append(self.cache[cache_key])
                else:
                    texts_to_embed.append(text)
                    cache_indices.append(j)
            
            # Embed uncached texts
            if texts_to_embed:
                new_embeddings = await self.embedder.embed_batch(texts_to_embed)
                
                # Insert into results and cache
                for idx, embedding in zip(cache_indices, new_embeddings):
                    batch[idx] = embedding
                    cache_key = hashlib.md5(texts_to_embed[cache_indices.index(idx)].encode()).hexdigest()
                    self.cache[cache_key] = embedding
            
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    def quantize_embeddings(
        self,
        embeddings: List[np.ndarray],
        bits: int = 8
    ) -> List[np.ndarray]:
        """Quantize embeddings to reduce storage."""
        quantized = []
        
        for embedding in embeddings:
            # Normalize to 0-1
            min_val = embedding.min()
            max_val = embedding.max()
            normalized = (embedding - min_val) / (max_val - min_val)
            
            # Quantize
            if bits == 8:
                quantized_embedding = (normalized * 255).astype(np.uint8)
            elif bits == 16:
                quantized_embedding = (normalized * 65535).astype(np.uint16)
            else:
                quantized_embedding = embedding  # No quantization
            
            quantized.append(quantized_embedding)
        
        return quantized
    
    async def selective_embedding(
        self,
        nodes: List[EntityNode],
        importance_threshold: float = 0.5
    ) -> List[EntityNode]:
        """Only embed important nodes to save resources."""
        nodes_to_embed = []
        
        for node in nodes:
            importance = self._calculate_importance(node)
            
            if importance >= importance_threshold:
                nodes_to_embed.append(node)
            else:
                # Use a default or zero embedding
                node.embedding = np.zeros(1536)
        
        # Batch embed important nodes
        if nodes_to_embed:
            texts = [node.summary for node in nodes_to_embed]
            embeddings = await self.batch_embed(texts)
            
            for node, embedding in zip(nodes_to_embed, embeddings):
                node.embedding = embedding
        
        return nodes
    
    def _calculate_importance(self, node: EntityNode) -> float:
        """Calculate node importance for embedding priority."""
        score = 0.0
        
        # Based on node properties
        if node.name:
            score += 0.3
        if node.summary and len(node.summary) > 50:
            score += 0.3
        if len(node.labels) > 1:
            score += 0.2
        if hasattr(node, 'degree') and node.degree > 5:
            score += 0.2
        
        return min(score, 1.0)
```

### Vector Search Optimization

```python
class VectorSearchOptimizer:
    """Optimize vector similarity search."""
    
    def __init__(self, driver):
        self.driver = driver
        self.index_cache = {}
    
    async def optimize_similarity_search(
        self,
        query_embedding: np.ndarray,
        limit: int = 10,
        use_approximate: bool = True
    ) -> List[Dict]:
        """Optimize vector similarity search."""
        if use_approximate:
            # Use approximate nearest neighbor
            return await self._approximate_search(query_embedding, limit)
        else:
            # Exact search with optimizations
            return await self._exact_search_optimized(query_embedding, limit)
    
    async def _approximate_search(
        self,
        query_embedding: np.ndarray,
        limit: int
    ) -> List[Dict]:
        """Use approximate nearest neighbor search."""
        query = """
        CALL db.index.vector.queryNodes(
            'entity_embedding',
            $limit,
            $embedding
        ) YIELD node, score
        RETURN node, score
        """
        
        results = await self.driver.execute(query, {
            'embedding': query_embedding.tolist(),
            'limit': limit * 2  # Get more for post-filtering
        })
        
        # Post-filter and limit
        filtered = self._post_filter_results(results)
        return filtered[:limit]
    
    async def _exact_search_optimized(
        self,
        query_embedding: np.ndarray,
        limit: int
    ) -> List[Dict]:
        """Exact search with optimizations."""
        # Pre-filter candidates
        query = """
        MATCH (n:Entity)
        WHERE n.embedding IS NOT NULL
        WITH n LIMIT 10000  // Pre-limit candidates
        WITH n, 
             gds.similarity.cosine(n.embedding, $embedding) as similarity
        WHERE similarity > 0.5  // Similarity threshold
        RETURN n, similarity
        ORDER BY similarity DESC
        LIMIT $limit
        """
        
        return await self.driver.execute(query, {
            'embedding': query_embedding.tolist(),
            'limit': limit
        })
    
    def _post_filter_results(
        self,
        results: List[Dict]
    ) -> List[Dict]:
        """Post-filter search results."""
        filtered = []
        
        for result in results:
            # Apply additional filters
            if result['score'] > 0.7:  # Quality threshold
                filtered.append(result)
        
        return filtered
    
    async def hybrid_search_optimization(
        self,
        query: str,
        query_embedding: np.ndarray,
        weights: Dict[str, float] = None
    ) -> List[Dict]:
        """Optimize hybrid search combining multiple methods."""
        weights = weights or {
            "semantic": 0.4,
            "keyword": 0.3,
            "graph": 0.3
        }
        
        # Run searches in parallel
        searches = await asyncio.gather(
            self._semantic_search(query_embedding),
            self._keyword_search(query),
            self._graph_search(query)
        )
        
        # Combine results efficiently
        combined = self._efficient_result_fusion(
            searches,
            weights
        )
        
        return combined
    
    def _efficient_result_fusion(
        self,
        search_results: List[List[Dict]],
        weights: Dict[str, float]
    ) -> List[Dict]:
        """Efficiently combine search results."""
        # Use reciprocal rank fusion
        fusion_scores = {}
        
        for i, (search_type, results) in enumerate(zip(weights.keys(), search_results)):
            weight = weights[search_type]
            
            for rank, result in enumerate(results):
                node_id = result.get('uuid')
                if node_id not in fusion_scores:
                    fusion_scores[node_id] = 0
                
                # RRF score
                fusion_scores[node_id] += weight / (60 + rank + 1)
        
        # Sort by fusion score
        sorted_results = sorted(
            fusion_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_results
```

---

## Concurrency and Parallelism

### Concurrency Control

```python
class ConcurrencyManager:
    """Manage concurrent operations in Graphiti."""
    
    def __init__(self, max_concurrency: int = None):
        self.max_concurrency = max_concurrency or int(os.getenv('SEMAPHORE_LIMIT', '10'))
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        self.rate_limiter = self._create_rate_limiter()
    
    def _create_rate_limiter(self):
        """Create a rate limiter for API calls."""
        return asyncio.Semaphore(100)  # 100 requests per second
    
    async def run_with_concurrency_limit(
        self,
        tasks: List[asyncio.Task],
        batch_size: int = None
    ) -> List[Any]:
        """Run tasks with concurrency limit."""
        batch_size = batch_size or self.max_concurrency
        results = []
        
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch)
            results.extend(batch_results)
        
        return results
    
    async def parallel_map(
        self,
        func: callable,
        items: List[Any],
        max_workers: int = None
    ) -> List[Any]:
        """Parallel map with controlled concurrency."""
        max_workers = max_workers or self.max_concurrency
        
        async def worker(item):
            async with self.semaphore:
                return await func(item)
        
        tasks = [worker(item) for item in items]
        return await asyncio.gather(*tasks)
    
    async def rate_limited_operation(
        self,
        func: callable,
        *args,
        **kwargs
    ):
        """Execute operation with rate limiting."""
        async with self.rate_limiter:
            await asyncio.sleep(0.01)  # 100 ops/second
            return await func(*args, **kwargs)
```

### Parallel Processing Strategies

```python
class ParallelProcessor:
    """Strategies for parallel processing in Graphiti."""
    
    def __init__(self, graphiti):
        self.graphiti = graphiti
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
    
    async def parallel_episode_processing(
        self,
        episodes: List[RawEpisode],
        strategy: str = "balanced"
    ) -> List[ProcessedEpisode]:
        """Process episodes in parallel with different strategies."""
        
        if strategy == "aggressive":
            # Maximum parallelism
            return await self._aggressive_parallel(episodes)
        elif strategy == "balanced":
            # Balanced parallelism
            return await self._balanced_parallel(episodes)
        elif strategy == "conservative":
            # Limited parallelism
            return await self._conservative_parallel(episodes)
        else:
            # Sequential
            return await self._sequential_processing(episodes)
    
    async def _aggressive_parallel(
        self,
        episodes: List[RawEpisode]
    ) -> List[ProcessedEpisode]:
        """Process all episodes in parallel."""
        tasks = [
            self._process_single_episode(episode)
            for episode in episodes
        ]
        
        return await asyncio.gather(*tasks)
    
    async def _balanced_parallel(
        self,
        episodes: List[RawEpisode]
    ) -> List[ProcessedEpisode]:
        """Process in balanced batches."""
        batch_size = min(10, len(episodes) // 2 + 1)
        results = []
        
        for i in range(0, len(episodes), batch_size):
            batch = episodes[i:i + batch_size]
            batch_tasks = [
                self._process_single_episode(episode)
                for episode in batch
            ]
            batch_results = await asyncio.gather(*batch_tasks)
            results.extend(batch_results)
        
        return results
    
    async def _conservative_parallel(
        self,
        episodes: List[RawEpisode]
    ) -> List[ProcessedEpisode]:
        """Limited parallelism for resource conservation."""
        semaphore = asyncio.Semaphore(3)
        
        async def process_with_limit(episode):
            async with semaphore:
                return await self._process_single_episode(episode)
        
        tasks = [process_with_limit(ep) for ep in episodes]
        return await asyncio.gather(*tasks)
    
    async def pipeline_processing(
        self,
        episodes: List[RawEpisode]
    ) -> List[ProcessedEpisode]:
        """Pipeline processing for optimal throughput."""
        # Stage 1: Entity extraction (CPU-bound)
        extraction_queue = asyncio.Queue()
        
        # Stage 2: Embedding generation (I/O-bound)
        embedding_queue = asyncio.Queue()
        
        # Stage 3: Database writes (I/O-bound)
        write_queue = asyncio.Queue()
        
        # Start pipeline workers
        workers = [
            asyncio.create_task(self._extraction_worker(extraction_queue, embedding_queue)),
            asyncio.create_task(self._embedding_worker(embedding_queue, write_queue)),
            asyncio.create_task(self._write_worker(write_queue))
        ]
        
        # Feed pipeline
        for episode in episodes:
            await extraction_queue.put(episode)
        
        # Signal completion
        await extraction_queue.put(None)
        
        # Wait for pipeline to complete
        await asyncio.gather(*workers)
```

---

## Memory Management

### Memory Optimization Strategies

```python
class MemoryManager:
    """Manage memory usage in Graphiti."""
    
    def __init__(self):
        self.cache_size_limit = 1000  # MB
        self.current_cache_size = 0
        self.cache = {}
    
    def estimate_memory_usage(self, obj: Any) -> int:
        """Estimate memory usage of an object in bytes."""
        import sys
        
        if isinstance(obj, dict):
            size = sys.getsizeof(obj)
            for key, value in obj.items():
                size += sys.getsizeof(key)
                size += self.estimate_memory_usage(value)
        elif isinstance(obj, list):
            size = sys.getsizeof(obj)
            for item in obj:
                size += self.estimate_memory_usage(item)
        elif isinstance(obj, np.ndarray):
            size = obj.nbytes
        else:
            size = sys.getsizeof(obj)
        
        return size
    
    def manage_cache(self, key: str, value: Any) -> bool:
        """Manage cache with memory limits."""
        value_size = self.estimate_memory_usage(value) / (1024 * 1024)  # Convert to MB
        
        # Check if adding would exceed limit
        if self.current_cache_size + value_size > self.cache_size_limit:
            # Evict least recently used
            self._evict_lru()
        
        # Add to cache
        self.cache[key] = {
            'value': value,
            'size': value_size,
            'last_accessed': time.time()
        }
        self.current_cache_size += value_size
        
        return True
    
    def _evict_lru(self):
        """Evict least recently used items."""
        if not self.cache:
            return
        
        # Sort by last accessed time
        sorted_items = sorted(
            self.cache.items(),
            key=lambda x: x[1]['last_accessed']
        )
        
        # Evict until we have space
        while self.current_cache_size > self.cache_size_limit * 0.8:  # Keep 20% free
            if not sorted_items:
                break
            
            key, item = sorted_items.pop(0)
            self.current_cache_size -= item['size']
            del self.cache[key]
    
    def clear_memory(self):
        """Clear memory and run garbage collection."""
        import gc
        
        self.cache.clear()
        self.current_cache_size = 0
        
        # Force garbage collection
        gc.collect()
```

### Streaming and Chunking

```python
class StreamProcessor:
    """Process data in streams to manage memory."""
    
    def __init__(self, graphiti):
        self.graphiti = graphiti
        self.chunk_size = 100
    
    async def stream_large_dataset(
        self,
        data_source: AsyncIterator,
        process_func: callable
    ):
        """Stream process large datasets."""
        buffer = []
        
        async for item in data_source:
            buffer.append(item)
            
            if len(buffer) >= self.chunk_size:
                # Process chunk
                await process_func(buffer)
                buffer = []
        
        # Process remaining
        if buffer:
            await process_func(buffer)
    
    async def chunked_file_processing(
        self,
        file_path: str,
        chunk_size: int = 1024 * 1024  # 1MB chunks
    ):
        """Process large files in chunks."""
        with open(file_path, 'r') as file:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                
                # Process chunk
                await self.graphiti.add_episode(
                    name=f"File_Chunk_{file.tell()}",
                    episode_body=chunk,
                    source=EpisodeType.text,
                    source_description=f"File: {file_path}",
                    reference_time=datetime.now(timezone.utc)
                )
```

---

## Caching Strategies

### Multi-Level Caching

```python
class MultiLevelCache:
    """Multi-level caching system for Graphiti."""
    
    def __init__(self):
        # L1: In-memory cache (fastest, smallest)
        self.l1_cache = {}
        self.l1_max_size = 100
        
        # L2: Redis cache (fast, larger)
        self.redis_client = None  # Initialize Redis connection
        
        # L3: Disk cache (slowest, largest)
        self.disk_cache_dir = "/tmp/graphiti_cache"
        os.makedirs(self.disk_cache_dir, exist_ok=True)
    
    async def get(self, key: str) -> Any:
        """Get value from cache hierarchy."""
        # Check L1
        if key in self.l1_cache:
            return self.l1_cache[key]
        
        # Check L2 (Redis)
        if self.redis_client:
            value = await self.redis_client.get(key)
            if value:
                # Promote to L1
                self._promote_to_l1(key, value)
                return json.loads(value)
        
        # Check L3 (Disk)
        disk_path = os.path.join(self.disk_cache_dir, f"{key}.cache")
        if os.path.exists(disk_path):
            with open(disk_path, 'r') as f:
                value = json.load(f)
            
            # Promote to L1 and L2
            self._promote_to_l1(key, value)
            if self.redis_client:
                await self._promote_to_l2(key, value)
            
            return value
        
        return None
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: int = 3600
    ):
        """Set value in cache hierarchy."""
        # Store in L1
        self._promote_to_l1(key, value)
        
        # Store in L2
        if self.redis_client:
            await self.redis_client.setex(
                key,
                ttl,
                json.dumps(value)
            )
        
        # Store in L3
        disk_path = os.path.join(self.disk_cache_dir, f"{key}.cache")
        with open(disk_path, 'w') as f:
            json.dump(value, f)
    
    def _promote_to_l1(self, key: str, value: Any):
        """Promote value to L1 cache."""
        if len(self.l1_cache) >= self.l1_max_size:
            # Evict oldest
            oldest_key = next(iter(self.l1_cache))
            del self.l1_cache[oldest_key]
        
        self.l1_cache[key] = value
```

### Query Result Caching

```python
class QueryCache:
    """Cache for query results."""
    
    def __init__(self, ttl: int = 300):  # 5 minutes default
        self.cache = {}
        self.ttl = ttl
    
    def cache_key(
        self,
        query: str,
        params: Dict = None
    ) -> str:
        """Generate cache key for query."""
        key_data = {
            'query': query,
            'params': params or {}
        }
        return hashlib.md5(
            json.dumps(key_data, sort_keys=True).encode()
        ).hexdigest()
    
    async def get_or_execute(
        self,
        query: str,
        execute_func: callable,
        params: Dict = None,
        force_refresh: bool = False
    ) -> Any:
        """Get from cache or execute query."""
        key = self.cache_key(query, params)
        
        if not force_refresh and key in self.cache:
            entry = self.cache[key]
            if time.time() - entry['timestamp'] < self.ttl:
                return entry['value']
        
        # Execute query
        result = await execute_func(query, params)
        
        # Cache result
        self.cache[key] = {
            'value': result,
            'timestamp': time.time()
        }
        
        return result
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern."""
        keys_to_remove = [
            key for key in self.cache
            if pattern in key
        ]
        
        for key in keys_to_remove:
            del self.cache[key]
```

---

## Batch Processing

### Optimized Batch Processing

```python
class BatchProcessor:
    """Optimized batch processing for Graphiti."""
    
    def __init__(self, graphiti):
        self.graphiti = graphiti
        self.optimal_batch_sizes = {
            'extraction': 10,
            'embedding': 100,
            'database_write': 500
        }
    
    async def adaptive_batch_processing(
        self,
        items: List[Any],
        process_func: callable,
        initial_batch_size: int = 10
    ) -> List[Any]:
        """Adaptively adjust batch size based on performance."""
        batch_size = initial_batch_size
        results = []
        
        i = 0
        while i < len(items):
            batch = items[i:i + batch_size]
            
            start_time = time.perf_counter()
            batch_results = await process_func(batch)
            duration = time.perf_counter() - start_time
            
            results.extend(batch_results)
            
            # Adjust batch size based on performance
            if duration < 1.0:  # Too fast, increase batch
                batch_size = min(batch_size * 2, 1000)
            elif duration > 5.0:  # Too slow, decrease batch
                batch_size = max(batch_size // 2, 1)
            
            i += len(batch)
            
            logger.info(f"Processed batch of {len(batch)} in {duration:.2f}s, new batch size: {batch_size}")
        
        return results
    
    async def pipeline_batch_processing(
        self,
        episodes: List[RawEpisode]
    ) -> List[ProcessedEpisode]:
        """Pipeline batch processing for maximum throughput."""
        # Stage 1: Extract entities in batches
        entity_batches = []
        for i in range(0, len(episodes), self.optimal_batch_sizes['extraction']):
            batch = episodes[i:i + self.optimal_batch_sizes['extraction']]
            entities = await self._batch_extract_entities(batch)
            entity_batches.append(entities)
        
        # Stage 2: Generate embeddings in larger batches
        all_entities = [e for batch in entity_batches for e in batch]
        embeddings = await self._batch_generate_embeddings(
            all_entities,
            self.optimal_batch_sizes['embedding']
        )
        
        # Stage 3: Write to database in even larger batches
        await self._batch_write_to_db(
            all_entities,
            embeddings,
            self.optimal_batch_sizes['database_write']
        )
        
        return all_entities
```

---

## Network Optimization

### Connection Pooling

```python
class ConnectionPool:
    """Connection pooling for database and API connections."""
    
    def __init__(self):
        self.db_pool = None
        self.api_pools = {}
        self.max_connections = 50
    
    async def initialize_db_pool(self, uri: str, user: str, password: str):
        """Initialize database connection pool."""
        from neo4j import AsyncGraphDatabase
        
        self.db_pool = AsyncGraphDatabase.driver(
            uri,
            auth=(user, password),
            max_connection_pool_size=self.max_connections,
            connection_acquisition_timeout=30,
            max_transaction_retry_time=30
        )
    
    async def get_db_connection(self):
        """Get connection from pool."""
        return self.db_pool.session()
    
    def get_api_client(self, service: str):
        """Get API client with connection pooling."""
        if service not in self.api_pools:
            import aiohttp
            
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300
            )
            
            self.api_pools[service] = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=30)
            )
        
        return self.api_pools[service]
```

### Request Optimization

```python
class RequestOptimizer:
    """Optimize network requests."""
    
    def __init__(self):
        self.compression_enabled = True
        self.retry_config = {
            'max_retries': 3,
            'backoff_factor': 2,
            'retry_on': [429, 500, 502, 503, 504]
        }
    
    async def optimized_request(
        self,
        client: aiohttp.ClientSession,
        method: str,
        url: str,
        **kwargs
    ) -> Dict:
        """Make optimized HTTP request."""
        # Add compression
        if self.compression_enabled:
            kwargs.setdefault('headers', {})['Accept-Encoding'] = 'gzip, deflate'
        
        # Retry logic
        for attempt in range(self.retry_config['max_retries']):
            try:
                async with client.request(method, url, **kwargs) as response:
                    if response.status in self.retry_config['retry_on']:
                        if attempt < self.retry_config['max_retries'] - 1:
                            await asyncio.sleep(
                                self.retry_config['backoff_factor'] ** attempt
                            )
                            continue
                    
                    response.raise_for_status()
                    return await response.json()
                    
            except aiohttp.ClientError as e:
                if attempt == self.retry_config['max_retries'] - 1:
                    raise
                
                await asyncio.sleep(
                    self.retry_config['backoff_factor'] ** attempt
                )
```

---

## Monitoring and Profiling

### Performance Monitoring

```python
class PerformanceMonitor:
    """Monitor Graphiti performance metrics."""
    
    def __init__(self):
        self.metrics = {
            'operations': {},
            'errors': {},
            'latencies': []
        }
        self.start_time = time.time()
    
    def record_operation(
        self,
        operation: str,
        duration: float,
        success: bool = True
    ):
        """Record operation metrics."""
        if operation not in self.metrics['operations']:
            self.metrics['operations'][operation] = {
                'count': 0,
                'total_duration': 0,
                'success_count': 0,
                'failure_count': 0
            }
        
        stats = self.metrics['operations'][operation]
        stats['count'] += 1
        stats['total_duration'] += duration
        
        if success:
            stats['success_count'] += 1
        else:
            stats['failure_count'] += 1
        
        # Record latency
        self.metrics['latencies'].append({
            'operation': operation,
            'duration': duration,
            'timestamp': time.time()
        })
    
    def get_statistics(self) -> Dict:
        """Get performance statistics."""
        uptime = time.time() - self.start_time
        stats = {
            'uptime_seconds': uptime,
            'operations': {}
        }
        
        for op, data in self.metrics['operations'].items():
            if data['count'] > 0:
                stats['operations'][op] = {
                    'count': data['count'],
                    'average_duration': data['total_duration'] / data['count'],
                    'success_rate': data['success_count'] / data['count'],
                    'throughput': data['count'] / uptime
                }
        
        # Calculate percentiles
        if self.metrics['latencies']:
            all_durations = [l['duration'] for l in self.metrics['latencies']]
            stats['latency_percentiles'] = {
                'p50': statistics.median(all_durations),
                'p95': statistics.quantiles(all_durations, n=20)[18],
                'p99': statistics.quantiles(all_durations, n=100)[98]
            }
        
        return stats
    
    async def export_metrics(self, format: str = "prometheus"):
        """Export metrics in various formats."""
        if format == "prometheus":
            return self._export_prometheus()
        elif format == "json":
            return json.dumps(self.get_statistics(), indent=2)
    
    def _export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        for op, data in self.metrics['operations'].items():
            op_clean = op.replace(' ', '_').lower()
            
            lines.append(f"graphiti_operation_count{{operation=\"{op_clean}\"}} {data['count']}")
            lines.append(f"graphiti_operation_duration_seconds{{operation=\"{op_clean}\"}} {data['total_duration']}")
            lines.append(f"graphiti_operation_success_total{{operation=\"{op_clean}\"}} {data['success_count']}")
            lines.append(f"graphiti_operation_failure_total{{operation=\"{op_clean}\"}} {data['failure_count']}")
        
        return '\n'.join(lines)
```

### Profiling Tools

```python
class Profiler:
    """Profile Graphiti operations."""
    
    def __init__(self):
        self.profiles = {}
    
    @contextmanager
    def profile_operation(self, name: str):
        """Profile a specific operation."""
        import cProfile
        import pstats
        import io
        
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            yield
        finally:
            profiler.disable()
            
            # Save profile
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
            ps.print_stats(20)  # Top 20 functions
            
            self.profiles[name] = {
                'stats': s.getvalue(),
                'timestamp': datetime.now(timezone.utc)
            }
    
    async def analyze_bottlenecks(self, graphiti) -> Dict:
        """Analyze performance bottlenecks."""
        bottlenecks = {}
        
        # Test different operations
        operations = [
            ('ingestion', self._test_ingestion),
            ('search', self._test_search),
            ('graph_traversal', self._test_traversal)
        ]
        
        for op_name, test_func in operations:
            with self.profile_operation(op_name):
                duration = await test_func(graphiti)
            
            bottlenecks[op_name] = {
                'duration': duration,
                'profile': self.profiles[op_name]['stats'][:500]  # First 500 chars
            }
        
        return bottlenecks
```

---

## Next Steps

This performance tuning guide provides comprehensive optimization strategies. Continue with:

- **[07_api_reference.md](./07_api_reference.md)** - Complete API documentation
- **[08_benchmarks_and_evaluation.md](./08_benchmarks_and_evaluation.md)** - Detailed benchmarks
- **[09_migration_guide.md](./09_migration_guide.md)** - Migration from other systems
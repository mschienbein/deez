# Practical Implementation Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Basic Usage Examples](#basic-usage-examples)
3. [Working with Episodes](#working-with-episodes)
4. [Custom Entity Types](#custom-entity-types)
5. [Search and Retrieval](#search-and-retrieval)
6. [Building a Chat Agent](#building-a-chat-agent)
7. [Real-World Examples](#real-world-examples)

---

## Getting Started

### Installation

```bash
# Basic installation
pip install graphiti-core

# With specific database support
pip install graphiti-core[neo4j]  # Neo4j support
pip install graphiti-core[falkordb]  # FalkorDB support
pip install graphiti-core[neptune]  # Amazon Neptune support

# With LLM provider support
pip install graphiti-core[anthropic,groq,google-genai]

# Using uv (recommended)
uv add graphiti-core[neo4j,anthropic]
```

### Environment Setup

Create a `.env` file:
```bash
# Required
OPENAI_API_KEY=sk-...

# Database Configuration (Neo4j)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Optional Performance Settings
SEMAPHORE_LIMIT=20  # Concurrent operations limit
USE_PARALLEL_RUNTIME=true  # For Neo4j Enterprise

# Alternative LLM Providers
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
GROQ_API_KEY=gsk-...
```

### Basic Initialization

```python
import asyncio
from datetime import datetime, timezone
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

async def main():
    # Initialize Graphiti with Neo4j
    graphiti = Graphiti(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )
    
    # Build indices (only needed once)
    await graphiti.build_indices_and_constraints()
    
    # Add your first episode
    await graphiti.add_episode(
        name="First Episode",
        episode_body="Alice is the CEO of TechCorp. She founded the company in 2020.",
        source=EpisodeType.text,
        source_description="Company history",
        reference_time=datetime.now(timezone.utc)
    )
    
    # Search the graph
    results = await graphiti.search("Who is the CEO?")
    for result in results:
        print(f"Fact: {result.fact}")
    
    # Clean up
    await graphiti.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Basic Usage Examples

### Adding Different Types of Episodes

```python
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
import json

async def add_various_episodes(graphiti: Graphiti):
    # 1. Text Episode (conversation, document, etc.)
    await graphiti.add_episode(
        name="Meeting Notes",
        episode_body="""
        During today's standup, Sarah mentioned she's leading the new ML project.
        The project aims to improve customer churn prediction by 25%.
        John from the data team will support with pipeline development.
        Expected completion: Q2 2024.
        """,
        source=EpisodeType.text,
        source_description="Daily standup meeting",
        reference_time=datetime(2024, 1, 15, 9, 0)
    )
    
    # 2. JSON Episode (structured data)
    customer_data = {
        "customer_id": "CUST-001",
        "name": "Acme Corporation",
        "industry": "Manufacturing",
        "account_manager": "Sarah Johnson",
        "contract_value": 150000,
        "renewal_date": "2024-12-31"
    }
    
    await graphiti.add_episode(
        name="Customer Record Update",
        episode_body=json.dumps(customer_data),
        source=EpisodeType.json,
        source_description="CRM system update",
        reference_time=datetime.now(timezone.utc)
    )
    
    # 3. Message Episode (chat, email, etc.)
    await graphiti.add_episode(
        name="Customer Support Chat",
        episode_body="Customer: My invoice shows the wrong amount. Agent: I'll fix that right away.",
        source=EpisodeType.message,
        source_description="Support chat transcript",
        reference_time=datetime.now(timezone.utc)
    )
```

### Bulk Episode Processing

```python
from graphiti_core.utils.bulk_utils import RawEpisode

async def bulk_ingestion(graphiti: Graphiti):
    # Prepare episodes
    episodes = []
    
    # Load from a data source (e.g., chat history)
    chat_messages = load_chat_history()  # Your function
    
    for i, message in enumerate(chat_messages):
        episodes.append(
            RawEpisode(
                name=f"Message_{i}",
                content=message['text'],
                source=EpisodeType.message,
                source_description="Chat history",
                reference_time=message['timestamp']
            )
        )
    
    # Process in bulk (much faster than individual adds)
    results = await graphiti.add_episodes_bulk(
        episodes,
        group_id="chat-session-123"  # Optional grouping
    )
    
    print(f"Processed {len(results.episodes)} episodes")
    print(f"Extracted {len(results.nodes)} entities")
    print(f"Created {len(results.edges)} relationships")
```

---

## Working with Episodes

### Episode Lifecycle Management

```python
class EpisodeManager:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
    
    async def add_versioned_episode(
        self,
        content: str,
        version: str,
        metadata: dict
    ):
        """
        Add episode with version tracking.
        """
        episode_name = f"{metadata.get('source', 'unknown')}_v{version}"
        
        result = await self.graphiti.add_episode(
            name=episode_name,
            episode_body=content,
            source=EpisodeType.text,
            source_description=json.dumps(metadata),
            reference_time=datetime.now(timezone.utc)
        )
        
        return result
    
    async def update_episode_context(
        self,
        episode_uuid: str,
        new_information: str
    ):
        """
        Add new information related to an existing episode.
        """
        # Retrieve original episode context
        original = await self.graphiti.get_episode(episode_uuid)
        
        # Create a follow-up episode
        await self.graphiti.add_episode(
            name=f"Update to {original.name}",
            episode_body=new_information,
            source=EpisodeType.text,
            source_description=f"Update to episode {episode_uuid}",
            reference_time=datetime.now(timezone.utc)
        )
```

### Handling Temporal Updates

```python
async def handle_fact_changes(graphiti: Graphiti):
    """
    Example of handling changing facts over time.
    """
    # Initial fact
    await graphiti.add_episode(
        name="Org Chart Q1",
        episode_body="Bob Smith is the VP of Sales at TechCorp.",
        source=EpisodeType.text,
        reference_time=datetime(2024, 1, 1)
    )
    
    # Fact changes
    await graphiti.add_episode(
        name="Org Chart Q2",
        episode_body="Alice Johnson is now the VP of Sales at TechCorp, replacing Bob Smith.",
        source=EpisodeType.text,
        reference_time=datetime(2024, 4, 1)
    )
    
    # Query historical state
    results_current = await graphiti.search("Who is the VP of Sales?")
    print("Current VP:", results_current[0].fact if results_current else "Unknown")
    
    # Query past state (requires custom temporal query)
    results_past = await graphiti.search(
        "Who was the VP of Sales?",
        time_filter=datetime(2024, 2, 1)  # Point-in-time query
    )
```

---

## Custom Entity Types

### Defining Domain-Specific Entities

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Define custom entity types
class Person(BaseModel):
    """Represents a person in the organization."""
    first_name: str = Field(..., description="Person's first name")
    last_name: str = Field(..., description="Person's last name")
    email: Optional[str] = Field(None, description="Email address")
    department: Optional[str] = Field(None, description="Department name")
    role: Optional[str] = Field(None, description="Job role")
    reports_to: Optional[str] = Field(None, description="Manager's name")

class Project(BaseModel):
    """Represents a project or initiative."""
    name: str = Field(..., description="Project name")
    code: Optional[str] = Field(None, description="Project code")
    status: str = Field(..., description="Current status")
    owner: Optional[str] = Field(None, description="Project owner")
    budget: Optional[float] = Field(None, description="Budget in USD")
    deadline: Optional[str] = Field(None, description="Deadline date")

class Meeting(BaseModel):
    """Represents a meeting or event."""
    title: str = Field(..., description="Meeting title")
    date: str = Field(..., description="Meeting date")
    attendees: List[str] = Field(default_factory=list, description="List of attendees")
    agenda: Optional[str] = Field(None, description="Meeting agenda")
    decisions: List[str] = Field(default_factory=list, description="Decisions made")

# Custom relationship types
class WorksOn(BaseModel):
    """Relationship: Person works on Project"""
    role: str = Field(..., description="Role in the project")
    allocation: float = Field(..., description="Time allocation percentage")
    start_date: str = Field(..., description="Start date")

class ReportsTo(BaseModel):
    """Relationship: Person reports to another Person"""
    effective_date: str = Field(..., description="When reporting relationship started")
```

### Using Custom Entities

```python
async def use_custom_entities(graphiti: Graphiti):
    # Register custom entity types
    graphiti.register_entity_types([
        Person,
        Project,
        Meeting,
        WorksOn,
        ReportsTo
    ])
    
    # Add episode with custom entities
    episode_content = """
    Sarah Johnson (sarah@techcorp.com) from Engineering is leading Project Apollo.
    She reports to Mike Chen, the VP of Engineering.
    The project has a budget of $500,000 and deadline of June 2024.
    Team members include John Doe and Jane Smith, both working 50% on the project.
    """
    
    result = await graphiti.add_episode(
        name="Project Kickoff",
        episode_body=episode_content,
        source=EpisodeType.text,
        reference_time=datetime.now(timezone.utc)
    )
    
    # The LLM will now extract entities according to your schemas
    print(f"Extracted {len(result.nodes)} entities with custom types")
```

### Entity Validation and Constraints

```python
from typing import Dict, Any

class EntityValidator:
    """
    Validate entities against business rules.
    """
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
    
    async def validate_person(self, person: Person) -> bool:
        """
        Validate person entity against business rules.
        """
        # Check email format
        if person.email and not self._is_valid_email(person.email):
            return False
        
        # Check department exists
        valid_departments = ["Engineering", "Sales", "Marketing", "HR"]
        if person.department and person.department not in valid_departments:
            return False
        
        # Check reporting structure (no circular reporting)
        if person.reports_to:
            chain = await self._get_reporting_chain(person.reports_to)
            if person.email in chain:
                return False
        
        return True
    
    async def _get_reporting_chain(self, manager_email: str) -> List[str]:
        """
        Get the reporting chain for validation.
        """
        chain = []
        current = manager_email
        
        while current:
            chain.append(current)
            # Query graph for manager's manager
            results = await self.graphiti.search(
                f"Who does {current} report to?"
            )
            current = self._extract_manager_from_results(results)
            
            # Prevent infinite loops
            if len(chain) > 10:
                break
        
        return chain
```

---

## Search and Retrieval

### Basic Search Operations

```python
async def search_examples(graphiti: Graphiti):
    # 1. Simple semantic search
    results = await graphiti.search("What projects are in progress?")
    
    # 2. Search with limit
    top_results = await graphiti.search(
        query="customer complaints",
        limit=5
    )
    
    # 3. Search with center node (contextual reranking)
    # First, find a relevant node
    initial_results = await graphiti.search("Sarah Johnson")
    if initial_results:
        center_node_uuid = initial_results[0].source_node_uuid
        
        # Search for related information
        related = await graphiti.search(
            "current projects",
            center_node_uuid=center_node_uuid
        )
    
    # 4. Group-specific search
    group_results = await graphiti.search(
        query="budget discussions",
        group_ids=["meeting-123", "meeting-456"]
    )
```

### Advanced Search Configuration

```python
from graphiti_core.search import SearchConfig
from graphiti_core.search.search_config_recipes import (
    EDGE_HYBRID_SEARCH_RRF,
    NODE_HYBRID_SEARCH_RRF,
    COMBINED_HYBRID_SEARCH_CROSS_ENCODER
)

async def advanced_search(graphiti: Graphiti):
    # 1. Use predefined search recipe
    results = await graphiti._search(
        query="Find all customer issues from last month",
        config=EDGE_HYBRID_SEARCH_RRF
    )
    
    # 2. Custom search configuration
    custom_config = SearchConfig(
        search_methods=["semantic", "keyword", "graph"],
        fusion_method="reciprocal_rank",
        semantic_weight=0.5,
        keyword_weight=0.3,
        graph_weight=0.2,
        use_reranking=True,
        limit=20
    )
    
    results = await graphiti._search(
        query="Technical architecture decisions",
        config=custom_config
    )
    
    # 3. Node-focused search (returns nodes instead of edges)
    node_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
    node_config.limit = 10
    
    node_results = await graphiti._search(
        query="All team members in Engineering",
        config=node_config
    )
    
    for node in node_results.nodes:
        print(f"Entity: {node.name}")
        print(f"Type: {', '.join(node.labels)}")
        print(f"Summary: {node.summary}")
        print("---")
```

### Building Search Filters

```python
from graphiti_core.search.search_filters import SearchFilters
from datetime import datetime, timedelta

async def filtered_search(graphiti: Graphiti):
    # Create filters
    filters = SearchFilters(
        # Temporal filters
        created_after=datetime.now() - timedelta(days=7),
        created_before=datetime.now(),
        
        # Entity type filters
        entity_types=["Person", "Project"],
        
        # Relationship filters
        edge_types=["WORKS_ON", "MANAGES"],
        
        # Group filters
        group_ids=["team-alpha", "team-beta"],
        
        # Confidence threshold
        min_confidence=0.7
    )
    
    # Apply filters to search
    results = await graphiti.search(
        query="recent team changes",
        filters=filters
    )
```

---

## Building a Chat Agent

### Simple Conversational Agent

```python
class GraphitiChatAgent:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
        self.conversation_history = []
        self.session_id = str(uuid4())
    
    async def chat(self, user_input: str) -> str:
        """
        Process user input and generate response.
        """
        # Add user input as episode
        await self.graphiti.add_episode(
            name=f"User_{len(self.conversation_history)}",
            episode_body=user_input,
            source=EpisodeType.message,
            source_description="User input",
            reference_time=datetime.now(timezone.utc),
            group_id=self.session_id
        )
        
        # Search for relevant context
        context = await self.graphiti.search(
            query=user_input,
            group_ids=[self.session_id],
            limit=10
        )
        
        # Generate response based on context
        response = self._generate_response(user_input, context)
        
        # Store agent response
        await self.graphiti.add_episode(
            name=f"Agent_{len(self.conversation_history)}",
            episode_body=response,
            source=EpisodeType.message,
            source_description="Agent response",
            reference_time=datetime.now(timezone.utc),
            group_id=self.session_id
        )
        
        # Update history
        self.conversation_history.append({
            "user": user_input,
            "agent": response,
            "timestamp": datetime.now(timezone.utc)
        })
        
        return response
    
    def _generate_response(
        self,
        user_input: str,
        context: List[Any]
    ) -> str:
        """
        Generate response using context from graph.
        """
        if not context:
            return "I don't have information about that. Can you provide more details?"
        
        # Format context into response
        facts = [result.fact for result in context[:3]]
        response = "Based on what I know:\n"
        for i, fact in enumerate(facts, 1):
            response += f"{i}. {fact}\n"
        
        return response
```

### Stateful Agent with Memory

```python
class StatefulAgent:
    def __init__(self, graphiti: Graphiti, user_id: str):
        self.graphiti = graphiti
        self.user_id = user_id
        self.user_profile = None
    
    async def initialize(self):
        """
        Load user profile and preferences.
        """
        # Search for user information
        user_info = await self.graphiti.search(
            f"user profile {self.user_id}"
        )
        
        if user_info:
            self.user_profile = self._parse_user_profile(user_info)
        else:
            # Create new user profile
            await self._create_user_profile()
    
    async def _create_user_profile(self):
        """
        Create a new user profile in the graph.
        """
        profile = {
            "user_id": self.user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "preferences": {},
            "interaction_count": 0
        }
        
        await self.graphiti.add_episode(
            name=f"User_Profile_{self.user_id}",
            episode_body=json.dumps(profile),
            source=EpisodeType.json,
            source_description="User profile",
            reference_time=datetime.now(timezone.utc)
        )
        
        self.user_profile = profile
    
    async def remember_preference(self, key: str, value: Any):
        """
        Store user preference in graph.
        """
        preference_update = {
            "user_id": self.user_id,
            "preference_key": key,
            "preference_value": value,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.graphiti.add_episode(
            name=f"Preference_Update_{self.user_id}",
            episode_body=json.dumps(preference_update),
            source=EpisodeType.json,
            source_description="User preference update",
            reference_time=datetime.now(timezone.utc)
        )
    
    async def get_personalized_context(self, query: str) -> List[Any]:
        """
        Get context personalized for the user.
        """
        # Search with user context
        base_results = await self.graphiti.search(query)
        
        # If user has preferences, rerank based on them
        if self.user_profile and self.user_profile.get("preferences"):
            # Filter/rerank based on preferences
            personalized = self._apply_preferences(
                base_results,
                self.user_profile["preferences"]
            )
            return personalized
        
        return base_results
```

---

## Real-World Examples

### Customer Support System

```python
class CustomerSupportGraph:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
    
    async def log_support_ticket(
        self,
        ticket_id: str,
        customer_id: str,
        issue: str,
        priority: str
    ):
        """
        Log a support ticket in the knowledge graph.
        """
        ticket_data = {
            "ticket_id": ticket_id,
            "customer_id": customer_id,
            "issue": issue,
            "priority": priority,
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.graphiti.add_episode(
            name=f"Ticket_{ticket_id}",
            episode_body=json.dumps(ticket_data),
            source=EpisodeType.json,
            source_description="Support ticket",
            reference_time=datetime.now(timezone.utc)
        )
    
    async def find_similar_issues(
        self,
        issue_description: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find similar past issues and their resolutions.
        """
        # Search for similar issues
        similar = await self.graphiti.search(
            query=issue_description,
            limit=limit * 2  # Get more to filter
        )
        
        # Filter for resolved issues
        resolved_issues = []
        for result in similar:
            if "resolved" in result.fact.lower() or "fixed" in result.fact.lower():
                resolved_issues.append({
                    "issue": result.fact,
                    "resolution": self._extract_resolution(result),
                    "confidence": result.score if hasattr(result, 'score') else 1.0
                })
        
        return resolved_issues[:limit]
    
    async def update_ticket_status(
        self,
        ticket_id: str,
        new_status: str,
        resolution: str = None
    ):
        """
        Update ticket status in the graph.
        """
        update_data = {
            "ticket_id": ticket_id,
            "status": new_status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        if resolution:
            update_data["resolution"] = resolution
        
        await self.graphiti.add_episode(
            name=f"Ticket_Update_{ticket_id}",
            episode_body=json.dumps(update_data),
            source=EpisodeType.json,
            source_description="Ticket status update",
            reference_time=datetime.now(timezone.utc)
        )
```

### Document Q&A System

```python
class DocumentQA:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
        self.document_index = {}
    
    async def ingest_document(
        self,
        doc_path: str,
        doc_type: str = "pdf"
    ):
        """
        Ingest a document into the knowledge graph.
        """
        # Parse document (implementation depends on doc_type)
        chunks = self._parse_document(doc_path, doc_type)
        
        doc_id = str(uuid4())
        self.document_index[doc_id] = {
            "path": doc_path,
            "type": doc_type,
            "ingested_at": datetime.now(timezone.utc)
        }
        
        # Add each chunk as an episode
        for i, chunk in enumerate(chunks):
            await self.graphiti.add_episode(
                name=f"Doc_{doc_id}_Chunk_{i}",
                episode_body=chunk['text'],
                source=EpisodeType.text,
                source_description=f"Document: {doc_path}, Page: {chunk.get('page', 'unknown')}",
                reference_time=datetime.now(timezone.utc),
                group_id=doc_id
            )
        
        return doc_id
    
    async def answer_question(
        self,
        question: str,
        doc_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        Answer a question based on ingested documents.
        """
        # Search for relevant information
        search_params = {"query": question, "limit": 10}
        if doc_ids:
            search_params["group_ids"] = doc_ids
        
        context = await self.graphiti.search(**search_params)
        
        if not context:
            return {
                "answer": "I couldn't find relevant information to answer your question.",
                "sources": [],
                "confidence": 0.0
            }
        
        # Generate answer from context
        answer = self._generate_answer(question, context)
        
        # Extract source references
        sources = [
            {
                "fact": result.fact,
                "source": result.source_description if hasattr(result, 'source_description') else "Unknown"
            }
            for result in context[:3]
        ]
        
        return {
            "answer": answer,
            "sources": sources,
            "confidence": self._calculate_confidence(context)
        }
    
    def _generate_answer(
        self,
        question: str,
        context: List[Any]
    ) -> str:
        """
        Generate an answer from context.
        """
        # In production, you'd use an LLM here
        # For demo, we'll create a simple answer
        facts = [r.fact for r in context[:3]]
        
        answer = "Based on the documents:\n\n"
        for fact in facts:
            answer += f"• {fact}\n"
        
        return answer
```

### Meeting Intelligence System

```python
class MeetingIntelligence:
    def __init__(self, graphiti: Graphiti):
        self.graphiti = graphiti
    
    async def process_meeting_transcript(
        self,
        transcript: str,
        meeting_metadata: Dict
    ):
        """
        Process meeting transcript to extract insights.
        """
        meeting_id = str(uuid4())
        
        # Add meeting metadata
        await self.graphiti.add_episode(
            name=f"Meeting_{meeting_id}_Metadata",
            episode_body=json.dumps(meeting_metadata),
            source=EpisodeType.json,
            source_description="Meeting metadata",
            reference_time=meeting_metadata.get('date', datetime.now(timezone.utc)),
            group_id=meeting_id
        )
        
        # Process transcript in chunks for speaker attribution
        segments = self._segment_transcript(transcript)
        
        for i, segment in enumerate(segments):
            await self.graphiti.add_episode(
                name=f"Meeting_{meeting_id}_Segment_{i}",
                episode_body=f"{segment['speaker']}: {segment['text']}",
                source=EpisodeType.message,
                source_description=f"Meeting transcript - {segment['speaker']}",
                reference_time=meeting_metadata.get('date', datetime.now(timezone.utc)),
                group_id=meeting_id
            )
        
        # Extract and store action items
        action_items = await self._extract_action_items(transcript)
        if action_items:
            await self.graphiti.add_episode(
                name=f"Meeting_{meeting_id}_Actions",
                episode_body=json.dumps(action_items),
                source=EpisodeType.json,
                source_description="Action items",
                reference_time=meeting_metadata.get('date', datetime.now(timezone.utc)),
                group_id=meeting_id
            )
        
        return meeting_id
    
    async def get_meeting_summary(
        self,
        meeting_id: str
    ) -> Dict[str, Any]:
        """
        Get a summary of a meeting.
        """
        # Retrieve all episodes for the meeting
        meeting_data = await self.graphiti.search(
            query="meeting discussion decisions action items",
            group_ids=[meeting_id],
            limit=50
        )
        
        summary = {
            "meeting_id": meeting_id,
            "key_topics": [],
            "decisions": [],
            "action_items": [],
            "participants": set()
        }
        
        for result in meeting_data:
            fact = result.fact
            
            # Extract different types of information
            if "decided" in fact.lower() or "agreed" in fact.lower():
                summary["decisions"].append(fact)
            elif "action" in fact.lower() or "will" in fact.lower():
                summary["action_items"].append(fact)
            
            # Extract participants (simplified)
            if ":" in fact:
                speaker = fact.split(":")[0].strip()
                summary["participants"].add(speaker)
        
        summary["participants"] = list(summary["participants"])
        return summary
    
    async def find_related_meetings(
        self,
        topic: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find meetings related to a specific topic.
        """
        results = await self.graphiti.search(
            query=f"meetings about {topic}",
            limit=limit * 3
        )
        
        # Group results by meeting
        meetings_map = {}
        for result in results:
            # Extract meeting ID from group_id or source
            meeting_id = self._extract_meeting_id(result)
            if meeting_id:
                if meeting_id not in meetings_map:
                    meetings_map[meeting_id] = {
                        "meeting_id": meeting_id,
                        "relevance_score": 0,
                        "relevant_facts": []
                    }
                meetings_map[meeting_id]["relevant_facts"].append(result.fact)
                meetings_map[meeting_id]["relevance_score"] += 1
        
        # Sort by relevance and return top meetings
        sorted_meetings = sorted(
            meetings_map.values(),
            key=lambda x: x["relevance_score"],
            reverse=True
        )
        
        return sorted_meetings[:limit]
```

---

## Next Steps

This practical implementation guide provides hands-on examples for using Graphiti. Continue with:

- **[04_advanced_features.md](./04_advanced_features.md)** - Communities, custom ontologies, and advanced features
- **[05_integration_patterns.md](./05_integration_patterns.md)** - Integration with LangChain, agent frameworks
- **[06_performance_tuning.md](./06_performance_tuning.md)** - Optimization strategies for production
# Integration Patterns with AI Frameworks

## Table of Contents
1. [LangChain Integration](#langchain-integration)
2. [LangGraph and Agent Architectures](#langgraph-and-agent-architectures)
3. [Strands Agents Integration](#strands-agents-integration)
4. [OpenAI Assistants API](#openai-assistants-api)
5. [Anthropic Claude Integration](#anthropic-claude-integration)
6. [AutoGPT and Autonomous Agents](#autogpt-and-autonomous-agents)
7. [MCP Server Integration](#mcp-server-integration)
8. [REST API Integration](#rest-api-integration)
9. [Event-Driven Architectures](#event-driven-architectures)
10. [Multi-Agent Systems](#multi-agent-systems)

---

## LangChain Integration

### Basic LangChain Memory with Graphiti

```python
from langchain.memory import ConversationSummaryMemory
from langchain.schema import BaseMemory
from typing import Any, Dict, List
import asyncio
from datetime import datetime, timezone

class GraphitiMemory(BaseMemory):
    """
    LangChain memory implementation backed by Graphiti.
    """
    def __init__(self, graphiti, session_id: str = None):
        self.graphiti = graphiti
        self.session_id = session_id or str(uuid4())
        self.memory_key = "chat_history"
    
    @property
    def memory_variables(self) -> List[str]:
        """Return memory variables."""
        return [self.memory_key]
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load memory variables from Graphiti."""
        # Run async code in sync context
        loop = asyncio.get_event_loop()
        history = loop.run_until_complete(self._load_history())
        return {self.memory_key: history}
    
    async def _load_history(self) -> str:
        """Load conversation history from graph."""
        results = await self.graphiti.search(
            query="conversation history",
            group_ids=[self.session_id],
            limit=10
        )
        
        history = []
        for result in results:
            history.append(result.fact)
        
        return "\n".join(history)
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Save conversation turn to Graphiti."""
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._save_turn(inputs, outputs))
    
    async def _save_turn(self, inputs: Dict[str, Any], outputs: Dict[str, str]):
        """Save a conversation turn."""
        # Save user input
        await self.graphiti.add_episode(
            name=f"User_{datetime.now().timestamp()}",
            episode_body=inputs.get("input", str(inputs)),
            source=EpisodeType.message,
            source_description="User input",
            reference_time=datetime.now(timezone.utc),
            group_id=self.session_id
        )
        
        # Save assistant output
        await self.graphiti.add_episode(
            name=f"Assistant_{datetime.now().timestamp()}",
            episode_body=outputs.get("output", str(outputs)),
            source=EpisodeType.message,
            source_description="Assistant response",
            reference_time=datetime.now(timezone.utc),
            group_id=self.session_id
        )
    
    def clear(self) -> None:
        """Clear memory (start new session)."""
        self.session_id = str(uuid4())
```

### LangChain Tool Integration

```python
from langchain.tools import BaseTool
from langchain.pydantic_v1 import Field
from typing import Optional, Type
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

class GraphitiSearchTool(BaseTool):
    """Tool for searching Graphiti knowledge graph."""
    
    name = "graphiti_search"
    description = "Search the knowledge graph for information about entities and relationships"
    args_schema: Type[BaseModel] = SearchInput
    graphiti: Any = Field(exclude=True)
    
    class SearchInput(BaseModel):
        query: str = Field(description="Search query")
        center_node: Optional[str] = Field(None, description="Optional center node for contextual search")
        limit: int = Field(10, description="Maximum results to return")
    
    def _run(
        self,
        query: str,
        center_node: Optional[str] = None,
        limit: int = 10,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Execute search synchronously."""
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(
            self.graphiti.search(query, center_node_uuid=center_node, limit=limit)
        )
        
        if not results:
            return "No relevant information found."
        
        response = "Found the following information:\n"
        for i, result in enumerate(results[:5], 1):
            response += f"{i}. {result.fact}\n"
        
        return response
    
    async def _arun(
        self,
        query: str,
        center_node: Optional[str] = None,
        limit: int = 10,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Execute search asynchronously."""
        results = await self.graphiti.search(
            query,
            center_node_uuid=center_node,
            limit=limit
        )
        
        if not results:
            return "No relevant information found."
        
        response = "Found the following information:\n"
        for i, result in enumerate(results[:5], 1):
            response += f"{i}. {result.fact}\n"
        
        return response

class GraphitiAddKnowledgeTool(BaseTool):
    """Tool for adding knowledge to Graphiti."""
    
    name = "graphiti_add_knowledge"
    description = "Add new information to the knowledge graph"
    graphiti: Any = Field(exclude=True)
    
    def _run(
        self,
        information: str,
        source: str = "agent_generated",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Add knowledge synchronously."""
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            self.graphiti.add_episode(
                name=f"Agent_Knowledge_{datetime.now().timestamp()}",
                episode_body=information,
                source=EpisodeType.text,
                source_description=source,
                reference_time=datetime.now(timezone.utc)
            )
        )
        
        return f"Successfully added knowledge to graph: {result.episode.uuid}"
```

### Complete LangChain Agent with Graphiti

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

async def create_graphiti_agent(graphiti):
    """Create a LangChain agent with Graphiti memory and tools."""
    
    # Initialize tools
    search_tool = GraphitiSearchTool(graphiti=graphiti)
    add_knowledge_tool = GraphitiAddKnowledgeTool(graphiti=graphiti)
    
    tools = [search_tool, add_knowledge_tool]
    
    # Initialize LLM
    llm = ChatOpenAI(
        model="gpt-4-turbo-preview",
        temperature=0.7
    )
    
    # Create prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI assistant with access to a knowledge graph.
        You can search for information and add new knowledge as you learn.
        Always search for relevant context before answering questions."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Create agent
    agent = create_openai_tools_agent(llm, tools, prompt)
    
    # Create memory
    memory = GraphitiMemory(graphiti)
    
    # Create executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        return_intermediate_steps=True
    )
    
    return agent_executor

# Usage
async def main():
    graphiti = Graphiti(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )
    
    agent = await create_graphiti_agent(graphiti)
    
    # Run the agent
    response = await agent.ainvoke({
        "input": "What do you know about our customer Acme Corp?"
    })
    
    print(response["output"])
```

---

## LangGraph and Agent Architectures

### Stateful Agent with LangGraph

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class AgentState(TypedDict):
    """Agent state with Graphiti context."""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    graph_context: List[Dict]
    current_entity: Optional[str]
    memory_summary: str

class GraphitiLangGraphAgent:
    """LangGraph agent with Graphiti memory."""
    
    def __init__(self, graphiti, llm):
        self.graphiti = graphiti
        self.llm = llm
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("retrieve_context", self.retrieve_context)
        workflow.add_node("process_query", self.process_query)
        workflow.add_node("update_memory", self.update_memory)
        workflow.add_node("generate_response", self.generate_response)
        
        # Add edges
        workflow.set_entry_point("retrieve_context")
        workflow.add_edge("retrieve_context", "process_query")
        workflow.add_edge("process_query", "update_memory")
        workflow.add_edge("update_memory", "generate_response")
        workflow.add_edge("generate_response", END)
        
        return workflow.compile()
    
    async def retrieve_context(self, state: AgentState) -> AgentState:
        """Retrieve relevant context from Graphiti."""
        last_message = state["messages"][-1]
        
        # Search for relevant context
        results = await self.graphiti.search(
            query=last_message.content,
            limit=10
        )
        
        # Extract entities mentioned
        entities = set()
        context = []
        
        for result in results:
            context.append({
                "fact": result.fact,
                "confidence": getattr(result, 'score', 1.0)
            })
            # Track entities
            if hasattr(result, 'source_node'):
                entities.add(result.source_node.name)
        
        state["graph_context"] = context
        state["current_entity"] = list(entities)[0] if entities else None
        
        return state
    
    async def process_query(self, state: AgentState) -> AgentState:
        """Process the query with context."""
        # Build context-aware prompt
        context_str = "\n".join([
            f"- {ctx['fact']}" for ctx in state["graph_context"]
        ])
        
        prompt = f"""
        Context from knowledge graph:
        {context_str}
        
        User query: {state["messages"][-1].content}
        
        Analyze this query considering the context.
        """
        
        # Process with LLM
        response = await self.llm.ainvoke(prompt)
        
        state["messages"].append(AIMessage(content=response.content))
        
        return state
    
    async def update_memory(self, state: AgentState) -> AgentState:
        """Update Graphiti with new information."""
        # Extract any new facts from the conversation
        last_ai_message = state["messages"][-1]
        
        # Add to Graphiti
        await self.graphiti.add_episode(
            name=f"Conversation_{datetime.now().timestamp()}",
            episode_body=last_ai_message.content,
            source=EpisodeType.message,
            source_description="Agent generated",
            reference_time=datetime.now(timezone.utc)
        )
        
        # Update memory summary
        state["memory_summary"] = f"Discussed: {state['current_entity']}"
        
        return state
    
    async def generate_response(self, state: AgentState) -> AgentState:
        """Generate final response."""
        # Response is already in messages
        return state
    
    async def run(self, user_input: str) -> str:
        """Run the agent with user input."""
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "graph_context": [],
            "current_entity": None,
            "memory_summary": ""
        }
        
        result = await self.graph.ainvoke(initial_state)
        
        return result["messages"][-1].content
```

### Multi-Step Planning Agent

```python
from langgraph.prebuilt import ToolExecutor
from langchain_core.agents import AgentAction, AgentFinish

class PlanningAgent:
    """Agent that plans multi-step tasks using Graphiti."""
    
    def __init__(self, graphiti, llm):
        self.graphiti = graphiti
        self.llm = llm
        self.tool_executor = ToolExecutor(self._get_tools())
    
    def _get_tools(self):
        """Get available tools."""
        return [
            GraphitiSearchTool(graphiti=self.graphiti),
            GraphitiAddKnowledgeTool(graphiti=self.graphiti)
        ]
    
    async def plan(self, objective: str) -> List[str]:
        """Create a plan for achieving the objective."""
        # Search for relevant context
        context = await self.graphiti.search(
            query=f"planning steps procedures {objective}",
            limit=5
        )
        
        prompt = f"""
        Objective: {objective}
        
        Relevant context:
        {context}
        
        Create a step-by-step plan to achieve this objective.
        Return as a numbered list.
        """
        
        response = await self.llm.ainvoke(prompt)
        
        # Parse steps
        steps = []
        for line in response.content.split('\n'):
            if line.strip() and line[0].isdigit():
                steps.append(line.strip())
        
        return steps
    
    async def execute_plan(self, steps: List[str]) -> Dict[str, Any]:
        """Execute a plan step by step."""
        results = {
            "steps_completed": [],
            "steps_failed": [],
            "knowledge_added": []
        }
        
        for step in steps:
            try:
                # Determine action for step
                action = await self._determine_action(step)
                
                if action.tool == "graphiti_search":
                    result = await self.tool_executor.ainvoke(action)
                    results["steps_completed"].append({
                        "step": step,
                        "result": result
                    })
                
                elif action.tool == "graphiti_add_knowledge":
                    result = await self.tool_executor.ainvoke(action)
                    results["knowledge_added"].append(result)
                    results["steps_completed"].append({
                        "step": step,
                        "result": "Knowledge added"
                    })
                
                # Update graph with step completion
                await self.graphiti.add_episode(
                    name=f"Plan_Step_Completed",
                    episode_body=f"Completed: {step}",
                    source=EpisodeType.text,
                    source_description="Plan execution",
                    reference_time=datetime.now(timezone.utc)
                )
                
            except Exception as e:
                results["steps_failed"].append({
                    "step": step,
                    "error": str(e)
                })
        
        return results
```

---

## Strands Agents Integration

### Graphiti Memory for Strands Agents

```python
from strands import Agent
from strands.models.openai import OpenAIModel
from strands_tools import Tool
import json

class GraphitiMemoryTool(Tool):
    """Strands tool for Graphiti memory operations."""
    
    def __init__(self, graphiti):
        self.graphiti = graphiti
        super().__init__(
            name="graphiti_memory",
            description="Search and store information in the knowledge graph",
            parameters={
                "operation": {
                    "type": "string",
                    "enum": ["search", "store", "update"],
                    "description": "Operation to perform"
                },
                "content": {
                    "type": "string",
                    "description": "Content to search for or store"
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional metadata",
                    "required": False
                }
            }
        )
    
    async def execute(self, operation: str, content: str, metadata: dict = None):
        """Execute memory operation."""
        if operation == "search":
            results = await self.graphiti.search(content, limit=5)
            return json.dumps([
                {"fact": r.fact, "confidence": getattr(r, 'score', 1.0)}
                for r in results
            ])
        
        elif operation == "store":
            result = await self.graphiti.add_episode(
                name=f"Agent_Memory_{datetime.now().timestamp()}",
                episode_body=content,
                source=EpisodeType.text,
                source_description=json.dumps(metadata) if metadata else "Agent memory",
                reference_time=datetime.now(timezone.utc)
            )
            return f"Stored in graph: {result.episode.uuid}"
        
        elif operation == "update":
            # Search for existing fact
            existing = await self.graphiti.search(content, limit=1)
            if existing:
                # Add new version (temporal update)
                result = await self.graphiti.add_episode(
                    name=f"Update_{datetime.now().timestamp()}",
                    episode_body=content,
                    source=EpisodeType.text,
                    source_description="Update to existing fact",
                    reference_time=datetime.now(timezone.utc)
                )
                return f"Updated fact: {result.episode.uuid}"
            else:
                return "No existing fact found to update"

class StrandsGraphitiAgent:
    """Strands agent with Graphiti integration."""
    
    def __init__(self, graphiti, openai_api_key: str):
        self.graphiti = graphiti
        
        # Initialize model
        self.model = OpenAIModel(
            client_args={"api_key": openai_api_key},
            model_id="gpt-4",
            params={"temperature": 0.7}
        )
        
        # Initialize tools
        self.memory_tool = GraphitiMemoryTool(graphiti)
        
        # Create agent
        self.agent = Agent(
            model=self.model,
            tools=[self.memory_tool],
            system_prompt=self._get_system_prompt()
        )
    
    def _get_system_prompt(self) -> str:
        """Get system prompt with memory instructions."""
        return """You are an AI assistant with access to a knowledge graph memory.
        
        Before answering any question:
        1. Search your memory for relevant information
        2. Use the context to provide accurate answers
        3. Store important new information you learn
        4. Update existing facts when you learn corrections
        
        Always ground your responses in the knowledge from your memory.
        If you don't have information, say so rather than guessing.
        """
    
    async def process(self, user_input: str) -> str:
        """Process user input with memory."""
        # First, store the user input
        await self.memory_tool.execute(
            operation="store",
            content=f"User asked: {user_input}",
            metadata={"type": "user_query"}
        )
        
        # Process with agent
        response = await self.agent.run(user_input)
        
        # Store the response
        await self.memory_tool.execute(
            operation="store",
            content=f"Agent responded: {response}",
            metadata={"type": "agent_response"}
        )
        
        return response
```

### Advanced Strands Pattern with Graphiti

```python
class ContextAwareStrandsAgent:
    """Advanced Strands agent with contextual memory."""
    
    def __init__(self, graphiti, model_config):
        self.graphiti = graphiti
        self.model = OpenAIModel(**model_config)
        self.context_window = []
        self.max_context_size = 10
    
    async def process_with_context(
        self,
        user_input: str,
        session_id: str = None
    ) -> Dict[str, Any]:
        """Process with full context awareness."""
        session_id = session_id or str(uuid4())
        
        # 1. Retrieve session context
        session_context = await self._get_session_context(session_id)
        
        # 2. Search for relevant facts
        relevant_facts = await self.graphiti.search(
            query=user_input,
            group_ids=[session_id],
            limit=10
        )
        
        # 3. Find related entities
        entities = await self._extract_entities(user_input)
        entity_context = await self._get_entity_context(entities)
        
        # 4. Build context window
        context = {
            "session_history": session_context,
            "relevant_facts": [f.fact for f in relevant_facts],
            "entity_context": entity_context,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # 5. Generate response with context
        prompt = self._build_contextual_prompt(user_input, context)
        
        agent = Agent(
            model=self.model,
            tools=[GraphitiMemoryTool(self.graphiti)],
            system_prompt=prompt
        )
        
        response = await agent.run(user_input)
        
        # 6. Update graph with interaction
        await self._update_graph(
            session_id=session_id,
            user_input=user_input,
            response=response,
            context=context
        )
        
        return {
            "response": response,
            "context_used": context,
            "session_id": session_id
        }
    
    async def _get_session_context(self, session_id: str) -> List[str]:
        """Get conversation history for session."""
        results = await self.graphiti.search(
            query="conversation history messages",
            group_ids=[session_id],
            limit=self.max_context_size
        )
        return [r.fact for r in results]
    
    async def _extract_entities(self, text: str) -> List[str]:
        """Extract entities mentioned in text."""
        # Use Graphiti's entity extraction
        episode = await self.graphiti.add_episode(
            name="Entity_Extraction_Temp",
            episode_body=text,
            source=EpisodeType.text,
            source_description="Entity extraction",
            reference_time=datetime.now(timezone.utc)
        )
        
        # Get extracted entities
        entities = []
        for node in episode.nodes:
            entities.append(node.name)
        
        return entities
    
    async def _get_entity_context(self, entities: List[str]) -> Dict[str, List[str]]:
        """Get context for each entity."""
        entity_context = {}
        
        for entity in entities:
            results = await self.graphiti.search(
                query=entity,
                limit=3
            )
            entity_context[entity] = [r.fact for r in results]
        
        return entity_context
    
    def _build_contextual_prompt(
        self,
        user_input: str,
        context: Dict
    ) -> str:
        """Build context-aware prompt."""
        return f"""You are an AI assistant with access to a knowledge graph.
        
        Current Context:
        - Session History: {json.dumps(context['session_history'])}
        - Relevant Facts: {json.dumps(context['relevant_facts'])}
        - Entity Information: {json.dumps(context['entity_context'])}
        
        Use this context to provide accurate, contextual responses.
        Reference specific facts when answering.
        Update your memory with any new information learned.
        
        User Input: {user_input}
        """
    
    async def _update_graph(
        self,
        session_id: str,
        user_input: str,
        response: str,
        context: Dict
    ):
        """Update graph with interaction."""
        interaction = {
            "user_input": user_input,
            "agent_response": response,
            "context_size": len(context["relevant_facts"]),
            "entities_referenced": list(context["entity_context"].keys()),
            "timestamp": context["timestamp"]
        }
        
        await self.graphiti.add_episode(
            name=f"Interaction_{session_id}_{datetime.now().timestamp()}",
            episode_body=json.dumps(interaction),
            source=EpisodeType.json,
            source_description="Agent interaction",
            reference_time=datetime.now(timezone.utc),
            group_id=session_id
        )
```

---

## OpenAI Assistants API

### Graphiti as Assistant File Search

```python
from openai import AsyncOpenAI
from typing import List, Dict, Any
import base64

class GraphitiAssistantIntegration:
    """Integrate Graphiti with OpenAI Assistants API."""
    
    def __init__(self, graphiti, openai_api_key: str):
        self.graphiti = graphiti
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.assistant = None
    
    async def create_assistant(self) -> str:
        """Create an assistant with Graphiti tools."""
        # Define custom functions for Graphiti
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_knowledge_graph",
                    "description": "Search the knowledge graph for information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum results",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "add_to_knowledge_graph",
                    "description": "Add new information to the knowledge graph",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Information to add"
                            },
                            "source": {
                                "type": "string",
                                "description": "Source of information"
                            }
                        },
                        "required": ["content"]
                    }
                }
            }
        ]
        
        # Create assistant
        self.assistant = await self.client.beta.assistants.create(
            name="Graphiti Knowledge Assistant",
            instructions="""You are an AI assistant with access to a knowledge graph.
            Always search the graph for relevant information before answering.
            Add new important information to the graph as you learn it.""",
            model="gpt-4-turbo-preview",
            tools=tools
        )
        
        return self.assistant.id
    
    async def handle_function_call(
        self,
        function_name: str,
        arguments: Dict[str, Any]
    ) -> str:
        """Handle function calls from the assistant."""
        if function_name == "search_knowledge_graph":
            results = await self.graphiti.search(
                query=arguments["query"],
                limit=arguments.get("limit", 5)
            )
            
            if not results:
                return "No relevant information found in the knowledge graph."
            
            response = "Found the following information:\n"
            for i, result in enumerate(results, 1):
                response += f"{i}. {result.fact}\n"
            
            return response
        
        elif function_name == "add_to_knowledge_graph":
            result = await self.graphiti.add_episode(
                name=f"Assistant_Knowledge_{datetime.now().timestamp()}",
                episode_body=arguments["content"],
                source=EpisodeType.text,
                source_description=arguments.get("source", "Assistant generated"),
                reference_time=datetime.now(timezone.utc)
            )
            
            return f"Successfully added to knowledge graph: {result.episode.uuid}"
        
        else:
            return f"Unknown function: {function_name}"
    
    async def run_thread(self, thread_id: str, user_message: str) -> str:
        """Run a conversation thread."""
        # Add message to thread
        await self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=user_message
        )
        
        # Run the assistant
        run = await self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant.id
        )
        
        # Wait for completion and handle function calls
        while run.status in ["queued", "in_progress", "requires_action"]:
            if run.status == "requires_action":
                # Handle function calls
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []
                
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    output = await self.handle_function_call(
                        function_name,
                        arguments
                    )
                    
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": output
                    })
                
                # Submit tool outputs
                run = await self.client.beta.threads.runs.submit_tool_outputs(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
            
            # Wait and check again
            await asyncio.sleep(1)
            run = await self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
        
        # Get the response
        messages = await self.client.beta.threads.messages.list(
            thread_id=thread_id
        )
        
        return messages.data[0].content[0].text.value
```

---

## Anthropic Claude Integration

### Claude with Graphiti Memory

```python
from anthropic import AsyncAnthropic
from typing import List, Dict, Any

class ClaudeGraphitiAgent:
    """Claude agent with Graphiti memory."""
    
    def __init__(self, graphiti, anthropic_api_key: str):
        self.graphiti = graphiti
        self.client = AsyncAnthropic(api_key=anthropic_api_key)
        self.conversation_history = []
    
    async def chat(
        self,
        user_message: str,
        use_tools: bool = True
    ) -> str:
        """Chat with Claude using Graphiti context."""
        # Search for relevant context
        context = await self.graphiti.search(user_message, limit=10)
        
        # Build context string
        context_str = self._format_context(context)
        
        # Prepare messages
        messages = self._build_messages(user_message, context_str)
        
        if use_tools:
            # Use Claude's tool use
            response = await self._chat_with_tools(messages)
        else:
            # Simple chat
            response = await self.client.messages.create(
                model="claude-3-opus-20240229",
                messages=messages,
                max_tokens=1000
            )
            response = response.content[0].text
        
        # Store interaction in Graphiti
        await self._store_interaction(user_message, response)
        
        return response
    
    def _format_context(self, results: List[Any]) -> str:
        """Format search results as context."""
        if not results:
            return "No relevant context found."
        
        context = "Relevant information from knowledge graph:\n"
        for i, result in enumerate(results[:5], 1):
            context += f"{i}. {result.fact}\n"
        
        return context
    
    def _build_messages(
        self,
        user_message: str,
        context: str
    ) -> List[Dict]:
        """Build message list for Claude."""
        messages = []
        
        # System message with context
        system_message = f"""You are an AI assistant with access to a knowledge graph.
        
        {context}
        
        Use this context to provide accurate, grounded responses.
        If the context doesn't contain relevant information, say so."""
        
        # Add conversation history
        for msg in self.conversation_history[-10:]:  # Last 10 messages
            messages.append(msg)
        
        # Add current message
        messages.append({
            "role": "user",
            "content": f"{system_message}\n\nUser: {user_message}"
        })
        
        return messages
    
    async def _chat_with_tools(self, messages: List[Dict]) -> str:
        """Chat with tool use capabilities."""
        tools = [
            {
                "name": "search_graph",
                "description": "Search the knowledge graph",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "add_knowledge",
                "description": "Add information to the knowledge graph",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Information to add"
                        }
                    },
                    "required": ["content"]
                }
            }
        ]
        
        response = await self.client.messages.create(
            model="claude-3-opus-20240229",
            messages=messages,
            tools=tools,
            max_tokens=1000
        )
        
        # Handle tool use
        if response.stop_reason == "tool_use":
            tool_use = response.content[-1]
            
            if tool_use.name == "search_graph":
                results = await self.graphiti.search(
                    tool_use.input["query"]
                )
                tool_result = self._format_context(results)
            
            elif tool_use.name == "add_knowledge":
                result = await self.graphiti.add_episode(
                    name=f"Claude_Knowledge_{datetime.now().timestamp()}",
                    episode_body=tool_use.input["content"],
                    source=EpisodeType.text,
                    source_description="Claude generated",
                    reference_time=datetime.now(timezone.utc)
                )
                tool_result = f"Added to graph: {result.episode.uuid}"
            
            # Continue conversation with tool result
            messages.append({
                "role": "assistant",
                "content": response.content
            })
            messages.append({
                "role": "user",
                "content": tool_result
            })
            
            # Get final response
            final_response = await self.client.messages.create(
                model="claude-3-opus-20240229",
                messages=messages,
                max_tokens=1000
            )
            
            return final_response.content[0].text
        
        return response.content[0].text
    
    async def _store_interaction(
        self,
        user_message: str,
        assistant_response: str
    ):
        """Store the interaction in Graphiti."""
        interaction = {
            "user": user_message,
            "assistant": assistant_response,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await self.graphiti.add_episode(
            name=f"Claude_Interaction_{datetime.now().timestamp()}",
            episode_body=json.dumps(interaction),
            source=EpisodeType.json,
            source_description="Claude conversation",
            reference_time=datetime.now(timezone.utc)
        )
        
        # Update conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": assistant_response
        })
```

---

## AutoGPT and Autonomous Agents

### Autonomous Agent with Graphiti

```python
class AutonomousGraphitiAgent:
    """Fully autonomous agent with Graphiti memory."""
    
    def __init__(self, graphiti, llm_client):
        self.graphiti = graphiti
        self.llm = llm_client
        self.goals = []
        self.completed_tasks = []
        self.memory_buffer = []
    
    async def set_goal(self, goal: str):
        """Set a high-level goal for the agent."""
        self.goals.append(goal)
        
        # Store goal in graph
        await self.graphiti.add_episode(
            name=f"Goal_{datetime.now().timestamp()}",
            episode_body=f"New goal: {goal}",
            source=EpisodeType.text,
            source_description="Agent goal",
            reference_time=datetime.now(timezone.utc)
        )
    
    async def run_autonomous_loop(
        self,
        max_iterations: int = 10
    ) -> List[Dict]:
        """Run autonomous loop to achieve goals."""
        results = []
        
        for iteration in range(max_iterations):
            if not self.goals:
                break
            
            current_goal = self.goals[0]
            
            # 1. Assess current state
            state = await self._assess_state(current_goal)
            
            # 2. Plan next action
            action = await self._plan_action(current_goal, state)
            
            # 3. Execute action
            result = await self._execute_action(action)
            
            # 4. Learn from result
            await self._learn_from_result(action, result)
            
            # 5. Check goal completion
            if await self._is_goal_complete(current_goal):
                self.goals.pop(0)
                self.completed_tasks.append(current_goal)
            
            results.append({
                "iteration": iteration,
                "goal": current_goal,
                "action": action,
                "result": result
            })
            
            # Prevent infinite loops
            if iteration > 0 and iteration % 5 == 0:
                if not await self._check_progress():
                    break
        
        return results
    
    async def _assess_state(self, goal: str) -> Dict:
        """Assess current state relative to goal."""
        # Search for relevant information
        context = await self.graphiti.search(
            query=f"current state progress {goal}",
            limit=10
        )
        
        # Get completed tasks
        completed = await self.graphiti.search(
            query="completed tasks actions",
            limit=5
        )
        
        return {
            "goal": goal,
            "context": [c.fact for c in context],
            "completed": [c.fact for c in completed],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def _plan_action(
        self,
        goal: str,
        state: Dict
    ) -> Dict:
        """Plan the next action."""
        prompt = f"""
        Goal: {goal}
        
        Current State:
        - Context: {json.dumps(state['context'])}
        - Completed: {json.dumps(state['completed'])}
        
        What is the next best action to take?
        Return as JSON with 'action', 'reason', and 'expected_outcome'.
        """
        
        response = await self.llm.generate_structured(
            prompt,
            response_model=ActionPlan
        )
        
        return response.dict()
    
    async def _execute_action(self, action: Dict) -> Dict:
        """Execute the planned action."""
        # This would integrate with actual tools/APIs
        # For demo, we'll simulate execution
        
        if "search" in action["action"].lower():
            results = await self.graphiti.search(
                action.get("search_query", action["action"])
            )
            return {
                "status": "success",
                "results": [r.fact for r in results[:3]]
            }
        
        elif "store" in action["action"].lower():
            result = await self.graphiti.add_episode(
                name=f"Action_{datetime.now().timestamp()}",
                episode_body=action["action"],
                source=EpisodeType.text,
                source_description="Agent action",
                reference_time=datetime.now(timezone.utc)
            )
            return {
                "status": "success",
                "stored": result.episode.uuid
            }
        
        else:
            # Generic action execution
            return {
                "status": "simulated",
                "action": action["action"]
            }
    
    async def _learn_from_result(
        self,
        action: Dict,
        result: Dict
    ):
        """Learn from action results."""
        learning = {
            "action": action,
            "result": result,
            "success": result.get("status") == "success",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Store learning in graph
        await self.graphiti.add_episode(
            name=f"Learning_{datetime.now().timestamp()}",
            episode_body=json.dumps(learning),
            source=EpisodeType.json,
            source_description="Agent learning",
            reference_time=datetime.now(timezone.utc)
        )
        
        # Update memory buffer
        self.memory_buffer.append(learning)
        
        # Consolidate memory if buffer is large
        if len(self.memory_buffer) > 10:
            await self._consolidate_memory()
    
    async def _consolidate_memory(self):
        """Consolidate short-term memory into long-term."""
        # Summarize memory buffer
        summary = {
            "actions_taken": len(self.memory_buffer),
            "successful": sum(1 for m in self.memory_buffer if m["success"]),
            "patterns": self._extract_patterns(self.memory_buffer)
        }
        
        # Store summary in graph
        await self.graphiti.add_episode(
            name=f"Memory_Consolidation_{datetime.now().timestamp()}",
            episode_body=json.dumps(summary),
            source=EpisodeType.json,
            source_description="Memory consolidation",
            reference_time=datetime.now(timezone.utc)
        )
        
        # Clear buffer
        self.memory_buffer = []
    
    async def _is_goal_complete(self, goal: str) -> bool:
        """Check if goal is complete."""
        # Search for completion indicators
        results = await self.graphiti.search(
            query=f"completed achieved {goal}",
            limit=5
        )
        
        # Simple heuristic - improve with LLM judgment
        for result in results:
            if "completed" in result.fact.lower() or "achieved" in result.fact.lower():
                return True
        
        return False
    
    async def _check_progress(self) -> bool:
        """Check if making progress."""
        # Compare recent actions to earlier ones
        recent = self.memory_buffer[-3:] if len(self.memory_buffer) >= 3 else []
        
        if not recent:
            return True
        
        # Check for repeated failures
        failures = sum(1 for m in recent if not m["success"])
        if failures >= 2:
            return False
        
        return True
```

---

## MCP Server Integration

### Graphiti MCP Server Implementation

```python
from mcp import Server, Tool, Resource
from mcp.types import TextContent, ImageContent
import asyncio

class GraphitiMCPServer:
    """MCP server for Graphiti."""
    
    def __init__(self, graphiti):
        self.graphiti = graphiti
        self.server = Server("graphiti-server")
        self._setup_tools()
        self._setup_resources()
    
    def _setup_tools(self):
        """Setup MCP tools."""
        
        @self.server.tool("search")
        async def search_graph(query: str, limit: int = 10) -> TextContent:
            """Search the knowledge graph."""
            results = await self.graphiti.search(query, limit=limit)
            
            if not results:
                return TextContent("No results found")
            
            response = "Search Results:\n"
            for i, result in enumerate(results, 1):
                response += f"{i}. {result.fact}\n"
            
            return TextContent(response)
        
        @self.server.tool("add_episode")
        async def add_episode(
            content: str,
            source: str = "mcp_client"
        ) -> TextContent:
            """Add new episode to the graph."""
            result = await self.graphiti.add_episode(
                name=f"MCP_{datetime.now().timestamp()}",
                episode_body=content,
                source=EpisodeType.text,
                source_description=source,
                reference_time=datetime.now(timezone.utc)
            )
            
            return TextContent(f"Added episode: {result.episode.uuid}")
        
        @self.server.tool("analyze")
        async def analyze_graph() -> TextContent:
            """Analyze graph statistics."""
            stats = await self._get_graph_stats()
            
            response = f"""Graph Statistics:
            - Nodes: {stats['nodes']}
            - Edges: {stats['edges']}
            - Communities: {stats['communities']}
            - Episodes: {stats['episodes']}
            """
            
            return TextContent(response)
    
    def _setup_resources(self):
        """Setup MCP resources."""
        
        @self.server.resource("graph/stats")
        async def get_stats() -> TextContent:
            """Get current graph statistics."""
            stats = await self._get_graph_stats()
            return TextContent(json.dumps(stats, indent=2))
        
        @self.server.resource("graph/schema")
        async def get_schema() -> TextContent:
            """Get graph schema information."""
            schema = await self._get_graph_schema()
            return TextContent(json.dumps(schema, indent=2))
    
    async def _get_graph_stats(self) -> Dict:
        """Get graph statistics."""
        stats = {}
        
        # Count nodes
        node_count = await self.graphiti.driver.execute(
            "MATCH (n) RETURN count(n) as count"
        )
        stats['nodes'] = node_count[0]['count']
        
        # Count edges
        edge_count = await self.graphiti.driver.execute(
            "MATCH ()-[r]->() RETURN count(r) as count"
        )
        stats['edges'] = edge_count[0]['count']
        
        # Count communities
        community_count = await self.graphiti.driver.execute(
            "MATCH (c:Community) RETURN count(c) as count"
        )
        stats['communities'] = community_count[0]['count']
        
        # Count episodes
        episode_count = await self.graphiti.driver.execute(
            "MATCH (e:Episode) RETURN count(e) as count"
        )
        stats['episodes'] = episode_count[0]['count']
        
        return stats
    
    async def _get_graph_schema(self) -> Dict:
        """Get graph schema."""
        schema = {
            "node_types": [],
            "edge_types": [],
            "indexes": []
        }
        
        # Get node labels
        labels = await self.graphiti.driver.execute(
            "CALL db.labels() YIELD label RETURN label"
        )
        schema['node_types'] = [l['label'] for l in labels]
        
        # Get relationship types
        rel_types = await self.graphiti.driver.execute(
            "CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"
        )
        schema['edge_types'] = [r['relationshipType'] for r in rel_types]
        
        # Get indexes
        indexes = await self.graphiti.driver.execute(
            "SHOW INDEXES YIELD name, type RETURN name, type"
        )
        schema['indexes'] = list(indexes)
        
        return schema
    
    async def run(self, host: str = "localhost", port: int = 3000):
        """Run the MCP server."""
        await self.server.run(host, port)

# Docker Compose for MCP Server
MCP_DOCKER_COMPOSE = """
version: '3.8'

services:
  graphiti-mcp:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=password
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - neo4j
    
  neo4j:
    image: neo4j:5-enterprise
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
    volumes:
      - neo4j_data:/data

volumes:
  neo4j_data:
"""
```

---

## REST API Integration

### FastAPI Server for Graphiti

```python
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn

class GraphitiAPI:
    """REST API for Graphiti."""
    
    def __init__(self, graphiti):
        self.graphiti = graphiti
        self.app = FastAPI(title="Graphiti API")
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.post("/episodes")
        async def add_episode(episode: EpisodeRequest):
            """Add a new episode."""
            result = await self.graphiti.add_episode(
                name=episode.name,
                episode_body=episode.content,
                source=episode.source,
                source_description=episode.description,
                reference_time=episode.reference_time or datetime.now(timezone.utc),
                group_id=episode.group_id
            )
            
            return {
                "episode_id": result.episode.uuid,
                "nodes_created": len(result.nodes),
                "edges_created": len(result.edges)
            }
        
        @self.app.get("/search")
        async def search(
            q: str,
            limit: int = 10,
            group_id: Optional[str] = None
        ):
            """Search the knowledge graph."""
            results = await self.graphiti.search(
                query=q,
                limit=limit,
                group_ids=[group_id] if group_id else None
            )
            
            return {
                "query": q,
                "count": len(results),
                "results": [
                    {
                        "fact": r.fact,
                        "confidence": getattr(r, 'score', 1.0),
                        "uuid": r.uuid
                    }
                    for r in results
                ]
            }
        
        @self.app.get("/nodes/{node_id}")
        async def get_node(node_id: str):
            """Get a specific node."""
            query = """
            MATCH (n:Entity {uuid: $uuid})
            RETURN n
            """
            
            result = await self.graphiti.driver.execute(
                query,
                {"uuid": node_id}
            )
            
            if not result:
                raise HTTPException(404, "Node not found")
            
            return result[0]['n']
        
        @self.app.get("/graph/stats")
        async def get_stats():
            """Get graph statistics."""
            stats = {}
            
            # Get various counts
            queries = {
                "nodes": "MATCH (n) RETURN count(n) as count",
                "edges": "MATCH ()-[r]->() RETURN count(r) as count",
                "episodes": "MATCH (e:Episode) RETURN count(e) as count",
                "communities": "MATCH (c:Community) RETURN count(c) as count"
            }
            
            for key, query in queries.items():
                result = await self.graphiti.driver.execute(query)
                stats[key] = result[0]['count']
            
            return stats
        
        @self.app.post("/bulk/episodes")
        async def bulk_add_episodes(
            episodes: List[EpisodeRequest],
            background_tasks: BackgroundTasks
        ):
            """Add multiple episodes in bulk."""
            task_id = str(uuid4())
            
            # Process in background
            background_tasks.add_task(
                self._process_bulk_episodes,
                episodes,
                task_id
            )
            
            return {
                "task_id": task_id,
                "episode_count": len(episodes),
                "status": "processing"
            }
        
        @self.app.get("/tasks/{task_id}")
        async def get_task_status(task_id: str):
            """Get bulk task status."""
            # This would check a task queue/database
            # For demo, return mock status
            return {
                "task_id": task_id,
                "status": "completed",
                "processed": 100,
                "failed": 0
            }
    
    async def _process_bulk_episodes(
        self,
        episodes: List[EpisodeRequest],
        task_id: str
    ):
        """Process episodes in bulk."""
        raw_episodes = []
        
        for ep in episodes:
            raw_episodes.append(
                RawEpisode(
                    name=ep.name,
                    content=ep.content,
                    source=ep.source,
                    source_description=ep.description,
                    reference_time=ep.reference_time or datetime.now(timezone.utc)
                )
            )
        
        # Process in bulk
        results = await self.graphiti.add_episodes_bulk(
            raw_episodes,
            group_id=episodes[0].group_id if episodes else None
        )
        
        # Store results (would go to database/cache)
        print(f"Task {task_id} completed: {len(results.episodes)} episodes processed")
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the API server."""
        uvicorn.run(self.app, host=host, port=port)

class EpisodeRequest(BaseModel):
    """Request model for episodes."""
    name: str
    content: str
    source: str = "api"
    description: Optional[str] = None
    reference_time: Optional[datetime] = None
    group_id: Optional[str] = None
```

---

## Event-Driven Architectures

### Kafka Integration

```python
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import json

class GraphitiKafkaIntegration:
    """Kafka integration for Graphiti."""
    
    def __init__(
        self,
        graphiti,
        kafka_bootstrap_servers: str = "localhost:9092"
    ):
        self.graphiti = graphiti
        self.bootstrap_servers = kafka_bootstrap_servers
        self.consumer = None
        self.producer = None
    
    async def start_consumer(
        self,
        topics: List[str],
        group_id: str = "graphiti-consumer"
    ):
        """Start consuming events from Kafka."""
        self.consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8'))
        )
        
        await self.consumer.start()
        
        try:
            async for msg in self.consumer:
                await self._process_message(msg)
        finally:
            await self.consumer.stop()
    
    async def _process_message(self, msg):
        """Process a Kafka message."""
        try:
            # Extract event data
            event = msg.value
            
            # Add to Graphiti based on event type
            if event.get("type") == "user_action":
                await self._process_user_action(event)
            
            elif event.get("type") == "system_event":
                await self._process_system_event(event)
            
            elif event.get("type") == "data_update":
                await self._process_data_update(event)
            
            else:
                # Generic processing
                await self.graphiti.add_episode(
                    name=f"Kafka_Event_{msg.timestamp}",
                    episode_body=json.dumps(event),
                    source=EpisodeType.json,
                    source_description=f"Kafka topic: {msg.topic}",
                    reference_time=datetime.fromtimestamp(msg.timestamp / 1000, tz=timezone.utc)
                )
            
            # Acknowledge message
            await self.consumer.commit()
            
        except Exception as e:
            logger.error(f"Error processing Kafka message: {e}")
    
    async def _process_user_action(self, event: Dict):
        """Process user action events."""
        await self.graphiti.add_episode(
            name=f"User_Action_{event.get('user_id')}",
            episode_body=f"User {event.get('user_id')} performed {event.get('action')}",
            source=EpisodeType.text,
            source_description="User action event",
            reference_time=datetime.fromisoformat(event.get('timestamp'))
        )
    
    async def start_producer(self):
        """Start Kafka producer for publishing events."""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        await self.producer.start()
    
    async def publish_graph_update(
        self,
        topic: str,
        update: Dict
    ):
        """Publish graph update events."""
        if not self.producer:
            await self.start_producer()
        
        event = {
            "type": "graph_update",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "update": update
        }
        
        await self.producer.send(topic, event)
    
    async def stop(self):
        """Stop Kafka connections."""
        if self.consumer:
            await self.consumer.stop()
        
        if self.producer:
            await self.producer.stop()
```

---

## Multi-Agent Systems

### Collaborative Multi-Agent System

```python
class GraphitiMultiAgentSystem:
    """Multi-agent system with shared Graphiti memory."""
    
    def __init__(self, graphiti):
        self.graphiti = graphiti
        self.agents = {}
        self.message_queue = asyncio.Queue()
    
    def register_agent(
        self,
        agent_id: str,
        agent_type: str,
        capabilities: List[str]
    ):
        """Register an agent in the system."""
        agent = {
            "id": agent_id,
            "type": agent_type,
            "capabilities": capabilities,
            "status": "active"
        }
        
        self.agents[agent_id] = agent
        
        # Store agent registration in graph
        asyncio.create_task(self._store_agent_registration(agent))
    
    async def _store_agent_registration(self, agent: Dict):
        """Store agent registration in graph."""
        await self.graphiti.add_episode(
            name=f"Agent_Registration_{agent['id']}",
            episode_body=json.dumps(agent),
            source=EpisodeType.json,
            source_description="Agent registration",
            reference_time=datetime.now(timezone.utc)
        )
    
    async def coordinate_task(
        self,
        task: str,
        required_capabilities: List[str]
    ) -> Dict:
        """Coordinate a task across multiple agents."""
        # Find capable agents
        capable_agents = self._find_capable_agents(required_capabilities)
        
        if not capable_agents:
            return {"error": "No capable agents found"}
        
        # Create task plan
        plan = await self._create_task_plan(task, capable_agents)
        
        # Execute plan
        results = await self._execute_plan(plan)
        
        # Store results in graph
        await self._store_task_results(task, results)
        
        return results
    
    def _find_capable_agents(
        self,
        required_capabilities: List[str]
    ) -> List[str]:
        """Find agents with required capabilities."""
        capable = []
        
        for agent_id, agent in self.agents.items():
            if agent["status"] == "active":
                if all(cap in agent["capabilities"] for cap in required_capabilities):
                    capable.append(agent_id)
        
        return capable
    
    async def _create_task_plan(
        self,
        task: str,
        agents: List[str]
    ) -> List[Dict]:
        """Create execution plan for task."""
        # Search for similar past tasks
        past_tasks = await self.graphiti.search(
            query=f"task plan execution {task}",
            limit=5
        )
        
        # Simple plan - could use LLM for complex planning
        plan = []
        
        for i, agent_id in enumerate(agents):
            plan.append({
                "step": i + 1,
                "agent": agent_id,
                "action": f"Process part {i+1} of: {task}",
                "dependencies": [i-1] if i > 0 else []
            })
        
        return plan
    
    async def _execute_plan(self, plan: List[Dict]) -> Dict:
        """Execute task plan across agents."""
        results = {
            "steps": [],
            "success": True
        }
        
        for step in plan:
            # Check dependencies
            if step["dependencies"]:
                for dep in step["dependencies"]:
                    if not results["steps"][dep].get("success"):
                        results["success"] = False
                        break
            
            if not results["success"]:
                break
            
            # Execute step
            agent_result = await self._execute_agent_step(
                step["agent"],
                step["action"]
            )
            
            results["steps"].append({
                "step": step["step"],
                "agent": step["agent"],
                "result": agent_result,
                "success": agent_result.get("status") == "success"
            })
        
        return results
    
    async def _execute_agent_step(
        self,
        agent_id: str,
        action: str
    ) -> Dict:
        """Execute a single agent step."""
        # This would call the actual agent
        # For demo, simulate execution
        
        # Agent searches its memory
        context = await self.graphiti.search(
            query=action,
            limit=5
        )
        
        # Agent processes action
        result = {
            "status": "success",
            "agent": agent_id,
            "action": action,
            "context_used": len(context),
            "output": f"Processed: {action}"
        }
        
        # Store agent action in graph
        await self.graphiti.add_episode(
            name=f"Agent_Action_{agent_id}_{datetime.now().timestamp()}",
            episode_body=json.dumps(result),
            source=EpisodeType.json,
            source_description=f"Agent {agent_id} action",
            reference_time=datetime.now(timezone.utc)
        )
        
        return result
    
    async def _store_task_results(
        self,
        task: str,
        results: Dict
    ):
        """Store task results in graph."""
        await self.graphiti.add_episode(
            name=f"Task_Results_{datetime.now().timestamp()}",
            episode_body=json.dumps({
                "task": task,
                "results": results,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }),
            source=EpisodeType.json,
            source_description="Multi-agent task results",
            reference_time=datetime.now(timezone.utc)
        )
    
    async def broadcast_message(
        self,
        sender_id: str,
        message: str,
        target_agents: List[str] = None
    ):
        """Broadcast message to agents."""
        msg = {
            "sender": sender_id,
            "message": message,
            "targets": target_agents or list(self.agents.keys()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Store message in graph
        await self.graphiti.add_episode(
            name=f"Agent_Message_{sender_id}_{datetime.now().timestamp()}",
            episode_body=json.dumps(msg),
            source=EpisodeType.json,
            source_description="Inter-agent communication",
            reference_time=datetime.now(timezone.utc)
        )
        
        # Add to message queue
        await self.message_queue.put(msg)
    
    async def process_messages(self):
        """Process inter-agent messages."""
        while True:
            msg = await self.message_queue.get()
            
            for target in msg["targets"]:
                if target in self.agents:
                    # Process message for target agent
                    await self._deliver_message(target, msg)
    
    async def _deliver_message(
        self,
        agent_id: str,
        message: Dict
    ):
        """Deliver message to specific agent."""
        # This would actually deliver to the agent
        # For demo, just log delivery
        logger.info(f"Delivered message to {agent_id}: {message['message']}")
```

---

## Next Steps

This integration patterns guide provides comprehensive examples for connecting Graphiti with various AI frameworks. Continue with:

- **[06_performance_tuning.md](./06_performance_tuning.md)** - Optimization strategies
- **[07_api_reference.md](./07_api_reference.md)** - Complete API documentation
- **[08_benchmarks_and_evaluation.md](./08_benchmarks_and_evaluation.md)** - Performance metrics
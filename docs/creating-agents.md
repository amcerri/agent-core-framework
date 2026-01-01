# Creating Agents

This guide explains how to create custom agents for the Agent Core Framework.

## Agent Contract

Agents are decision-making units that:

- Interpret inputs within execution context
- Decide which actions to take
- Return structured outputs with requested actions
- Do not perform I/O directly (use tools via runtime)
- Do not orchestrate other agents directly

Contract: [agent_core/contracts/agent.py](../agent_core/contracts/agent.py)

## Base Agent Class

The framework provides `BaseAgent` as a foundation for implementing agents:

```python
from agent_core.agents.base import BaseAgent
from agent_core.contracts.agent import AgentInput, AgentResult
from agent_core.contracts.execution_context import ExecutionContext

class MyAgent(BaseAgent):
    @property
    def agent_id(self) -> str:
        return "my_agent"
    
    @property
    def agent_version(self) -> str:
        return "1.0.0"
    
    @property
    def capabilities(self) -> list[str]:
        return ["query", "analysis"]
    
    def run(self, input_data: AgentInput, context: ExecutionContext) -> AgentResult:
        # Process input and decide actions
        # Return structured result with actions
        pass
```

Base class: [agent_core/agents/base.py](../agent_core/agents/base.py)

## Agent Implementation Example

```python
from agent_core.agents.base import BaseAgent
from agent_core.contracts.agent import AgentInput, AgentResult
from agent_core.contracts.execution_context import ExecutionContext

class QueryAgent(BaseAgent):
    @property
    def agent_id(self) -> str:
        return "query_agent"
    
    @property
    def agent_version(self) -> str:
        return "1.0.0"
    
    @property
    def capabilities(self) -> list[str]:
        return ["query", "search"]
    
    def run(self, input_data: AgentInput, context: ExecutionContext) -> AgentResult:
        query = input_data.payload.get("query", "")
        
        # Decide actions based on input
        actions = []
        if query:
            actions.append({
                "type": "tool",
                "tool_id": "search_tool",
                "payload": {"query": query}
            })
        
        return AgentResult(
            status="success",
            output={"query": query},
            actions=actions,
            errors=[],
            metrics={}
        )
```

## Agent Registration

Register agents with the runtime:

```python
from agent_core.runtime import Runtime
from agent_core.configuration.loader import load_config

config = load_config()
runtime = Runtime(config=config)

# Register agent
agent = QueryAgent()
runtime.register_agent(agent)
```

## Agent Responsibilities

Agents should:

- ✅ Process input and make decisions
- ✅ Return structured results with actions
- ✅ Declare capabilities for routing
- ✅ Respect execution context (permissions, budget, locale)

Agents should not:

- ❌ Perform I/O directly (use tools via runtime)
- ❌ Orchestrate other agents directly
- ❌ Manage retries or policies (handled by runtime)
- ❌ Mutate shared state directly (use services via runtime)

## Related Documentation

- [Overview](./overview.md) - Framework introduction
- [Architecture](./architecture.md) - System architecture
- [Runtime API](./runtime-api.md) - Runtime execution
- [Contracts](./contracts.md) - Agent contract details

---

Back to [docs index](./README.md)  
Back to [repository root](../README.md)


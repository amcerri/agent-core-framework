# Runtime API

This document describes the Runtime class and its methods for executing agents and managing components.

## Runtime Class

The `Runtime` class is the central control plane for the framework. It manages execution lifecycle, agent routing, and action execution.

Implementation: [agent_core/runtime/runtime.py](../agent_core/runtime/runtime.py)

## Initialization

```python
from agent_core.runtime import Runtime
from agent_core.configuration.loader import load_config
from agent_core.observability.noop import NoOpObservabilitySink

config = load_config()
runtime = Runtime(
    config=config,
    agents={},      # Optional: dict of agent_id -> Agent
    tools={},       # Optional: dict of tool_id -> Tool
    services={},    # Optional: dict of service_id -> Service
    observability_sink=None  # Optional: ObservabilitySink (defaults to NoOp)
)
```

## Component Registration

### Register Agent

```python
from agent_core.agents.base import BaseAgent

class MyAgent(BaseAgent):
    # ... implementation

agent = MyAgent()
runtime.register_agent(agent)
```

### Register Tool

```python
from agent_core.tools.base import BaseTool

class MyTool(BaseTool):
    # ... implementation

tool = MyTool()
runtime.register_tool(tool)
```

### Register Service

```python
from agent_core.services.base import BaseService

class MyService(BaseService):
    # ... implementation

service = MyService()
runtime.register_service(service)
```

## Agent Execution

Execute an agent synchronously:

```python
result = runtime.execute_agent(
    agent_id="my_agent",           # Optional: explicit agent ID
    input_data={"query": "test"},   # Optional: input data
    initiator="user:test",          # Optional: caller identity
    required_capabilities=["query"], # Optional: required capabilities
    context=None                    # Optional: ExecutionContext
)
```

The method returns an `AgentResult` with:

- `status`: Execution status ("success", "failure")
- `output`: Agent output data
- `actions`: List of requested actions
- `errors`: List of errors
- `metrics`: Execution metrics

## Execution Context

The runtime creates an `ExecutionContext` if not provided:

```python
from agent_core.runtime.execution_context import create_execution_context

context = create_execution_context(
    initiator="user:test",
    permissions={"read": True},
    budget={"time_limit": 60},
    locale="en-US"
)

result = runtime.execute_agent(
    agent_id="my_agent",
    input_data={"query": "test"},
    context=context
)
```

## Action Execution

Actions requested by agents are automatically executed by the runtime with:

- Permission evaluation
- Policy enforcement
- Budget checking
- Audit event emission

Actions are executed via the `ActionExecutor`:

```python
# Actions are automatically executed when returned by agents
# No manual action execution needed
```

Implementation: [agent_core/runtime/action_execution.py](../agent_core/runtime/action_execution.py)

## Error Handling

Errors are automatically classified and handled:

```python
from agent_core.runtime.error_classification import ErrorClassifier

# Errors are automatically classified during execution
# Retry policies are applied for retryable errors
```

Implementation: [agent_core/runtime/error_classification.py](../agent_core/runtime/error_classification.py)

## Lifecycle Management

The runtime manages execution lifecycle:

- `INITIALIZING`: Runtime initialization
- `READY`: Ready for execution
- `EXECUTING`: Agent execution in progress
- `COMPLETED`: Execution completed successfully
- `FAILED`: Execution failed
- `TERMINATED`: Execution terminated

Access lifecycle events:

```python
events = runtime.get_lifecycle_events()
```

Implementation: [agent_core/runtime/lifecycle.py](../agent_core/runtime/lifecycle.py)

## Related Documentation

- [Overview](./overview.md) - Framework introduction
- [Architecture](./architecture.md) - System architecture
- [Creating Agents](./creating-agents.md) - Agent implementation
- [Configuration](./configuration.md) - Runtime configuration

---

Back to [docs index](./README.md)  
Back to [repository root](../README.md)


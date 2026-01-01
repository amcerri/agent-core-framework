# Orchestration and Flows

This guide explains how to define and execute flows in the Agent Core Framework.

## Flow Overview

Flows are declarative orchestration graphs that define:

- Nodes: Agent, tool, or condition nodes
- Transitions: Explicit paths between nodes
- State: Data passed between nodes
- Entrypoint: Starting node

Implementation: [agent_core/orchestration](../agent_core/orchestration/)

## Flow Definition (YAML)

Flows are defined in YAML format:

```yaml
flows:
  my_flow:
    flow_id: "my_flow"
    version: "1.0.0"
    entrypoint: "start"
    nodes:
      start:
        type: "agent"
        agent_id: "query_agent"
        input:
          query: "{{input.query}}"
      process:
        type: "tool"
        tool_id: "process_tool"
        payload:
          data: "{{node_start_result}}"
      check:
        type: "condition"
        condition:
          status: "success"
    transitions:
      - from: "start"
        to: "process"
        condition:
          status: "success"
      - from: "process"
        to: "check"
      - from: "check"
        to: "end"
        condition:
          result: true
```

## Loading Flows

Load flows from YAML:

```python
from agent_core.orchestration.yaml_loader import load_flow_from_yaml

flow_config = load_flow_from_yaml("flows/my_flow.yaml")
```

Or from dictionary:

```python
from agent_core.orchestration.yaml_loader import load_flow_from_dict

flow_dict = {
    "flow_id": "my_flow",
    "version": "1.0.0",
    "entrypoint": "start",
    "nodes": {...},
    "transitions": [...]
}
flow_config = load_flow_from_dict(flow_dict)
```

Implementation: [agent_core/orchestration/yaml_loader.py](../agent_core/orchestration/yaml_loader.py)

## Flow Execution

Execute flows using a flow engine:

```python
from agent_core.orchestration import SimpleFlowEngine
from agent_core.runtime.execution_context import create_execution_context
from agent_core.configuration.schemas import RuntimeConfig

# Create execution context
context = create_execution_context(
    initiator="user:test",
    runtime_config=RuntimeConfig(runtime_id="test", concurrency=1)
)

# Create flow engine
engine = SimpleFlowEngine(
    flow=flow_config,
    context=context,
    runtime=runtime
)

# Execute flow
result = engine.execute(input_data={"query": "example"})
```

Implementation: [agent_core/orchestration/flow_engine.py](../agent_core/orchestration/flow_engine.py)

## Node Types

### Agent Nodes

Execute an agent:

```yaml
agent_node:
  type: "agent"
  agent_id: "my_agent"
  input:
    query: "{{input.query}}"
  input_from_state: ["previous_result"]
```

### Tool Nodes

Execute a tool:

```yaml
tool_node:
  type: "tool"
  tool_id: "my_tool"
  payload:
    data: "{{node_agent_node_result}}"
  input_from_state: ["state_key"]
```

### Condition Nodes

Evaluate conditions:

```yaml
condition_node:
  type: "condition"
  condition:
    status: "success"
```

## LangGraph Integration

For advanced orchestration, use LangGraph backend:

```python
from agent_core.orchestration import LangGraphFlowEngine

engine = LangGraphFlowEngine(
    flow=flow_config,
    context=context,
    runtime=runtime
)

result = engine.execute(input_data={"query": "example"})
```

Implementation: [agent_core/orchestration/langgraph_engine.py](../agent_core/orchestration/langgraph_engine.py)

## Flow State

Flow state is managed automatically:

- `current_node`: Current node identifier
- `state_data`: Data passed between nodes
- `history`: Execution history

Access state:

```python
state = engine.get_state()
print(state.current_node)
print(state.state_data)
print(state.history)
```

Implementation: [agent_core/orchestration/state.py](../agent_core/orchestration/state.py)

## Related Documentation

- [Overview](./overview.md) - Framework introduction
- [Architecture](./architecture.md) - System architecture
- [Configuration](./configuration.md) - Flow configuration
- [Creating Agents](./creating-agents.md) - Agent implementation

---

Back to [docs index](./README.md)  
Back to [repository root](../README.md)


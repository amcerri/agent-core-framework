# Contracts

This document describes the core contracts and interfaces that govern all interactions within the Agent Core Framework.

## Contract Overview

Contracts define the formal interfaces and data schemas that ensure compatibility and correctness. All components must conform to these contracts.

## Agent Contract

Agents implement the `Agent` protocol:

```python
class Agent(Protocol):
    agent_id: str
    agent_version: str
    capabilities: list[str]
    
    def run(
        self,
        input_data: AgentInput,
        context: ExecutionContext
    ) -> AgentResult:
        ...
```

Contract: [agent_core/contracts/agent.py](../agent_core/contracts/agent.py)

### AgentInput

```python
class AgentInput(BaseModel):
    payload: dict[str, Any]
```

### AgentResult

```python
class AgentResult(BaseModel):
    status: str
    output: dict[str, Any]
    actions: list[dict[str, Any]]
    errors: list[dict[str, Any]]
    metrics: dict[str, Any]
```

## Tool Contract

Tools implement the `Tool` protocol:

```python
class Tool(Protocol):
    tool_id: str
    tool_version: str
    permissions_required: list[str]
    
    def execute(
        self,
        input_data: ToolInput,
        context: ExecutionContext
    ) -> ToolResult:
        ...
```

Contract: [agent_core/contracts/tool.py](../agent_core/contracts/tool.py)

### ToolInput

```python
class ToolInput(BaseModel):
    payload: dict[str, Any]
```

### ToolResult

```python
class ToolResult(BaseModel):
    status: str
    output: dict[str, Any]
    errors: list[Error]
    metrics: dict[str, Any]
```

## Service Contract

Services implement the `Service` protocol:

```python
class Service(Protocol):
    service_id: str
    service_version: str
    capabilities: list[str]
    
    def check_permission(
        self,
        action: str,
        context: ExecutionContext
    ) -> bool:
        ...
```

Contract: [agent_core/contracts/service.py](../agent_core/contracts/service.py)

## Flow Contract

Flows implement the `Flow` protocol:

```python
class Flow(Protocol):
    flow_id: str
    flow_version: str
    entrypoint: str
    nodes: dict[str, dict[str, Any]]
    transitions: list[dict[str, Any]]
```

Contract: [agent_core/contracts/flow.py](../agent_core/contracts/flow.py)

### FlowState

```python
class FlowState(BaseModel):
    current_node: str
    state_data: dict[str, Any]
    history: list[dict[str, Any]]
```

## ExecutionContext Contract

The ExecutionContext carries cross-cutting concerns:

```python
class ExecutionContext(BaseModel):
    run_id: str
    correlation_id: str
    initiator: str
    permissions: dict[str, Any]
    budget: dict[str, Any]
    locale: str
    observability: dict[str, Any]
    metadata: dict[str, Any]
```

Contract: [agent_core/contracts/execution_context.py](../agent_core/contracts/execution_context.py)

## Error Contract

Errors are structured objects:

```python
class Error(BaseModel):
    error_id: str
    error_type: ErrorCategory
    message: str
    severity: ErrorSeverity
    retryable: bool
    source: str
    metadata: dict[str, Any]
```

Contract: [agent_core/contracts/errors.py](../agent_core/contracts/errors.py)

### ErrorCategory

```python
class ErrorCategory(str, Enum):
    VALIDATION_ERROR = "validation_error"
    PERMISSION_ERROR = "permission_error"
    BUDGET_EXCEEDED = "budget_exceeded"
    TIMEOUT = "timeout"
    EXECUTION_FAILURE = "execution_failure"
    DEPENDENCY_FAILURE = "dependency_failure"
```

## Observability Contracts

### CorrelationFields

```python
class CorrelationFields(BaseModel):
    run_id: str
    correlation_id: str
    component_type: ComponentType
    component_id: str
    component_version: str
    timestamp: str
```

Contract: [agent_core/contracts/observability.py](../agent_core/contracts/observability.py)

## Contract Compliance

All implementations must:

- Conform to protocol interfaces
- Validate inputs and outputs
- Emit required observability signals
- Respect governance constraints
- Handle errors according to error model

## Related Documentation

- [Architecture](./architecture.md) - System architecture
- [Creating Agents](./creating-agents.md) - Agent implementation
- [Creating Tools](./creating-tools.md) - Tool implementation
- [Creating Services](./creating-services.md) - Service implementation

---

Back to [docs index](./README.md)  
Back to [repository root](../README.md)


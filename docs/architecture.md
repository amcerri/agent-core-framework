# Architecture Overview

This document provides a detailed overview of the Agent Core Framework architecture, design patterns, and system boundaries.

## System Architecture

The framework follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    Runtime (Control Plane)              │
│  - Lifecycle Management                                 │
│  - Agent Routing                                        │
│  - Action Execution                                     │
│  - Observability Coordination                           │
└─────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐  ┌─────────▼─────────┐  ┌──────▼──────┐
│   Agents     │  │   Orchestration    │  │ Governance  │
│ (Decision)   │  │   (Flows)         │  │ (Security)  │
└───────┬──────┘  └─────────┬─────────┘  └──────┬──────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐  ┌─────────▼─────────┐  ┌──────▼──────┐
│    Tools     │  │    Services       │  │Observability│
│ (Side Effects)│ │ (Shared State)     │  │ (Signals)   │
└──────────────┘  └────────────────────┘  └─────────────┘
```

## Layer Descriptions

### Runtime Layer

The runtime is the central control plane that orchestrates all execution. It:

- Manages execution lifecycle (initialization → ready → executing → completed/failed → terminated)
- Routes agent selection based on capabilities or explicit IDs
- Executes actions (tool/service invocations) with governance enforcement
- Coordinates observability signal emission
- Enforces budgets and policies

Implementation: [agent_core/runtime](../agent_core/runtime/)

### Agent Layer

Agents are decision-making units that:

- Interpret inputs within execution context
- Decide which actions to take
- Return structured outputs with requested actions
- Do not perform I/O directly (must use tools via runtime)
- Do not orchestrate other agents directly

Base class: [agent_core/agents/base.py](../agent_core/agents/base.py)  
Contract: [agent_core/contracts/agent.py](../agent_core/contracts/agent.py)

### Tool Layer

Tools are execution units that:

- Perform a single, well-defined capability
- Encapsulate side effects or external interactions
- Validate inputs and outputs
- Declare required permissions
- Are stateless by default

Base class: [agent_core/tools/base.py](../agent_core/tools/base.py)  
Contract: [agent_core/contracts/tool.py](../agent_core/contracts/tool.py)

### Service Layer

Services provide governed access to shared capabilities:

- Own persistent or shared state
- Enforce access control and auditing
- Abstract vendor-specific implementations
- Provide governed access to resources

Base class: [agent_core/services/base.py](../agent_core/services/base.py)  
Contract: [agent_core/contracts/service.py](../agent_core/contracts/service.py)

### Orchestration Layer

Orchestration is expressed via declarative flows:

- YAML-based flow definitions
- Explicit node types (agent, tool, condition)
- Deterministic transitions
- Optional LangGraph backend for advanced orchestration

Implementation: [agent_core/orchestration](../agent_core/orchestration/)

### Governance Layer

Governance ensures controlled execution:

- **Permissions**: Evaluated before tool/service execution
- **Policies**: Allow, deny, or require approval for actions
- **Budgets**: Track and enforce time, call, and cost limits
- **Audit**: Emit events for side-effecting actions

Implementation: [agent_core/governance](../agent_core/governance/)

### Observability Layer

Observability provides visibility into execution:

- **Logging**: Structured logs with correlation fields
- **Tracing**: Distributed traces with spans
- **Metrics**: Latency, errors, and resource usage
- **Audit**: Security-relevant event emission

Implementation: [agent_core/observability](../agent_core/observability/)

## Execution Context

The ExecutionContext carries all cross-cutting concerns:

- `run_id`: Unique identifier for execution lifecycle
- `correlation_id`: Correlation across logs, traces, metrics
- `initiator`: Identity of caller
- `permissions`: Effective permission set
- `budget`: Time, call, and cost limits
- `locale`: Language and regional preferences
- `observability`: Trace and logging metadata
- `metadata`: Free-form contextual data

The context is immutable and propagated throughout execution.

Contract: [agent_core/contracts/execution_context.py](../agent_core/contracts/execution_context.py)

## Error Model

Errors are first-class structured objects (not exceptions):

- `error_id`: Unique identifier
- `error_type`: Category (validation_error, permission_error, budget_exceeded, timeout, execution_failure, dependency_failure)
- `message`: Human-readable message
- `severity`: Level (low, medium, high, critical)
- `retryable`: Whether error can be retried
- `source`: Component that generated error
- `metadata`: Additional context

Contract: [agent_core/contracts/errors.py](../agent_core/contracts/errors.py)

## Configuration

Configuration is YAML-based and validated:

- Default location: `./config/agent-core.yaml`
- Environment variable: `AGENT_CORE_CONFIG`
- Supports environment-specific overrides
- All configuration validated at startup

Implementation: [agent_core/configuration](../agent_core/configuration/)

## Design Principles

1. **Vendor Neutrality**: Core framework is provider-agnostic
2. **Explicit Contracts**: All interactions governed by well-defined contracts
3. **Governance First**: Built-in security and policy enforcement
4. **Observability**: First-class structured signals
5. **Deterministic Execution**: Reproducible behavior
6. **Separation of Concerns**: Clear boundaries between layers

## Related Documentation

- [Overview](./overview.md) - Framework introduction
- [Configuration](./configuration.md) - Configuration reference
- [Runtime API](./runtime-api.md) - Runtime class details
- [Contracts](./contracts.md) - Contract definitions

---

Back to [docs index](./README.md)  
Back to [repository root](../README.md)


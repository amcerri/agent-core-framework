# Agent Core Framework Overview

## Purpose

The Agent Core Framework is a foundational, vendor-agnostic framework for building multi-agent systems. It provides a stable, extensible core with explicit orchestration, governance, and observability capabilities.

## Key Design Principles

- **Vendor Neutrality**: Core framework is provider-agnostic; vendor-specific implementations live in adapters
- **Explicit Contracts**: All interactions are governed by well-defined contracts and schemas
- **Governance First**: Built-in support for permissions, policies, budgets, and audit enforcement
- **Observability**: First-class structured logging, tracing, metrics, and audit events
- **Deterministic Execution**: Reproducible behavior with explicit orchestration and routing
- **Separation of Concerns**: Clear boundaries between agents (decision-making), tools (side effects), services (shared state), and orchestration

## Architecture Overview

The framework is organized into several key layers:

- **Runtime**: Execution control plane managing lifecycle, routing, and orchestration
- **Contracts**: Formal interfaces and schemas for agents, tools, services, and flows
- **Orchestration**: Declarative flow engine with YAML support and optional LangGraph integration
- **Governance**: Permission evaluation, policy enforcement, budget tracking, and audit emission
- **Observability**: Structured logging, tracing, metrics, and audit event emission
- **Configuration**: YAML-based configuration with validation and environment overrides

## Core Components

### Runtime

The runtime is the central control plane that:
- Manages execution lifecycle (initialization, execution, completion, termination)
- Routes agent selection based on capabilities and configuration
- Executes actions (tool/service invocations) with governance enforcement
- Emits observability signals throughout execution

Implementation: [agent_core/runtime](../agent_core/runtime/)

### Agents

Agents are decision-making units that:
- Interpret inputs within a given context
- Decide which actions to take
- Return structured outputs with requested actions
- Do not perform I/O directly (use tools via runtime)
- Do not orchestrate other agents directly

Base class: [agent_core/agents/base.py](../agent_core/agents/base.py)

### Tools

Tools are execution units that:
- Perform a single, well-defined capability
- Encapsulate side effects or external interactions
- Validate inputs and outputs
- Declare required permissions
- Are stateless by default

Base class: [agent_core/tools/base.py](../agent_core/tools/base.py)

### Services

Services provide governed access to shared capabilities:
- Own persistent or shared state
- Enforce access control and auditing
- Abstract vendor-specific implementations
- Provide governed access to resources

Base class: [agent_core/services/base.py](../agent_core/services/base.py)

### Orchestration

Orchestration is expressed via declarative flows:
- YAML-based flow definitions
- Explicit node types (agent, tool, condition)
- Deterministic transitions
- Optional LangGraph backend for advanced orchestration

Implementation: [agent_core/orchestration](../agent_core/orchestration/)

### Governance

Governance ensures controlled execution:
- Permission evaluation before execution
- Policy enforcement (allow, deny, require approval)
- Budget tracking and enforcement (time, calls, cost)
- Audit event emission for side-effecting actions

Implementation: [agent_core/governance](../agent_core/governance/)

### Observability

Observability provides visibility into execution:
- Structured logging with correlation fields
- Distributed tracing with spans
- Metrics for latency, errors, and resource usage
- Audit events for security-relevant actions

Implementation: [agent_core/observability](../agent_core/observability/)

## Execution Flow

1. **Initialization**: Runtime loads configuration and registers components
2. **Context Creation**: Execution context is created with permissions, budget, and observability metadata
3. **Agent Selection**: Router selects appropriate agent based on capabilities or explicit ID
4. **Agent Execution**: Agent processes input and returns actions
5. **Action Execution**: Runtime executes requested actions with governance enforcement
6. **Observability**: Signals are emitted throughout execution
7. **Completion**: Lifecycle transitions to completed or failed state

## Error Handling

Errors are first-class structured objects:
- All exceptions are classified into standard error categories
- Retry policies respect idempotency and budget constraints
- Non-retryable errors (validation, permission, budget) terminate execution
- Retryable errors (timeout, execution failure) may trigger retries

Implementation: [agent_core/runtime/error_classification.py](../agent_core/runtime/error_classification.py), [agent_core/runtime/retry_policy.py](../agent_core/runtime/retry_policy.py)

## Configuration

Configuration is YAML-based and validated:
- Default location: `./config/agent-core.yaml`
- Environment variable override: `AGENT_CORE_CONFIG`
- Supports environment-specific overrides
- All configuration is validated at startup

Implementation: [agent_core/configuration](../agent_core/configuration/)

## Getting Started

1. Install the framework (see [Installation](./installation.md))
2. Create a configuration file
3. Implement your agents, tools, and services
4. Register components with the runtime
5. Execute agents via the runtime

For detailed guides, see:
- [Creating Agents](./creating-agents.md)
- [Creating Tools](./creating-tools.md)
- [Creating Services](./creating-services.md)
- [Orchestration and Flows](./flows.md)

## Related Documentation

- [Architecture Overview](./architecture.md) - Detailed system architecture
- [Configuration](./configuration.md) - Configuration system reference
- [Runtime API](./runtime-api.md) - Runtime class and methods
- [Contracts](./contracts.md) - Core contracts and interfaces

---

Back to [docs index](./README.md)  
Back to [repository root](../README.md)


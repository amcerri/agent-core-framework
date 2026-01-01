# Agent Core Framework

A foundational, vendor-agnostic framework for building multi-agent systems with explicit orchestration, governance, and observability.

---

## About

**Agent Core Framework** is an open-source framework designed to serve as a foundational layer for building multi-agent systems. It provides a stable, extensible core with clear separation of concerns and built-in support for governance, observability, and policy enforcement.

Key features:

- **Core Runtime**: Execution control plane with lifecycle management and routing
- **Agent/Tool/Service Abstractions**: Base classes and contracts for implementing capabilities
- **Orchestration**: Declarative flow engine with YAML support and optional LangGraph integration
- **Governance**: Permissions, policies, budgets, and audit enforcement
- **Observability**: Structured logging, tracing, metrics, and audit events
- **Error Handling**: Structured error classification and retry policies respecting idempotency and budgets
- **Configuration**: YAML-based configuration with validation and environment overrides

---

## Table of Contents

1. Features  
2. Project Status  
3. Getting Started  
4. Usage  
5. Configuration  
6. Documentation  
7. Contributing  
8. Roadmap  
9. License  
10. Contact  

---

## Features

- **Runtime**: Synchronous execution with lifecycle management, agent routing, and action execution
- **Agents**: Base abstractions for decision-making units with capability-based routing
- **Tools**: Base abstractions for side-effecting operations with permission enforcement
- **Services**: Base abstractions for governed access to shared state and resources
- **Orchestration**: Flow engine with YAML support and optional LangGraph backend
- **Scheduling**: Priority-based scheduling with thread-based concurrency limits
- **Error Handling**: Structured error classification and retry policies
- **Governance**: Permissions, policies, budgets, and audit event emission
- **Observability**: Structured logging, tracing, metrics, and audit events
- **Configuration**: YAML-based configuration with validation and environment overrides

---

## Project Status

| Area | Status |
| --- | --- |
| Core runtime | ✅ Implemented |
| Agent interfaces | ✅ Implemented |
| Tool registry | ✅ Implemented |
| Service abstractions | ✅ Implemented |
| Orchestration engine | ✅ Implemented |
| Error handling model | ✅ Implemented |
| Configuration system | ✅ Implemented |
| Scheduling | ✅ Implemented |
| Tests | ✅ Complete |
| Examples | ✅ Implemented |
| Docker | ✅ Implemented |
| Developer Tooling | ✅ Implemented |

---

## Getting Started

### Requirements

- Python >= 3.10
- Poetry (recommended) or pip for dependency management

### Installation

Install from source:

```bash
git clone https://github.com/amcerri/agent-core-framework.git
cd agent-core-framework
poetry install
```

Or install with pip:

```bash
pip install -e .
```

For LangGraph support (optional):

```bash
poetry install --extras langgraph
```

**Using Make (Recommended for Development):**

```bash
# Install dependencies
make install

# Install with LangGraph support
make install-langgraph

# Verify installation
make verify

# See all available commands
make help
```

### Docker Installation (Optional)

For a reproducible development environment:

```bash
# Build image
docker build -t agent-core-framework .

# Run with mounted configuration
docker run -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/examples:/app/examples:ro \
  agent-core-framework \
  python examples/minimal_example.py
```

Or use docker-compose:

```bash
docker-compose up
```

**Using Make:**

```bash
# Build Docker image
make docker-build

# Run example in Docker
make docker-run

# Start with docker-compose
make docker-compose-up
```

See [Docker Usage](./docs/docker.md) for detailed instructions.

---

## Usage

Basic example:

```python
from agent_core.configuration.loader import load_config
from agent_core.runtime import Runtime

# Load configuration
config = load_config()

# Initialize runtime
runtime = Runtime(
    config=config,
    agents={},  # Register your agents
    tools={},   # Register your tools
    services={} # Register your services
)

# Execute an agent
result = runtime.execute_agent(
    agent_id="my_agent",
    input_data={"query": "example"}
)
```

For more examples and detailed usage, see the [documentation](./docs/README.md).

---

## Configuration

Configuration is defined using YAML files. By default, the framework looks for `./config/agent-core.yaml` or uses the `AGENT_CORE_CONFIG` environment variable.

Configuration includes:

- Runtime settings (concurrency, timeouts, locale)
- Agent definitions and capabilities
- Tool definitions and permissions
- Service definitions and access policies
- Flow definitions (orchestration graphs)
- Governance settings (permissions, budgets, policies)
- Observability settings (exporters, sampling, redaction)

See [Configuration](./docs/configuration.md) for details.

---

## Documentation

Public-facing documentation lives in the `docs/` directory.

Start here:

- [`docs/README.md`](./docs/README.md)

For detailed guides and examples, see the [documentation index](./docs/README.md).

---

---

## Roadmap

Completed:

- ✅ Core runtime implementation
- ✅ Agent, Tool, and Service interfaces
- ✅ Orchestration engine with YAML support
- ✅ Error classification and retry policies
- ✅ Governance (permissions, policies, budgets)
- ✅ Observability integration
- ✅ Configuration system
- ✅ Scheduling with priority and concurrency

Planned:

- 🔄 Example projects and usage guides
- 🔄 Additional adapters and integrations
- 🔄 Enhanced observability exporters
- 🔄 Performance optimizations

---

## License

This project is currently private and not open for public use. License terms will be determined once the framework is fully validated and production-ready.

---

## Contact

Maintainer: [Artur M.](https://github.com/amcerri)  
Repository: [`https://github.com/amcerri/agent-core-framework`](https://github.com/amcerri/agent-core-framework)


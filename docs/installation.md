# Installation

This guide covers how to install and set up the Agent Core Framework.

## Requirements

- Python >= 3.10
- Poetry (recommended) or pip for dependency management

## Installation Methods

### Using Poetry (Recommended)

1. Clone the repository:

```bash
git clone https://github.com/amcerri/agent-core-framework.git
cd agent-core-framework
```

2. Install dependencies:

```bash
poetry install
```

3. For LangGraph support (optional):

```bash
poetry install --extras langgraph
```

### Using pip

1. Clone the repository:

```bash
git clone https://github.com/amcerri/agent-core-framework.git
cd agent-core-framework
```

2. Install in development mode:

```bash
pip install -e .
```

3. For LangGraph support (optional):

```bash
pip install -e ".[langgraph]"
```

## Verify Installation

After installation, verify that the framework can be imported:

```python
from agent_core.runtime import Runtime
from agent_core.configuration.loader import load_config

# Should not raise ImportError
```

## Next Steps

- Create a configuration file (see [Configuration](./configuration.md))
- Review the [Overview](./overview.md) for architecture details
- Check out [Creating Agents](./creating-agents.md) to get started

---

Back to [docs index](./README.md)  
Back to [repository root](../README.md)


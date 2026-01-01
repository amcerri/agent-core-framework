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

Or using Make:

```bash
make verify
```

## Docker Installation (Optional)

For a reproducible development environment using Docker:

1. Build the Docker image:

```bash
docker build -t agent-core-framework .
```

2. Run with mounted configuration:

```bash
docker run -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/examples:/app/examples:ro \
  agent-core-framework \
  python examples/minimal_example.py
```

For more details, see [Docker Usage](./docker.md).

## Using Make Commands

The project includes a `Makefile` with convenient commands for common tasks:

```bash
# See all available commands
make help

# Install dependencies
make install

# Run tests
make test

# Format and lint code
make format
make lint

# Run the example
make run-example
```

See the [Makefile](../Makefile) for all available commands.

## Next Steps

- Create a configuration file (see [Configuration](./configuration.md))
- Review the [Overview](./overview.md) for architecture details
- Check out [Creating Agents](./creating-agents.md) to get started
- For Docker usage, see [Docker Usage](./docker.md)

---

Back to [docs index](./README.md)  
Back to [repository root](../README.md)


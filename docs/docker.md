# Docker Usage

This guide explains how to use Docker with the Agent Core Framework for reproducible development and testing environments.

## Overview

Docker support is **optional** and provided for:

- Reproducible local development environments
- Consistent CI/CD execution
- Simplified onboarding
- Environment isolation

The framework works identically with or without Docker. No framework behavior depends on Docker.

## Prerequisites

- Docker installed and running
- Docker Compose (optional, for `docker-compose.yml`)

## Quick Start

### Using Dockerfile

1. Build the image:

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

### Using docker-compose

1. Ensure configuration exists:

```bash
# Create config directory if it doesn't exist
mkdir -p config

# Copy example config (if needed)
cp examples/config/agent-core.yaml config/
```

2. Start the container:

```bash
docker-compose up
```

3. Run commands interactively:

```bash
docker-compose exec agent-core python examples/minimal_example.py
```

## Configuration

Configuration must be provided externally - never embedded in Docker images.

### Mounting Configuration

Mount your configuration directory:

```bash
docker run -v /path/to/your/config:/app/config:ro agent-core-framework
```

### Environment Variables

Override configuration location:

```bash
docker run -e AGENT_CORE_CONFIG=/app/config/custom.yaml \
  -v /path/to/config:/app/config:ro \
  agent-core-framework
```

## Running Examples

Run the minimal example:

```bash
docker run -v $(pwd)/config:/app/config:ro \
  -v $(pwd)/examples:/app/examples:ro \
  agent-core-framework \
  python examples/minimal_example.py
```

Or with docker-compose:

```bash
docker-compose run --rm agent-core python examples/minimal_example.py
```

## Development Workflow

For development with live code changes:

```bash
docker-compose up -d
docker-compose exec agent-core python examples/minimal_example.py
```

Code changes in `agent_core/` are reflected immediately when mounted as a volume.

## Building with LangGraph Support

To include optional LangGraph dependencies:

```bash
docker build --build-arg EXTRAS=langgraph -t agent-core-framework:langgraph .
```

Or modify the Dockerfile to install extras by default.

## Important Notes

### Configuration and Secrets

- **Never** embed configuration or secrets in Docker images
- Always mount configuration files as volumes
- Use environment variables only for configuration paths, not values
- Secrets should be provided via mounted files or secret management systems

### Stateless Containers

- Containers are stateless by design
- No persistent state is stored in containers
- All state should be externalized (services, databases, etc.)

### Behavior Consistency

- Framework behavior is identical inside and outside Docker
- No Docker-specific code paths exist
- All contracts and governance rules apply identically

## Troubleshooting

### Configuration Not Found

If you see configuration errors:

1. Verify config directory is mounted: `docker run -v $(pwd)/config:/app/config:ro ...`
2. Check config file exists: `ls config/agent-core.yaml`
3. Verify path: `docker run -e AGENT_CORE_CONFIG=/app/config/agent-core.yaml ...`

### Permission Issues

If you encounter permission errors:

1. Ensure config files are readable: `chmod 644 config/*.yaml`
2. Use read-only mounts: `:ro` flag in volume mounts
3. Check file ownership matches container user

### Dependencies Not Found

If imports fail:

1. Rebuild image: `docker build -t agent-core-framework .`
2. Verify Poetry installed dependencies: `docker run agent-core-framework poetry show`
3. Check Python version: `docker run agent-core-framework python --version`

## Related Documentation

- [Installation](./installation.md) - Non-Docker installation
- [Configuration](./configuration.md) - Configuration system
- [Examples](../examples/README.md) - Example usage

---

Back to [docs index](./README.md)  
Back to [repository root](../README.md)


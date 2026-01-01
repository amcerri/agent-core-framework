# Configuration

This document describes the configuration system for the Agent Core Framework.

## Configuration Loading

Configuration is loaded from YAML files. The framework looks for configuration in this order:

1. Path provided to `load_config(config_path)`
2. `AGENT_CORE_CONFIG` environment variable
3. `./config/agent-core.yaml` (default)

Example:

```python
from agent_core.configuration.loader import load_config

# Uses default location or AGENT_CORE_CONFIG
config = load_config()

# Or specify explicit path
config = load_config("/path/to/config.yaml")
```

Implementation: [agent_core/configuration/loader.py](../agent_core/configuration/loader.py)

## Configuration Schema

Configuration is organized into sections:

### Runtime Configuration

```yaml
runtime:
  runtime_id: "my-runtime"
  mode: "development"  # development, staging, production
  concurrency: 4      # Maximum concurrent executions
  timeouts:
    default: 60
  default_locale: "en-US"
  fail_fast: false
```

Schema: [agent_core/configuration/schemas.py](../agent_core/configuration/schemas.py#L13)

### Agent Configuration

```yaml
agents:
  my_agent:
    agent_id: "my_agent"
    version: "1.0.0"
    enabled: true
    capabilities:
      - "query"
      - "analysis"
    provider_binding: "openai"
    defaults:
      model: "gpt-4"
```

Schema: [agent_core/configuration/schemas.py](../agent_core/configuration/schemas.py#L45)

### Tool Configuration

```yaml
tools:
  my_tool:
    tool_id: "my_tool"
    version: "1.0.0"
    enabled: true
    permissions_required:
      - "read"
      - "write"
    timeouts:
      execution: 30
    retry_policy:
      max_attempts: 3
      initial_delay: 1.0
```

Schema: [agent_core/configuration/schemas.py](../agent_core/configuration/schemas.py#L71)

### Service Configuration

```yaml
services:
  my_service:
    service_id: "my_service"
    version: "1.0.0"
    capabilities:
      - "storage"
    provider_binding: "postgres"
    access_policies:
      read: ["user", "admin"]
      write: ["admin"]
```

Schema: [agent_core/configuration/schemas.py](../agent_core/configuration/schemas.py#L97)

### Flow Configuration

```yaml
flows:
  my_flow:
    flow_id: "my_flow"
    version: "1.0.0"
    entrypoint: "start"
    nodes:
      start:
        type: "agent"
        agent_id: "my_agent"
    transitions:
      - from: "start"
        to: "end"
```

Schema: [agent_core/configuration/schemas.py](../agent_core/configuration/schemas.py#L119)

### Governance Configuration

```yaml
governance:
  permissions:
    default: []
  budgets:
    time_limit: 300
    max_calls: 100
    cost_limit: 10.0
  policies:
    - action: "tool.execute:*"
      outcome: "allow"
  approvals:
    required_for: []
```

Schema: [agent_core/configuration/schemas.py](../agent_core/configuration/schemas.py#L166)

### Observability Configuration

```yaml
observability:
  enabled: true
  sampling:
    rate: 1.0
  exporters:
    logging:
      level: "INFO"
  redaction:
    patterns: []
  audit:
    enabled: true
```

Schema: [agent_core/configuration/schemas.py](../agent_core/configuration/schemas.py#L190)

## Environment Overrides

Configuration supports environment-specific overrides:

```yaml
environment:
  name: "production"
  overrides:
    runtime:
      mode: "production"
      concurrency: 8
    governance:
      budgets:
        cost_limit: 50.0
```

Implementation: [agent_core/configuration/validation.py](../agent_core/configuration/validation.py)

## Validation

All configuration is validated at startup:

- Schema validation (Pydantic)
- Business logic validation
- Required fields checked
- Invalid configuration fails fast with clear errors

Implementation: [agent_core/configuration/validation.py](../agent_core/configuration/validation.py)

## Related Documentation

- [Architecture](./architecture.md) - System architecture
- [Runtime API](./runtime-api.md) - Using configuration with runtime
- [Overview](./overview.md) - Framework introduction

---

Back to [docs index](./README.md)  
Back to [repository root](../README.md)


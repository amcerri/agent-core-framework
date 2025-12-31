"""Configuration management for Agent Core Framework.

This package provides configuration schemas and YAML loading functionality
for the framework. Configuration is validated at startup and must conform
to the schemas defined in `.docs/06-configuration.md`.
"""

from agent_core.configuration.loader import (
    ConfigurationError,
    load_config,
    load_config_from_dict,
)
from agent_core.configuration.schemas import (
    AgentCoreConfig,
    AgentConfig,
    EnvironmentConfig,
    FlowConfig,
    GovernanceConfig,
    ObservabilityConfig,
    ProviderConfig,
    RuntimeConfig,
    ServiceConfig,
    ToolConfig,
)
from agent_core.configuration.validation import (
    apply_environment_overrides,
    validate_and_apply_overrides,
    validate_config,
)

__all__ = [
    "AgentCoreConfig",
    "AgentConfig",
    "apply_environment_overrides",
    "ConfigurationError",
    "EnvironmentConfig",
    "FlowConfig",
    "GovernanceConfig",
    "ObservabilityConfig",
    "ProviderConfig",
    "RuntimeConfig",
    "ServiceConfig",
    "ToolConfig",
    "load_config",
    "load_config_from_dict",
    "validate_and_apply_overrides",
    "validate_config",
]


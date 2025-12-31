"""Configuration validation and environment override logic.

Provides startup validation and deterministic environment override merging
as specified in `.docs/06-configuration.md`.
"""

from datetime import datetime, timezone
from typing import Any

from agent_core.configuration.loader import ConfigurationError
from agent_core.configuration.schemas import AgentCoreConfig
from agent_core.contracts.observability import (
    ComponentType,
    CorrelationFields,
)
from agent_core.observability.logging import get_logger
from agent_core.utils.ids import generate_correlation_id, generate_run_id


def validate_config(config: AgentCoreConfig) -> None:
    """Validate configuration at startup.

    Performs business logic validation beyond schema validation.
    Ensures configuration is complete and consistent.

    Args:
        config: Configuration to validate.

    Raises:
        ConfigurationError: If validation fails with actionable error message.
    """
    errors: list[str] = []

    # Validate runtime configuration is present
    if config.runtime is None:
        errors.append("Runtime configuration is required but not provided.")

    # Validate agent configurations
    for agent_id, agent_config in config.agents.items():
        if agent_config.agent_id != agent_id:
            errors.append(
                f"Agent configuration key '{agent_id}' does not match "
                f"agent_id '{agent_config.agent_id}'."
            )
        if agent_config.provider_binding and config.providers is None:
            errors.append(
                f"Agent '{agent_id}' references provider_binding "
                f"'{agent_config.provider_binding}' but no providers are configured."
            )

    # Validate tool configurations
    for tool_id, tool_config in config.tools.items():
        if tool_config.tool_id != tool_id:
            errors.append(
                f"Tool configuration key '{tool_id}' does not match "
                f"tool_id '{tool_config.tool_id}'."
            )

    # Validate service configurations
    for service_id, service_config in config.services.items():
        if service_config.service_id != service_id:
            errors.append(
                f"Service configuration key '{service_id}' does not match "
                f"service_id '{service_config.service_id}'."
            )
        if service_config.provider_binding and config.providers is None:
            errors.append(
                f"Service '{service_id}' references provider_binding "
                f"'{service_config.provider_binding}' but no providers are configured."
            )

    # Validate flow configurations
    for flow_id, flow_config in config.flows.items():
        if flow_config.flow_id != flow_id:
            errors.append(
                f"Flow configuration key '{flow_id}' does not match "
                f"flow_id '{flow_config.flow_id}'."
            )
        if flow_config.entrypoint not in flow_config.nodes:
            errors.append(
                f"Flow '{flow_id}' entrypoint '{flow_config.entrypoint}' "
                "does not exist in nodes."
            )

    if errors:
        error_message = "Configuration validation failed:\n" + "\n".join(
            f"  - {error}" for error in errors
        )
        raise ConfigurationError(error_message)


def _deep_merge_dict(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries.

    Args:
        base: Base dictionary.
        override: Override dictionary.

    Returns:
        Merged dictionary.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge_dict(result[key], value)
        else:
            result[key] = value
    return result


def apply_environment_overrides(
    base_config: AgentCoreConfig,
    environment_name: str | None = None,
) -> AgentCoreConfig:
    """Apply environment-specific overrides to base configuration.

    Merges environment overrides into base configuration deterministically.
    Overrides are applied at the section level (e.g., runtime, agents, etc.).
    For dict sections (agents, tools, services, flows), individual items are
    deep-merged. For other sections, overrides replace the base.

    Args:
        base_config: Base configuration to apply overrides to.
        environment_name: Optional environment name. If None, uses
            base_config.environment.name if available.

    Returns:
        New AgentCoreConfig instance with overrides applied.

    Raises:
        ConfigurationError: If override application fails or violates contracts.
    """
    # Always return a new instance
    base_dict = base_config.model_dump(exclude_none=False)

    # Determine environment name
    if environment_name is None:
        if base_config.environment is not None:
            environment_name = base_config.environment.name
        else:
            # No environment specified, return new instance of base config
            return AgentCoreConfig(**base_dict)

    # Get overrides from environment config
    if base_config.environment is None:
        # No environment config, return new instance of base config
        return AgentCoreConfig(**base_dict)

    overrides = base_config.environment.overrides
    if not overrides:
        # No overrides specified, return new instance of base config
        return AgentCoreConfig(**base_dict)

    # Apply overrides at section level
    # For dict sections (agents, tools, services, flows), deep merge individual items
    # For other sections, replace entirely
    for section_key, section_override in overrides.items():
        if section_key in base_dict:
            if isinstance(section_override, dict):
                # Merge dict sections (e.g., agents, tools, services, flows)
                if isinstance(base_dict[section_key], dict):
                    base_dict[section_key] = _deep_merge_dict(
                        base_dict[section_key], section_override
                    )
                else:
                    # Replace non-dict sections
                    base_dict[section_key] = section_override
            else:
                # Replace non-dict sections
                base_dict[section_key] = section_override
        else:
            # New section from override
            base_dict[section_key] = section_override

    # Validate merged configuration
    try:
        merged_config = AgentCoreConfig(**base_dict)
    except Exception as e:
        raise ConfigurationError(
            f"Failed to apply environment overrides for '{environment_name}': {e}"
        ) from e

    return merged_config


def validate_and_apply_overrides(
    config: AgentCoreConfig,
    environment_name: str | None = None,
    emit_observability: bool = True,
) -> AgentCoreConfig:
    """Validate configuration and apply environment overrides.

    This is the main entry point for startup configuration validation.
    It validates the base configuration, applies environment overrides,
    and emits observability signals.

    Args:
        config: Base configuration to validate and apply overrides to.
        environment_name: Optional environment name for overrides.
        emit_observability: Whether to emit observability signals.

    Returns:
        Validated and merged configuration.

    Raises:
        ConfigurationError: If validation or override application fails.
    """
    # Create minimal correlation context for startup
    correlation = CorrelationFields(
        run_id=generate_run_id(),
        correlation_id=generate_correlation_id(),
        component_type=ComponentType.RUNTIME,
        component_id="runtime:startup",
        component_version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )

    logger = None
    if emit_observability:
        logger = get_logger("agent_core.configuration", correlation)

    # Log startup
    if logger:
        logger.info(
            "Starting configuration validation",
            extra={"environment": environment_name or "default"},
        )

    # Validate base configuration
    try:
        validate_config(config)
        if logger:
            logger.info("Base configuration validation passed")
    except ConfigurationError as e:
        if logger:
            logger.error(
                "Configuration validation failed",
                extra={"error": str(e)},
            )
        raise

    # Apply environment overrides
    try:
        merged_config = apply_environment_overrides(config, environment_name)
        if logger:
            logger.info(
                "Environment overrides applied",
                extra={"environment": environment_name or "default"},
            )
    except ConfigurationError as e:
        if logger:
            logger.error(
                "Failed to apply environment overrides",
                extra={"error": str(e), "environment": environment_name or "default"},
            )
        raise

    # Validate merged configuration
    try:
        validate_config(merged_config)
        if logger:
            logger.info("Merged configuration validation passed")
    except ConfigurationError as e:
        if logger:
            logger.error(
                "Merged configuration validation failed",
                extra={"error": str(e)},
            )
        raise

    if logger:
        logger.info("Configuration validation and override application completed")

    return merged_config


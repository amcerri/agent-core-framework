"""YAML configuration loader.

Loads and validates configuration from YAML files. Supports default
location (`./config/agent-core.yaml`) and environment variable override
(`AGENT_CORE_CONFIG`).
"""

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from agent_core.configuration.schemas import AgentCoreConfig


class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails."""

    pass


def load_config(config_path: str | None = None) -> AgentCoreConfig:
    """Load configuration from YAML file.

    Configuration is loaded from:
    1. `config_path` if provided
    2. `AGENT_CORE_CONFIG` environment variable if set
    3. `./config/agent-core.yaml` as default

    Args:
        config_path: Optional path to configuration file. If None, uses
            environment variable or default location.

    Returns:
        Validated AgentCoreConfig instance.

    Raises:
        ConfigurationError: If configuration file cannot be loaded or
            validation fails.
    """
    # Determine config file path
    if config_path is None:
        config_path = os.getenv("AGENT_CORE_CONFIG")
        if config_path is None:
            config_path = "./config/agent-core.yaml"

    config_path = Path(config_path)

    # Check if file exists
    if not config_path.exists():
        raise ConfigurationError(
            f"Configuration file not found: {config_path}. "
            "Set AGENT_CORE_CONFIG environment variable or create "
            "./config/agent-core.yaml"
        )

    if not config_path.is_file():
        raise ConfigurationError(f"Configuration path is not a file: {config_path}")

    # Load YAML
    try:
        with open(config_path, encoding="utf-8") as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(
            f"Failed to parse YAML configuration file {config_path}: {e}"
        ) from e
    except OSError as e:
        raise ConfigurationError(f"Failed to read configuration file {config_path}: {e}") from e

    # Handle empty file (yaml.safe_load returns None for empty files)
    if config_data is None:
        config_data = {}

    # Validate and return
    try:
        return AgentCoreConfig(**config_data)
    except ValidationError as e:
        raise ConfigurationError(f"Configuration validation failed for {config_path}: {e}") from e


def load_config_from_dict(config_data: dict[str, Any]) -> AgentCoreConfig:
    """Load configuration from a dictionary.

    Useful for testing or programmatic configuration.

    Args:
        config_data: Configuration data as a dictionary.

    Returns:
        Validated AgentCoreConfig instance.

    Raises:
        ConfigurationError: If validation fails.
    """
    try:
        return AgentCoreConfig(**config_data)
    except ValidationError as e:
        raise ConfigurationError(f"Configuration validation failed: {e}") from e

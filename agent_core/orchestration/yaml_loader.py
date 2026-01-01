"""YAML flow loader.

Provides utilities for loading flow definitions from YAML files.
Flows are loaded as FlowConfig instances and can be executed via FlowEngine.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from agent_core.configuration.schemas import FlowConfig


class FlowLoadError(Exception):
    """Raised when flow loading fails."""

    pass


def load_flow_from_yaml(yaml_path: str | Path) -> FlowConfig:
    """Load a flow definition from a YAML file.

    Args:
        yaml_path: Path to YAML file containing flow definition.

    Returns:
        FlowConfig instance representing the flow.

    Raises:
        FlowLoadError: If flow loading or validation fails.
    """
    yaml_path = Path(yaml_path)

    if not yaml_path.exists():
        raise FlowLoadError(f"Flow YAML file not found: {yaml_path}")

    if not yaml_path.is_file():
        raise FlowLoadError(f"Flow path is not a file: {yaml_path}")

    try:
        with open(yaml_path, encoding="utf-8") as f:
            flow_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise FlowLoadError(f"Failed to parse YAML file {yaml_path}: {e}") from e
    except OSError as e:
        raise FlowLoadError(f"Failed to read YAML file {yaml_path}: {e}") from e

    if flow_data is None:
        raise FlowLoadError(f"Flow YAML file is empty: {yaml_path}")

    try:
        return FlowConfig(**flow_data)
    except ValidationError as e:
        raise FlowLoadError(f"Flow validation failed for {yaml_path}: {e}") from e


def load_flow_from_dict(flow_data: dict[str, Any]) -> FlowConfig:
    """Load a flow definition from a dictionary.

    Args:
        flow_data: Dictionary containing flow definition.

    Returns:
        FlowConfig instance representing the flow.

    Raises:
        FlowLoadError: If flow validation fails.
    """
    try:
        return FlowConfig(**flow_data)
    except ValidationError as e:
        raise FlowLoadError(f"Flow validation failed: {e}") from e

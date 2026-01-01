"""Unit tests for YAML flow loader."""

import tempfile
from pathlib import Path

import pytest
import yaml

from agent_core.orchestration.yaml_loader import (
    FlowLoadError,
    load_flow_from_dict,
    load_flow_from_yaml,
)


class TestYamlLoader:
    """Test YAML flow loader."""

    def test_load_flow_from_dict(self):
        """Test loading flow from dictionary."""
        flow_data = {
            "flow_id": "test_flow",
            "version": "1.0.0",
            "entrypoint": "start",
            "nodes": {
                "start": {"type": "agent", "agent_id": "agent1"},
            },
            "transitions": [],
        }

        flow_config = load_flow_from_dict(flow_data)

        assert flow_config.flow_id == "test_flow"
        assert flow_config.version == "1.0.0"
        assert flow_config.entrypoint == "start"

    def test_load_flow_from_dict_invalid(self):
        """Test loading invalid flow from dictionary."""
        flow_data = {"flow_id": "test"}  # Missing required fields

        with pytest.raises(FlowLoadError):
            load_flow_from_dict(flow_data)

    def test_load_flow_from_yaml(self):
        """Test loading flow from YAML file."""
        flow_data = {
            "flow_id": "test_flow",
            "version": "1.0.0",
            "entrypoint": "start",
            "nodes": {
                "start": {"type": "agent", "agent_id": "agent1"},
            },
            "transitions": [],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(flow_data, f)
            yaml_path = f.name

        try:
            flow_config = load_flow_from_yaml(yaml_path)

            assert flow_config.flow_id == "test_flow"
            assert flow_config.version == "1.0.0"
            assert flow_config.entrypoint == "start"
        finally:
            Path(yaml_path).unlink()

    def test_load_flow_from_yaml_missing_file(self):
        """Test loading flow from non-existent YAML file."""
        with pytest.raises(FlowLoadError, match="not found"):
            load_flow_from_yaml("/nonexistent/flow.yaml")

    def test_load_flow_from_yaml_invalid_yaml(self):
        """Test loading invalid YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            yaml_path = f.name

        try:
            with pytest.raises(FlowLoadError, match="Failed to parse"):
                load_flow_from_yaml(yaml_path)
        finally:
            Path(yaml_path).unlink()

    def test_load_flow_from_yaml_empty_file(self):
        """Test loading empty YAML file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml_path = f.name

        try:
            with pytest.raises(FlowLoadError, match="empty"):
                load_flow_from_yaml(yaml_path)
        finally:
            Path(yaml_path).unlink()

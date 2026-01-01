"""Unit tests for configuration loader."""

import os

import pytest
import yaml

from agent_core.configuration.loader import (
    ConfigurationError,
    load_config,
    load_config_from_dict,
)
from agent_core.configuration.schemas import (
    AgentCoreConfig,
)


class TestLoadConfig:
    """Test load_config function."""

    def test_load_config_from_valid_file(self, tmp_path):
        """Test loading configuration from a valid YAML file."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "runtime": {
                "runtime_id": "test-runtime",
                "mode": "development",
                "concurrency": 2,
            }
        }
        config_file.write_text(yaml.dump(config_data))

        config = load_config(str(config_file))

        assert isinstance(config, AgentCoreConfig)
        assert config.runtime is not None
        assert config.runtime.runtime_id == "test-runtime"
        assert config.runtime.mode == "development"
        assert config.runtime.concurrency == 2

    def test_load_config_with_all_sections(self, tmp_path):
        """Test loading configuration with all sections."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "runtime": {
                "runtime_id": "test-runtime",
                "mode": "production",
            },
            "agents": {
                "agent1": {
                    "agent_id": "agent1",
                    "version": "1.0.0",
                    "enabled": True,
                }
            },
            "tools": {
                "tool1": {
                    "tool_id": "tool1",
                    "version": "1.0.0",
                    "permissions_required": ["read"],
                }
            },
            "services": {
                "service1": {
                    "service_id": "service1",
                    "version": "1.0.0",
                    "capabilities": ["read", "write"],
                }
            },
            "flows": {
                "flow1": {
                    "flow_id": "flow1",
                    "version": "1.0.0",
                    "entrypoint": "start",
                }
            },
            "providers": {
                "llm": {"provider": "openai"},
            },
            "governance": {
                "permissions": {},
            },
            "observability": {
                "enabled": True,
            },
            "environment": {
                "name": "test",
            },
        }
        config_file.write_text(yaml.dump(config_data))

        config = load_config(str(config_file))

        assert config.runtime is not None
        assert len(config.agents) == 1
        assert len(config.tools) == 1
        assert len(config.services) == 1
        assert len(config.flows) == 1
        assert config.providers is not None
        assert config.governance is not None
        assert config.observability is not None
        assert config.environment is not None

    def test_load_config_with_defaults(self, tmp_path):
        """Test that configuration uses defaults for optional fields."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "runtime": {
                "runtime_id": "test-runtime",
            }
        }
        config_file.write_text(yaml.dump(config_data))

        config = load_config(str(config_file))

        assert config.runtime is not None
        assert config.runtime.mode == "development"  # default
        assert config.runtime.concurrency == 1  # default
        assert config.runtime.default_locale == "en-US"  # default
        assert config.runtime.fail_fast is False  # default

    def test_load_config_missing_file(self):
        """Test that load_config raises error for missing file."""
        with pytest.raises(ConfigurationError, match="Configuration file not found"):
            load_config("/nonexistent/path/config.yaml")

    def test_load_config_invalid_yaml(self, tmp_path):
        """Test that load_config raises error for invalid YAML."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("invalid: yaml: content: [unclosed")

        with pytest.raises(ConfigurationError, match="Failed to parse YAML"):
            load_config(str(config_file))

    def test_load_config_invalid_schema(self, tmp_path):
        """Test that load_config raises error for invalid schema."""
        config_file = tmp_path / "config.yaml"
        config_data = {
            "runtime": {
                "runtime_id": 123,  # Should be string
            }
        }
        config_file.write_text(yaml.dump(config_data))

        with pytest.raises(ConfigurationError, match="Configuration validation failed"):
            load_config(str(config_file))

    def test_load_config_empty_file(self, tmp_path):
        """Test that load_config handles empty file."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")

        config = load_config(str(config_file))

        assert isinstance(config, AgentCoreConfig)
        assert config.runtime is None

    def test_load_config_from_environment_variable(self, tmp_path, monkeypatch):
        """Test that load_config uses AGENT_CORE_CONFIG environment variable."""
        config_file = tmp_path / "env-config.yaml"
        config_data = {
            "runtime": {
                "runtime_id": "env-runtime",
            }
        }
        config_file.write_text(yaml.dump(config_data))

        monkeypatch.setenv("AGENT_CORE_CONFIG", str(config_file))
        config = load_config()

        assert config.runtime is not None
        assert config.runtime.runtime_id == "env-runtime"

    def test_load_config_default_location(self, tmp_path, monkeypatch):
        """Test that load_config uses default location when env var not set."""
        # Create config directory and file
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "agent-core.yaml"
        config_data = {
            "runtime": {
                "runtime_id": "default-runtime",
            }
        }
        config_file.write_text(yaml.dump(config_data))

        # Change to tmp_path directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            monkeypatch.delenv("AGENT_CORE_CONFIG", raising=False)
            config = load_config()
            assert config.runtime is not None
            assert config.runtime.runtime_id == "default-runtime"
        finally:
            os.chdir(original_cwd)


class TestLoadConfigFromDict:
    """Test load_config_from_dict function."""

    def test_load_config_from_valid_dict(self):
        """Test loading configuration from a valid dictionary."""
        config_data = {
            "runtime": {
                "runtime_id": "test-runtime",
                "mode": "development",
            }
        }

        config = load_config_from_dict(config_data)

        assert isinstance(config, AgentCoreConfig)
        assert config.runtime is not None
        assert config.runtime.runtime_id == "test-runtime"

    def test_load_config_from_dict_invalid_schema(self):
        """Test that load_config_from_dict raises error for invalid schema."""
        config_data = {
            "runtime": {
                "runtime_id": 123,  # Should be string
            }
        }

        with pytest.raises(ConfigurationError, match="Configuration validation failed"):
            load_config_from_dict(config_data)

    def test_load_config_from_dict_empty(self):
        """Test loading configuration from empty dictionary."""
        config = load_config_from_dict({})

        assert isinstance(config, AgentCoreConfig)
        assert config.runtime is None

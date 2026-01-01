"""Unit tests for configuration validation."""

import pytest

from agent_core.configuration.loader import ConfigurationError, load_config_from_dict
from agent_core.configuration.validation import (
    apply_environment_overrides,
    validate_and_apply_overrides,
    validate_config,
)


class TestValidateConfig:
    """Test validate_config function."""

    def test_validate_config_with_valid_runtime(self):
        """Test that valid configuration passes validation."""
        config = load_config_from_dict(
            {
                "runtime": {
                    "runtime_id": "test-runtime",
                }
            }
        )

        # Should not raise
        validate_config(config)

    def test_validate_config_missing_runtime(self):
        """Test that missing runtime configuration fails validation."""
        config = load_config_from_dict({})

        with pytest.raises(ConfigurationError, match="Runtime configuration is required"):
            validate_config(config)

    def test_validate_config_agent_id_mismatch(self):
        """Test that agent_id mismatch fails validation."""
        config = load_config_from_dict(
            {
                "runtime": {"runtime_id": "test-runtime"},
                "agents": {
                    "agent1": {
                        "agent_id": "agent2",  # Mismatch
                        "version": "1.0.0",
                    }
                },
            }
        )

        with pytest.raises(ConfigurationError, match="does not match"):
            validate_config(config)

    def test_validate_config_tool_id_mismatch(self):
        """Test that tool_id mismatch fails validation."""
        config = load_config_from_dict(
            {
                "runtime": {"runtime_id": "test-runtime"},
                "tools": {
                    "tool1": {
                        "tool_id": "tool2",  # Mismatch
                        "version": "1.0.0",
                    }
                },
            }
        )

        with pytest.raises(ConfigurationError, match="does not match"):
            validate_config(config)

    def test_validate_config_service_id_mismatch(self):
        """Test that service_id mismatch fails validation."""
        config = load_config_from_dict(
            {
                "runtime": {"runtime_id": "test-runtime"},
                "services": {
                    "service1": {
                        "service_id": "service2",  # Mismatch
                        "version": "1.0.0",
                    }
                },
            }
        )

        with pytest.raises(ConfigurationError, match="does not match"):
            validate_config(config)

    def test_validate_config_flow_id_mismatch(self):
        """Test that flow_id mismatch fails validation."""
        config = load_config_from_dict(
            {
                "runtime": {"runtime_id": "test-runtime"},
                "flows": {
                    "flow1": {
                        "flow_id": "flow2",  # Mismatch
                        "version": "1.0.0",
                        "entrypoint": "start",
                        "nodes": {"start": {}},
                    }
                },
            }
        )

        with pytest.raises(ConfigurationError, match="does not match"):
            validate_config(config)

    def test_validate_config_agent_provider_binding_without_providers(self):
        """Test that agent with provider_binding but no providers fails."""
        config = load_config_from_dict(
            {
                "runtime": {"runtime_id": "test-runtime"},
                "agents": {
                    "agent1": {
                        "agent_id": "agent1",
                        "version": "1.0.0",
                        "provider_binding": "llm:openai",
                    }
                },
            }
        )

        with pytest.raises(ConfigurationError, match="no providers are configured"):
            validate_config(config)

    def test_validate_config_service_provider_binding_without_providers(self):
        """Test that service with provider_binding but no providers fails."""
        config = load_config_from_dict(
            {
                "runtime": {"runtime_id": "test-runtime"},
                "services": {
                    "service1": {
                        "service_id": "service1",
                        "version": "1.0.0",
                        "provider_binding": "database:postgres",
                    }
                },
            }
        )

        with pytest.raises(ConfigurationError, match="no providers are configured"):
            validate_config(config)

    def test_validate_config_flow_entrypoint_not_in_nodes(self):
        """Test that flow with entrypoint not in nodes fails."""
        config = load_config_from_dict(
            {
                "runtime": {"runtime_id": "test-runtime"},
                "flows": {
                    "flow1": {
                        "flow_id": "flow1",
                        "version": "1.0.0",
                        "entrypoint": "missing_node",
                        "nodes": {"start": {}},
                    }
                },
            }
        )

        with pytest.raises(ConfigurationError, match="does not exist in nodes"):
            validate_config(config)

    def test_validate_config_multiple_errors(self):
        """Test that multiple validation errors are all reported."""
        config = load_config_from_dict(
            {
                "runtime": {"runtime_id": "test-runtime"},
                "agents": {
                    "agent1": {
                        "agent_id": "agent2",  # Mismatch
                        "version": "1.0.0",
                    }
                },
                "tools": {
                    "tool1": {
                        "tool_id": "tool2",  # Mismatch
                        "version": "1.0.0",
                    }
                },
            }
        )

        with pytest.raises(ConfigurationError) as exc_info:
            validate_config(config)

        error_message = str(exc_info.value)
        assert "agent1" in error_message
        assert "tool1" in error_message


class TestApplyEnvironmentOverrides:
    """Test apply_environment_overrides function."""

    def test_apply_overrides_with_no_environment_config(self):
        """Test that config without environment config returns unchanged."""
        config = load_config_from_dict(
            {
                "runtime": {
                    "runtime_id": "test-runtime",
                    "mode": "development",
                }
            }
        )

        result = apply_environment_overrides(config)

        assert result.runtime is not None
        assert result.runtime.mode == "development"
        assert result is not config  # New instance

    def test_apply_overrides_with_empty_overrides(self):
        """Test that config with empty overrides returns unchanged."""
        config = load_config_from_dict(
            {
                "runtime": {
                    "runtime_id": "test-runtime",
                    "mode": "development",
                },
                "environment": {
                    "name": "production",
                    "overrides": {},
                },
            }
        )

        result = apply_environment_overrides(config)

        assert result.runtime is not None
        assert result.runtime.mode == "development"

    def test_apply_overrides_runtime_section(self):
        """Test that runtime section can be overridden."""
        config = load_config_from_dict(
            {
                "runtime": {
                    "runtime_id": "test-runtime",
                    "mode": "development",
                },
                "environment": {
                    "name": "production",
                    "overrides": {
                        "runtime": {
                            "mode": "production",
                        }
                    },
                },
            }
        )

        result = apply_environment_overrides(config)

        assert result.runtime is not None
        assert result.runtime.runtime_id == "test-runtime"  # Preserved
        assert result.runtime.mode == "production"  # Overridden

    def test_apply_overrides_agents_section(self):
        """Test that agents section can be merged."""
        config = load_config_from_dict(
            {
                "runtime": {"runtime_id": "test-runtime"},
                "agents": {
                    "agent1": {
                        "agent_id": "agent1",
                        "version": "1.0.0",
                        "enabled": True,
                    }
                },
                "environment": {
                    "name": "production",
                    "overrides": {
                        "agents": {
                            "agent1": {
                                "enabled": False,  # Override
                            },
                            "agent2": {  # New agent
                                "agent_id": "agent2",
                                "version": "1.0.0",
                            },
                        }
                    },
                },
            }
        )

        result = apply_environment_overrides(config)

        assert len(result.agents) == 2
        assert result.agents["agent1"].enabled is False  # Overridden
        assert result.agents["agent1"].version == "1.0.0"  # Preserved
        assert "agent2" in result.agents  # New agent added

    def test_apply_overrides_with_explicit_environment_name(self):
        """Test that explicit environment name can be provided."""
        config = load_config_from_dict(
            {
                "runtime": {
                    "runtime_id": "test-runtime",
                    "mode": "development",
                },
                "environment": {
                    "name": "production",
                    "overrides": {
                        "runtime": {
                            "mode": "production",
                        }
                    },
                },
            }
        )

        result = apply_environment_overrides(config, environment_name="staging")

        # Should still use environment config's overrides
        assert result.runtime.mode == "production"

    def test_apply_overrides_validates_merged_config(self):
        """Test that merged config is validated."""
        config = load_config_from_dict(
            {
                "runtime": {"runtime_id": "test-runtime"},
                "environment": {
                    "name": "production",
                    "overrides": {
                        "runtime": {
                            "runtime_id": 123,  # Invalid type
                        }
                    },
                },
            }
        )

        with pytest.raises(ConfigurationError, match="Failed to apply environment overrides"):
            apply_environment_overrides(config)


class TestValidateAndApplyOverrides:
    """Test validate_and_apply_overrides function."""

    def test_validate_and_apply_overrides_success(self):
        """Test successful validation and override application."""
        config = load_config_from_dict(
            {
                "runtime": {"runtime_id": "test-runtime"},
                "environment": {
                    "name": "production",
                    "overrides": {
                        "runtime": {
                            "mode": "production",
                        }
                    },
                },
            }
        )

        result = validate_and_apply_overrides(config, emit_observability=False)

        assert result.runtime is not None
        assert result.runtime.mode == "production"

    def test_validate_and_apply_overrides_fails_on_invalid_base(self):
        """Test that invalid base config fails before applying overrides."""
        config = load_config_from_dict({})  # Missing runtime

        with pytest.raises(ConfigurationError, match="Runtime configuration is required"):
            validate_and_apply_overrides(config, emit_observability=False)

    def test_validate_and_apply_overrides_fails_on_invalid_merged(self):
        """Test that invalid merged config fails validation."""
        config = load_config_from_dict(
            {
                "runtime": {"runtime_id": "test-runtime"},
                "environment": {
                    "name": "production",
                    "overrides": {
                        "agents": {
                            "agent1": {
                                "agent_id": "agent2",  # Mismatch
                                "version": "1.0.0",
                            }
                        }
                    },
                },
            }
        )

        with pytest.raises(ConfigurationError, match="does not match"):
            validate_and_apply_overrides(config, emit_observability=False)

    def test_validate_and_apply_overrides_with_observability(self):
        """Test that observability signals are emitted when enabled."""
        config = load_config_from_dict(
            {
                "runtime": {"runtime_id": "test-runtime"},
            }
        )

        # Should not raise, observability is emitted
        result = validate_and_apply_overrides(config, emit_observability=True)

        assert result.runtime is not None

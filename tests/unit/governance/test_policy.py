"""Unit tests for policy engine."""

import pytest

from agent_core.configuration.schemas import GovernanceConfig
from agent_core.governance.policy import PolicyEngine, PolicyError, PolicyOutcome
from agent_core.runtime.execution_context import create_execution_context


class TestPolicyEngine:
    """Test PolicyEngine."""

    def test_evaluate_policy_no_config_defaults_to_allow(self):
        """Test that no policy config defaults to ALLOW."""
        context = create_execution_context(initiator="user:test")
        engine = PolicyEngine(context)

        outcome = engine.evaluate_policy("tool.execute", resource_id="tool1", resource_type="tool")
        assert outcome == PolicyOutcome.ALLOW

    def test_evaluate_policy_exact_match_allow(self):
        """Test policy evaluation with exact action match - ALLOW."""
        context = create_execution_context(initiator="user:test")
        governance_config = GovernanceConfig(
            policies={"tool.execute": {"outcome": "allow"}},
        )
        engine = PolicyEngine(context, governance_config)

        outcome = engine.evaluate_policy("tool.execute", resource_id="tool1", resource_type="tool")
        assert outcome == PolicyOutcome.ALLOW

    def test_evaluate_policy_exact_match_deny(self):
        """Test policy evaluation with exact action match - DENY."""
        context = create_execution_context(initiator="user:test")
        governance_config = GovernanceConfig(
            policies={"tool.execute": {"outcome": "deny"}},
        )
        engine = PolicyEngine(context, governance_config)

        outcome = engine.evaluate_policy("tool.execute", resource_id="tool1", resource_type="tool")
        assert outcome == PolicyOutcome.DENY

    def test_evaluate_policy_exact_match_require_approval(self):
        """Test policy evaluation with exact action match - REQUIRE_APPROVAL."""
        context = create_execution_context(initiator="user:test")
        governance_config = GovernanceConfig(
            policies={"tool.execute": {"outcome": "require_approval"}},
        )
        engine = PolicyEngine(context, governance_config)

        outcome = engine.evaluate_policy("tool.execute", resource_id="tool1", resource_type="tool")
        assert outcome == PolicyOutcome.REQUIRE_APPROVAL

    def test_evaluate_policy_pattern_match(self):
        """Test policy evaluation with pattern matching."""
        context = create_execution_context(initiator="user:test")
        governance_config = GovernanceConfig(
            policies={"tool.*": {"outcome": "deny"}},
        )
        engine = PolicyEngine(context, governance_config)

        # Should match pattern "tool.*"
        outcome = engine.evaluate_policy("tool.execute", resource_id="tool1", resource_type="tool")
        assert outcome == PolicyOutcome.DENY

        outcome = engine.evaluate_policy("tool.read", resource_id="tool2", resource_type="tool")
        assert outcome == PolicyOutcome.DENY

    def test_evaluate_policy_no_match_defaults_to_allow(self):
        """Test that no matching policy defaults to ALLOW."""
        context = create_execution_context(initiator="user:test")
        governance_config = GovernanceConfig(
            policies={"service.read": {"outcome": "deny"}},
        )
        engine = PolicyEngine(context, governance_config)

        # No matching policy for tool.execute
        outcome = engine.evaluate_policy("tool.execute", resource_id="tool1", resource_type="tool")
        assert outcome == PolicyOutcome.ALLOW

    def test_evaluate_policy_invalid_outcome_raises_error(self):
        """Test that invalid policy outcome raises PolicyError."""
        context = create_execution_context(initiator="user:test")
        governance_config = GovernanceConfig(
            policies={"tool.execute": {"outcome": "invalid"}},
        )
        engine = PolicyEngine(context, governance_config)

        with pytest.raises(PolicyError, match="Invalid policy outcome"):
            engine.evaluate_policy("tool.execute", resource_id="tool1", resource_type="tool")

    def test_evaluate_policy_no_outcome_defaults_to_allow(self):
        """Test that policy config without outcome defaults to ALLOW."""
        context = create_execution_context(initiator="user:test")
        governance_config = GovernanceConfig(
            policies={"tool.execute": {}},
        )
        engine = PolicyEngine(context, governance_config)

        outcome = engine.evaluate_policy("tool.execute", resource_id="tool1", resource_type="tool")
        assert outcome == PolicyOutcome.ALLOW

    def test_requires_approval(self):
        """Test requires_approval convenience method."""
        context = create_execution_context(initiator="user:test")
        governance_config = GovernanceConfig(
            policies={"tool.execute": {"outcome": "require_approval"}},
        )
        engine = PolicyEngine(context, governance_config)

        assert (
            engine.requires_approval("tool.execute", resource_id="tool1", resource_type="tool")
            is True
        )
        assert (
            engine.requires_approval("tool.read", resource_id="tool2", resource_type="tool")
            is False
        )

    def test_is_allowed(self):
        """Test is_allowed convenience method."""
        context = create_execution_context(initiator="user:test")
        governance_config = GovernanceConfig(
            policies={
                "tool.execute": {"outcome": "allow"},
                "tool.delete": {"outcome": "deny"},
            },
        )
        engine = PolicyEngine(context, governance_config)

        assert engine.is_allowed("tool.execute", resource_id="tool1", resource_type="tool") is True
        assert engine.is_allowed("tool.delete", resource_id="tool2", resource_type="tool") is False
        assert (
            engine.is_allowed("tool.read", resource_id="tool3", resource_type="tool") is True
        )  # No policy, defaults to allow

    def test_policy_engine_uses_context(self):
        """Test that engine uses execution context."""
        context = create_execution_context(initiator="user:test")
        engine = PolicyEngine(context)

        assert engine.context == context

    def test_policy_engine_uses_governance_config(self):
        """Test that engine uses governance configuration."""
        context = create_execution_context(initiator="user:test")
        governance_config = GovernanceConfig(
            policies={"tool.execute": {"outcome": "deny"}},
        )
        engine = PolicyEngine(context, governance_config)

        assert engine.governance_config == governance_config

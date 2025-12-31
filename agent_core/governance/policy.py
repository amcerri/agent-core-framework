"""Policy evaluation engine.

Provides policy evaluation that returns explicit outcomes:
allow, deny, or require-approval. Policies are evaluated at
well-defined enforcement points and outcomes are observable.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from agent_core.configuration.schemas import GovernanceConfig
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.observability import ComponentType, CorrelationFields
from agent_core.observability.logging import get_logger


class PolicyOutcome(str, Enum):
    """Policy evaluation outcome.

    Policies return explicit outcomes that determine whether
    an action is allowed, denied, or requires approval.
    """

    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class PolicyError(Exception):
    """Raised when policy evaluation fails.

    This exception indicates that policy evaluation encountered
    an error (not a denial, but an evaluation failure).
    """

    pass


class PolicyEngine:
    """Policy evaluation engine.

    Evaluates policies based on configuration and execution context.
    Policy evaluation is deterministic and observable.
    """

    def __init__(
        self,
        context: ExecutionContext,
        governance_config: GovernanceConfig | None = None,
    ):
        """Initialize policy engine.

        Args:
            context: Execution context for policy evaluation.
            governance_config: Optional governance configuration.
        """
        self.context = context
        self.governance_config = governance_config or GovernanceConfig()

        # Create correlation for observability
        correlation = CorrelationFields(
            run_id=context.run_id,
            correlation_id=context.correlation_id,
            component_type=ComponentType.RUNTIME,
            component_id="governance:policy",
            component_version="1.0.0",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.logger = get_logger("agent_core.governance.policy", correlation)

    def evaluate_policy(
        self,
        action: str,
        resource_id: str | None = None,
        resource_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PolicyOutcome:
        """Evaluate policy for an action.

        Evaluates policies based on:
        - Action type (e.g., 'tool.execute', 'service.read')
        - Resource identifier and type
        - Execution context (initiator, permissions, budget)
        - Policy configuration

        Args:
            action: Action identifier (e.g., 'tool.execute', 'service.write').
            resource_id: Optional resource identifier.
            resource_type: Optional resource type (e.g., 'tool', 'service').
            metadata: Optional additional metadata for policy evaluation.

        Returns:
            PolicyOutcome indicating allow, deny, or require-approval.

        Raises:
            PolicyError: If policy evaluation fails (not a denial).
        """
        if metadata is None:
            metadata = {}

        policies = self.governance_config.policies

        # If no policies configured, default to ALLOW
        if not policies:
            self.logger.debug(
                "No policies configured, defaulting to ALLOW",
                extra={
                    "action": action,
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                },
            )
            return PolicyOutcome.ALLOW

        # Evaluate policies in order
        # Policy structure: {"action_pattern": {"outcome": "allow|deny|require_approval", ...}}
        # For now, we support simple action-based policies

        # Check for exact action match
        if action in policies:
            policy_config = policies[action]
            outcome = self._evaluate_policy_config(
                policy_config, action, resource_id, resource_type, metadata
            )
            self._log_policy_outcome(action, resource_id, resource_type, outcome)
            return outcome

        # Check for pattern-based policies (e.g., "tool.*" matches "tool.execute")
        for policy_pattern, policy_config in policies.items():
            if self._matches_pattern(action, policy_pattern):
                outcome = self._evaluate_policy_config(
                    policy_config, action, resource_id, resource_type, metadata
                )
                self._log_policy_outcome(action, resource_id, resource_type, outcome)
                return outcome

        # No matching policy, default to ALLOW
        self.logger.debug(
            "No matching policy found, defaulting to ALLOW",
            extra={
                "action": action,
                "resource_id": resource_id,
                "resource_type": resource_type,
            },
        )
        return PolicyOutcome.ALLOW

    def _evaluate_policy_config(
        self,
        policy_config: dict[str, Any],
        action: str,
        resource_id: str | None,
        resource_type: str | None,
        metadata: dict[str, Any],
    ) -> PolicyOutcome:
        """Evaluate a single policy configuration.

        Args:
            policy_config: Policy configuration dictionary.
            action: Action identifier.
            resource_id: Optional resource identifier.
            resource_type: Optional resource type.
            metadata: Additional metadata.

        Returns:
            PolicyOutcome.

        Raises:
            PolicyError: If policy configuration is invalid.
        """
        # Policy config can specify:
        # - "outcome": "allow" | "deny" | "require_approval"
        # - "conditions": {...} (future: conditional evaluation)

        if "outcome" in policy_config:
            outcome_str = policy_config["outcome"]
            try:
                return PolicyOutcome(outcome_str)
            except ValueError as e:
                raise PolicyError(
                    f"Invalid policy outcome: {outcome_str}. "
                    f"Must be one of: {[o.value for o in PolicyOutcome]}"
                ) from e

        # Default to ALLOW if no outcome specified
        return PolicyOutcome.ALLOW

    def _matches_pattern(self, action: str, pattern: str) -> bool:
        """Check if action matches a policy pattern.

        Supports simple wildcard patterns:
        - "tool.*" matches "tool.execute", "tool.read", etc.
        - Exact match if no wildcard

        Args:
            action: Action identifier.
            pattern: Policy pattern.

        Returns:
            True if action matches pattern, False otherwise.
        """
        if pattern == action:
            return True

        # Simple wildcard support: "tool.*" matches "tool.execute"
        if pattern.endswith(".*"):
            prefix = pattern[:-2]
            return action.startswith(prefix + ".")

        return False

    def _log_policy_outcome(
        self,
        action: str,
        resource_id: str | None,
        resource_type: str | None,
        outcome: PolicyOutcome,
    ) -> None:
        """Log policy evaluation outcome.

        Args:
            action: Action identifier.
            resource_id: Optional resource identifier.
            resource_type: Optional resource type.
            outcome: Policy outcome.
        """
        log_level = "info" if outcome == PolicyOutcome.ALLOW else "warning"
        log_message = f"Policy evaluation: {outcome.value}"

        extra = {
            "action": action,
            "outcome": outcome.value,
            "resource_id": resource_id,
            "resource_type": resource_type,
            "initiator": self.context.initiator,
        }

        if log_level == "info":
            self.logger.info(log_message, extra=extra)
        else:
            self.logger.warning(log_message, extra=extra)

    def requires_approval(
        self,
        action: str,
        resource_id: str | None = None,
        resource_type: str | None = None,
    ) -> bool:
        """Check if an action requires approval.

        Convenience method to check if policy outcome is REQUIRE_APPROVAL.

        Args:
            action: Action identifier.
            resource_id: Optional resource identifier.
            resource_type: Optional resource type.

        Returns:
            True if approval is required, False otherwise.
        """
        outcome = self.evaluate_policy(action, resource_id, resource_type)
        return outcome == PolicyOutcome.REQUIRE_APPROVAL

    def is_allowed(
        self,
        action: str,
        resource_id: str | None = None,
        resource_type: str | None = None,
    ) -> bool:
        """Check if an action is allowed.

        Convenience method to check if policy outcome is ALLOW.

        Args:
            action: Action identifier.
            resource_id: Optional resource identifier.
            resource_type: Optional resource type.

        Returns:
            True if action is allowed, False otherwise.
        """
        outcome = self.evaluate_policy(action, resource_id, resource_type)
        return outcome == PolicyOutcome.ALLOW

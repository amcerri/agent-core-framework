"""Unit tests for error classification."""

from agent_core.configuration.loader import ConfigurationError
from agent_core.contracts.errors import ErrorCategory, ErrorSeverity
from agent_core.governance.audit import AuditEmissionError
from agent_core.governance.budget import BudgetExhaustedError
from agent_core.governance.permissions import PermissionError
from agent_core.governance.policy import PolicyError
from agent_core.orchestration.flow_engine import FlowExecutionError
from agent_core.orchestration.yaml_loader import FlowLoadError
from agent_core.runtime.action_execution import ActionExecutionError
from agent_core.runtime.error_classification import ErrorClassifier
from agent_core.runtime.routing import RoutingError


class TestErrorClassifier:
    """Test error classification functionality."""

    def test_classify_permission_error(self):
        """Test classification of PermissionError."""
        error = PermissionError(
            "Permission denied",
            required_permissions=["read", "write"],
            available_permissions={"read": True},
        )
        classified = ErrorClassifier.classify(error, source="tool:test_tool")

        assert classified.error_type == ErrorCategory.PERMISSION_ERROR
        assert classified.severity == ErrorSeverity.HIGH
        assert classified.retryable is False
        assert classified.source == "tool:test_tool"
        assert "required_permissions" in classified.metadata
        assert classified.metadata["required_permissions"] == ["read", "write"]

    def test_classify_budget_exhausted_error(self):
        """Test classification of BudgetExhaustedError."""
        error = BudgetExhaustedError(
            "Budget exhausted",
            budget_type="time",
            limit=60.0,
            consumed=65.0,
        )
        classified = ErrorClassifier.classify(error, source="runtime:test")

        assert classified.error_type == ErrorCategory.BUDGET_EXCEEDED
        assert classified.severity == ErrorSeverity.HIGH
        assert classified.retryable is False
        assert classified.source == "runtime:test"
        assert "budget_type" in classified.metadata
        assert classified.metadata["budget_type"] == "time"

    def test_classify_configuration_error(self):
        """Test classification of ConfigurationError."""
        error = ConfigurationError("Invalid configuration")
        classified = ErrorClassifier.classify(error, source="config:loader")

        assert classified.error_type == ErrorCategory.VALIDATION_ERROR
        assert classified.severity == ErrorSeverity.MEDIUM
        assert classified.retryable is False
        assert classified.source == "config:loader"

    def test_classify_routing_error(self):
        """Test classification of RoutingError."""
        error = RoutingError("Agent not found")
        classified = ErrorClassifier.classify(error, source="runtime:router")

        assert classified.error_type == ErrorCategory.VALIDATION_ERROR
        assert classified.severity == ErrorSeverity.MEDIUM
        assert classified.retryable is False
        assert classified.source == "runtime:router"

    def test_classify_flow_load_error(self):
        """Test classification of FlowLoadError."""
        error = FlowLoadError("Failed to load flow")
        classified = ErrorClassifier.classify(error, source="orchestration:yaml_loader")

        assert classified.error_type == ErrorCategory.VALIDATION_ERROR
        assert classified.severity == ErrorSeverity.MEDIUM
        assert classified.retryable is False

    def test_classify_flow_execution_error(self):
        """Test classification of FlowExecutionError."""
        error = FlowExecutionError("Flow execution failed")
        classified = ErrorClassifier.classify(error, source="orchestration:flow_engine")

        assert classified.error_type == ErrorCategory.EXECUTION_FAILURE
        assert classified.severity == ErrorSeverity.HIGH
        assert classified.retryable is True

    def test_classify_action_execution_error(self):
        """Test classification of ActionExecutionError."""
        error = ActionExecutionError("Action execution failed")
        classified = ErrorClassifier.classify(error, source="runtime:action_executor")

        assert classified.error_type == ErrorCategory.EXECUTION_FAILURE
        assert classified.severity == ErrorSeverity.HIGH
        assert classified.retryable is True

    def test_classify_policy_error(self):
        """Test classification of PolicyError."""
        error = PolicyError("Policy violation")
        classified = ErrorClassifier.classify(error, source="governance:policy")

        assert classified.error_type == ErrorCategory.PERMISSION_ERROR
        assert classified.severity == ErrorSeverity.HIGH
        assert classified.retryable is False

    def test_classify_audit_emission_error(self):
        """Test classification of AuditEmissionError."""
        error = AuditEmissionError("Audit emission failed")
        classified = ErrorClassifier.classify(error, source="governance:audit")

        assert classified.error_type == ErrorCategory.EXECUTION_FAILURE
        assert classified.severity == ErrorSeverity.HIGH
        assert classified.retryable is True

    def test_classify_timeout_error(self):
        """Test classification of TimeoutError."""
        error = TimeoutError("Operation timed out")
        classified = ErrorClassifier.classify(error, source="runtime:timeout")

        assert classified.error_type == ErrorCategory.TIMEOUT
        assert classified.severity == ErrorSeverity.MEDIUM
        assert classified.retryable is True

    def test_classify_unknown_error(self):
        """Test classification of unknown exceptions."""
        error = ValueError("Unknown error")
        classified = ErrorClassifier.classify(error, source="runtime:unknown")

        assert classified.error_type == ErrorCategory.EXECUTION_FAILURE
        assert classified.severity == ErrorSeverity.HIGH
        assert classified.retryable is True
        assert "exception_type" in classified.metadata
        assert classified.metadata["exception_type"] == "ValueError"

    def test_all_errors_conform_to_contract(self):
        """Test that all classified errors conform to the Error contract."""
        test_errors = [
            PermissionError("Permission denied"),
            BudgetExhaustedError("Budget exhausted", "time", 60.0, 65.0),
            ConfigurationError("Invalid config"),
            RoutingError("Routing failed"),
            FlowLoadError("Flow load failed"),
            FlowExecutionError("Flow execution failed"),
            ActionExecutionError("Action failed"),
            PolicyError("Policy violation"),
            AuditEmissionError("Audit failed"),
            TimeoutError("Timeout"),
            ValueError("Unknown error"),
        ]

        for error in test_errors:
            classified = ErrorClassifier.classify(error, source="test:source")

            # Verify all required fields are present
            assert classified.error_id is not None
            assert classified.error_type is not None
            assert classified.message is not None
            assert classified.severity is not None
            assert isinstance(classified.retryable, bool)
            assert classified.source is not None
            assert isinstance(classified.metadata, dict)

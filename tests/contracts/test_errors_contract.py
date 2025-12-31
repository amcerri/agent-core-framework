"""Contract tests for Error model."""

import pytest
from pydantic import ValidationError

from agent_core.contracts.errors import Error, ErrorCategory, ErrorSeverity


class TestErrorSchema:
    """Test Error schema validation."""

    def test_error_creation_with_required_fields(self):
        """Test that Error can be created with all required fields."""
        error = Error(
            error_id="err_123",
            error_type=ErrorCategory.VALIDATION_ERROR,
            message="Invalid input",
            severity=ErrorSeverity.MEDIUM,
            retryable=False,
            source="agent:test_agent",
        )

        assert error.error_id == "err_123"
        assert error.error_type == ErrorCategory.VALIDATION_ERROR
        assert error.message == "Invalid input"
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.retryable is False
        assert error.source == "agent:test_agent"
        assert error.metadata == {}

    def test_error_creation_with_metadata(self):
        """Test that Error can be created with metadata."""
        error = Error(
            error_id="err_123",
            error_type=ErrorCategory.EXECUTION_FAILURE,
            message="Execution failed",
            severity=ErrorSeverity.HIGH,
            retryable=True,
            source="tool:test_tool",
            metadata={"retry_count": 3, "last_error": "timeout"},
        )

        assert error.metadata == {"retry_count": 3, "last_error": "timeout"}

    def test_error_requires_all_required_fields(self):
        """Test that Error requires all mandatory fields."""
        with pytest.raises(ValidationError):
            Error(
                error_id="err_123",
                error_type=ErrorCategory.VALIDATION_ERROR,
                message="Invalid input",
            )

    def test_error_category_enum(self):
        """Test that all error categories are available."""
        categories = [
            ErrorCategory.VALIDATION_ERROR,
            ErrorCategory.PERMISSION_ERROR,
            ErrorCategory.BUDGET_EXCEEDED,
            ErrorCategory.TIMEOUT,
            ErrorCategory.EXECUTION_FAILURE,
            ErrorCategory.DEPENDENCY_FAILURE,
        ]

        for category in categories:
            error = Error(
                error_id="err_123",
                error_type=category,
                message="Test error",
                severity=ErrorSeverity.LOW,
                retryable=False,
                source="test",
            )
            assert error.error_type == category

    def test_error_severity_enum(self):
        """Test that all severity levels are available."""
        severities = [
            ErrorSeverity.LOW,
            ErrorSeverity.MEDIUM,
            ErrorSeverity.HIGH,
            ErrorSeverity.CRITICAL,
        ]

        for severity in severities:
            error = Error(
                error_id="err_123",
                error_type=ErrorCategory.VALIDATION_ERROR,
                message="Test error",
                severity=severity,
                retryable=False,
                source="test",
            )
            assert error.severity == severity

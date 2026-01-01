"""Unit tests for retry policy."""

import time

import pytest

from agent_core.contracts.errors import Error, ErrorCategory, ErrorSeverity
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.governance.budget import BudgetEnforcer, BudgetExhaustedError, BudgetTracker
from agent_core.runtime.retry_policy import RetryPolicy
from agent_core.utils.ids import generate_correlation_id, generate_run_id


def create_test_context() -> ExecutionContext:
    """Create a test execution context."""
    return ExecutionContext(
        run_id=generate_run_id(),
        correlation_id=generate_correlation_id(),
        initiator="test:user",
        permissions={},
        budget={},
        locale="en-US",
        observability={},
    )


class TestRetryPolicy:
    """Test retry policy functionality."""

    def test_should_retry_retryable_error(self):
        """Test that retryable errors are retried."""
        policy = RetryPolicy(max_attempts=3)
        error = Error(
            error_id=generate_run_id(),
            error_type=ErrorCategory.TIMEOUT,
            message="Timeout",
            severity=ErrorSeverity.MEDIUM,
            retryable=True,
            source="test:source",
        )

        assert policy.should_retry(error, attempt=1, is_idempotent=True) is True
        assert policy.should_retry(error, attempt=2, is_idempotent=True) is True
        assert policy.should_retry(error, attempt=3, is_idempotent=True) is False  # Max attempts

    def test_should_retry_non_retryable_error(self):
        """Test that non-retryable errors are not retried."""
        policy = RetryPolicy(max_attempts=3)
        error = Error(
            error_id=generate_run_id(),
            error_type=ErrorCategory.PERMISSION_ERROR,
            message="Permission denied",
            severity=ErrorSeverity.HIGH,
            retryable=False,
            source="test:source",
        )

        assert policy.should_retry(error, attempt=1, is_idempotent=True) is False

    def test_should_retry_non_idempotent_operation(self):
        """Test that non-idempotent operations are not retried."""
        policy = RetryPolicy(max_attempts=3)
        error = Error(
            error_id=generate_run_id(),
            error_type=ErrorCategory.TIMEOUT,
            message="Timeout",
            severity=ErrorSeverity.MEDIUM,
            retryable=True,
            source="test:source",
        )

        assert policy.should_retry(error, attempt=1, is_idempotent=False) is False

    def test_should_retry_validation_error(self):
        """Test that validation errors are never retried."""
        policy = RetryPolicy(max_attempts=3)
        error = Error(
            error_id=generate_run_id(),
            error_type=ErrorCategory.VALIDATION_ERROR,
            message="Validation failed",
            severity=ErrorSeverity.MEDIUM,
            retryable=True,  # Even if marked retryable, validation errors should not retry
            source="test:source",
        )

        assert policy.should_retry(error, attempt=1, is_idempotent=True) is False

    def test_should_retry_permission_error(self):
        """Test that permission errors are never retried."""
        policy = RetryPolicy(max_attempts=3)
        error = Error(
            error_id=generate_run_id(),
            error_type=ErrorCategory.PERMISSION_ERROR,
            message="Permission denied",
            severity=ErrorSeverity.HIGH,
            retryable=True,  # Even if marked retryable, permission errors should not retry
            source="test:source",
        )

        assert policy.should_retry(error, attempt=1, is_idempotent=True) is False

    def test_should_retry_budget_exceeded_error(self):
        """Test that budget exceeded errors are never retried."""
        policy = RetryPolicy(max_attempts=3)
        error = Error(
            error_id=generate_run_id(),
            error_type=ErrorCategory.BUDGET_EXCEEDED,
            message="Budget exceeded",
            severity=ErrorSeverity.HIGH,
            retryable=True,  # Even if marked retryable, budget errors should not retry
            source="test:source",
        )

        assert policy.should_retry(error, attempt=1, is_idempotent=True) is False

    def test_should_retry_budget_exhausted(self):
        """Test that retries are prevented when budget is exhausted."""
        context = create_test_context()
        budget_tracker = BudgetTracker(context)
        budget_tracker.cost_limit = 100.0
        budget_tracker.record_cost(150.0)  # Exceed budget

        budget_enforcer = BudgetEnforcer(budget_tracker, governance_config=None)

        policy = RetryPolicy(
            max_attempts=3,
            budget_tracker=budget_tracker,
            budget_enforcer=budget_enforcer,
        )

        error = Error(
            error_id=generate_run_id(),
            error_type=ErrorCategory.TIMEOUT,
            message="Timeout",
            severity=ErrorSeverity.MEDIUM,
            retryable=True,
            source="test:source",
        )

        # Should not retry because budget is exhausted
        assert policy.should_retry(error, attempt=1, is_idempotent=True) is False

    def test_get_retry_delay(self):
        """Test retry delay calculation."""
        policy = RetryPolicy(
            max_attempts=3,
            initial_delay=1.0,
            max_delay=10.0,
            exponential_base=2.0,
        )

        delay1 = policy.get_retry_delay(attempt=1)
        delay2 = policy.get_retry_delay(attempt=2)
        delay3 = policy.get_retry_delay(attempt=3)

        # Delays should increase exponentially
        assert delay1 > 0
        assert delay2 > delay1
        assert delay3 > delay2

        # Delays should be capped at max_delay
        assert delay1 <= 10.0
        assert delay2 <= 10.0
        assert delay3 <= 10.0

    def test_execute_with_retry_success(self):
        """Test successful execution without retries."""
        policy = RetryPolicy(max_attempts=3)

        def operation():
            return "success"

        context = create_test_context()
        result = policy.execute_with_retry(operation, context, is_idempotent=True)

        assert result == "success"

    def test_execute_with_retry_succeeds_after_retries(self):
        """Test execution that succeeds after retries."""
        policy = RetryPolicy(max_attempts=3, initial_delay=0.1)

        attempt_count = {"count": 0}

        def operation():
            attempt_count["count"] += 1
            if attempt_count["count"] < 3:
                raise TimeoutError("Timeout")
            return "success"

        context = create_test_context()
        result = policy.execute_with_retry(operation, context, is_idempotent=True)

        assert result == "success"
        assert attempt_count["count"] == 3

    def test_execute_with_retry_exhausts_retries(self):
        """Test execution that exhausts all retries."""
        policy = RetryPolicy(max_attempts=3, initial_delay=0.1)

        def operation():
            raise TimeoutError("Timeout")

        context = create_test_context()

        with pytest.raises(TimeoutError, match="Timeout"):
            policy.execute_with_retry(operation, context, is_idempotent=True)

    def test_execute_with_retry_non_retryable_error(self):
        """Test that non-retryable errors are not retried."""
        policy = RetryPolicy(max_attempts=3)

        def operation():
            raise PermissionError("Permission denied")

        context = create_test_context()

        with pytest.raises(PermissionError, match="Permission denied"):
            policy.execute_with_retry(operation, context, is_idempotent=True)

    def test_execute_with_retry_non_idempotent_operation(self):
        """Test that non-idempotent operations are not retried."""
        policy = RetryPolicy(max_attempts=3)

        def operation():
            raise TimeoutError("Timeout")

        context = create_test_context()

        with pytest.raises(TimeoutError, match="Timeout"):
            policy.execute_with_retry(operation, context, is_idempotent=False)

    def test_execute_with_retry_respects_budget(self):
        """Test that retries respect budget constraints."""
        context = create_test_context()
        budget_tracker = BudgetTracker(context)
        budget_tracker.cost_limit = 100.0
        budget_tracker.record_cost(150.0)  # Exceed budget

        budget_enforcer = BudgetEnforcer(budget_tracker, governance_config=None)

        policy = RetryPolicy(
            max_attempts=3,
            budget_tracker=budget_tracker,
            budget_enforcer=budget_enforcer,
        )

        def operation():
            raise TimeoutError("Timeout")

        # Should not retry due to budget exhaustion
        with pytest.raises(TimeoutError, match="Timeout"):
            policy.execute_with_retry(operation, context, is_idempotent=True)

    def test_retry_policy_deterministic(self):
        """Test that retry policy behavior is deterministic."""
        policy = RetryPolicy(max_attempts=3, initial_delay=1.0)

        error = Error(
            error_id=generate_run_id(),
            error_type=ErrorCategory.TIMEOUT,
            message="Timeout",
            severity=ErrorSeverity.MEDIUM,
            retryable=True,
            source="test:source",
        )

        # Same inputs should produce same results
        result1 = policy.should_retry(error, attempt=1, is_idempotent=True)
        result2 = policy.should_retry(error, attempt=1, is_idempotent=True)

        assert result1 == result2


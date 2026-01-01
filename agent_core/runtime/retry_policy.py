"""Retry policy implementation.

Implements retry logic that respects idempotency and budget constraints.
Retries are only performed for retryable errors and when budgets allow.
"""

import random
import time
from collections.abc import Callable
from typing import Any

from agent_core.contracts.errors import Error, ErrorCategory
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.governance.budget import BudgetEnforcer, BudgetExhaustedError, BudgetTracker


class RetryPolicy:
    """Retry policy that respects idempotency and budget constraints.

    Retries are only performed when:
    - The error is retryable (Error.retryable == True)
    - The operation is idempotent (if applicable)
    - Budget constraints allow retries
    - Maximum retry attempts have not been exceeded
    """

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        budget_tracker: BudgetTracker | None = None,
        budget_enforcer: BudgetEnforcer | None = None,
    ):
        """Initialize retry policy.

        Args:
            max_attempts: Maximum number of retry attempts (including initial attempt).
            initial_delay: Initial delay in seconds before first retry.
            max_delay: Maximum delay in seconds between retries.
            exponential_base: Base for exponential backoff calculation.
            budget_tracker: Optional budget tracker for checking budget constraints.
            budget_enforcer: Optional budget enforcer for enforcing budget limits.
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.budget_tracker = budget_tracker
        self.budget_enforcer = budget_enforcer

    def should_retry(
        self,
        error: Error,
        attempt: int,
        is_idempotent: bool = True,
    ) -> bool:
        """Determine if an error should be retried.

        Args:
            error: Structured error object.
            attempt: Current attempt number (1-indexed, 1 = initial attempt).
            is_idempotent: Whether the operation is idempotent. Defaults to True.

        Returns:
            True if the error should be retried, False otherwise.

        Notes:
            - Non-retryable errors are never retried.
            - Non-idempotent operations are never retried (safety).
            - Budget constraints are checked before retrying.
            - Maximum attempts must not be exceeded.
        """
        # Never retry if max attempts exceeded
        if attempt >= self.max_attempts:
            return False

        # Never retry non-retryable errors
        if not error.retryable:
            return False

        # Never retry non-idempotent operations (safety)
        if not is_idempotent:
            return False

        # Never retry certain error categories
        if error.error_type in (
            ErrorCategory.VALIDATION_ERROR,
            ErrorCategory.PERMISSION_ERROR,
            ErrorCategory.BUDGET_EXCEEDED,
        ):
            return False

        # Check budget constraints
        if self.budget_enforcer is not None:
            try:
                self.budget_enforcer.check_budget()
            except BudgetExhaustedError:
                # Budget exhausted - cannot retry
                return False

        return True

    def get_retry_delay(self, attempt: int) -> float:
        """Calculate delay before next retry attempt.

        Args:
            attempt: Current attempt number (1-indexed).

        Returns:
            Delay in seconds before next retry attempt.

        Notes:
            - Uses exponential backoff with jitter.
            - Delay is capped at max_delay.
        """
        # Calculate exponential backoff: initial_delay * (exponential_base ^ (attempt - 1))
        delay = self.initial_delay * (self.exponential_base ** (attempt - 1))

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add small jitter to prevent thundering herd
        jitter = random.uniform(0.0, delay * 0.1)  # 10% jitter
        delay = delay + jitter

        return delay

    def execute_with_retry(
        self,
        operation: Callable[[], Any],
        context: ExecutionContext,
        is_idempotent: bool = True,
        error_classifier: Callable[[Exception, str], Error] | None = None,
        source: str = "runtime:retry_policy",
    ) -> Any:
        """Execute an operation with retry logic.

        Args:
            operation: Callable to execute (no arguments).
            context: Execution context for the operation.
            is_idempotent: Whether the operation is idempotent. Defaults to True.
            error_classifier: Optional function to classify exceptions. If None, uses default.
            source: Source component identifier for error classification.

        Returns:
            Result of the operation if successful.

        Raises:
            Exception: The last exception raised if all retries are exhausted.

        Notes:
            - Retries are only performed for retryable errors.
            - Budget constraints are checked before each retry.
            - Idempotency constraints are enforced.
        """
        from agent_core.runtime.error_classification import ErrorClassifier

        if error_classifier is None:
            error_classifier = ErrorClassifier.classify

        last_exception: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                # Execute operation
                result = operation()
                return result

            except Exception as e:
                # Classify error
                error = error_classifier(e, source)
                last_exception = e

                # Check if we should retry
                if not self.should_retry(error, attempt, is_idempotent=is_idempotent):
                    # Cannot retry - raise exception
                    raise e

                # Calculate delay before retry
                delay = self.get_retry_delay(attempt)

                # Wait before retry
                time.sleep(delay)

        # All retries exhausted - raise last exception
        if last_exception is not None:
            raise last_exception

        # Should not reach here, but raise generic error if we do
        raise RuntimeError("Retry policy execution failed without exception")

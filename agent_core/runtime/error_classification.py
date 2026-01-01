"""Error classification and mapping.

Maps exceptions to structured Error objects conforming to the error contract.
All errors must be classified according to the ErrorCategory enumeration.
"""

from typing import Any

from agent_core.configuration.loader import ConfigurationError
from agent_core.contracts.errors import Error, ErrorCategory, ErrorSeverity
from agent_core.governance.audit import AuditEmissionError
from agent_core.governance.budget import BudgetExhaustedError
from agent_core.governance.permissions import PermissionError
from agent_core.governance.policy import PolicyError
from agent_core.orchestration.flow_engine import FlowExecutionError
from agent_core.orchestration.yaml_loader import FlowLoadError
from agent_core.runtime.action_execution import ActionExecutionError
from agent_core.runtime.routing import RoutingError
from agent_core.utils.ids import generate_run_id


class ErrorClassifier:
    """Classifies exceptions and converts them to structured Error objects.

    All exceptions must be mapped to one of the standard ErrorCategory values.
    Classification determines retryability and error handling behavior.
    """

    @staticmethod
    def classify(exception: Exception, source: str) -> Error:
        """Classify an exception and convert it to a structured Error.

        Args:
            exception: Exception to classify.
            source: Source component identifier (e.g., 'agent:my_agent', 'tool:my_tool').

        Returns:
            Structured Error object conforming to the error contract.

        Notes:
            - All errors must conform to the Error schema.
            - Retryability is determined by error category and context.
            - Non-retryable errors: validation_error, permission_error, budget_exceeded.
            - Potentially retryable errors: timeout, execution_failure, dependency_failure.
        """
        # Map known exception types to error categories
        if isinstance(exception, PermissionError):
            return ErrorClassifier._classify_permission_error(exception, source)
        elif isinstance(exception, BudgetExhaustedError):
            return ErrorClassifier._classify_budget_error(exception, source)
        elif isinstance(exception, ConfigurationError):
            return ErrorClassifier._classify_validation_error(exception, source)
        elif isinstance(exception, RoutingError):
            return ErrorClassifier._classify_routing_error(exception, source)
        elif isinstance(exception, FlowLoadError):
            return ErrorClassifier._classify_validation_error(exception, source)
        elif isinstance(exception, FlowExecutionError):
            return ErrorClassifier._classify_execution_failure(exception, source)
        elif isinstance(exception, ActionExecutionError):
            return ErrorClassifier._classify_action_execution_error(exception, source)
        elif isinstance(exception, PolicyError):
            return ErrorClassifier._classify_permission_error(exception, source)
        elif isinstance(exception, AuditEmissionError):
            # Audit errors are typically non-fatal but should be logged
            return ErrorClassifier._classify_execution_failure(exception, source)
        elif isinstance(exception, TimeoutError):
            return ErrorClassifier._classify_timeout_error(exception, source)
        else:
            # Unknown exception - classify as execution_failure
            return ErrorClassifier._classify_unknown_error(exception, source)

    @staticmethod
    def _classify_permission_error(exception: PermissionError, source: str) -> Error:
        """Classify permission-related errors.

        Permission errors are non-retryable as they indicate authorization failures.
        """
        metadata: dict[str, Any] = {}
        if hasattr(exception, "required_permissions"):
            metadata["required_permissions"] = exception.required_permissions
        if hasattr(exception, "available_permissions"):
            metadata["available_permissions"] = list(exception.available_permissions.keys())

        return Error(
            error_id=generate_run_id(),
            error_type=ErrorCategory.PERMISSION_ERROR,
            message=str(exception),
            severity=ErrorSeverity.HIGH,
            retryable=False,
            source=source,
            metadata=metadata,
        )

    @staticmethod
    def _classify_budget_error(exception: BudgetExhaustedError, source: str) -> Error:
        """Classify budget-related errors.

        Budget errors are non-retryable as they indicate resource limits.
        """
        metadata: dict[str, Any] = {}
        if hasattr(exception, "budget_type"):
            metadata["budget_type"] = exception.budget_type
        if hasattr(exception, "limit"):
            metadata["limit"] = exception.limit
        if hasattr(exception, "consumed"):
            metadata["consumed"] = exception.consumed

        return Error(
            error_id=generate_run_id(),
            error_type=ErrorCategory.BUDGET_EXCEEDED,
            message=str(exception),
            severity=ErrorSeverity.HIGH,
            retryable=False,
            source=source,
            metadata=metadata,
        )

    @staticmethod
    def _classify_validation_error(exception: Exception, source: str) -> Error:
        """Classify validation-related errors.

        Validation errors are non-retryable as they indicate invalid input or configuration.
        """
        return Error(
            error_id=generate_run_id(),
            error_type=ErrorCategory.VALIDATION_ERROR,
            message=str(exception),
            severity=ErrorSeverity.MEDIUM,
            retryable=False,
            source=source,
            metadata={"exception_type": type(exception).__name__},
        )

    @staticmethod
    def _classify_timeout_error(exception: TimeoutError, source: str) -> Error:
        """Classify timeout errors.

        Timeout errors are potentially retryable, depending on context and idempotency.
        """
        return Error(
            error_id=generate_run_id(),
            error_type=ErrorCategory.TIMEOUT,
            message=str(exception),
            severity=ErrorSeverity.MEDIUM,
            retryable=True,  # Timeouts are potentially retryable
            source=source,
            metadata={"exception_type": type(exception).__name__},
        )

    @staticmethod
    def _classify_execution_failure(exception: Exception, source: str) -> Error:
        """Classify execution failure errors.

        Execution failures are potentially retryable, depending on context and idempotency.
        """
        return Error(
            error_id=generate_run_id(),
            error_type=ErrorCategory.EXECUTION_FAILURE,
            message=str(exception),
            severity=ErrorSeverity.HIGH,
            retryable=True,  # Execution failures are potentially retryable
            source=source,
            metadata={"exception_type": type(exception).__name__},
        )

    @staticmethod
    def _classify_routing_error(exception: RoutingError, source: str) -> Error:
        """Classify routing errors.

        Routing errors are typically non-retryable as they indicate configuration issues.
        """
        return Error(
            error_id=generate_run_id(),
            error_type=ErrorCategory.VALIDATION_ERROR,  # Routing errors are validation-like
            message=str(exception),
            severity=ErrorSeverity.MEDIUM,
            retryable=False,
            source=source,
            metadata={"exception_type": type(exception).__name__},
        )

    @staticmethod
    def _classify_action_execution_error(exception: ActionExecutionError, source: str) -> Error:
        """Classify action execution errors.

        Action execution errors may be retryable depending on the underlying cause.
        For now, we classify them as execution_failure (potentially retryable).
        """
        return Error(
            error_id=generate_run_id(),
            error_type=ErrorCategory.EXECUTION_FAILURE,
            message=str(exception),
            severity=ErrorSeverity.HIGH,
            retryable=True,  # Action execution errors are potentially retryable
            source=source,
            metadata={"exception_type": type(exception).__name__},
        )

    @staticmethod
    def _classify_unknown_error(exception: Exception, source: str) -> Error:
        """Classify unknown exceptions.

        Unknown exceptions are classified as execution_failure and are potentially retryable.
        """
        return Error(
            error_id=generate_run_id(),
            error_type=ErrorCategory.EXECUTION_FAILURE,
            message=str(exception),
            severity=ErrorSeverity.HIGH,
            retryable=True,  # Unknown errors are potentially retryable (conservative)
            source=source,
            metadata={
                "exception_type": type(exception).__name__,
                "exception_module": type(exception).__module__,
            },
        )

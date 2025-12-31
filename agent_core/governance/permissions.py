"""Permission evaluation logic.

Provides permission checking and evaluation for tools and services.
Permissions are resolved before execution and missing permissions
result in immediate failure.
"""

from datetime import datetime, timezone
from typing import Any

from agent_core.contracts.errors import Error, ErrorCategory, ErrorSeverity
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.observability import ComponentType, CorrelationFields
from agent_core.observability.logging import get_logger
from agent_core.utils.ids import generate_run_id


class PermissionError(Exception):
    """Raised when permission evaluation fails.

    This exception indicates that required permissions are missing
    or insufficient for the requested action.
    """

    def __init__(
        self,
        message: str,
        required_permissions: list[str] | None = None,
        available_permissions: dict[str, Any] | None = None,
    ):
        """Initialize permission error.

        Args:
            message: Human-readable error message.
            required_permissions: List of permissions that were required.
            available_permissions: Available permissions from context.
        """
        super().__init__(message)
        self.required_permissions = required_permissions or []
        self.available_permissions = available_permissions or {}


class PermissionEvaluator:
    """Evaluates permissions for tools and services.

    Checks if required permissions are present in the execution context.
    Permission evaluation is deterministic and observable.
    """

    def __init__(self, context: ExecutionContext):
        """Initialize permission evaluator.

        Args:
            context: Execution context containing permissions.
        """
        self.context = context

        # Create correlation for observability
        correlation = CorrelationFields(
            run_id=context.run_id,
            correlation_id=context.correlation_id,
            component_type=ComponentType.RUNTIME,
            component_id="governance:permissions",
            component_version="1.0.0",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.logger = get_logger("agent_core.governance.permissions", correlation)

    def check_permissions(
        self,
        required_permissions: list[str],
        resource_id: str | None = None,
        resource_type: str | None = None,
    ) -> bool:
        """Check if all required permissions are present.

        Args:
            required_permissions: List of permission identifiers required.
            resource_id: Optional resource identifier (for logging).
            resource_type: Optional resource type (e.g., 'tool', 'service').

        Returns:
            True if all required permissions are present, False otherwise.

        Raises:
            PermissionError: If required permissions are missing.
        """
        if not required_permissions:
            # No permissions required, always allowed
            return True

        available_permissions = self.context.permissions

        # Check if all required permissions are present
        missing_permissions = []
        for perm in required_permissions:
            # Permissions can be:
            # 1. Boolean flags (e.g., {"read": True, "write": False})
            # 2. List of granted permissions (e.g., {"permissions": ["read", "write"]})
            # 3. Nested structures (e.g., {"tools": {"tool1": True}})

            if not self._has_permission(perm, available_permissions):
                missing_permissions.append(perm)

        if missing_permissions:
            error_message = (
                f"Missing required permissions: {missing_permissions}. "
                f"Available permissions: {list(available_permissions.keys())}"
            )

            # Log permission denial
            self.logger.warning(
                "Permission check failed",
                extra={
                    "required_permissions": required_permissions,
                    "missing_permissions": missing_permissions,
                    "resource_id": resource_id,
                    "resource_type": resource_type,
                    "initiator": self.context.initiator,
                },
            )

            raise PermissionError(
                error_message,
                required_permissions=required_permissions,
                available_permissions=available_permissions,
            )

        # Log permission grant
        self.logger.debug(
            "Permission check passed",
            extra={
                "required_permissions": required_permissions,
                "resource_id": resource_id,
                "resource_type": resource_type,
            },
        )

        return True

    def _has_permission(self, permission: str, available_permissions: dict[str, Any]) -> bool:
        """Check if a specific permission is granted.

        Supports multiple permission formats:
        - Boolean flags: {"read": True}
        - List format: {"permissions": ["read", "write"]}
        - Nested structures: {"tools": {"tool1": True}}

        Args:
            permission: Permission identifier to check.
            available_permissions: Available permissions dictionary.

        Returns:
            True if permission is granted, False otherwise.
        """
        # Direct boolean flag
        if permission in available_permissions:
            value = available_permissions[permission]
            if isinstance(value, bool):
                return value
            # Non-boolean values are treated as granted if present
            return True

        # Check in "permissions" list
        if "permissions" in available_permissions:
            perms_list = available_permissions["permissions"]
            if isinstance(perms_list, list):
                return permission in perms_list

        # Check nested structures (e.g., {"tools": {"tool1": True}})
        # Try to find permission as a key in nested dicts
        for _key, value in available_permissions.items():
            if isinstance(value, dict):
                if permission in value:
                    perm_value = value[permission]
                    if isinstance(perm_value, bool):
                        return perm_value
                    return True

        return False

    def to_error(
        self,
        permission_error: PermissionError,
        source: str,
    ) -> Error:
        """Convert PermissionError to structured Error.

        Args:
            permission_error: PermissionError instance.
            source: Source component identifier.

        Returns:
            Structured Error instance.
        """
        return Error(
            error_id=generate_run_id(),  # Use run_id generator for error_id
            error_type=ErrorCategory.PERMISSION_ERROR,
            message=str(permission_error),
            severity=ErrorSeverity.HIGH,
            retryable=False,
            source=source,
            metadata={
                "required_permissions": permission_error.required_permissions,
                "available_permissions": list(permission_error.available_permissions.keys()),
            },
        )

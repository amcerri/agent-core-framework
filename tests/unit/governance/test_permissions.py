"""Unit tests for permission evaluation."""

import pytest

from agent_core.contracts.execution_context import ExecutionContext
from agent_core.governance.permissions import PermissionError, PermissionEvaluator
from agent_core.runtime.execution_context import create_execution_context


class TestPermissionEvaluator:
    """Test PermissionEvaluator."""

    def test_check_permissions_no_required(self):
        """Test that no required permissions always passes."""
        context = create_execution_context(initiator="user:test", permissions={})
        evaluator = PermissionEvaluator(context)

        assert evaluator.check_permissions([]) is True

    def test_check_permissions_boolean_flag(self):
        """Test permission check with boolean flags."""
        context = create_execution_context(
            initiator="user:test",
            permissions={"read": True, "write": False},
        )
        evaluator = PermissionEvaluator(context)

        # Should pass with read permission
        assert evaluator.check_permissions(["read"]) is True

        # Should fail with write permission (False)
        with pytest.raises(PermissionError, match="Missing required permissions"):
            evaluator.check_permissions(["write"])

    def test_check_permissions_list_format(self):
        """Test permissions in list format."""
        context = create_execution_context(
            initiator="user:test",
            permissions={"permissions": ["read", "write", "execute"]},
        )
        evaluator = PermissionEvaluator(context)

        assert evaluator.check_permissions(["read"]) is True
        assert evaluator.check_permissions(["read", "write"]) is True

        with pytest.raises(PermissionError):
            evaluator.check_permissions(["delete"])

    def test_check_permissions_nested_structure(self):
        """Test permissions in nested structure."""
        context = create_execution_context(
            initiator="user:test",
            permissions={"tools": {"tool1": True, "tool2": False}},
        )
        evaluator = PermissionEvaluator(context)

        # Should work with nested structure - check for permission that exists
        assert evaluator.check_permissions(["tool1"]) is True

        # Should fail for permission that is False in nested structure
        with pytest.raises(PermissionError):
            evaluator.check_permissions(["tool2"])

        # Should fail for permission that doesn't exist in nested structure
        with pytest.raises(PermissionError):
            evaluator.check_permissions(["tool3"])

    def test_check_permissions_multiple_required(self):
        """Test checking multiple required permissions."""
        context = create_execution_context(
            initiator="user:test",
            permissions={"read": True, "write": True, "execute": False},
        )
        evaluator = PermissionEvaluator(context)

        assert evaluator.check_permissions(["read", "write"]) is True

        with pytest.raises(PermissionError, match="Missing required permissions"):
            evaluator.check_permissions(["read", "execute"])

    def test_check_permissions_missing_all(self):
        """Test when all required permissions are missing."""
        context = create_execution_context(
            initiator="user:test",
            permissions={"read": True},
        )
        evaluator = PermissionEvaluator(context)

        with pytest.raises(PermissionError) as exc_info:
            evaluator.check_permissions(["write", "delete"])

        assert "write" in exc_info.value.required_permissions
        assert "delete" in exc_info.value.required_permissions

    def test_check_permissions_with_resource_info(self):
        """Test permission check with resource information."""
        context = create_execution_context(
            initiator="user:test",
            permissions={"read": True},
        )
        evaluator = PermissionEvaluator(context)

        # Should not raise, just log resource info
        assert (
            evaluator.check_permissions(["read"], resource_id="tool1", resource_type="tool") is True
        )

    def test_to_error(self):
        """Test converting PermissionError to structured Error."""
        context = create_execution_context(initiator="user:test", permissions={})
        evaluator = PermissionEvaluator(context)

        try:
            evaluator.check_permissions(["write"])
        except PermissionError as e:
            error = evaluator.to_error(e, source="test:component")
            assert error.error_type.value == "permission_error"
            assert error.severity.value == "high"
            assert error.retryable is False
            assert "write" in error.metadata["required_permissions"]

    def test_permission_evaluator_uses_context(self):
        """Test that evaluator uses execution context."""
        context = create_execution_context(
            initiator="user:test",
            permissions={"read": True},
        )
        evaluator = PermissionEvaluator(context)

        assert evaluator.context == context

"""Unit tests for BaseService."""

import pytest

from agent_core.contracts.execution_context import ExecutionContext
from agent_core.runtime.execution_context import create_execution_context
from agent_core.services.base import BaseService


class ConcreteService(BaseService):
    """Concrete service implementation for testing."""

    def __init__(self, service_id: str, version: str, capabilities: list[str]):
        """Initialize concrete service."""
        self._service_id = service_id
        self._version = version
        self._capabilities = capabilities

    @property
    def service_id(self) -> str:
        """Service identifier."""
        return self._service_id

    @property
    def service_version(self) -> str:
        """Service version."""
        return self._version

    @property
    def capabilities(self) -> list[str]:
        """Service capabilities."""
        return self._capabilities

    def check_permission(self, action: str, context: ExecutionContext) -> bool:
        """Check permission."""
        # Simple permission check: allow if action is in context permissions
        permissions = context.permissions
        if isinstance(permissions, dict):
            return permissions.get(action, False)
        return False


class TestBaseService:
    """Test BaseService."""

    def test_base_service_is_abstract(self):
        """Test that BaseService cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseService()  # type: ignore

    def test_concrete_service_implements_interface(self):
        """Test that concrete service implements the Service interface."""
        service = ConcreteService("service1", "1.0.0", ["read", "write"])

        assert service.service_id == "service1"
        assert service.service_version == "1.0.0"
        assert service.capabilities == ["read", "write"]

    def test_concrete_service_check_permission(self):
        """Test that concrete service can check permissions."""
        service = ConcreteService("service1", "1.0.0", ["read"])
        context = create_execution_context(
            initiator="user:test",
            permissions={"read": True, "write": False},
        )

        assert service.check_permission("read", context) is True
        assert service.check_permission("write", context) is False
        assert service.check_permission("delete", context) is False

    def test_service_conforms_to_protocol(self):
        """Test that BaseService subclasses conform to Service Protocol."""
        service = ConcreteService("service1", "1.0.0", ["read"])

        # Type check: service should be assignable to Service Protocol
        service_protocol: BaseService = service
        assert service_protocol.service_id == "service1"

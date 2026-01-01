# Creating Services

This guide explains how to create custom services for the Agent Core Framework.

## Service Contract

Services provide governed access to shared capabilities:

- Own persistent or shared state
- Enforce access control and auditing
- Abstract vendor-specific implementations
- Provide governed access to resources

Contract: [agent_core/contracts/service.py](../agent_core/contracts/service.py)

## Base Service Class

The framework provides `BaseService` as a foundation for implementing services:

```python
from agent_core.services.base import BaseService
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.service import ServiceInput, ServiceResult

class MyService(BaseService):
    @property
    def service_id(self) -> str:
        return "my_service"
    
    @property
    def service_version(self) -> str:
        return "1.0.0"
    
    @property
    def capabilities(self) -> list[str]:
        return ["storage", "retrieval"]
    
    def check_permission(self, action: str, context: ExecutionContext) -> bool:
        # Check if action is permitted
        pass
    
    def execute(
        self, input_data: ServiceInput, context: ExecutionContext
    ) -> ServiceResult:
        # Execute service action
        # Return structured result
        pass
```

Base class: [agent_core/services/base.py](../agent_core/services/base.py)

## Service Implementation Example

```python
from agent_core.services.base import BaseService
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.service import ServiceInput, ServiceResult

class StorageService(BaseService):
    def __init__(self):
        self._storage = {}  # Service-owned state
    
    @property
    def service_id(self) -> str:
        return "storage_service"
    
    @property
    def service_version(self) -> str:
        return "1.0.0"
    
    @property
    def capabilities(self) -> list[str]:
        return ["storage", "retrieval"]
    
    def check_permission(self, action: str, context: ExecutionContext) -> bool:
        # Check permissions from context
        permissions = context.permissions
        if action in ["read", "get"]:
            return permissions.get("read", False) or permissions.get("storage", False)
        elif action in ["write", "set"]:
            return permissions.get("write", False) or permissions.get("storage", False)
        return False
    
    def execute(
        self, input_data: ServiceInput, context: ExecutionContext
    ) -> ServiceResult:
        """Execute a service action.
        
        Supported actions: "get", "set"
        """
        action = input_data.action
        payload = input_data.payload
        
        # Check permission (runtime also checks, but service should verify)
        if not self.check_permission(action, context):
            return ServiceResult(
                status="error",
                output={},
                errors=[{"error": "permission_denied"}],
                metrics={},
            )
        
        # Execute action
        if action == "get":
            key = payload.get("key")
            value = self._storage.get(key) if key else None
            return ServiceResult(
                status="success",
                output={"key": key, "value": value},
                errors=[],
                metrics={},
            )
        elif action == "set":
            key = payload.get("key")
            value = payload.get("value")
            if key and value:
                self._storage[key] = value
                return ServiceResult(
                    status="success",
                    output={"key": key, "stored": True},
                    errors=[],
                    metrics={},
                )
            return ServiceResult(
                status="error",
                output={},
                errors=[{"error": "missing_parameters"}],
                metrics={},
            )
        else:
            return ServiceResult(
                status="error",
                output={},
                errors=[{"error": "unknown_action"}],
                metrics={},
            )
    
    def get(self, key: str) -> dict | None:
        """Service-specific method (not part of base contract)."""
        return self._storage.get(key)
    
    def set(self, key: str, value: dict) -> None:
        """Service-specific method (not part of base contract)."""
        self._storage[key] = value
```

## Service Registration

Register services with the runtime:

```python
from agent_core.runtime import Runtime
from agent_core.configuration.loader import load_config

config = load_config()
runtime = Runtime(config=config)

# Register service
service = StorageService()
runtime.register_service(service)
```

## Service Responsibilities

Services should:

- ✅ Own persistent or shared state
- ✅ Enforce access control via `check_permission`
- ✅ Abstract vendor-specific implementations
- ✅ Provide governed access to resources

Services should not:

- ❌ Allow direct state mutation from agents/tools
- ❌ Bypass access control checks
- ❌ Leak vendor-specific concepts into core

## Related Documentation

- [Overview](./overview.md) - Framework introduction
- [Architecture](./architecture.md) - System architecture
- [Runtime API](./runtime-api.md) - Runtime execution
- [Contracts](./contracts.md) - Service contract details

---

Back to [docs index](./README.md)  
Back to [repository root](../README.md)


"""Runtime components for Agent Core Framework.

This package provides the core runtime that manages execution lifecycle,
context propagation, and component orchestration.
"""

from agent_core.runtime.execution_context import (
    create_execution_context,
    ensure_immutable,
    propagate_execution_context,
)
from agent_core.runtime.lifecycle import (
    LifecycleEvent,
    LifecycleManager,
    LifecycleState,
)
from agent_core.runtime.routing import Router, RoutingError
from agent_core.runtime.runtime import Runtime

__all__ = [
    "LifecycleEvent",
    "LifecycleManager",
    "LifecycleState",
    "Router",
    "RoutingError",
    "Runtime",
    "create_execution_context",
    "ensure_immutable",
    "propagate_execution_context",
]


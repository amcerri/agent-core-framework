"""Runtime components for Agent Core Framework.

This package provides the core runtime that manages execution lifecycle,
context propagation, component orchestration, and action execution.
"""

from agent_core.runtime.action_execution import ActionExecutionError, ActionExecutor
from agent_core.runtime.error_classification import ErrorClassifier
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
from agent_core.runtime.retry_policy import RetryPolicy
from agent_core.runtime.routing import Router, RoutingError
from agent_core.runtime.runtime import Runtime

__all__ = [
    "ActionExecutionError",
    "ActionExecutor",
    "ErrorClassifier",
    "LifecycleEvent",
    "LifecycleManager",
    "LifecycleState",
    "RetryPolicy",
    "Router",
    "RoutingError",
    "Runtime",
    "create_execution_context",
    "ensure_immutable",
    "propagate_execution_context",
]

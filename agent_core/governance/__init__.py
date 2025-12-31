"""Governance infrastructure for Agent Core Framework.

This package provides permissions evaluation and policy enforcement
for the framework. Governance is enforced centrally by the runtime.
"""

from agent_core.governance.permissions import PermissionError, PermissionEvaluator
from agent_core.governance.policy import PolicyEngine, PolicyOutcome

__all__ = [
    "PermissionError",
    "PermissionEvaluator",
    "PolicyEngine",
    "PolicyOutcome",
]

"""Observability infrastructure for Agent Core Framework.

This package provides interfaces and implementations for emitting
observability signals (logs, traces, metrics, audit events).
"""

from agent_core.observability.interface import ObservabilitySink
from agent_core.observability.noop import NoOpObservabilitySink

__all__ = ["ObservabilitySink", "NoOpObservabilitySink"]

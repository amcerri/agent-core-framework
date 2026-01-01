"""Orchestration infrastructure for Agent Core Framework.

This package provides flow engine interfaces and implementations for
executing declarative orchestration graphs.
"""

from agent_core.orchestration.base import BaseFlowEngine
from agent_core.orchestration.flow_engine import FlowExecutionError, SimpleFlowEngine
from agent_core.orchestration.scheduler import ScheduledTask, Scheduler
from agent_core.orchestration.state import FlowStateManager
from agent_core.orchestration.yaml_loader import (
    FlowLoadError,
    load_flow_from_dict,
    load_flow_from_yaml,
)

# LangGraphFlowEngine is conditionally exported if LangGraph is available
try:
    from agent_core.orchestration.langgraph_engine import LangGraphFlowEngine

    __all__ = [
        "BaseFlowEngine",
        "FlowExecutionError",
        "FlowStateManager",
        "FlowLoadError",
        "LangGraphFlowEngine",
        "Scheduler",
        "ScheduledTask",
        "SimpleFlowEngine",
        "load_flow_from_dict",
        "load_flow_from_yaml",
    ]
except ImportError:
    # LangGraph not available
    __all__ = [
        "BaseFlowEngine",
        "FlowExecutionError",
        "FlowStateManager",
        "FlowLoadError",
        "Scheduler",
        "ScheduledTask",
        "SimpleFlowEngine",
        "load_flow_from_dict",
        "load_flow_from_yaml",
    ]

# For backward compatibility, FlowEngine is an alias for SimpleFlowEngine
FlowEngine = SimpleFlowEngine

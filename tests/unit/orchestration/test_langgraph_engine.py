"""Unit tests for LangGraph flow engine.

Tests verify that LangGraph types do not leak outside the orchestration package
and that the implementation remains replaceable.
"""

import pytest

from agent_core.configuration.schemas import AgentCoreConfig, FlowConfig, RuntimeConfig
from agent_core.orchestration.base import BaseFlowEngine
from agent_core.orchestration.flow_engine import FlowExecutionError
from agent_core.runtime.execution_context import create_execution_context
from agent_core.runtime.runtime import Runtime


class TestLangGraphTypeIsolation:
    """Test that LangGraph types do not leak outside orchestration package."""

    def test_langgraph_imports_isolated(self):
        """Test that LangGraph imports are only in langgraph_engine module."""
        # Import orchestration package
        import agent_core.orchestration

        # Check that LangGraph types are not in public API
        public_api = dir(agent_core.orchestration)

        # LangGraph-specific types should not be in public API
        langgraph_types = ["StateGraph", "END", "START", "add_messages"]
        for langgraph_type in langgraph_types:
            assert langgraph_type not in public_api, (
                f"LangGraph type {langgraph_type} leaked to public API"
            )

    def test_langgraph_engine_implements_base_interface(self):
        """Test that LangGraphFlowEngine implements BaseFlowEngine interface."""
        try:
            from agent_core.orchestration.langgraph_engine import LangGraphFlowEngine

            # Check that it's a subclass of BaseFlowEngine
            assert issubclass(LangGraphFlowEngine, BaseFlowEngine)

            # Check that it has required methods
            assert hasattr(LangGraphFlowEngine, "execute")
            assert hasattr(LangGraphFlowEngine, "get_state")
        except ImportError:
            # LangGraph not available, skip test
            pytest.skip("LangGraph not available")

    def test_langgraph_engine_not_available_raises_error(self):
        """Test that LangGraphFlowEngine raises error when LangGraph is not available."""
        # This test verifies the error handling when LangGraph is not installed
        # We can't easily test this without mocking, but the code should handle it gracefully
        try:
            from agent_core.orchestration.langgraph_engine import LANGGRAPH_AVAILABLE

            if not LANGGRAPH_AVAILABLE:
                # Try to create engine - should raise error
                config = AgentCoreConfig(runtime=RuntimeConfig(runtime_id="test"))
                runtime = Runtime(config=config)
                context = create_execution_context(initiator="user:test")
                flow_config = FlowConfig(
                    flow_id="test",
                    version="1.0.0",
                    entrypoint="start",
                    nodes={"start": {"type": "agent", "agent_id": "agent1"}},
                    transitions=[],
                )

                from agent_core.orchestration.langgraph_engine import LangGraphFlowEngine

                with pytest.raises(FlowExecutionError, match="LangGraph is not available"):
                    LangGraphFlowEngine(flow_config, context, runtime)
        except ImportError:
            # Module itself can't be imported, which is fine
            pass


class TestLangGraphEngineReplaceability:
    """Test that LangGraphFlowEngine is replaceable."""

    def test_simple_and_langgraph_engines_are_interchangeable(self):
        """Test that SimpleFlowEngine and LangGraphFlowEngine are interchangeable."""
        config = AgentCoreConfig(runtime=RuntimeConfig(runtime_id="test"))
        runtime = Runtime(config=config)
        context = create_execution_context(initiator="user:test")
        flow_config = FlowConfig(
            flow_id="test",
            version="1.0.0",
            entrypoint="start",
            nodes={"start": {"type": "agent", "agent_id": "agent1"}},
            transitions=[],
        )

        # Both engines should accept the same inputs
        from agent_core.orchestration.flow_engine import SimpleFlowEngine

        simple_engine = SimpleFlowEngine(flow_config, context, runtime)
        assert isinstance(simple_engine, BaseFlowEngine)

        # If LangGraph is available, test LangGraphFlowEngine
        try:
            from agent_core.orchestration.langgraph_engine import (
                LANGGRAPH_AVAILABLE,
                LangGraphFlowEngine,
            )

            if LANGGRAPH_AVAILABLE:
                langgraph_engine = LangGraphFlowEngine(flow_config, context, runtime)
                assert isinstance(langgraph_engine, BaseFlowEngine)
                # Both should have the same interface
                assert hasattr(simple_engine, "execute")
                assert hasattr(langgraph_engine, "execute")
                assert hasattr(simple_engine, "get_state")
                assert hasattr(langgraph_engine, "get_state")
        except ImportError:
            # LangGraph not available, skip
            pass

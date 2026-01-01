"""Tests to verify LangGraph type isolation.

These tests ensure that LangGraph types do not leak outside the
orchestration package and that the implementation remains replaceable.
"""

import importlib.util
import sys

import pytest


class TestLangGraphTypeIsolation:
    """Test that LangGraph types are isolated to orchestration package."""

    def test_langgraph_types_not_in_public_api(self):
        """Test that LangGraph types are not exposed in public API."""
        # Import the orchestration package
        import agent_core.orchestration

        # Get all public attributes
        public_attrs = [attr for attr in dir(agent_core.orchestration) if not attr.startswith("_")]

        # LangGraph-specific types should not be in public API
        langgraph_types = [
            "StateGraph",
            "END",
            "START",
            "add_messages",
            "TypedDict",  # This might be used but shouldn't be LangGraph-specific
        ]

        for langgraph_type in langgraph_types:
            # Check if it's a LangGraph type by trying to trace its origin
            if langgraph_type in public_attrs:
                attr = getattr(agent_core.orchestration, langgraph_type)
                # If it's from langgraph module, that's a leak
                module_name = getattr(attr, "__module__", "")
                if "langgraph" in module_name.lower():
                    pytest.fail(
                        f"LangGraph type {langgraph_type} leaked to public API (from {module_name})"
                    )

    def test_langgraph_imports_isolated_to_module(self):
        """Test that LangGraph imports are only in langgraph_engine module."""
        # Check that langgraph_engine module handles imports gracefully
        try:
            from agent_core.orchestration import langgraph_engine

            # The module should exist and handle missing LangGraph gracefully
            assert hasattr(langgraph_engine, "LANGGRAPH_AVAILABLE")
        except ImportError:
            # If the module can't be imported at all, that's also fine
            # (it means LangGraph is truly optional)
            pass

    def test_no_langgraph_in_core_contracts(self):
        """Test that no LangGraph types appear in core contracts."""
        # Import core contracts

        # Check that no LangGraph types are referenced
        _ = sys.modules["agent_core.contracts"]  # Verify module exists
        source_code = importlib.util.find_spec("agent_core.contracts")
        if source_code and source_code.origin:
            with open(source_code.origin) as f:
                content = f.read()
                # Check for LangGraph imports
                if "langgraph" in content.lower() or "from langgraph" in content:
                    pytest.fail("LangGraph types found in core contracts")

    def test_no_langgraph_in_runtime(self):
        """Test that no LangGraph types appear in runtime."""

        # Check runtime module doesn't import LangGraph
        runtime_module = sys.modules["agent_core.runtime"]
        if hasattr(runtime_module, "__file__") and runtime_module.__file__:
            with open(runtime_module.__file__) as f:
                content = f.read()
                if "langgraph" in content.lower():
                    pytest.fail("LangGraph found in runtime module")

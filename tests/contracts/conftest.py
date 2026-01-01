"""Shared fixtures and configuration for contract tests."""

import uuid

import pytest

from agent_core.contracts.execution_context import ExecutionContext
from agent_core.utils.ids import generate_correlation_id, generate_run_id


@pytest.fixture
def sample_run_id() -> str:
    """Generate a sample run_id for testing."""
    return generate_run_id()


@pytest.fixture
def sample_correlation_id() -> str:
    """Generate a sample correlation_id for testing."""
    return generate_correlation_id()


@pytest.fixture
def minimal_execution_context(
    sample_run_id: str,
    sample_correlation_id: str,
) -> ExecutionContext:
    """Create a minimal ExecutionContext with required fields only."""
    return ExecutionContext(
        run_id=sample_run_id,
        correlation_id=sample_correlation_id,
        initiator="user:test",
        permissions={},
        budget={},
        locale="en-US",
        observability={},
    )


@pytest.fixture
def execution_context_with_metadata(
    sample_run_id: str,
    sample_correlation_id: str,
) -> ExecutionContext:
    """Create an ExecutionContext with metadata."""
    return ExecutionContext(
        run_id=sample_run_id,
        correlation_id=sample_correlation_id,
        initiator="user:test",
        permissions={"read": True, "write": False},
        budget={"time_limit": 60, "max_calls": 100},
        locale="en-US",
        observability={"trace_id": "trace-123"},
        metadata={"custom": "value", "nested": {"key": "value"}},
    )


@pytest.fixture
def invalid_uuid_string() -> str:
    """Return an invalid UUID string for testing validation."""
    return "not-a-valid-uuid"


@pytest.fixture
def valid_uuid_v4() -> str:
    """Return a valid UUID v4 string."""
    return str(uuid.uuid4())

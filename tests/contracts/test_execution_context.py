"""Contract tests for ExecutionContext schema."""

import uuid

import pytest
from pydantic import ValidationError

from agent_core.contracts.execution_context import ExecutionContext
from agent_core.utils.ids import generate_correlation_id, generate_run_id


class TestExecutionContextSchema:
    """Test ExecutionContext schema validation and invariants."""

    def test_execution_context_creation_with_valid_fields(self):
        """Test that ExecutionContext can be created with all required fields."""
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        context = ExecutionContext(
            run_id=run_id,
            correlation_id=correlation_id,
            initiator="user:test",
            permissions={"read": True},
            budget={"time_limit": 60},
            locale="en-US",
            observability={"trace_id": "trace-123"},
        )

        assert context.run_id == run_id
        assert context.correlation_id == correlation_id
        assert context.initiator == "user:test"
        assert context.permissions == {"read": True}
        assert context.budget == {"time_limit": 60}
        assert context.locale == "en-US"
        assert context.observability == {"trace_id": "trace-123"}
        assert context.metadata == {}

    def test_execution_context_is_immutable(self):
        """Test that ExecutionContext is immutable (frozen)."""
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        context = ExecutionContext(
            run_id=run_id,
            correlation_id=correlation_id,
            initiator="user:test",
            permissions={},
            budget={},
            locale="en-US",
            observability={},
        )

        with pytest.raises(ValidationError):
            context.run_id = "new-id"

    def test_execution_context_rejects_invalid_uuid_format(self):
        """Test that ExecutionContext rejects invalid UUID formats."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionContext(
                run_id="not-a-uuid",
                correlation_id=generate_correlation_id(),
                initiator="user:test",
                permissions={},
                budget={},
                locale="en-US",
                observability={},
            )

        assert "Invalid UUID format" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            ExecutionContext(
                run_id=generate_run_id(),
                correlation_id="not-a-uuid",
                initiator="user:test",
                permissions={},
                budget={},
                locale="en-US",
                observability={},
            )

        assert "Invalid UUID format" in str(exc_info.value)

    def test_execution_context_rejects_extra_fields(self):
        """Test that ExecutionContext rejects extra fields (extra='forbid')."""
        with pytest.raises(ValidationError) as exc_info:
            ExecutionContext(
                run_id=generate_run_id(),
                correlation_id=generate_correlation_id(),
                initiator="user:test",
                permissions={},
                budget={},
                locale="en-US",
                observability={},
                extra_field="not-allowed",
            )

        assert "extra_field" in str(exc_info.value)

    def test_execution_context_metadata_defaults_to_empty_dict(self):
        """Test that metadata field defaults to empty dict if not provided."""
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        context = ExecutionContext(
            run_id=run_id,
            correlation_id=correlation_id,
            initiator="user:test",
            permissions={},
            budget={},
            locale="en-US",
            observability={},
        )

        assert context.metadata == {}

    def test_execution_context_accepts_custom_metadata(self):
        """Test that ExecutionContext accepts custom metadata."""
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        context = ExecutionContext(
            run_id=run_id,
            correlation_id=correlation_id,
            initiator="user:test",
            permissions={},
            budget={},
            locale="en-US",
            observability={},
            metadata={"custom": "value", "nested": {"key": "value"}},
        )

        assert context.metadata == {"custom": "value", "nested": {"key": "value"}}


class TestIDGeneration:
    """Test ID generation utilities."""

    def test_generate_run_id_returns_valid_uuid_v4(self):
        """Test that generate_run_id returns a valid UUID v4 string."""
        run_id = generate_run_id()

        assert isinstance(run_id, str)
        uuid_obj = uuid.UUID(run_id)
        assert uuid_obj.version == 4

    def test_generate_correlation_id_returns_valid_uuid_v4(self):
        """Test that generate_correlation_id returns a valid UUID v4 string."""
        correlation_id = generate_correlation_id()

        assert isinstance(correlation_id, str)
        uuid_obj = uuid.UUID(correlation_id)
        assert uuid_obj.version == 4

    def test_generated_ids_are_unique(self):
        """Test that generated IDs are unique."""
        run_ids = {generate_run_id() for _ in range(100)}
        correlation_ids = {generate_correlation_id() for _ in range(100)}

        assert len(run_ids) == 100
        assert len(correlation_ids) == 100

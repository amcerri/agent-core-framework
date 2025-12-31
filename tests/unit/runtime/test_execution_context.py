"""Unit tests for ExecutionContext creation and propagation."""

import pytest
from pydantic import ValidationError

from agent_core.configuration.schemas import RuntimeConfig
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.runtime.execution_context import (
    create_execution_context,
    ensure_immutable,
    propagate_execution_context,
)


class TestCreateExecutionContext:
    """Test create_execution_context function."""

    def test_create_execution_context_with_minimal_args(self):
        """Test creating ExecutionContext with minimal required arguments."""
        context = create_execution_context(initiator="user:test")

        assert isinstance(context, ExecutionContext)
        assert context.initiator == "user:test"
        assert context.run_id is not None
        assert context.correlation_id is not None
        assert context.permissions == {}
        assert context.budget == {}
        assert context.locale == "en-US"  # Default
        assert context.observability == {}
        assert context.metadata == {}

    def test_create_execution_context_with_all_args(self):
        """Test creating ExecutionContext with all arguments provided."""
        context = create_execution_context(
            initiator="user:test",
            permissions={"read": True, "write": False},
            budget={"time_limit": 60, "max_calls": 100},
            locale="fr-FR",
            observability={"trace_id": "trace-123"},
            metadata={"custom": "value"},
        )

        assert context.initiator == "user:test"
        assert context.permissions == {"read": True, "write": False}
        assert context.budget == {"time_limit": 60, "max_calls": 100}
        assert context.locale == "fr-FR"
        assert context.observability == {"trace_id": "trace-123"}
        assert context.metadata == {"custom": "value"}

    def test_create_execution_context_with_runtime_config(self):
        """Test creating ExecutionContext with runtime config defaults."""
        runtime_config = RuntimeConfig(
            runtime_id="test-runtime",
            default_locale="de-DE",
        )

        context = create_execution_context(
            initiator="user:test",
            runtime_config=runtime_config,
        )

        assert context.locale == "de-DE"  # From runtime config

    def test_create_execution_context_locale_override(self):
        """Test that explicit locale overrides runtime config default."""
        runtime_config = RuntimeConfig(
            runtime_id="test-runtime",
            default_locale="de-DE",
        )

        context = create_execution_context(
            initiator="user:test",
            locale="es-ES",
            runtime_config=runtime_config,
        )

        assert context.locale == "es-ES"  # Explicit override

    def test_create_execution_context_generates_unique_ids(self):
        """Test that each context gets unique run_id and correlation_id."""
        context1 = create_execution_context(initiator="user:test1")
        context2 = create_execution_context(initiator="user:test2")

        assert context1.run_id != context2.run_id
        assert context1.correlation_id != context2.correlation_id

    def test_create_execution_context_is_immutable(self):
        """Test that created ExecutionContext is immutable."""
        context = create_execution_context(initiator="user:test")

        # Attempting to modify should raise ValidationError
        with pytest.raises(ValidationError):
            context.run_id = "new-id"

        with pytest.raises(ValidationError):
            context.initiator = "new-initiator"

    def test_create_execution_context_preserves_correlation_fields(self):
        """Test that correlation fields are properly set."""
        context = create_execution_context(initiator="user:test")

        # Verify UUID format
        import uuid

        uuid.UUID(context.run_id)
        uuid.UUID(context.correlation_id)

        # Verify they are different (correlation_id is separate from run_id)
        assert context.run_id != context.correlation_id


class TestPropagateExecutionContext:
    """Test propagate_execution_context function."""

    def test_propagate_execution_context_preserves_correlation_fields(self):
        """Test that propagation preserves correlation fields."""
        original = create_execution_context(
            initiator="user:test",
            permissions={"read": True},
            budget={"time_limit": 60},
            locale="en-US",
            observability={"trace_id": "trace-123"},
            metadata={"original": "value"},
        )

        propagated = propagate_execution_context(original)

        assert propagated.run_id == original.run_id
        assert propagated.correlation_id == original.correlation_id
        assert propagated.initiator == original.initiator
        assert propagated.permissions == original.permissions
        assert propagated.budget == original.budget
        assert propagated.locale == original.locale
        assert propagated.observability == original.observability
        assert propagated.metadata == original.metadata

    def test_propagate_execution_context_updates_metadata(self):
        """Test that propagation can update metadata."""
        original = create_execution_context(
            initiator="user:test",
            metadata={"key1": "value1", "key2": "value2"},
        )

        propagated = propagate_execution_context(
            original,
            metadata_updates={"key2": "updated", "key3": "new"},
        )

        assert propagated.metadata == {
            "key1": "value1",  # Preserved
            "key2": "updated",  # Updated
            "key3": "new",  # Added
        }

    def test_propagate_execution_context_with_empty_metadata_updates(self):
        """Test that propagation with empty updates preserves metadata."""
        original = create_execution_context(
            initiator="user:test",
            metadata={"key": "value"},
        )

        propagated = propagate_execution_context(original, metadata_updates={})

        assert propagated.metadata == original.metadata

    def test_propagate_execution_context_creates_new_instance(self):
        """Test that propagation creates a new immutable instance."""
        original = create_execution_context(
            initiator="user:test",
            metadata={"key": "value"},
        )

        propagated = propagate_execution_context(
            original,
            metadata_updates={"new": "data"},
        )

        # Should be different instances
        assert propagated is not original

        # Original should be unchanged
        assert original.metadata == {"key": "value"}
        assert propagated.metadata == {"key": "value", "new": "data"}

    def test_propagate_execution_context_is_immutable(self):
        """Test that propagated context is immutable."""
        original = create_execution_context(initiator="user:test")
        propagated = propagate_execution_context(original)

        with pytest.raises(ValidationError):
            propagated.run_id = "new-id"


class TestEnsureImmutable:
    """Test ensure_immutable function."""

    def test_ensure_immutable_with_valid_context(self):
        """Test that ensure_immutable accepts valid immutable context."""
        context = create_execution_context(initiator="user:test")

        result = ensure_immutable(context)

        assert result is context  # Should return same instance

    def test_ensure_immutable_verifies_frozen(self):
        """Test that ensure_immutable verifies context is frozen."""
        context = create_execution_context(initiator="user:test")

        # Should not raise since ExecutionContext is always frozen
        ensure_immutable(context)

    def test_ensure_immutable_preserves_context(self):
        """Test that ensure_immutable doesn't modify context."""
        context = create_execution_context(
            initiator="user:test",
            metadata={"key": "value"},
        )

        result = ensure_immutable(context)

        assert result.metadata == {"key": "value"}
        assert result.initiator == "user:test"


class TestExecutionContextPropagationInvariants:
    """Test invariants for ExecutionContext propagation."""

    def test_correlation_fields_always_present(self):
        """Test that correlation fields are always present in created contexts."""
        context = create_execution_context(initiator="user:test")

        assert context.run_id is not None
        assert context.correlation_id is not None
        assert len(context.run_id) > 0
        assert len(context.correlation_id) > 0

    def test_correlation_fields_preserved_through_propagation(self):
        """Test that correlation fields are preserved through propagation."""
        original = create_execution_context(initiator="user:test")
        propagated = propagate_execution_context(original)

        assert propagated.run_id == original.run_id
        assert propagated.correlation_id == original.correlation_id

    def test_multiple_propagations_preserve_correlation(self):
        """Test that multiple propagations preserve correlation fields."""
        original = create_execution_context(initiator="user:test")
        propagated1 = propagate_execution_context(original, {"step": 1})
        propagated2 = propagate_execution_context(propagated1, {"step": 2})

        assert propagated2.run_id == original.run_id
        assert propagated2.correlation_id == original.correlation_id
        assert propagated2.metadata["step"] == 2

    def test_immutability_guarantee(self):
        """Test that contexts remain immutable through all operations."""
        context = create_execution_context(initiator="user:test")
        propagated = propagate_execution_context(context, {"update": True})

        # Both should be immutable
        with pytest.raises(ValidationError):
            context.run_id = "new"
        with pytest.raises(ValidationError):
            propagated.run_id = "new"

    def test_different_contexts_have_different_ids(self):
        """Test that different execution contexts have different IDs."""
        context1 = create_execution_context(initiator="user:test1")
        context2 = create_execution_context(initiator="user:test2")

        assert context1.run_id != context2.run_id
        assert context1.correlation_id != context2.correlation_id


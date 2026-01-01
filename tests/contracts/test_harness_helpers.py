"""Test the contract test harness helpers."""

import pytest
from pydantic import BaseModel

from agent_core.contracts.execution_context import ExecutionContext
from tests.contracts.helpers import (
    assert_schema_defaults,
    assert_schema_immutable,
    assert_schema_rejects_extra_fields,
    assert_schema_requires_fields,
    assert_uuid_v4,
)


class TestHarnessHelpers:
    """Test that the contract test harness helpers work correctly."""

    def test_assert_schema_immutable(self, minimal_execution_context):
        """Test that assert_schema_immutable works correctly."""
        # ExecutionContext should be immutable
        assert_schema_immutable(minimal_execution_context)

        # A non-frozen model should fail
        class NonFrozenModel(BaseModel):
            field: str

        instance = NonFrozenModel(field="test")
        with pytest.raises(AssertionError, match="is not frozen"):
            assert_schema_immutable(instance)

    def test_assert_schema_rejects_extra_fields(self, sample_run_id, sample_correlation_id):
        """Test that assert_schema_rejects_extra_fields works correctly."""
        valid_data = {
            "run_id": sample_run_id,
            "correlation_id": sample_correlation_id,
            "initiator": "user:test",
            "permissions": {},
            "budget": {},
            "locale": "en-US",
            "observability": {},
        }

        # ExecutionContext should reject extra fields
        assert_schema_rejects_extra_fields(ExecutionContext, valid_data)

        # A model that allows extra fields should fail the assertion
        class ExtraFieldsAllowed(BaseModel):
            model_config = {"extra": "allow"}
            field: str

        with pytest.raises(AssertionError, match="accepts extra fields"):
            assert_schema_rejects_extra_fields(
                ExtraFieldsAllowed,
                {"field": "test"},
            )

    def test_assert_schema_requires_fields(self):
        """Test that assert_schema_requires_fields works correctly."""

        class RequiredFieldsModel(BaseModel):
            required_field: str
            optional_field: str | None = None

        # Should pass: required_field is required
        assert_schema_requires_fields(RequiredFieldsModel, ["required_field"])

        # Should fail: optional_field is not required
        with pytest.raises(AssertionError, match="does not require field"):
            assert_schema_requires_fields(RequiredFieldsModel, ["optional_field"])

    def test_assert_schema_defaults(self, sample_run_id, sample_correlation_id):
        """Test that assert_schema_defaults works correctly."""
        minimal_data = {
            "run_id": sample_run_id,
            "correlation_id": sample_correlation_id,
            "initiator": "user:test",
            "permissions": {},
            "budget": {},
            "locale": "en-US",
            "observability": {},
        }

        # ExecutionContext.metadata should default to {}
        assert_schema_defaults(ExecutionContext, "metadata", {}, minimal_data)

        # Wrong default should fail
        with pytest.raises(AssertionError, match="has default value"):
            assert_schema_defaults(ExecutionContext, "metadata", None, minimal_data)

    def test_assert_uuid_v4(self, sample_run_id):
        """Test that assert_uuid_v4 works correctly."""
        # Valid UUID v4 should pass
        assert_uuid_v4(sample_run_id, "run_id")

        # Invalid UUID should fail
        with pytest.raises(AssertionError, match="must be a valid UUID"):
            assert_uuid_v4("not-a-uuid", "field")

        # UUID v1 should fail (not v4)
        import uuid

        uuid_v1 = str(uuid.uuid1())
        with pytest.raises(AssertionError, match="must be a UUID v4"):
            assert_uuid_v4(uuid_v1, "field")


class TestHarnessFixtures:
    """Test that the contract test harness fixtures work correctly."""

    def test_minimal_execution_context(self, minimal_execution_context):
        """Test that minimal_execution_context fixture works."""
        assert isinstance(minimal_execution_context, ExecutionContext)
        assert minimal_execution_context.initiator == "user:test"
        assert minimal_execution_context.metadata == {}

    def test_execution_context_with_metadata(self, execution_context_with_metadata):
        """Test that execution_context_with_metadata fixture works."""
        assert isinstance(execution_context_with_metadata, ExecutionContext)
        assert execution_context_with_metadata.metadata == {
            "custom": "value",
            "nested": {"key": "value"},
        }

    def test_sample_ids(self, sample_run_id, sample_correlation_id):
        """Test that ID fixtures work."""
        assert isinstance(sample_run_id, str)
        assert isinstance(sample_correlation_id, str)
        assert_uuid_v4(sample_run_id, "run_id")
        assert_uuid_v4(sample_correlation_id, "correlation_id")

"""Helper utilities for contract testing."""

import uuid
from typing import Any

from pydantic import BaseModel, ValidationError


def assert_schema_immutable(model_instance: BaseModel) -> None:
    """Assert that a Pydantic model instance is immutable (frozen).

    Args:
        model_instance: A Pydantic model instance to test.

    Raises:
        AssertionError: If the model is not frozen or allows field mutation.
    """
    if not model_instance.model_config.get("frozen", False):
        raise AssertionError(
            f"Model {type(model_instance).__name__} is not frozen. "
            "Contract schemas must be immutable."
        )

    # Try to mutate a field to verify immutability
    model_class = type(model_instance)
    first_field = list(model_class.model_fields.keys())[0]
    original_value = getattr(model_instance, first_field)

    try:
        setattr(model_instance, first_field, "test_mutation")
        raise AssertionError(
            f"Model {type(model_instance).__name__} allows field mutation. "
            "Contract schemas must be immutable."
        )
    except ValidationError:
        # Expected: frozen models raise ValidationError on mutation
        pass
    except Exception as e:
        raise AssertionError(
            f"Unexpected error when testing immutability: {e}"
        ) from e


def assert_schema_rejects_extra_fields(
    model_class: type[BaseModel],
    valid_data: dict[str, Any],
    extra_field_name: str = "extra_field",
    extra_field_value: Any = "not_allowed",
) -> None:
    """Assert that a Pydantic model rejects extra fields.

    Args:
        model_class: The Pydantic model class to test.
        valid_data: Valid data for creating an instance.
        extra_field_name: Name of the extra field to add.
        extra_field_value: Value for the extra field.

    Raises:
        AssertionError: If the model accepts extra fields.
    """
    data_with_extra = {**valid_data, extra_field_name: extra_field_value}

    try:
        model_class(**data_with_extra)
        raise AssertionError(
            f"Model {model_class.__name__} accepts extra fields. "
            "Contract schemas must reject extra fields (extra='forbid')."
        )
    except ValidationError as e:
        # Expected: models with extra='forbid' raise ValidationError
        error_str = str(e)
        if extra_field_name not in error_str:
            raise AssertionError(
                f"ValidationError raised but does not mention extra field '{extra_field_name}'. "
                f"Error: {error_str}"
            ) from e
    except Exception as e:
        raise AssertionError(
            f"Unexpected error when testing extra field rejection: {e}"
        ) from e


def assert_schema_requires_fields(
    model_class: type[BaseModel],
    required_fields: list[str],
) -> None:
    """Assert that a Pydantic model requires specific fields.

    Args:
        model_class: The Pydantic model class to test.
        required_fields: List of field names that must be required.

    Raises:
        AssertionError: If any required field is missing.
    """
    # Get all fields and their requirements
    model_fields = model_class.model_fields

    for field_name in required_fields:
        if field_name not in model_fields:
            raise AssertionError(
                f"Field '{field_name}' does not exist in model {model_class.__name__}."
            )

        field_info = model_fields[field_name]
        # Check if field is required (no default and not Optional)
        is_required = field_info.is_required()

        if not is_required:
            raise AssertionError(
                f"Model {model_class.__name__} does not require field '{field_name}'. "
                "All specified fields must be required."
            )


def assert_schema_defaults(
    model_class: type[BaseModel],
    field_name: str,
    default_value: Any,
    minimal_data: dict[str, Any],
) -> None:
    """Assert that a Pydantic model field has the expected default value.

    Args:
        model_class: The Pydantic model class to test.
        field_name: Name of the field to check.
        minimal_data: Minimal data required to create an instance.

    Raises:
        AssertionError: If the default value is not as expected.
    """
    instance = model_class(**minimal_data)
    actual_value = getattr(instance, field_name)

    if actual_value != default_value:
        raise AssertionError(
            f"Field '{field_name}' in {model_class.__name__} has default value "
            f"{actual_value}, but expected {default_value}."
        )


def assert_uuid_format(value: str, field_name: str = "field") -> None:
    """Assert that a string is a valid UUID format.

    Args:
        value: The string to validate.
        field_name: Name of the field being validated (for error messages).

    Raises:
        AssertionError: If the value is not a valid UUID.
    """
    try:
        uuid.UUID(value)
    except ValueError as e:
        raise AssertionError(
            f"Field '{field_name}' must be a valid UUID format. "
            f"Got: {value}"
        ) from e


def assert_uuid_v4(value: str, field_name: str = "field") -> None:
    """Assert that a string is a valid UUID v4.

    Args:
        value: The string to validate.
        field_name: Name of the field being validated (for error messages).

    Raises:
        AssertionError: If the value is not a valid UUID v4.
    """
    try:
        uuid_obj = uuid.UUID(value)
        if uuid_obj.version != 4:
            raise AssertionError(
                f"Field '{field_name}' must be a UUID v4. "
                f"Got UUID version {uuid_obj.version}."
            )
    except ValueError as e:
        raise AssertionError(
            f"Field '{field_name}' must be a valid UUID format. "
            f"Got: {value}"
        ) from e


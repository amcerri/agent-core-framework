"""ExecutionContext creation and propagation utilities.

Provides runtime-side utilities for creating and propagating ExecutionContext
instances. Ensures immutability and consistent correlation field propagation.
"""

from typing import Any

from agent_core.configuration.schemas import RuntimeConfig
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.utils.ids import generate_correlation_id, generate_run_id


def create_execution_context(
    initiator: str,
    permissions: dict[str, Any] | None = None,
    budget: dict[str, Any] | None = None,
    locale: str | None = None,
    observability: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    runtime_config: RuntimeConfig | None = None,
) -> ExecutionContext:
    """Create a new ExecutionContext instance.

    Creates an immutable ExecutionContext with all required fields.
    Uses runtime configuration defaults when available.

    Args:
        initiator: Identity of the caller (user, system, or service).
        permissions: Effective permission set. Defaults to empty dict.
        budget: Time, call, and cost limits. Defaults to empty dict.
        locale: Language and regional preferences. Uses runtime_config.default_locale
            if provided, otherwise "en-US".
        observability: Trace and logging propagation metadata. Defaults to empty dict.
        metadata: Free-form contextual data. Defaults to empty dict.
        runtime_config: Optional runtime configuration for defaults.

    Returns:
        Immutable ExecutionContext instance with all required fields.

    Notes:
        - run_id and correlation_id are automatically generated (UUID v4).
        - correlation_id is generated per context to ensure proper correlation.
        - The returned context is immutable (frozen) and cannot be modified.
    """
    # Generate unique IDs
    run_id = generate_run_id()
    correlation_id = generate_correlation_id()

    # Use runtime config defaults if available
    if locale is None:
        if runtime_config is not None:
            locale = runtime_config.default_locale
        else:
            locale = "en-US"

    # Set defaults for optional fields
    if permissions is None:
        permissions = {}
    if budget is None:
        budget = {}
    if observability is None:
        observability = {}
    if metadata is None:
        metadata = {}

    return ExecutionContext(
        run_id=run_id,
        correlation_id=correlation_id,
        initiator=initiator,
        permissions=permissions,
        budget=budget,
        locale=locale,
        observability=observability,
        metadata=metadata,
    )


def propagate_execution_context(
    context: ExecutionContext,
    metadata_updates: dict[str, Any] | None = None,
) -> ExecutionContext:
    """Create a new ExecutionContext with updated metadata.

    Since ExecutionContext is immutable, this function creates a new instance
    with the same correlation fields but potentially updated metadata.

    Args:
        context: Original ExecutionContext to propagate.
        metadata_updates: Optional metadata updates to merge into existing metadata.

    Returns:
        New immutable ExecutionContext instance with preserved correlation fields
        and updated metadata.

    Notes:
        - All correlation fields (run_id, correlation_id) are preserved.
        - All other fields (initiator, permissions, budget, locale, observability)
          are preserved unchanged.
        - Only metadata is updated by merging metadata_updates into existing metadata.
        - The original context remains unchanged (immutability guarantee).
    """
    # Merge metadata updates
    if metadata_updates is None:
        metadata_updates = {}

    updated_metadata = {**context.metadata, **metadata_updates}

    # Create new context with same fields but updated metadata
    return ExecutionContext(
        run_id=context.run_id,
        correlation_id=context.correlation_id,
        initiator=context.initiator,
        permissions=context.permissions,
        budget=context.budget,
        locale=context.locale,
        observability=context.observability,
        metadata=updated_metadata,
    )


def ensure_immutable(context: ExecutionContext) -> ExecutionContext:
    """Ensure an ExecutionContext is immutable.

    This is a no-op since ExecutionContext is already immutable (frozen),
    but serves as a runtime check and documentation of the immutability guarantee.

    Args:
        context: ExecutionContext to verify.

    Returns:
        The same ExecutionContext instance (no copy needed since it's immutable).

    Raises:
        ValueError: If the context is not properly immutable (should never happen
            with proper ExecutionContext instances).

    Notes:
        - This function verifies that the context is frozen.
        - In practice, this is a no-op since ExecutionContext is always frozen.
        - Useful for runtime assertions and documentation.
    """
    if not context.model_config.get("frozen", False):
        raise ValueError(
            "ExecutionContext must be immutable (frozen). This indicates a contract violation."
        )

    return context

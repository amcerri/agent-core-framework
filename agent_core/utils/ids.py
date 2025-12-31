"""ID generation utilities.

Provides helpers for generating run_id and correlation_id using UUID v4.
"""

import uuid


def generate_run_id() -> str:
    """Generate a unique run_id using UUID v4.

    Returns:
        A UUID v4 string representing a unique execution lifecycle identifier.
    """
    return str(uuid.uuid4())


def generate_correlation_id() -> str:
    """Generate a unique correlation_id using UUID v4.

    Returns:
        A UUID v4 string for correlating logs, traces, metrics, and audit events.
    """
    return str(uuid.uuid4())

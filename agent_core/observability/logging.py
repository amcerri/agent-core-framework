"""Structured logging with correlation fields.

Provides structured logging using Python's stdlib logging with JSON
formatting. Ensures correlation fields are always present and supports
redaction hooks for sensitive data.
"""

import json
import logging
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from agent_core.contracts.observability import (
    ComponentType,
    CorrelationFields,
    LogEvent,
    LogLevel,
)


class CorrelationJSONFormatter(logging.Formatter):
    """JSON formatter that includes correlation fields in all log records.

    This formatter ensures that every log record includes the required
    correlation fields (run_id, correlation_id, component_type, component_id,
    component_version, timestamp).

    Attributes:
        redaction_hook: Optional callable that redacts sensitive data from
            log metadata. Should accept (metadata: dict[str, Any]) -> dict[str, Any].
    """

    def __init__(
        self,
        redaction_hook: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ):
        """Initialize the JSON formatter.

        Args:
            redaction_hook: Optional function to redact sensitive data from
                log metadata. If None, no redaction is performed.
        """
        super().__init__()
        self.redaction_hook = redaction_hook

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as JSON with correlation fields.

        Args:
            record: The log record to format.

        Returns:
            JSON string containing the structured log data.
        """
        # Extract correlation fields from record if present
        correlation = CorrelationFields(
            run_id=getattr(record, "run_id", "unknown"),
            correlation_id=getattr(record, "correlation_id", "unknown"),
            component_type=getattr(record, "component_type", ComponentType.RUNTIME),
            component_id=getattr(record, "component_id", "unknown"),
            component_version=getattr(record, "component_version", "unknown"),
            timestamp=getattr(record, "timestamp", datetime.now(timezone.utc).isoformat()),
        )

        # Build metadata from record attributes (excluding standard fields)
        metadata: dict[str, Any] = {}
        excluded_fields = {
            "name",
            "msg",
            "args",
            "created",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "thread",
            "threadName",
            "exc_info",
            "exc_text",
            "stack_info",
            # Correlation fields
            "run_id",
            "correlation_id",
            "component_type",
            "component_id",
            "component_version",
            "timestamp",
        }

        for key, value in record.__dict__.items():
            if key not in excluded_fields:
                metadata[key] = value

        # Apply redaction hook if provided
        if self.redaction_hook is not None:
            metadata = self.redaction_hook(metadata)

        # Map stdlib log levels to LogLevel enum
        level_map = {
            logging.DEBUG: LogLevel.DEBUG,
            logging.INFO: LogLevel.INFO,
            logging.WARNING: LogLevel.WARN,
            logging.ERROR: LogLevel.ERROR,
            logging.CRITICAL: LogLevel.ERROR,
        }
        log_level = level_map.get(record.levelno, LogLevel.INFO)

        # Create LogEvent structure
        log_event = LogEvent(
            correlation=correlation,
            level=log_level,
            message=record.getMessage(),
            metadata=metadata,
        )

        # Convert to JSON
        return json.dumps(
            {
                "correlation": {
                    "run_id": log_event.correlation.run_id,
                    "correlation_id": log_event.correlation.correlation_id,
                    "component_type": log_event.correlation.component_type.value,
                    "component_id": log_event.correlation.component_id,
                    "component_version": log_event.correlation.component_version,
                    "timestamp": log_event.correlation.timestamp,
                },
                "level": log_event.level.value,
                "message": log_event.message,
                "metadata": log_event.metadata,
            },
            default=str,
        )


class CorrelationLoggerAdapter(logging.LoggerAdapter):
    """Logger adapter that adds correlation fields to all log records.

    This adapter ensures that correlation fields are included in every
    log record by adding them as extra attributes.
    """

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """Process log message and add correlation fields.

        Args:
            msg: Log message.
            kwargs: Logging keyword arguments.

        Returns:
            Tuple of (message, kwargs) with correlation fields added to extra.
        """
        extra = kwargs.get("extra", {})
        extra.update(
            {
                "run_id": self.extra["run_id"],
                "correlation_id": self.extra["correlation_id"],
                "component_type": self.extra["component_type"],
                "component_id": self.extra["component_id"],
                "component_version": self.extra["component_version"],
                "timestamp": self.extra["timestamp"],
            }
        )
        kwargs["extra"] = extra
        return msg, kwargs


def get_logger(
    name: str,
    correlation: CorrelationFields,
    redaction_hook: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> logging.LoggerAdapter:
    """Get a logger configured with correlation fields.

    Creates a logger adapter that automatically includes correlation fields in
    all log records. The logger uses JSON formatting and supports
    redaction hooks for sensitive data.

    Args:
        name: Logger name (typically module or component name).
        correlation: Correlation fields to include in all log records.
        redaction_hook: Optional function to redact sensitive data from
            log metadata.

    Returns:
        LoggerAdapter instance configured with correlation fields and JSON formatting.
    """
    logger = logging.getLogger(name)

    # Only add handler if logger doesn't already have one
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = CorrelationJSONFormatter(redaction_hook=redaction_hook)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    # Create adapter with correlation fields
    adapter = CorrelationLoggerAdapter(
        logger,
        {
            "run_id": correlation.run_id,
            "correlation_id": correlation.correlation_id,
            "component_type": correlation.component_type,
            "component_id": correlation.component_id,
            "component_version": correlation.component_version,
            "timestamp": correlation.timestamp,
        },
    )

    return adapter

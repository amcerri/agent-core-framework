"""Unit tests for structured logging."""

import json
import logging
from io import StringIO

from agent_core.contracts.observability import (
    ComponentType,
    CorrelationFields,
)
from agent_core.observability.logging import (
    CorrelationJSONFormatter,
    CorrelationLoggerAdapter,
    get_logger,
)
from agent_core.utils.ids import generate_correlation_id, generate_run_id


class TestCorrelationJSONFormatter:
    """Test CorrelationJSONFormatter."""

    def test_formatter_includes_correlation_fields(self):
        """Test that formatter includes all required correlation fields."""
        formatter = CorrelationJSONFormatter()
        logger = logging.getLogger("test")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.run_id = run_id
        record.correlation_id = correlation_id
        record.component_type = ComponentType.AGENT
        record.component_id = "agent:test_agent"
        record.component_version = "1.0.0"
        record.timestamp = "2024-01-01T00:00:00Z"

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert "correlation" in data
        assert data["correlation"]["run_id"] == run_id
        assert data["correlation"]["correlation_id"] == correlation_id
        assert data["correlation"]["component_type"] == "agent"
        assert data["correlation"]["component_id"] == "agent:test_agent"
        assert data["correlation"]["component_version"] == "1.0.0"
        assert data["correlation"]["timestamp"] == "2024-01-01T00:00:00Z"

    def test_formatter_includes_log_level(self):
        """Test that formatter includes log level."""
        formatter = CorrelationJSONFormatter()
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        for level, expected in [
            (logging.DEBUG, "DEBUG"),
            (logging.INFO, "INFO"),
            (logging.WARNING, "WARN"),
            (logging.ERROR, "ERROR"),
            (logging.CRITICAL, "ERROR"),
        ]:
            record = logging.LogRecord(
                name="test",
                level=level,
                pathname="test.py",
                lineno=1,
                msg="Test message",
                args=(),
                exc_info=None,
            )
            record.run_id = run_id
            record.correlation_id = correlation_id
            record.component_type = ComponentType.RUNTIME
            record.component_id = "runtime:test"
            record.component_version = "1.0.0"
            record.timestamp = "2024-01-01T00:00:00Z"

            formatted = formatter.format(record)
            data = json.loads(formatted)

            assert data["level"] == expected

    def test_formatter_includes_message(self):
        """Test that formatter includes log message."""
        formatter = CorrelationJSONFormatter()
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test log message",
            args=(),
            exc_info=None,
        )
        record.run_id = run_id
        record.correlation_id = correlation_id
        record.component_type = ComponentType.RUNTIME
        record.component_id = "runtime:test"
        record.component_version = "1.0.0"
        record.timestamp = "2024-01-01T00:00:00Z"

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert data["message"] == "Test log message"

    def test_formatter_includes_metadata(self):
        """Test that formatter includes metadata from extra fields."""
        formatter = CorrelationJSONFormatter()
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.run_id = run_id
        record.correlation_id = correlation_id
        record.component_type = ComponentType.RUNTIME
        record.component_id = "runtime:test"
        record.component_version = "1.0.0"
        record.timestamp = "2024-01-01T00:00:00Z"
        record.custom_field = "custom_value"
        record.another_field = 42

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert "metadata" in data
        assert data["metadata"]["custom_field"] == "custom_value"
        assert data["metadata"]["another_field"] == 42

    def test_formatter_applies_redaction_hook(self):
        """Test that formatter applies redaction hook to metadata."""

        def redact_sensitive(metadata: dict) -> dict:
            """Redact sensitive fields."""
            redacted = metadata.copy()
            if "password" in redacted:
                redacted["password"] = "[REDACTED]"
            if "api_key" in redacted:
                redacted["api_key"] = "[REDACTED]"
            return redacted

        formatter = CorrelationJSONFormatter(redaction_hook=redact_sensitive)
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.run_id = run_id
        record.correlation_id = correlation_id
        record.component_type = ComponentType.RUNTIME
        record.component_id = "runtime:test"
        record.component_version = "1.0.0"
        record.timestamp = "2024-01-01T00:00:00Z"
        record.password = "secret123"
        record.api_key = "key123"
        record.safe_field = "safe_value"

        formatted = formatter.format(record)
        data = json.loads(formatted)

        assert data["metadata"]["password"] == "[REDACTED]"
        assert data["metadata"]["api_key"] == "[REDACTED]"
        assert data["metadata"]["safe_field"] == "safe_value"

    def test_formatter_handles_missing_correlation_fields(self):
        """Test that formatter handles missing correlation fields gracefully."""
        formatter = CorrelationJSONFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        # No correlation fields set

        formatted = formatter.format(record)
        data = json.loads(formatted)

        # Should use defaults
        assert data["correlation"]["run_id"] == "unknown"
        assert data["correlation"]["correlation_id"] == "unknown"
        assert data["correlation"]["component_type"] == "runtime"
        assert data["correlation"]["component_id"] == "unknown"
        assert data["correlation"]["component_version"] == "unknown"


class TestCorrelationLoggerAdapter:
    """Test CorrelationLoggerAdapter."""

    def test_adapter_adds_correlation_fields(self):
        """Test that adapter adds correlation fields to log records."""
        logger = logging.getLogger("test_adapter")
        logger.setLevel(logging.INFO)

        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        adapter = CorrelationLoggerAdapter(
            logger,
            {
                "run_id": run_id,
                "correlation_id": correlation_id,
                "component_type": ComponentType.TOOL,
                "component_id": "tool:test_tool",
                "component_version": "1.0.0",
                "timestamp": "2024-01-01T00:00:00Z",
            },
        )

        # Capture log output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = CorrelationJSONFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        adapter.info("Test message")

        output = stream.getvalue()
        data = json.loads(output)

        assert data["correlation"]["run_id"] == run_id
        assert data["correlation"]["correlation_id"] == correlation_id
        assert data["correlation"]["component_type"] == "tool"
        assert data["correlation"]["component_id"] == "tool:test_tool"


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_returns_adapter_with_correlation(self):
        """Test that get_logger returns adapter with correlation fields."""
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        correlation = CorrelationFields(
            run_id=run_id,
            correlation_id=correlation_id,
            component_type=ComponentType.SERVICE,
            component_id="service:test_service",
            component_version="1.0.0",
            timestamp="2024-01-01T00:00:00Z",
        )

        logger = get_logger("test_logger", correlation)

        assert isinstance(logger, CorrelationLoggerAdapter)
        assert logger.extra["run_id"] == run_id
        assert logger.extra["correlation_id"] == correlation_id
        assert logger.extra["component_type"] == ComponentType.SERVICE

    def test_get_logger_includes_correlation_in_logs(self):
        """Test that logs from get_logger include correlation fields."""
        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        correlation = CorrelationFields(
            run_id=run_id,
            correlation_id=correlation_id,
            component_type=ComponentType.FLOW,
            component_id="flow:test_flow",
            component_version="1.0.0",
            timestamp="2024-01-01T00:00:00Z",
        )

        logger = get_logger("test_logger", correlation)

        # Capture log output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = CorrelationJSONFormatter()
        handler.setFormatter(formatter)
        logger.logger.addHandler(handler)

        logger.info("Test log message")

        output = stream.getvalue()
        data = json.loads(output)

        assert data["correlation"]["run_id"] == run_id
        assert data["correlation"]["correlation_id"] == correlation_id
        assert data["correlation"]["component_type"] == "flow"
        assert data["correlation"]["component_id"] == "flow:test_flow"
        assert data["message"] == "Test log message"

    def test_get_logger_applies_redaction_hook(self):
        """Test that get_logger applies redaction hook."""

        def redact(metadata: dict) -> dict:
            """Redact sensitive data."""
            return {k: "[REDACTED]" if "secret" in k.lower() else v for k, v in metadata.items()}

        run_id = generate_run_id()
        correlation_id = generate_correlation_id()

        correlation = CorrelationFields(
            run_id=run_id,
            correlation_id=correlation_id,
            component_type=ComponentType.RUNTIME,
            component_id="runtime:test",
            component_version="1.0.0",
            timestamp="2024-01-01T00:00:00Z",
        )

        logger = get_logger("test_logger", correlation, redaction_hook=redact)

        # Capture log output
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        formatter = CorrelationJSONFormatter(redaction_hook=redact)
        handler.setFormatter(formatter)
        logger.logger.addHandler(handler)

        logger.info(
            "Test message", extra={"secret_key": "value123", "public_field": "public_value"}
        )

        output = stream.getvalue()
        data = json.loads(output)

        assert data["metadata"]["secret_key"] == "[REDACTED]"
        assert data["metadata"]["public_field"] == "public_value"

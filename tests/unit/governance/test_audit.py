"""Unit tests for audit emission."""

import pytest

from agent_core.contracts.observability import AuditEvent
from agent_core.governance.audit import AuditEmissionError, AuditEmitter
from agent_core.observability.noop import NoOpObservabilitySink
from agent_core.runtime.execution_context import create_execution_context


class FailingObservabilitySink:
    """Observability sink that fails on audit emission."""

    def emit_log(self, log_event):
        """Emit log (no-op)."""
        pass

    def emit_trace(self, span):
        """Emit trace (no-op)."""
        pass

    def emit_metric(self, metric):
        """Emit metric (no-op)."""
        pass

    def emit_audit(self, audit_event):
        """Emit audit (raises exception)."""
        raise RuntimeError("Audit emission failed")


class TestAuditEmitter:
    """Test AuditEmitter."""

    def test_emit_permission_decision_allowed(self):
        """Test emitting audit event for allowed permission decision."""
        context = create_execution_context(initiator="user:test")
        sink = NoOpObservabilitySink()
        emitter = AuditEmitter(context, sink)

        # Should not raise
        emitter.emit_permission_decision(
            action="tool.execute",
            target_resource="tool:my_tool",
            decision_outcome="allowed",
            permission="read",
        )

    def test_emit_permission_decision_denied(self):
        """Test emitting audit event for denied permission decision."""
        context = create_execution_context(initiator="user:test")
        sink = NoOpObservabilitySink()
        emitter = AuditEmitter(context, sink)

        # Should not raise
        emitter.emit_permission_decision(
            action="tool.execute",
            target_resource="tool:my_tool",
            decision_outcome="denied",
            permission="write",
        )

    def test_emit_permission_decision_without_permission(self):
        """Test emitting audit event without permission identifier."""
        context = create_execution_context(initiator="user:test")
        sink = NoOpObservabilitySink()
        emitter = AuditEmitter(context, sink)

        # Should not raise
        emitter.emit_permission_decision(
            action="service.read",
            target_resource="service:my_service",
            decision_outcome="allowed",
        )

    def test_emit_policy_decision_allow(self):
        """Test emitting audit event for policy decision (allow)."""
        context = create_execution_context(initiator="user:test")
        sink = NoOpObservabilitySink()
        emitter = AuditEmitter(context, sink)

        # Should not raise
        emitter.emit_policy_decision(
            action="tool.execute",
            target_resource="tool:my_tool",
            decision_outcome="allow",
            policy="tool.policy",
        )

    def test_emit_policy_decision_deny(self):
        """Test emitting audit event for policy decision (deny)."""
        context = create_execution_context(initiator="user:test")
        sink = NoOpObservabilitySink()
        emitter = AuditEmitter(context, sink)

        # Should not raise
        emitter.emit_policy_decision(
            action="tool.delete",
            target_resource="tool:my_tool",
            decision_outcome="deny",
            policy="tool.delete.policy",
        )

    def test_emit_policy_decision_require_approval(self):
        """Test emitting audit event for policy decision (require_approval)."""
        context = create_execution_context(initiator="user:test")
        sink = NoOpObservabilitySink()
        emitter = AuditEmitter(context, sink)

        # Should not raise
        emitter.emit_policy_decision(
            action="service.write",
            target_resource="service:my_service",
            decision_outcome="require_approval",
            policy="service.write.policy",
        )

    def test_emit_budget_exhaustion_time(self):
        """Test emitting audit event for time budget exhaustion."""
        context = create_execution_context(initiator="user:test")
        sink = NoOpObservabilitySink()
        emitter = AuditEmitter(context, sink)

        # Should not raise
        emitter.emit_budget_exhaustion(
            budget_type="time",
            limit=60.0,
            consumed=65.0,
        )

    def test_emit_budget_exhaustion_calls(self):
        """Test emitting audit event for call budget exhaustion."""
        context = create_execution_context(initiator="user:test")
        sink = NoOpObservabilitySink()
        emitter = AuditEmitter(context, sink)

        # Should not raise
        emitter.emit_budget_exhaustion(
            budget_type="calls",
            limit=100,
            consumed=101,
        )

    def test_emit_budget_exhaustion_cost(self):
        """Test emitting audit event for cost budget exhaustion."""
        context = create_execution_context(initiator="user:test")
        sink = NoOpObservabilitySink()
        emitter = AuditEmitter(context, sink)

        # Should not raise
        emitter.emit_budget_exhaustion(
            budget_type="cost",
            limit=10.0,
            consumed=12.5,
        )

    def test_emit_governance_decision(self):
        """Test emitting audit event for general governance decision."""
        context = create_execution_context(initiator="user:test")
        sink = NoOpObservabilitySink()
        emitter = AuditEmitter(context, sink)

        # Should not raise
        emitter.emit_governance_decision(
            action="custom.action",
            target_resource="resource:custom",
            decision_outcome="allowed",
            policy_or_permission="custom.policy",
            component_id="governance:custom",
        )

    def test_audit_emission_failure_raises_error(self):
        """Test that audit emission failure raises AuditEmissionError."""
        context = create_execution_context(initiator="user:test")
        sink = FailingObservabilitySink()
        emitter = AuditEmitter(context, sink)

        with pytest.raises(AuditEmissionError, match="Failed to emit audit event"):
            emitter.emit_permission_decision(
                action="tool.execute",
                target_resource="tool:my_tool",
                decision_outcome="allowed",
            )

    def test_audit_emitter_uses_context(self):
        """Test that emitter uses execution context."""
        context = create_execution_context(initiator="user:test")
        sink = NoOpObservabilitySink()
        emitter = AuditEmitter(context, sink)

        assert emitter.context == context

    def test_audit_emitter_uses_sink(self):
        """Test that emitter uses observability sink."""
        context = create_execution_context(initiator="user:test")
        sink = NoOpObservabilitySink()
        emitter = AuditEmitter(context, sink)

        assert emitter.sink == sink


class TestAuditEventStructure:
    """Test that audit events are structured correctly."""

    def test_permission_audit_event_structure(self):
        """Test that permission audit events have correct structure."""
        context = create_execution_context(initiator="user:test")
        captured_events = []

        class CapturingSink:
            """Sink that captures audit events."""

            def emit_log(self, log_event):
                pass

            def emit_trace(self, span):
                pass

            def emit_metric(self, metric):
                pass

            def emit_audit(self, audit_event: AuditEvent):
                captured_events.append(audit_event)

        sink = CapturingSink()
        emitter = AuditEmitter(context, sink)

        emitter.emit_permission_decision(
            action="tool.execute",
            target_resource="tool:my_tool",
            decision_outcome="allowed",
            permission="read",
        )

        assert len(captured_events) == 1
        event = captured_events[0]
        assert event.initiator_identity == "user:test"
        assert event.action == "tool.execute"
        assert event.target_resource == "tool:my_tool"
        assert event.decision_outcome == "allowed"
        assert event.policy_or_permission == "read"
        assert event.correlation.run_id == context.run_id
        assert event.correlation.correlation_id == context.correlation_id

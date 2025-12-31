"""Unit tests for action execution."""

import pytest

from agent_core.configuration.schemas import AgentCoreConfig, GovernanceConfig, RuntimeConfig
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.tool import ToolInput, ToolResult
from agent_core.governance.budget import BudgetExhaustedError, BudgetTracker
from agent_core.governance.permissions import PermissionError
from agent_core.governance.policy import PolicyOutcome
from agent_core.runtime.action_execution import ActionExecutionError, ActionExecutor
from agent_core.runtime.execution_context import create_execution_context
from agent_core.tools.base import BaseTool
from agent_core.utils.ids import generate_correlation_id, generate_run_id


class MockTool(BaseTool):
    """Mock tool for testing."""

    def __init__(self, tool_id: str, permissions: list[str] = None):
        """Initialize mock tool."""
        self._tool_id = tool_id
        self._permissions = permissions or []

    @property
    def tool_id(self) -> str:
        """Tool identifier."""
        return self._tool_id

    @property
    def tool_version(self) -> str:
        """Tool version."""
        return "1.0.0"

    @property
    def permissions_required(self) -> list[str]:
        """Required permissions."""
        return self._permissions

    def execute(self, input_data: ToolInput, context: ExecutionContext) -> ToolResult:
        """Execute tool."""
        return ToolResult(
            status="success",
            output={"result": f"executed_{self._tool_id}"},
            metrics={"latency_ms": 10.0},
        )


class MockObservabilitySink:
    """Mock observability sink for testing."""

    def __init__(self):
        """Initialize mock sink."""
        self.audit_events = []

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
        """Emit audit event."""
        self.audit_events.append(audit_event)


@pytest.fixture
def mock_config():
    """Create a mock configuration."""
    return AgentCoreConfig(
        runtime=RuntimeConfig(runtime_id="test_runtime"),
        governance=GovernanceConfig(),
    )


@pytest.fixture
def mock_context():
    """Create a mock execution context."""
    return create_execution_context(
        initiator="user:test",
        permissions={"read": True, "write": False},
        budget={"call_limit": 100, "time_limit_seconds": 60},
    )


@pytest.fixture
def mock_tools():
    """Create mock tools."""
    return {
        "tool1": MockTool("tool1", permissions=["read"]),
        "tool2": MockTool("tool2", permissions=["write"]),
    }


@pytest.fixture
def mock_services():
    """Create mock services (empty for now)."""
    return {}


@pytest.fixture
def mock_sink():
    """Create a mock observability sink."""
    return MockObservabilitySink()


class TestActionExecutor:
    """Test ActionExecutor."""

    def test_execute_tool_action_success(
        self, mock_config, mock_context, mock_tools, mock_services, mock_sink
    ):
        """Test successful tool action execution."""
        executor = ActionExecutor(
            context=mock_context,
            config=mock_config,
            tools=mock_tools,
            services=mock_services,
            sink=mock_sink,
        )

        action = {"type": "tool", "tool_id": "tool1", "payload": {"test": "data"}}
        result = executor.execute_action(action)

        assert result["type"] == "tool"
        assert result["tool_id"] == "tool1"
        assert result["status"] == "success"
        assert result["output"]["result"] == "executed_tool1"

    def test_execute_tool_action_not_registered(
        self, mock_config, mock_context, mock_tools, mock_services, mock_sink
    ):
        """Test tool action execution with unregistered tool."""
        executor = ActionExecutor(
            context=mock_context,
            config=mock_config,
            tools=mock_tools,
            services=mock_services,
            sink=mock_sink,
        )

        action = {"type": "tool", "tool_id": "unknown_tool", "payload": {}}
        with pytest.raises(ActionExecutionError, match="not registered"):
            executor.execute_action(action)

    def test_execute_tool_action_missing_permission(
        self, mock_config, mock_context, mock_tools, mock_services, mock_sink
    ):
        """Test tool action execution with missing permission."""
        executor = ActionExecutor(
            context=mock_context,
            config=mock_config,
            tools=mock_tools,
            services=mock_services,
            sink=mock_sink,
        )

        # tool2 requires "write" permission, but context only has "read"
        action = {"type": "tool", "tool_id": "tool2", "payload": {}}
        with pytest.raises(ActionExecutionError, match="Permission denied"):
            executor.execute_action(action)

    def test_execute_tool_action_policy_deny(
        self, mock_config, mock_context, mock_tools, mock_services, mock_sink
    ):
        """Test tool action execution with policy denial."""
        # Configure policy to deny tool.execute
        mock_config.governance.policies = {"tool.execute": {"outcome": "deny"}}

        executor = ActionExecutor(
            context=mock_context,
            config=mock_config,
            tools=mock_tools,
            services=mock_services,
            sink=mock_sink,
        )

        action = {"type": "tool", "tool_id": "tool1", "payload": {}}
        with pytest.raises(ActionExecutionError, match="Policy denied"):
            executor.execute_action(action)

    def test_execute_tool_action_budget_exhausted(
        self, mock_config, mock_context, mock_tools, mock_services, mock_sink
    ):
        """Test tool action execution with budget exhaustion."""
        # Set call limit to 0 to trigger exhaustion
        context = create_execution_context(
            initiator="user:test",
            permissions={"read": True},
            budget={"call_limit": 0},
        )

        budget_tracker = BudgetTracker(context)

        executor = ActionExecutor(
            context=context,
            config=mock_config,
            tools=mock_tools,
            services=mock_services,
            sink=mock_sink,
            budget_tracker=budget_tracker,
        )

        action = {"type": "tool", "tool_id": "tool1", "payload": {}}
        with pytest.raises(ActionExecutionError, match="Budget exhausted"):
            executor.execute_action(action)

    def test_execute_tool_action_unknown_type(
        self, mock_config, mock_context, mock_tools, mock_services, mock_sink
    ):
        """Test action execution with unknown action type."""
        executor = ActionExecutor(
            context=mock_context,
            config=mock_config,
            tools=mock_tools,
            services=mock_services,
            sink=mock_sink,
        )

        action = {"type": "unknown", "tool_id": "tool1"}
        with pytest.raises(ActionExecutionError, match="Unknown action type"):
            executor.execute_action(action)

    def test_execute_tool_action_missing_type(
        self, mock_config, mock_context, mock_tools, mock_services, mock_sink
    ):
        """Test action execution with missing type field."""
        executor = ActionExecutor(
            context=mock_context,
            config=mock_config,
            tools=mock_tools,
            services=mock_services,
            sink=mock_sink,
        )

        action = {"tool_id": "tool1"}
        with pytest.raises(ActionExecutionError, match="must specify 'type'"):
            executor.execute_action(action)

    def test_execute_tool_action_audit_emission(
        self, mock_config, mock_context, mock_tools, mock_services, mock_sink
    ):
        """Test that audit events are emitted for tool execution."""
        executor = ActionExecutor(
            context=mock_context,
            config=mock_config,
            tools=mock_tools,
            services=mock_services,
            sink=mock_sink,
        )

        action = {"type": "tool", "tool_id": "tool1", "payload": {}}
        executor.execute_action(action)

        # Check that audit events were emitted
        assert len(mock_sink.audit_events) > 0
        # Should have permission decision audit event
        permission_audits = [e for e in mock_sink.audit_events if e.action == "tool.execute"]
        assert len(permission_audits) > 0

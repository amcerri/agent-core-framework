"""Minimal end-to-end example demonstrating Agent Core Framework usage.

This example demonstrates:
- Runtime execution with agent, tool, and service
- Governance (permissions, budgets, audit)
- Observability (structured logging with correlation fields)
- Flow execution (YAML-based with template variable resolution)
- Service registration and access

Run with:
    python minimal_example.py
"""

import sys
from pathlib import Path

# Add parent directory to path to import agent_core
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Any

from agent_core.agents.base import BaseAgent
from agent_core.configuration.loader import load_config
from agent_core.contracts.agent import AgentInput, AgentResult
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.observability import ComponentType, CorrelationFields
from agent_core.contracts.service import ServiceInput, ServiceResult
from agent_core.contracts.tool import ToolInput, ToolResult
from agent_core.observability.logging import get_logger
from agent_core.orchestration import SimpleFlowEngine, load_flow_from_yaml
from agent_core.runtime.execution_context import create_execution_context
from agent_core.runtime.runtime import Runtime
from agent_core.services.base import BaseService
from agent_core.tools.base import BaseTool


class QueryAgent(BaseAgent):
    """Simple query agent that processes user queries."""

    @property
    def agent_id(self) -> str:
        """Agent identifier."""
        return "query_agent"

    @property
    def agent_version(self) -> str:
        """Agent version."""
        return "1.0.0"

    @property
    def capabilities(self) -> list[str]:
        """Agent capabilities."""
        return ["query", "search"]

    def run(self, input_data: AgentInput, context: ExecutionContext) -> AgentResult:
        """Execute agent and request tool execution."""
        query = input_data.payload.get("query", "")

        # Log agent execution
        correlation = CorrelationFields(
            run_id=context.run_id,
            correlation_id=context.correlation_id,
            component_type=ComponentType.AGENT,
            component_id=self.agent_id,
            component_version=self.agent_version,
            timestamp=context.observability.get("timestamp", ""),
        )
        logger = get_logger(__name__, correlation)
        logger.info("Agent processing query", extra={"query": query})

        # Decide actions based on input
        actions = []
        if query:
            actions.append({
                "type": "tool",
                "tool_id": "search_tool",
                "payload": {"query": query}
            })

        return AgentResult(
            status="success",
            output={"query": query, "processed": True},
            actions=actions,
            errors=[],
            metrics={"action_count": len(actions)},
        )


class SearchTool(BaseTool):
    """Simple search tool that performs mock search operations."""

    @property
    def tool_id(self) -> str:
        """Tool identifier."""
        return "search_tool"

    @property
    def tool_version(self) -> str:
        """Tool version."""
        return "1.0.0"

    @property
    def permissions_required(self) -> list[str]:
        """Required permissions."""
        return ["search"]

    def execute(self, input_data: ToolInput, context: ExecutionContext) -> ToolResult:
        """Execute search tool."""
        query = input_data.payload.get("query", "")

        # Log tool execution
        correlation = CorrelationFields(
            run_id=context.run_id,
            correlation_id=context.correlation_id,
            component_type=ComponentType.TOOL,
            component_id=self.tool_id,
            component_version=self.tool_version,
            timestamp=context.observability.get("timestamp", ""),
        )
        logger = get_logger(__name__, correlation)
        logger.info("Tool executing search", extra={"query": query})

        # Mock search operation
        results = [
            {"title": f"Result 1 for {query}", "url": "https://example.com/1"},
            {"title": f"Result 2 for {query}", "url": "https://example.com/2"},
        ]

        return ToolResult(
            status="success",
            output={"results": results, "count": len(results)},
            errors=[],
            metrics={"result_count": len(results), "latency_ms": 10.0},
        )


class StorageService(BaseService):
    """Simple storage service for demonstration."""

    def __init__(self):
        """Initialize storage service with empty storage."""
        self._storage: dict[str, dict[str, Any]] = {}

    @property
    def service_id(self) -> str:
        """Service identifier."""
        return "storage_service"

    @property
    def service_version(self) -> str:
        """Service version."""
        return "1.0.0"

    @property
    def capabilities(self) -> list[str]:
        """Service capabilities."""
        return ["storage", "retrieval"]

    def check_permission(self, action: str, context: ExecutionContext) -> bool:
        """Check if action is permitted."""
        permissions = context.permissions
        if action == "read" or action == "get":
            return permissions.get("read", False) or permissions.get("storage", False)
        elif action == "write" or action == "set":
            return permissions.get("write", False) or permissions.get("storage", False)
        return False

    def execute(
        self, input_data: ServiceInput, context: ExecutionContext
    ) -> ServiceResult:
        """Execute a service action.

        Supported actions:
        - "get": Retrieve a value by key (payload: {"key": str})
        - "set": Store a value by key (payload: {"key": str, "value": dict})

        Args:
            input_data: Service input with action and payload.
            context: Execution context.

        Returns:
            ServiceResult with execution status and output.
        """
        action = input_data.action
        payload = input_data.payload

        # Check permission (runtime also checks, but service should verify)
        if not self.check_permission(action, context):
            return ServiceResult(
                status="error",
                output={},
                errors=[
                    {
                        "error": "permission_denied",
                        "message": f"Permission denied for action '{action}'",
                    }
                ],
                metrics={},
            )

        # Execute action
        if action == "get":
            key = payload.get("key")
            if key is None:
                return ServiceResult(
                    status="error",
                    output={},
                    errors=[
                        {
                            "error": "missing_key",
                            "message": "Payload must contain 'key' for 'get' action",
                        }
                    ],
                    metrics={},
                )
            value = self._storage.get(key)
            return ServiceResult(
                status="success",
                output={"key": key, "value": value},
                errors=[],
                metrics={"operation": "get"},
            )

        elif action == "set":
            key = payload.get("key")
            value = payload.get("value")
            if key is None or value is None:
                return ServiceResult(
                    status="error",
                    output={},
                    errors=[
                        {
                            "error": "missing_parameters",
                            "message": "Payload must contain 'key' and 'value' for 'set' action",
                        }
                    ],
                    metrics={},
                )
            if not isinstance(value, dict):
                return ServiceResult(
                    status="error",
                    output={},
                    errors=[
                        {
                            "error": "invalid_value",
                            "message": "Value must be a dictionary",
                        }
                    ],
                    metrics={},
                )
            self._storage[key] = value
            return ServiceResult(
                status="success",
                output={"key": key, "stored": True},
                errors=[],
                metrics={"operation": "set"},
            )

        else:
            return ServiceResult(
                status="error",
                output={},
                errors=[
                    {
                        "error": "unknown_action",
                        "message": f"Unknown action '{action}'. Supported: 'get', 'set'",
                    }
                ],
                metrics={},
            )

    def get(self, key: str) -> dict[str, Any] | None:
        """Get value from storage (service-specific method for direct access)."""
        return self._storage.get(key)

    def set(self, key: str, value: dict[str, Any]) -> None:
        """Set value in storage (service-specific method for direct access)."""
        self._storage[key] = value


def main():
    """Run the minimal end-to-end example."""
    print("=" * 60)
    print("Agent Core Framework - Minimal End-to-End Example")
    print("=" * 60)
    print()

    # Load configuration
    config_path = Path(__file__).parent / "config" / "agent-core.yaml"
    print(f"Loading configuration from: {config_path}")
    try:
        config = load_config(str(config_path))
    except Exception as e:
        print(f"Error loading config: {e}")
        print("Using minimal default configuration...")
        from agent_core.configuration.schemas import AgentCoreConfig, RuntimeConfig
        config = AgentCoreConfig(runtime=RuntimeConfig(runtime_id="example_runtime"))

    print("Configuration loaded successfully")
    print()

    # Create runtime
    print("Creating runtime...")
    runtime = Runtime(config=config)

    # Register components
    print("Registering components...")
    agent = QueryAgent()
    tool = SearchTool()
    service = StorageService()
    runtime.register_agent(agent)
    runtime.register_tool(tool)
    runtime.register_service(service)
    print(f"  - Registered agent: {agent.agent_id}")
    print(f"  - Registered tool: {tool.tool_id}")
    print(f"  - Registered service: {service.service_id}")
    print()

    # Example 1: Direct agent execution
    print("-" * 60)
    print("Example 1: Direct Agent Execution")
    print("-" * 60)
    context = create_execution_context(
        initiator="user:example",
        permissions={"search": True},
        budget={"time_limit": 60, "max_calls": 10},
    )
    print(f"Created execution context: run_id={context.run_id[:8]}...")
    print(f"  - Permissions: {context.permissions}")
    print(f"  - Budget: {context.budget}")
    print()

    result = runtime.execute_agent(
        agent_id="query_agent",
        input_data={"query": "example query"},
        context=context,
    )
    print(f"Agent execution result: status={result.status}")
    print(f"  - Output: {result.output}")
    print(f"  - Actions executed: {len(result.actions)}")
    print(f"  - Errors: {len(result.errors)}")
    if result.metrics:
        print(f"  - Metrics: {result.metrics}")
    print()

    # Example 2: Flow execution
    print("-" * 60)
    print("Example 2: Flow Execution (YAML)")
    print("-" * 60)
    flow_path = Path(__file__).parent / "flows" / "simple_flow.yaml"
    print(f"Loading flow from: {flow_path}")
    try:
        flow_config = load_flow_from_yaml(str(flow_path))
        print(f"Loaded flow: {flow_config.flow_id} v{flow_config.version}")
        print(f"  - Entrypoint: {flow_config.entrypoint}")
        print(f"  - Nodes: {list(flow_config.nodes.keys())}")
        print()

        # Create new context for flow
        flow_context = create_execution_context(
            initiator="user:example",
            permissions={"search": True},
            budget={"time_limit": 60, "max_calls": 10},
        )

        # Execute flow
        engine = SimpleFlowEngine(
            flow=flow_config,
            context=flow_context,
            runtime=runtime,
        )
        print("Executing flow...")
        flow_result = engine.execute(input_data={"query": "flow query"})
        print(f"Flow execution result: status={flow_result.get('status')}")
        print(f"  - Final node: {flow_result.get('final_node')}")
        print(f"  - Flow ID: {flow_result.get('flow_id')}")
        print()

        # Show flow state
        state = engine.get_state()
        print(f"Flow state:")
        print(f"  - Current node: {state.current_node}")
        print(f"  - History entries: {len(state.history)}")
        print()

    except Exception as e:
        print(f"Error executing flow: {e}")
        print("(Flow execution requires flow file - continuing without it)")
        print()

    # Example 3: Service execution via runtime
    print("-" * 60)
    print("Example 3: Service Execution via Runtime")
    print("-" * 60)
    print("Demonstrating service execution through runtime actions...")
    print(f"  - Service ID: {service.service_id}")
    print(f"  - Service capabilities: {service.capabilities}")
    print()

    # Create context with storage permissions
    service_context = create_execution_context(
        initiator="user:example",
        permissions={"storage": True, "write": True, "read": True},
        budget={"time_limit": 60, "max_calls": 10},
    )

    # Create an agent that requests service actions
    class ServiceAgent(BaseAgent):
        """Agent that requests service actions."""

        @property
        def agent_id(self) -> str:
            return "service_agent"

        @property
        def agent_version(self) -> str:
            return "1.0.0"

        @property
        def capabilities(self) -> list[str]:
            return ["service_access"]

        def run(self, input_data: AgentInput, context: ExecutionContext) -> AgentResult:
            """Request service actions."""
            actions = [
                {
                    "type": "service",
                    "service_id": "storage_service",
                    "action": "set",
                    "payload": {"key": "example_key", "value": {"data": "example_value"}},
                },
                {
                    "type": "service",
                    "service_id": "storage_service",
                    "action": "get",
                    "payload": {"key": "example_key"},
                },
            ]
            return AgentResult(
                status="success",
                output={"requested_actions": len(actions)},
                actions=actions,
                errors=[],
                metrics={},
            )

    service_agent = ServiceAgent()
    runtime.register_agent(service_agent)

    # Execute agent which will trigger service actions
    print("Executing agent that requests service actions...")
    service_result = runtime.execute_agent(
        agent_id="service_agent",
        input_data={},
        context=service_context,
    )
    print(f"Agent execution result: status={service_result.status}")
    print(f"  - Actions requested: {len(service_result.actions)}")
    print(f"  - Errors: {len(service_result.errors)}")
    print()

    # Show that service storage was updated
    print("Verifying service execution...")
    stored_value = service.get("example_key")
    print(f"  - Service storage contains: {len(service._storage)} item(s)")
    if stored_value:
        print(f"  - Retrieved value: {stored_value}")
    print()

    # Example 4: Governance enforcement
    print("-" * 60)
    print("Example 4: Governance Enforcement")
    print("-" * 60)
    print("Testing permission enforcement...")
    restricted_context = create_execution_context(
        initiator="user:restricted",
        permissions={},  # No permissions
        budget={"time_limit": 60, "max_calls": 10},
    )
    restricted_result = runtime.execute_agent(
        agent_id="query_agent",
        input_data={"query": "restricted query"},
        context=restricted_context,
    )
    print(f"Restricted execution result: status={restricted_result.status}")
    if restricted_result.errors:
        print(f"  - Errors (expected): {len(restricted_result.errors)}")
        for error in restricted_result.errors[:1]:  # Show first error
            error_msg = error.get('error') or error.get('message', 'Unknown error')
            print(f"    - {error_msg}")
    print()

    print("=" * 60)
    print("Example completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()


"""Main runtime implementation.

The runtime is the control plane of the framework, responsible for
execution lifecycle, routing, and orchestration.
"""

from datetime import datetime, timezone
from typing import Any

from agent_core.configuration.schemas import AgentCoreConfig, RuntimeConfig
from agent_core.contracts.agent import Agent, AgentInput, AgentResult
from agent_core.contracts.execution_context import ExecutionContext
from agent_core.contracts.observability import ComponentType, CorrelationFields
from agent_core.observability.logging import get_logger
from agent_core.runtime.execution_context import create_execution_context
from agent_core.runtime.lifecycle import LifecycleEvent, LifecycleManager, LifecycleState
from agent_core.runtime.routing import Router, RoutingError
from agent_core.utils.ids import generate_correlation_id, generate_run_id


class Runtime:
    """Main runtime implementation.

    The runtime manages execution lifecycle, agent routing, and observability.
    All agent invocations go through the runtime.
    """

    def __init__(
        self,
        config: AgentCoreConfig,
        agents: dict[str, Agent] | None = None,
    ):
        """Initialize runtime.

        Args:
            config: Runtime configuration.
            agents: Optional dictionary of agent_id -> Agent instances.
                If None, agents must be registered later.
        """
        self.config = config
        self.agents: dict[str, Agent] = agents or {}
        self.router = Router(self.agents)

        # Validate runtime config is present
        if config.runtime is None:
            raise ValueError("Runtime configuration is required.")

    def register_agent(self, agent: Agent) -> None:
        """Register an agent with the runtime.

        Args:
            agent: Agent instance to register.
        """
        self.agents[agent.agent_id] = agent
        # Update router with new agents
        self.router = Router(self.agents)

    def execute_agent(
        self,
        agent_id: str | None = None,
        input_data: dict[str, Any] | None = None,
        initiator: str = "system:runtime",
        required_capabilities: list[str] | None = None,
        context: ExecutionContext | None = None,
    ) -> AgentResult:
        """Execute an agent synchronously.

        This is the main synchronous execution entry point for v1.
        All agent invocations must go through this method.

        Args:
            agent_id: Optional explicit agent identifier.
            input_data: Optional input data for the agent.
            initiator: Identity of the caller. Defaults to "system:runtime".
            required_capabilities: Optional list of required capabilities.
            context: Optional execution context. If None, one will be created.

        Returns:
            AgentResult from agent execution.

        Raises:
            RoutingError: If agent selection fails.
            RuntimeError: If execution fails.
        """
        # Create execution context if not provided
        if context is None:
            context = create_execution_context(
                initiator=initiator,
                runtime_config=self.config.runtime,
            )

        # Create lifecycle manager
        lifecycle = LifecycleManager(context)

        # Create correlation for observability
        correlation = CorrelationFields(
            run_id=context.run_id,
            correlation_id=context.correlation_id,
            component_type=ComponentType.RUNTIME,
            component_id="runtime:main",
            component_version="1.0.0",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        logger = get_logger("agent_core.runtime", correlation)

        try:
            # Emit lifecycle event: initialization started
            logger.info("Runtime execution started", extra={"agent_id": agent_id})

            # Transition to ready
            lifecycle.transition_to(LifecycleState.READY)

            # Select agent
            try:
                agent = self.router.select_agent(
                    agent_id=agent_id,
                    required_capabilities=required_capabilities,
                    context=context,
                )
                logger.info(
                    "Agent selected",
                    extra={"agent_id": agent.agent_id, "agent_version": agent.agent_version},
                )
            except RoutingError as e:
                # Routing errors before execution should terminate, not fail
                lifecycle.transition_to(LifecycleState.TERMINATED, {"error": str(e)})
                logger.error("Agent selection failed", extra={"error": str(e)})
                # Re-raise RoutingError - don't continue execution
                raise

            # Transition to executing
            lifecycle.transition_to(LifecycleState.EXECUTING)

            # Prepare agent input
            agent_input = AgentInput(payload=input_data or {})

            # Execute agent
            logger.info("Agent execution started", extra={"agent_id": agent.agent_id})
            result = agent.run(agent_input, context)
            logger.info(
                "Agent execution completed",
                extra={
                    "agent_id": agent.agent_id,
                    "status": result.status,
                },
            )

            # Transition based on result
            if result.status == "success":
                lifecycle.transition_to(LifecycleState.COMPLETED)
            else:
                lifecycle.transition_to(LifecycleState.FAILED, {"status": result.status})

            return result

        except RoutingError:
            # RoutingError is already handled and re-raised, don't catch it again
            raise

        except Exception as e:
            # Only transition to FAILED if we're in EXECUTING state
            # (routing errors already transitioned to TERMINATED)
            if lifecycle.get_state() == LifecycleState.EXECUTING:
                lifecycle.transition_to(LifecycleState.FAILED, {"error": str(e)})
            logger.error("Runtime execution failed", extra={"error": str(e)})
            raise RuntimeError(f"Runtime execution failed: {e}") from e

        finally:
            # Transition to terminated if not already in terminal state
            # (routing errors already transitioned to TERMINATED, so this is a no-op in that case)
            if not lifecycle.is_terminal():
                lifecycle.transition_to(LifecycleState.TERMINATED)
                logger.info("Runtime execution terminated")

    def get_lifecycle_events(self) -> list[tuple[LifecycleEvent, dict[str, Any]]]:
        """Get lifecycle events from last execution.

        Returns:
            List of (event, metadata) tuples from the last execution.
        """
        # Note: This is a simplified version. In a full implementation,
        # lifecycle events would be tracked per execution.
        return []


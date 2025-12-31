"""Deterministic routing logic.

Provides deterministic agent selection based on configuration and
capabilities. No implicit LLM semantic routing is allowed.
"""

from typing import Any

from agent_core.contracts.agent import Agent
from agent_core.contracts.execution_context import ExecutionContext


class RoutingError(Exception):
    """Raised when routing fails."""

    pass


class Router:
    """Deterministic agent router.

    Selects agents based on explicit configuration, capabilities, and
    governance constraints. No semantic inference is performed.
    """

    def __init__(self, agents: dict[str, Agent]):
        """Initialize router with registered agents.

        Args:
            agents: Dictionary of agent_id -> Agent instances.
        """
        self.agents = agents

    def select_agent(
        self,
        agent_id: str | None = None,
        required_capabilities: list[str] | None = None,
        context: ExecutionContext | None = None,
    ) -> Agent:
        """Select an agent deterministically.

        Selection is based on:
        1. Explicit agent_id if provided
        2. Required capabilities matching agent capabilities
        3. Configuration and governance constraints

        Args:
            agent_id: Optional explicit agent identifier.
            required_capabilities: Optional list of required capabilities.
            context: Optional execution context for governance checks.

        Returns:
            Selected Agent instance.

        Raises:
            RoutingError: If no suitable agent is found or selection is ambiguous.
        """
        # If explicit agent_id is provided, use it
        if agent_id is not None:
            if agent_id not in self.agents:
                raise RoutingError(f"Agent '{agent_id}' is not registered.")
            return self.agents[agent_id]

        # If capabilities are required, find matching agents
        if required_capabilities is not None:
            matching_agents = []
            for agent_id_key, agent in self.agents.items():
                agent_capabilities = set(agent.capabilities)
                required_set = set(required_capabilities)
                if required_set.issubset(agent_capabilities):
                    matching_agents.append((agent_id_key, agent))

            if not matching_agents:
                raise RoutingError(
                    f"No agent found with required capabilities: {required_capabilities}"
                )

            if len(matching_agents) > 1:
                # Multiple agents match - resolve deterministically by agent_id (alphabetical)
                matching_agents.sort(key=lambda x: x[0])
                # Use first match (deterministic tie-breaking)
                return matching_agents[0][1]

            return matching_agents[0][1]

        # No selection criteria provided
        raise RoutingError(
            "Agent selection requires either agent_id or required_capabilities. "
            "No implicit routing is allowed."
        )

    def list_agents(self) -> list[str]:
        """List all registered agent IDs.

        Returns:
            List of agent identifiers.
        """
        return list(self.agents.keys())

    def get_agent(self, agent_id: str) -> Agent | None:
        """Get an agent by ID.

        Args:
            agent_id: Agent identifier.

        Returns:
            Agent instance if found, None otherwise.
        """
        return self.agents.get(agent_id)

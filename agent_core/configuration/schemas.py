"""Configuration schemas.

Defines Pydantic schemas for all configuration sections as specified
in `.docs/06-configuration.md`. All configuration must conform to
these schemas.
"""

from typing import Any

from pydantic import BaseModel, Field


class RuntimeConfig(BaseModel):
    """Runtime configuration schema.

    Defines global runtime behavior and constraints.
    """

    runtime_id: str = Field(
        ...,
        description="Unique identifier for the runtime instance.",
    )
    mode: str = Field(
        default="development",
        description="Execution mode (e.g., development, staging, production).",
    )
    concurrency: int = Field(
        default=1,
        description="Maximum concurrent executions allowed.",
    )
    timeouts: dict[str, Any] = Field(
        default_factory=dict,
        description="Global timeout defaults.",
    )
    default_locale: str = Field(
        default="en-US",
        description="Default language/region if not provided in ExecutionContext.",
    )
    fail_fast: bool = Field(
        default=False,
        description="Whether the runtime should stop on first unrecoverable error.",
    )


class AgentConfig(BaseModel):
    """Agent configuration schema.

    Defines which agents are available and how they are instantiated.
    """

    agent_id: str = Field(..., description="Unique identifier for the agent.")
    version: str = Field(..., description="Version identifier for the agent.")
    enabled: bool = Field(
        default=True,
        description="Whether the agent is enabled.",
    )
    capabilities: list[str] = Field(
        default_factory=list,
        description="List of capabilities this agent provides.",
    )
    provider_binding: str | None = Field(
        default=None,
        description="Provider binding reference.",
    )
    defaults: dict[str, Any] = Field(
        default_factory=dict,
        description="Default configuration for the agent.",
    )


class ToolConfig(BaseModel):
    """Tool configuration schema.

    Defines side-effecting tools and their execution constraints.
    """

    tool_id: str = Field(..., description="Unique identifier for the tool.")
    version: str = Field(..., description="Version identifier for the tool.")
    enabled: bool = Field(
        default=True,
        description="Whether the tool is enabled.",
    )
    permissions_required: list[str] = Field(
        default_factory=list,
        description="List of permissions required to execute this tool.",
    )
    timeouts: dict[str, Any] = Field(
        default_factory=dict,
        description="Timeout configuration for the tool.",
    )
    retry_policy: dict[str, Any] = Field(
        default_factory=dict,
        description="Retry policy configuration.",
    )


class ServiceConfig(BaseModel):
    """Service configuration schema.

    Defines governed services, including stateful services.
    """

    service_id: str = Field(..., description="Unique identifier for the service.")
    version: str = Field(..., description="Version identifier for the service.")
    capabilities: list[str] = Field(
        default_factory=list,
        description="List of capabilities this service provides.",
    )
    provider_binding: str | None = Field(
        default=None,
        description="Provider binding reference.",
    )
    access_policies: dict[str, Any] = Field(
        default_factory=dict,
        description="Access policy configuration.",
    )


class FlowConfig(BaseModel):
    """Flow configuration schema.

    Defines orchestration logic declaratively.
    """

    flow_id: str = Field(..., description="Unique identifier for the flow.")
    version: str = Field(..., description="Version identifier for the flow.")
    entrypoint: str = Field(..., description="Identifier of the entry point node.")
    nodes: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Dictionary of node definitions keyed by node identifier.",
    )
    transitions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of transition definitions between nodes.",
    )
    error_handling: dict[str, Any] = Field(
        default_factory=dict,
        description="Error handling behavior configuration.",
    )


class ProviderConfig(BaseModel):
    """Provider configuration schema.

    Selects concrete implementations for abstract services.
    """

    llm: dict[str, Any] | None = Field(
        default=None,
        description="LLM provider configuration.",
    )
    embedding: dict[str, Any] | None = Field(
        default=None,
        description="Embedding provider configuration.",
    )
    vector_store: dict[str, Any] | None = Field(
        default=None,
        description="Vector store provider configuration.",
    )
    database: dict[str, Any] | None = Field(
        default=None,
        description="Database provider configuration.",
    )


class GovernanceConfig(BaseModel):
    """Governance configuration schema.

    Defines security, permissions, and budget enforcement.
    """

    permissions: dict[str, Any] = Field(
        default_factory=dict,
        description="Permission configuration.",
    )
    budgets: dict[str, Any] = Field(
        default_factory=dict,
        description="Budget configuration.",
    )
    policies: dict[str, Any] = Field(
        default_factory=dict,
        description="Policy configuration.",
    )
    approvals: dict[str, Any] = Field(
        default_factory=dict,
        description="Approval configuration.",
    )


class ObservabilityConfig(BaseModel):
    """Observability configuration schema.

    Controls observability behavior without changing code.
    """

    enabled: bool = Field(
        default=True,
        description="Whether observability is enabled.",
    )
    sampling: dict[str, Any] = Field(
        default_factory=dict,
        description="Sampling configuration.",
    )
    exporters: dict[str, Any] = Field(
        default_factory=dict,
        description="Exporter configuration.",
    )
    redaction: dict[str, Any] = Field(
        default_factory=dict,
        description="Redaction rules configuration.",
    )
    audit: dict[str, Any] = Field(
        default_factory=dict,
        description="Audit event configuration.",
    )


class EnvironmentConfig(BaseModel):
    """Environment configuration schema.

    Supports environment-specific configuration without duplication.
    """

    name: str = Field(
        default="default",
        description="Environment name.",
    )
    overrides: dict[str, Any] = Field(
        default_factory=dict,
        description="Environment-specific overrides.",
    )


class AgentCoreConfig(BaseModel):
    """Root configuration schema.

    Contains all configuration sections. All sections are optional
    unless explicitly required.
    """

    runtime: RuntimeConfig | None = Field(
        default=None,
        description="Runtime configuration.",
    )
    agents: dict[str, AgentConfig] = Field(
        default_factory=dict,
        description="Agent configurations keyed by agent_id.",
    )
    tools: dict[str, ToolConfig] = Field(
        default_factory=dict,
        description="Tool configurations keyed by tool_id.",
    )
    services: dict[str, ServiceConfig] = Field(
        default_factory=dict,
        description="Service configurations keyed by service_id.",
    )
    flows: dict[str, FlowConfig] = Field(
        default_factory=dict,
        description="Flow configurations keyed by flow_id.",
    )
    providers: ProviderConfig | None = Field(
        default=None,
        description="Provider configuration.",
    )
    governance: GovernanceConfig | None = Field(
        default=None,
        description="Governance configuration.",
    )
    observability: ObservabilityConfig | None = Field(
        default=None,
        description="Observability configuration.",
    )
    environment: EnvironmentConfig | None = Field(
        default=None,
        description="Environment configuration.",
    )


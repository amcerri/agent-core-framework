# Examples

This directory contains example implementations demonstrating how to use the Agent Core Framework.

## Minimal End-to-End Example

The `minimal_example.py` script demonstrates a complete end-to-end usage of the framework, including:

- **Runtime Execution**: Creating and using the runtime to execute agents
- **Agent/Tool/Service Components**: Implementation and registration of all component types
- **Governance**: Permission evaluation, budget tracking, and audit emission
- **Observability**: Structured logging with correlation fields
- **Flow Execution**: Declarative YAML-based orchestration with template variable resolution

### Running the Example

1. Ensure the framework is installed (see [Installation](../docs/installation.md))

2. Run the example:

```bash
cd examples
python minimal_example.py
```

### What the Example Demonstrates

1. **Agent Implementation (`QueryAgent`)**:
   - Receives input: `{"query": "example query"}`
   - Processes the query and decides to request a tool action
   - Returns action: `{"type": "tool", "tool_id": "search_tool", "payload": {"query": "example query"}}`
   - Output: `{"query": "example query", "processed": True}`
   - Metrics: `{"action_count": 1}`

2. **Tool Implementation (`SearchTool`)**:
   - Receives input: `{"query": "example query"}`
   - Performs mock search operation (returns 2 mock results)
   - Requires permission: `["search"]`
   - Returns: `{"results": [...], "count": 2}`
   - Metrics: `{"result_count": 2, "latency_ms": 10.0}`

3. **Service Implementation (`StorageService`)**:
   - Provides storage capabilities: `["storage", "retrieval"]`
   - Enforces access control via `check_permission(action, context)`
   - Supports `read` and `write` actions
   - Maintains internal state: `{"key": {"data": "value"}}`

4. **Runtime Setup**:
   - Loads configuration from `config/agent-core.yaml`
   - Creates runtime instance
   - Registers agent, tool, and service components

5. **Direct Agent Execution**:
   - Creates execution context with permissions and budget
   - Executes agent: `runtime.execute_agent(agent_id="query_agent", input_data={"query": "example query"})`
   - Runtime automatically executes requested tool actions with governance enforcement
   - Returns structured result with output, actions, errors, and metrics

6. **Flow Execution**:
   - Loads flow from `flows/simple_flow.yaml`
   - Flow defines 3 nodes: `start` (agent) → `search` (tool) → `end` (agent)
   - Template variables resolved: `{{input.query}}` → `"flow query"`, `{{node_start_result.output.query}}` → previous node's output
   - Executes nodes sequentially with state management

7. **Service Access**:
   - Demonstrates service registration: `runtime.register_service(service)`
   - Shows permission checking: `service.check_permission("write", context)`
   - Direct service access for demonstration (in production, accessed via runtime actions)

8. **Governance Enforcement**:
   - Demonstrates permission denial when required permissions are missing
   - Shows error handling: permission errors are captured and returned in result
   - Example: Agent requests tool action but context has no `"search"` permission → action denied

### Example Structure

```
examples/
├── README.md               # This file
├── minimal_example.py      # Main example script
├── config/
│   └── agent-core.yaml     # Configuration file
└── flows/
    └── simple_flow.yaml    # Flow definition
```

### Key Concepts Demonstrated

- **Architectural Boundaries**: 
  - Agents receive `AgentInput`, process it, and return `AgentResult` with requested actions
  - Runtime receives actions (e.g., `{"type": "tool", "tool_id": "search_tool"}`) and executes them
  - Agents never call tools directly; they return actions for runtime to execute

- **Component Types**: 
  - **Agents**: Decision-making units that process input and decide actions (e.g., `QueryAgent`)
  - **Tools**: Side-effecting operations with permission requirements (e.g., `SearchTool` requires `"search"` permission)
  - **Services**: Governed access to shared state with permission checking (e.g., `StorageService`)

- **Governance Enforcement**: 
  - Permissions checked before tool/service execution (e.g., `SearchTool` requires `["search"]`)
  - Budget limits enforced (e.g., `{"time_limit": 60, "max_calls": 10}`)
  - Permission denial returns structured errors in result

- **Observability Signals**: 
  - All operations emit structured JSON logs with correlation fields (`run_id`, `correlation_id`, `component_type`, etc.)
  - Example log: `{"correlation": {"run_id": "...", "component_type": "agent", ...}, "level": "INFO", "message": "Agent processing query", ...}`

- **Declarative Orchestration**: 
  - Flows defined in YAML with explicit nodes and transitions
  - Example flow: `start` (agent) → `search` (tool) → `end` (agent)
  - State managed automatically between nodes

- **Template Variables**: 
  - Flow templates use `{{variable}}` syntax for dynamic values
  - `{{input.query}}` resolves to flow input data
  - `{{node_start_result.output.query}}` resolves to previous node's output
  - Templates resolved before node execution

### Next Steps

- Review the [Creating Agents](../docs/creating-agents.md) guide
- Explore [Orchestration and Flows](../docs/flows.md) for advanced flow patterns
- Check the [Runtime API](../docs/runtime-api.md) reference

---

Back to [repository root](../README.md)


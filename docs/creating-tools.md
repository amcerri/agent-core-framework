# Creating Tools

This guide explains how to create custom tools for the Agent Core Framework.

## Tool Contract

Tools are execution units that:

- Perform a single, well-defined capability
- Encapsulate side effects or external interactions
- Validate inputs and outputs
- Declare required permissions
- Are stateless by default

Contract: [agent_core/contracts/tool.py](../agent_core/contracts/tool.py)

## Base Tool Class

The framework provides `BaseTool` as a foundation for implementing tools:

```python
from agent_core.tools.base import BaseTool
from agent_core.contracts.tool import ToolInput, ToolResult
from agent_core.contracts.execution_context import ExecutionContext

class MyTool(BaseTool):
    @property
    def tool_id(self) -> str:
        return "my_tool"
    
    @property
    def tool_version(self) -> str:
        return "1.0.0"
    
    @property
    def permissions_required(self) -> list[str]:
        return ["read", "write"]
    
    def execute(self, input_data: ToolInput, context: ExecutionContext) -> ToolResult:
        # Execute tool logic
        # Return structured result
        pass
```

Base class: [agent_core/tools/base.py](../agent_core/tools/base.py)

## Tool Implementation Example

```python
from agent_core.tools.base import BaseTool
from agent_core.contracts.tool import ToolInput, ToolResult
from agent_core.contracts.execution_context import ExecutionContext

class SearchTool(BaseTool):
    @property
    def tool_id(self) -> str:
        return "search_tool"
    
    @property
    def tool_version(self) -> str:
        return "1.0.0"
    
    @property
    def permissions_required(self) -> list[str]:
        return ["search"]
    
    def execute(self, input_data: ToolInput, context: ExecutionContext) -> ToolResult:
        query = input_data.payload.get("query", "")
        
        # Perform search operation
        results = self._perform_search(query)
        
        return ToolResult(
            status="success",
            output={"results": results},
            errors=[],
            metrics={"result_count": len(results)}
        )
    
    def _perform_search(self, query: str) -> list[dict]:
        # Tool-specific implementation
        return []
```

## Tool Registration

Register tools with the runtime:

```python
from agent_core.runtime import Runtime
from agent_core.configuration.loader import load_config

config = load_config()
runtime = Runtime(config=config)

# Register tool
tool = SearchTool()
runtime.register_tool(tool)
```

## Tool Responsibilities

Tools should:

- ✅ Perform a single, well-defined operation
- ✅ Validate inputs and outputs
- ✅ Declare required permissions
- ✅ Respect timeouts and budgets
- ✅ Surface structured errors

Tools should not:

- ❌ Implement orchestration logic
- ❌ Invoke other agents or tools directly
- ❌ Manage hidden state (use services for shared state)

## Related Documentation

- [Overview](./overview.md) - Framework introduction
- [Architecture](./architecture.md) - System architecture
- [Runtime API](./runtime-api.md) - Runtime execution
- [Contracts](./contracts.md) - Tool contract details

---

Back to [docs index](./README.md)  
Back to [repository root](../README.md)


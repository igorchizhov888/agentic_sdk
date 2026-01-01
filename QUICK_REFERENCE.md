# Agentic SDK - Quick Reference

## Creating a New Tool
```python
from agentic_sdk.core.interfaces.tool import ITool, ToolSchema, ToolExecutionContext, ToolExecutionResult
from pydantic import BaseModel
from typing import Any, Dict

class MyToolInput(BaseModel):
    param1: str
    param2: int

class MyToolOutput(BaseModel):
    result: str

class MyTool(ITool):
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="my_tool",
            version="1.0.0",
            description="What this tool does",
            input_schema=MyToolInput.model_json_schema(),
            output_schema=MyToolOutput.model_json_schema(),
            category="general",
            tags=["example"],
        )
    
    async def validate_input(self, params: Dict[str, Any]) -> bool:
        try:
            MyToolInput(**params)
            return True
        except:
            return False
    
    async def execute(self, params: Dict[str, Any], context: ToolExecutionContext) -> ToolExecutionResult:
        try:
            input_data = MyToolInput(**params)
            # Do work here
            output = MyToolOutput(result="done")
            
            return ToolExecutionResult(
                tool_name=self.schema.name,
                tool_version=self.schema.version,
                execution_id=context.execution_id,
                success=True,
                output=output.model_dump(),
                duration_seconds=0.0,
            )
        except Exception as e:
            return ToolExecutionResult(
                tool_name=self.schema.name,
                tool_version=self.schema.version,
                execution_id=context.execution_id,
                success=False,
                output=None,
                duration_seconds=0.0,
                error=str(e),
            )
    
    async def health_check(self) -> bool:
        return True
    
    def get_dependencies(self) -> list[str]:
        return []
```

## Using MCP Server
```python
from agentic_sdk.mcp.server import MCPServer
from uuid import uuid4
from agentic_sdk.core.interfaces.tool import ToolExecutionContext

# Start server
mcp = MCPServer()
await mcp.start()

# Register tool
tool = MyTool()
await mcp.register_tool(tool)

# List tools
tools = await mcp.list_tools()

# Create context
context = ToolExecutionContext(
    tool_name="my_tool",
    tool_version="1.0.0",
    execution_id=uuid4(),
    agent_id=uuid4(),
    session_id=uuid4(),
    trace_id="trace-123",
    span_id="span-456",
)

# Execute tool
params = {"param1": "test", "param2": 42}
result = await mcp.invoke_tool("my_tool", params, context)

# Check result
if result.success:
    print(result.output)
else:
    print(result.error)

# Stop server
await mcp.stop()
```

## Common Commands
```bash
# Install in dev mode
pip install --break-system-packages -e .

# Run tests
python3 examples/test_mcp_verbose.py

# Check installation
python3 -c "import agentic_sdk; print(agentic_sdk.__version__)"

# Git commands
git status
git add .
git commit -m "message"
git push
```

## Project Structure
```
agentic_sdk/
├── src/agentic_sdk/
│   ├── core/interfaces/    # IAgent, ITool
│   ├── mcp/               # MCP Server
│   ├── adapters/          # Framework adapters (empty)
│   ├── runtime/           # Execution engine (future)
│   └── cli/               # Commands (future)
├── examples/              # Working examples
└── tests/                 # Test suite (future)
```

## Key Files

- `src/agentic_sdk/core/interfaces/tool.py` - Tool interface
- `src/agentic_sdk/core/interfaces/agent.py` - Agent interface
- `src/agentic_sdk/mcp/server.py` - MCP server
- `examples/tools/calculator_tool.py` - Example tool
- `examples/test_mcp_verbose.py` - Test suite

## Troubleshooting

**Import errors:**
```bash
pip install --break-system-packages -e .
```

**Tool not found:**
Check tool is registered: `await mcp.list_tools()`

**Validation failed:**
Print schema: `print(tool.schema.input_schema)`

## Next Development Tasks

1. Build a file reader tool
2. Build an HTTP client tool
3. Implement agent runtime
4. Add context persistence
5. Create CLI commands

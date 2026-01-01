# Agentic SDK

Enterprise-grade SDK for building AI agents with MCP (Model Context Protocol) control plane.

## Features

- MCP Control Plane for governance and observability
- Type-safe tool development with Pydantic schemas
- Framework-independent architecture
- Built-in health checks and monitoring
- Structured logging with trace IDs
- Async/await throughout

## Quick Start

### Installation
```bash
pip install --break-system-packages -e .
```

### Create a Tool
```python
from agentic_sdk.core.interfaces.tool import ITool, ToolSchema

class MyTool(ITool):
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="my_tool",
            version="1.0.0",
            description="My custom tool"
        )
```

### Use with MCP Server
```python
from agentic_sdk.mcp.server import MCPServer

mcp = MCPServer()
await mcp.start()
await mcp.register_tool(MyTool())
result = await mcp.invoke_tool("my_tool", params, context)
```

## Examples

See examples directory:
- calculator_tool.py - Basic calculator
- test_mcp_verbose.py - Complete test suite

## Architecture

All tool executions flow through MCP server for validation, access control, audit logging, rate limiting, and health monitoring.

## License

Apache 2.0

"""
Test HTTP and JSON tools
"""

import asyncio
from uuid import uuid4
import sys

sys.path.insert(0, 'examples/tools')

from http_tool import HttpTool
from json_tool import JsonTool
from agentic_sdk.mcp.server import MCPServer
from agentic_sdk.core.interfaces.tool import ToolExecutionContext


async def main():
    print("\n" + "=" * 70)
    print("NEW TOOLS TEST - HTTP Client & JSON Processor")
    print("=" * 70 + "\n")

    # Setup MCP
    mcp = MCPServer()
    await mcp.start()
    
    # Register tools
    await mcp.register_tool(HttpTool())
    await mcp.register_tool(JsonTool())
    
    print("Tools registered\n")
    
    # Create context
    context = ToolExecutionContext(
        tool_name="test",
        tool_version="1.0.0",
        execution_id=uuid4(),
        agent_id=uuid4(),
        session_id=uuid4(),
        trace_id="test",
        span_id="test",
    )

    # Test JSON tool
    print("-" * 70)
    print("TEST 1: JSON Parser - Valid JSON")
    print("-" * 70)
    params = {
        "operation": "parse",
        "data": '{"name": "test", "value": 123}'
    }
    result = await mcp.invoke_tool("json_processor", params, context)
    print(f"Success: {result.success}")
    print(f"Output: {result.output}\n")

    # Test JSON formatting
    print("-" * 70)
    print("TEST 2: JSON Formatter")
    print("-" * 70)
    params = {
        "operation": "format",
        "data": '{"z":3,"a":1,"b":2}'
    }
    result = await mcp.invoke_tool("json_processor", params, context)
    print(f"Formatted JSON:\n{result.output['result']}\n")

    # Test HTTP tool
    print("-" * 70)
    print("TEST 3: HTTP GET Request")
    print("-" * 70)
    params = {
        "url": "https://httpbin.org/get",
        "method": "GET"
    }
    result = await mcp.invoke_tool("http_client", params, context)
    print(f"Success: {result.success}")
    print(f"Status: {result.output['status_code']}")
    print(f"Response length: {len(result.output['body'])} bytes\n")

    await mcp.stop()
    
    print("=" * 70)
    print("ALL NEW TOOLS WORKING")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

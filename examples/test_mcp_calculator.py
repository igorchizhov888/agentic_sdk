"""
Test script: MCP Server with Calculator Tool
"""

import asyncio
from uuid import uuid4
import sys
sys.path.insert(0, 'examples/tools')

from calculator_tool import CalculatorTool
from agentic_sdk.mcp.server import MCPServer, MCPServerConfig
from agentic_sdk.core.interfaces.tool import ToolExecutionContext


async def main():
    print("=" * 50)
    print("Testing MCP Server with Calculator Tool")
    print("=" * 50)
    print()

    # Initialize MCP server
    config = MCPServerConfig()
    mcp = MCPServer(config)
    await mcp.start()
    
    print(f"MCP Server started (ID: {mcp.config.server_id})")
    print()

    # Register calculator tool
    tool = CalculatorTool()
    registration = await mcp.register_tool(tool)
    print(f"Tool registered: {registration.tool_name} v{registration.tool_version}")
    print()

    # List available tools
    tools = await mcp.list_tools()
    print(f"Available tools: {len(tools)}")
    for t in tools:
        print(f"  - {t['name']} v{t['version']}: {t['description']}")
    print()

    # Create execution context
    context = ToolExecutionContext(
        tool_name="calculator",
        tool_version="1.0.0",
        execution_id=uuid4(),
        agent_id=uuid4(),
        session_id=uuid4(),
        trace_id="test-trace",
        span_id="test-span",
    )

    # Test addition
    print("Test 1: Addition (10 + 5)")
    params = {"operation": "add", "a": 10, "b": 5}
    result = await mcp.invoke_tool("calculator", params, context)
    print(f"  Success: {result.success}")
    print(f"  Result: {result.output}")
    print(f"  Duration: {result.duration_seconds:.4f}s")
    print()

    # Test multiplication
    print("Test 2: Multiplication (7 * 8)")
    params = {"operation": "multiply", "a": 7, "b": 8}
    result = await mcp.invoke_tool("calculator", params, context)
    print(f"  Success: {result.success}")
    print(f"  Result: {result.output}")
    print()

    # Test division by zero (should fail gracefully)
    print("Test 3: Division by zero (10 / 0)")
    params = {"operation": "divide", "a": 10, "b": 0}
    result = await mcp.invoke_tool("calculator", params, context)
    print(f"  Success: {result.success}")
    print(f"  Error: {result.error}")
    print()

    # Cleanup
    await mcp.stop()
    print("MCP Server stopped")
    print()
    print("=" * 50)
    print("All tests completed!")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())

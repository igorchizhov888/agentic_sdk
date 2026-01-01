"""
Verbose test script with detailed output
"""

import asyncio
from uuid import uuid4
import sys
sys.path.insert(0, 'examples/tools')

from calculator_tool import CalculatorTool
from agentic_sdk.mcp.server import MCPServer, MCPServerConfig
from agentic_sdk.core.interfaces.tool import ToolExecutionContext


async def main():
    print("\n" + "=" * 60)
    print("MCP SERVER + CALCULATOR TOOL - VERBOSE TEST")
    print("=" * 60 + "\n")

    # Initialize MCP server
    config = MCPServerConfig()
    mcp = MCPServer(config)
    await mcp.start()
    
    print(f"[SUCCESS] MCP Server started")
    print(f"          Server ID: {mcp.config.server_id}")
    print(f"          Max concurrent: {mcp.config.max_concurrent_executions}\n")

    # Register calculator tool
    tool = CalculatorTool()
    registration = await mcp.register_tool(tool)
    print(f"[SUCCESS] Tool registered")
    print(f"          Name: {registration.tool_name}")
    print(f"          Version: {registration.tool_version}")
    print(f"          Tool ID: {registration.tool_id}")
    print(f"          Health: {registration.health_status}\n")

    # List available tools
    tools = await mcp.list_tools()
    print(f"[INFO] Available tools: {len(tools)}")
    for t in tools:
        print(f"       - {t['name']} v{t['version']}")
        print(f"         {t['description']}")
        print(f"         Category: {t['category']}, Tags: {t['tags']}\n")

    # Create execution context
    context = ToolExecutionContext(
        tool_name="calculator",
        tool_version="1.0.0",
        execution_id=uuid4(),
        agent_id=uuid4(),
        session_id=uuid4(),
        trace_id="test-trace-001",
        span_id="test-span-001",
    )

    print("-" * 60)
    print("EXECUTING TESTS")
    print("-" * 60 + "\n")

    # Test 1: Addition
    print("TEST 1: Addition (10 + 5)")
    params = {"operation": "add", "a": 10, "b": 5}
    result = await mcp.invoke_tool("calculator", params, context)
    print(f"  Success: {result.success}")
    print(f"  Output: {result.output}")
    print(f"  Duration: {result.duration_seconds:.6f}s\n")

    # Test 2: Subtraction
    print("TEST 2: Subtraction (100 - 37)")
    params = {"operation": "subtract", "a": 100, "b": 37}
    result = await mcp.invoke_tool("calculator", params, context)
    print(f"  Success: {result.success}")
    print(f"  Output: {result.output}")
    print(f"  Duration: {result.duration_seconds:.6f}s\n")

    # Test 3: Multiplication
    print("TEST 3: Multiplication (7 * 8)")
    params = {"operation": "multiply", "a": 7, "b": 8}
    result = await mcp.invoke_tool("calculator", params, context)
    print(f"  Success: {result.success}")
    print(f"  Output: {result.output}")
    print(f"  Duration: {result.duration_seconds:.6f}s\n")

    # Test 4: Division
    print("TEST 4: Division (144 / 12)")
    params = {"operation": "divide", "a": 144, "b": 12}
    result = await mcp.invoke_tool("calculator", params, context)
    print(f"  Success: {result.success}")
    print(f"  Output: {result.output}")
    print(f"  Duration: {result.duration_seconds:.6f}s\n")

    # Test 5: Error case - Division by zero
    print("TEST 5: Division by zero (10 / 0) - Should fail gracefully")
    params = {"operation": "divide", "a": 10, "b": 0}
    result = await mcp.invoke_tool("calculator", params, context)
    print(f"  Success: {result.success}")
    print(f"  Error: {result.error}")
    print(f"  Duration: {result.duration_seconds:.6f}s\n")

    # Test 6: Invalid operation
    print("TEST 6: Invalid operation - Should fail")
    params = {"operation": "power", "a": 2, "b": 3}
    result = await mcp.invoke_tool("calculator", params, context)
    print(f"  Success: {result.success}")
    print(f"  Error: {result.error}\n")

    print("-" * 60)
    print("STATISTICS")
    print("-" * 60 + "\n")
    
    reg = mcp._tool_registry["calculator:1.0.0"]
    print(f"Tool: {reg.tool_name}")
    print(f"Total invocations: {reg.invocation_count}")
    print(f"Total errors: {reg.error_count}")
    print(f"Success rate: {((reg.invocation_count - reg.error_count) / reg.invocation_count * 100):.1f}%\n")

    # Cleanup
    await mcp.stop()
    print("[SUCCESS] MCP Server stopped\n")
    print("=" * 60)
    print("ALL TESTS COMPLETED SUCCESSFULLY")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

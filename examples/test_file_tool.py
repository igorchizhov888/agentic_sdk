"""
Test file reader/writer tool
"""

import asyncio
from uuid import uuid4
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, 'examples/tools')

from file_tool import FileReaderWriterTool
from agentic_sdk.mcp.server import MCPServer
from agentic_sdk.core.interfaces.tool import ToolExecutionContext


async def main():
    print("\n" + "=" * 60)
    print("FILE TOOL TEST")
    print("=" * 60 + "\n")

    # Create temp directory for testing
    temp_dir = tempfile.mkdtemp()
    test_file = Path(temp_dir) / "test.txt"
    print(f"Test directory: {temp_dir}\n")

    # Initialize MCP server
    mcp = MCPServer()
    await mcp.start()
    print("[SUCCESS] MCP Server started\n")

    # Register file tool (allow temp directory)
    tool = FileReaderWriterTool(allowed_directories=[temp_dir])
    await mcp.register_tool(tool)
    print("[SUCCESS] File tool registered\n")

    # Create execution context
    context = ToolExecutionContext(
        tool_name="file_tool",
        tool_version="1.0.0",
        execution_id=uuid4(),
        agent_id=uuid4(),
        session_id=uuid4(),
        trace_id="test-trace",
        span_id="test-span",
    )

    print("-" * 60)
    print("TEST 1: Write to file")
    print("-" * 60)
    params = {
        "file_path": str(test_file),
        "content": "Hello from Agentic SDK!\nLine 2\nLine 3",
        "encoding": "utf-8",
    }
    result = await mcp.invoke_tool("file_tool", params, context)
    print(f"Success: {result.success}")
    print(f"Message: {result.output['message']}")
    print(f"Size: {result.output['size_bytes']} bytes\n")

    print("-" * 60)
    print("TEST 2: Read from file")
    print("-" * 60)
    params = {
        "file_path": str(test_file),
        "encoding": "utf-8",
    }
    result = await mcp.invoke_tool("file_tool", params, context)
    print(f"Success: {result.success}")
    print(f"Content:\n{result.output['content']}")
    print(f"Size: {result.output['size_bytes']} bytes\n")

    print("-" * 60)
    print("TEST 3: Append to file")
    print("-" * 60)
    params = {
        "file_path": str(test_file),
        "content": "\nAppended line!",
        "append": True,
    }
    result = await mcp.invoke_tool("file_tool", params, context)
    print(f"Success: {result.success}")
    print(f"Message: {result.output['message']}\n")

    print("-" * 60)
    print("TEST 4: Read again (should show appended content)")
    print("-" * 60)
    params = {
        "file_path": str(test_file),
    }
    result = await mcp.invoke_tool("file_tool", params, context)
    print(f"Content:\n{result.output['content']}\n")

    print("-" * 60)
    print("TEST 5: Try to access file outside allowed directory (should fail)")
    print("-" * 60)
    params = {
        "file_path": "/etc/passwd",
    }
    result = await mcp.invoke_tool("file_tool", params, context)
    print(f"Success: {result.success}")
    print(f"Error: {result.error}\n")

    # Cleanup
    await mcp.stop()
    import shutil
    shutil.rmtree(temp_dir)
    
    print("=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

"""
Test Basic Agent Runtime

Shows agent planning and executing multi-step tasks.
"""

import asyncio
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, 'examples/tools')

from calculator_tool import CalculatorTool
from file_tool import FileReaderWriterTool
from agentic_sdk.mcp.server import MCPServer
from agentic_sdk.runtime.basic_agent import BasicAgent
from agentic_sdk.core.interfaces.agent import AgentConfig


async def main():
    print("\n" + "=" * 70)
    print("AGENT RUNTIME TEST - Multi-Step Task Execution")
    print("=" * 70 + "\n")

    # Setup test environment
    temp_dir = tempfile.mkdtemp()
    test_file = Path(temp_dir) / "numbers.txt"
    test_file.write_text("10\n20\n30")
    print(f"Test file created: {test_file}")
    print(f"Content: 10, 20, 30\n")

    # Initialize MCP Server
    print("Initializing MCP Server...")
    mcp = MCPServer()
    await mcp.start()
    
    # Register tools
    print("Registering tools...")
    await mcp.register_tool(CalculatorTool())
    await mcp.register_tool(FileReaderWriterTool(allowed_directories=[temp_dir]))
    
    tools = await mcp.list_tools()
    print(f"Available tools: {len(tools)}")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")
    print()

    # Create agent
    print("Creating agent...")
    config = AgentConfig(
        name="demo_agent",
        model="gpt-4",  # Not used yet, placeholder
        system_prompt="You are a helpful assistant",
        max_iterations=5,
    )
    agent = BasicAgent(config=config, mcp_server=mcp)
    print(f"Agent created: {agent.agent_id}\n")

    # Test 1: Simple calculation
    print("=" * 70)
    print("TEST 1: Simple Calculation")
    print("=" * 70)
    task = "Calculate 25 + 17"
    print(f"Task: {task}\n")
    
    result = await agent.execute(task)
    
    print(f"Success: {result.success}")
    print(f"Iterations: {result.iterations}")
    print(f"Tools used: {result.tools_invoked}")
    print(f"Output:\n{result.output}")
    print(f"Duration: {result.duration_seconds:.3f}s\n")

    # Test 2: File reading
    print("=" * 70)
    print("TEST 2: File Reading")
    print("=" * 70)
    task = f"Read file {test_file}"
    print(f"Task: {task}\n")
    
    result = await agent.execute(task)
    
    print(f"Success: {result.success}")
    print(f"Tools used: {result.tools_invoked}")
    print(f"Output:\n{result.output}")
    print(f"Duration: {result.duration_seconds:.3f}s\n")

    # Test 3: Multiplication
    print("=" * 70)
    print("TEST 3: Multiplication")
    print("=" * 70)
    task = "Multiply 12 times 8"
    print(f"Task: {task}\n")
    
    result = await agent.execute(task)
    
    print(f"Success: {result.success}")
    print(f"Tools used: {result.tools_invoked}")
    print(f"Output:\n{result.output}")
    print(f"Duration: {result.duration_seconds:.3f}s\n")

    # Test 4: Division
    print("=" * 70)
    print("TEST 4: Division")
    print("=" * 70)
    task = "Divide 100 by 4"
    print(f"Task: {task}\n")
    
    result = await agent.execute(task)
    
    print(f"Success: {result.success}")
    print(f"Tools used: {result.tools_invoked}")
    print(f"Output:\n{result.output}\n")

    # Cleanup
    await mcp.stop()
    import shutil
    shutil.rmtree(temp_dir)
    
    print("=" * 70)
    print("ALL AGENT TESTS COMPLETED")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

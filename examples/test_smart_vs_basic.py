"""
Compare Basic Agent (keyword) vs Smart Agent (LLM)
"""

import asyncio
import sys

sys.path.insert(0, 'examples/tools')

from calculator_tool import CalculatorTool
from file_tool import FileReaderWriterTool
from http_tool import HttpTool
from json_tool import JsonTool

from agentic_sdk.mcp.server import MCPServer
from agentic_sdk.runtime.basic_agent import BasicAgent
from agentic_sdk.runtime.smart_agent import SmartAgent
from agentic_sdk.core.interfaces.agent import AgentConfig


async def main():
    print("\n" + "=" * 70)
    print("AGENT COMPARISON: Basic (Keyword) vs Smart (LLM)")
    print("=" * 70 + "\n")

    # Setup MCP
    mcp = MCPServer()
    await mcp.start()
    
    # Register all tools
    await mcp.register_tool(CalculatorTool())
    await mcp.register_tool(FileReaderWriterTool())
    await mcp.register_tool(HttpTool())
    await mcp.register_tool(JsonTool())
    
    print("Tools registered: 4\n")

    # Create both agents
    config = AgentConfig(
        name="test_agent",
        model="claude-haiku-4-5",
        system_prompt="You are a helpful assistant",
        max_iterations=5,
    )
    
    basic_agent = BasicAgent(config=config, mcp_server=mcp)
    smart_agent = SmartAgent(config=config, mcp_server=mcp)

    # Test tasks
    tasks = [
        "Calculate 245 plus 783",
        "What is 100 divided by 25?",
        "Multiply 12 by 34",
    ]

    for task in tasks:
        print("=" * 70)
        print(f"TASK: {task}")
        print("=" * 70)
        
        # Basic agent
        print("\n[BASIC AGENT - Keyword Planning]")
        result = await basic_agent.execute(task)
        print(f"Success: {result.success}")
        if result.success:
            print(f"Output: {result.output}")
        else:
            print(f"Failed: {result.error}")
        print(f"Duration: {result.duration_seconds:.3f}s")
        
        # Smart agent
        print("\n[SMART AGENT - LLM Planning]")
        result = await smart_agent.execute(task)
        print(f"Success: {result.success}")
        if result.success:
            print(f"Output: {result.output}")
        else:
            print(f"Failed: {result.error}")
        print(f"Duration: {result.duration_seconds:.3f}s")
        print()

    # Complex task that basic agent can't handle
    print("=" * 70)
    print("COMPLEX TASK (LLM should handle better)")
    print("=" * 70)
    
    complex_task = "I need to know the result of adding 150 and 250, then dividing that sum by 10"
    
    print(f"\nTask: {complex_task}\n")
    
    print("[BASIC AGENT]")
    result = await basic_agent.execute(complex_task)
    print(f"Success: {result.success}")
    print(f"Output: {result.output[:100]}...")
    
    print("\n[SMART AGENT]")
    result = await smart_agent.execute(complex_task)
    print(f"Success: {result.success}")
    print(f"Output: {result.output}")

    await mcp.stop()
    
    print("\n" + "=" * 70)
    print("COMPARISON COMPLETE")
    print("=" * 70 + "\n")
    print("Smart Agent uses LLM planning for better understanding!")
    print()


if __name__ == "__main__":
    asyncio.run(main())

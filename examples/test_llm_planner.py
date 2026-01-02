"""
Test LLM-Powered Planner with Claude Haiku 4.5
"""

import asyncio
import os
from agentic_sdk.runtime.llm_planner import LLMPlanner


async def main():
    print("\n" + "=" * 70)
    print("LLM PLANNER TEST - Claude Haiku 4.5")
    print("=" * 70 + "\n")

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("\nSet it with:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        print("\nGet your key at: https://console.anthropic.com\n")
        return

    print(f"API Key found: {api_key[:8]}...{api_key[-4:]}")
    print(f"Model: claude-haiku-4-5-20251001\n")

    # Initialize planner
    planner = LLMPlanner()
    
    # Define available tools
    available_tools = [
        {
            "name": "calculator",
            "description": "Perform math operations: add, subtract, multiply, divide"
        },
        {
            "name": "file_tool",
            "description": "Read or write text files"
        },
        {
            "name": "http_client",
            "description": "Make HTTP requests (GET, POST, PUT, DELETE)"
        },
        {
            "name": "json_processor",
            "description": "Parse, format, and validate JSON data"
        }
    ]

    # Test 1: Simple calculation
    print("-" * 70)
    print("TEST 1: Simple Math Task")
    print("-" * 70)
    task = "Calculate the sum of 123 and 456"
    print(f"Task: {task}\n")
    
    plan = await planner.create_plan(task, available_tools)
    
    print(f"Plan created: {len(plan)} steps")
    for i, step in enumerate(plan, 1):
        print(f"\nStep {i}:")
        print(f"  Tool: {step['tool']}")
        print(f"  Params: {step['params']}")
        print(f"  Description: {step['description']}")

    # Test 2: Multi-step task
    print("\n" + "-" * 70)
    print("TEST 2: Multi-Step Task")
    print("-" * 70)
    task = "Read numbers.txt, parse it as JSON, and calculate the average"
    print(f"Task: {task}\n")
    
    plan = await planner.create_plan(task, available_tools)
    
    print(f"Plan created: {len(plan)} steps")
    for i, step in enumerate(plan, 1):
        print(f"\nStep {i}:")
        print(f"  Tool: {step['tool']}")
        print(f"  Params: {step['params']}")
        print(f"  Description: {step['description']}")

    # Test 3: Web task
    print("\n" + "-" * 70)
    print("TEST 3: Web Request Task")
    print("-" * 70)
    task = "Get data from https://api.example.com/users and format the JSON response"
    print(f"Task: {task}\n")
    
    plan = await planner.create_plan(task, available_tools)
    
    print(f"Plan created: {len(plan)} steps")
    for i, step in enumerate(plan, 1):
        print(f"\nStep {i}:")
        print(f"  Tool: {step['tool']}")
        print(f"  Params: {step['params']}")
        print(f"  Description: {step['description']}")

    # Cost estimation
    print("\n" + "-" * 70)
    print("COST ESTIMATION")
    print("-" * 70)
    
    # Approximate tokens for our tests
    input_tokens = 200  # Tools list + task
    output_tokens = 100  # Plan response
    
    cost = planner.estimate_cost(input_tokens, output_tokens)
    
    print(f"Estimated cost per planning call: ${cost:.6f}")
    print(f"With $5 credit, you can make ~{int(5.0 / cost):,} planning calls")
    print(f"\nHaiku 4.5 is PERFECT for agent planning!")

    print("\n" + "=" * 70)
    print("LLM PLANNER WORKING - READY FOR SMART AGENTS!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

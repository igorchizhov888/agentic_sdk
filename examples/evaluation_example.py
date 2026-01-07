"""Evaluation test suite for agent prompts"""
import asyncio
import sys
import os

# Fix imports
sys.path.insert(0, '.')
sys.path.insert(0, 'examples/tools')

from src.agentic_sdk.eval import AgentEvaluator, TestCase
from src.agentic_sdk.mcp.server import MCPServer
from src.agentic_sdk.runtime.smart_agent import SmartAgent
from src.agentic_sdk.core.interfaces.agent import AgentConfig
from src.agentic_sdk.prompts import PromptManager, PromptStorage
from calculator_tool import CalculatorTool


# Define test cases - focus on correct output, not exact step count
EVAL_SUITE = [
    TestCase(
        id="calc_simple_add",
        task="Add 10 and 5",
        expected_tools=["calculator"],
        validator=lambda r: "15" in r.output or "15.0" in r.output,
        metadata={"category": "basic_math", "difficulty": "easy"}
    ),
    
    TestCase(
        id="calc_multi_step",
        task="Add 100 and 50, then multiply by 2",
        expected_tools=["calculator"],
        validator=lambda r: "300" in r.output or "300.0" in r.output,
        metadata={"category": "basic_math", "difficulty": "medium"}
    ),
    
    TestCase(
        id="calc_complex",
        task="Calculate (25 + 17) divided by 2",
        expected_tools=["calculator"],
        validator=lambda r: "21" in r.output or "21.0" in r.output,
        metadata={"category": "basic_math", "difficulty": "medium"}
    ),
    
    TestCase(
        id="calc_three_steps",
        task="Add 10 and 20, multiply result by 3, then divide by 2",
        expected_tools=["calculator"],
        validator=lambda r: "45" in r.output or "45.0" in r.output,
        metadata={"category": "basic_math", "difficulty": "hard"}
    ),
]


async def evaluate_prompt_version(version: int):
    """Evaluate a specific prompt version"""
    print(f"\n{'='*60}")
    print(f"Evaluating Prompt Version {version}")
    print(f"{'='*60}\n")
    
    # Setup
    storage = PromptStorage("prompts.db")
    manager = PromptManager(storage)
    manager.activate_version("agent_planner", version)
    
    mcp = MCPServer()
    await mcp.start()
    await mcp.register_tool(CalculatorTool())
    
    config = AgentConfig(
        name="eval_agent",
        model="claude-haiku-4-5",
        system_prompt="You are helpful",
        max_iterations=10
    )
    
    agent = SmartAgent(config, mcp, api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Run evaluation
    evaluator = AgentEvaluator()
    results = await evaluator.run_eval_suite(
        agent=agent,
        test_cases=EVAL_SUITE,
        run_id=f"prompt-v{version}-{int(asyncio.get_event_loop().time())}",
        prompt_version=version
    )
    
    # Print results
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    print(f"Pass rate: {passed/total*100:.1f}%")
    print(f"Total cost: ${sum(r.cost for r in results):.4f}")
    print(f"Avg duration: {sum(r.duration_seconds for r in results)/total:.3f}s\n")
    
    print("Individual Results:")
    print("-" * 60)
    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"[{status}] {r.test_case_id}")
        print(f"      Steps: {r.steps_taken}, Duration: {r.duration_seconds:.3f}s")
        if not r.passed:
            print(f"      Reason: {r.failure_reason}")
    
    await mcp.stop()
    return results


async def main():
    print("\n" + "="*60)
    print("AGENT EVALUATION FRAMEWORK")
    print("="*60)
    
    # Evaluate version 1
    results_v1 = await evaluate_prompt_version(1)
    
    # Evaluate version 3
    results_v3 = await evaluate_prompt_version(3)
    
    # Compare
    print(f"\n{'='*60}")
    print("COMPARISON: Version 1 vs Version 3")
    print(f"{'='*60}\n")
    
    v1_passed = sum(1 for r in results_v1 if r.passed)
    v3_passed = sum(1 for r in results_v3 if r.passed)
    
    v1_cost = sum(r.cost for r in results_v1)
    v3_cost = sum(r.cost for r in results_v3)
    
    v1_time = sum(r.duration_seconds for r in results_v1) / len(results_v1)
    v3_time = sum(r.duration_seconds for r in results_v3) / len(results_v3)
    
    print(f"Pass Rate:")
    print(f"  V1: {v1_passed}/{len(results_v1)} ({v1_passed/len(results_v1)*100:.1f}%)")
    print(f"  V3: {v3_passed}/{len(results_v3)} ({v3_passed/len(results_v3)*100:.1f}%)")
    
    print(f"\nCost:")
    print(f"  V1: ${v1_cost:.4f}")
    print(f"  V3: ${v3_cost:.4f}")
    print(f"  Difference: ${v3_cost - v1_cost:.4f}")
    
    print(f"\nAvg Duration:")
    print(f"  V1: {v1_time:.3f}s")
    print(f"  V3: {v3_time:.3f}s")
    print(f"  Difference: {v3_time - v1_time:.3f}s")
    
    # Recommendation
    print(f"\n{'='*60}")
    if v3_passed > v1_passed:
        print("RECOMMENDATION: Deploy Version 3 (better accuracy)")
    elif v3_passed == v1_passed and v3_cost < v1_cost:
        print("RECOMMENDATION: Deploy Version 3 (same accuracy, lower cost)")
    elif v3_passed == v1_passed and v3_time < v1_time:
        print("RECOMMENDATION: Deploy Version 3 (same accuracy, faster)")
    else:
        print("RECOMMENDATION: Keep Version 1 (current is better)")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(main())

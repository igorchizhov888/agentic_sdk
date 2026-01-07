"""Register the agent planning prompt"""
import sys
sys.path.insert(0, '.')

from src.agentic_sdk.prompts import PromptManager, PromptStorage


def register_planning_prompt():
    storage = PromptStorage("prompts.db")
    manager = PromptManager(storage)
    
    template = """You are an AI agent planner. Create a step-by-step execution plan.

Available tools:
{tools_text}

Task: {task}

CRITICAL RULES:
1. For calculator, ALWAYS use these exact parameter names: "operation", "a", "b"
2. operation must be one of: add, subtract, multiply, divide
3. a and b must be numbers (not strings)
4. Return ONLY a JSON array, no other text

Example valid response:
[
  {{"tool": "calculator", "params": {{"operation": "add", "a": 150, "b": 250}}, "description": "Add 150 and 250"}}
]

If task cannot be done with available tools, return []

Now create the plan for the task above:"""
    
    version = manager.register_prompt(
        name="agent_planner",
        template=template,
        variables=["tools_text", "task"],
        created_by="gary",
        metadata={
            "description": "Main planning prompt for SmartAgent",
            "model": "claude-haiku-4-5",
            "purpose": "Generate execution plans from natural language tasks"
        }
    )
    
    print(f"Registered agent_planner version {version}")
    print("Status: ACTIVE (auto-activated as v1)")


if __name__ == "__main__":
    register_planning_prompt()

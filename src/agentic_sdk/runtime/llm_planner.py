"""
LLM-Powered Planner using Anthropic Claude
"""

import os
from typing import Any, Dict, List
import anthropic
from structlog import get_logger

logger = get_logger(__name__)


class LLMPlanner:
    """LLM-powered task planner using Claude Haiku 4.5."""

    def __init__(self, api_key: str = None, model: str = "claude-haiku-4-5-20251001"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        logger.info("llm_planner_initialized", model=model)

    async def create_plan(
        self,
        task: str,
        available_tools: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Create execution plan using Claude."""
        
        # Build detailed tool descriptions with example params
        tool_descriptions = []
        for tool in available_tools:
            if tool['name'] == 'calculator':
                desc = """- calculator: Perform math operations
  Example params: {"operation": "add", "a": 10, "b": 5}
  Operations: add, subtract, multiply, divide
  IMPORTANT: Use exact keys "operation", "a", "b" """
            elif tool['name'] == 'file_tool':
                desc = """- file_tool: Read or write text files
  Read example: {"file_path": "/path/to/file.txt"}
  Write example: {"file_path": "/path/to/file.txt", "content": "text", "append": false}"""
            elif tool['name'] == 'http_client':
                desc = """- http_client: Make HTTP requests
  Example: {"url": "https://api.example.com", "method": "GET"}"""
            elif tool['name'] == 'json_processor':
                desc = """- json_processor: Parse and format JSON
  Example: {"operation": "parse", "data": "{\\"key\\": \\"value\\"}"}"""
            else:
                desc = f"- {tool['name']}: {tool['description']}"
            
            tool_descriptions.append(desc)
        
        tools_text = "\n".join(tool_descriptions)
        
        prompt = f"""You are an AI agent planner. Create a step-by-step execution plan.

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

        try:
            logger.debug("llm_planning_request", task=task)
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            
            # Clean response
            import json
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()
            
            plan = json.loads(response_text)
            
            logger.info("llm_plan_created", steps=len(plan), task=task)
            logger.debug("llm_plan_details", plan=plan)
            
            return plan
            
        except json.JSONDecodeError as e:
            logger.error("llm_plan_parse_error", error=str(e), response=response_text)
            return []
        except Exception as e:
            logger.error("llm_planning_failed", error=str(e))
            return []

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost of API call."""
        input_cost = input_tokens * 0.80 / 1_000_000
        output_cost = output_tokens * 4.0 / 1_000_000
        return input_cost + output_cost

"""
LLM-Powered Planner using Anthropic Claude
"""

import os
from typing import Any, Dict, List, Optional, Tuple
import json
import anthropic
from structlog import get_logger
from agentic_sdk.prompts import PromptManager, PromptStorage

logger = get_logger(__name__)


class LLMPlanner:
    """LLM-powered task planner using Claude Haiku 4.5."""

    def __init__(
        self, 
        api_key: str = None, 
        model: str = "claude-haiku-4-5-20251001",
        prompt_manager: Optional[PromptManager] = None
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Initialize prompt manager
        if prompt_manager is None:
            storage = PromptStorage("prompts.db")
            self.prompt_manager = PromptManager(storage)
        else:
            self.prompt_manager = prompt_manager
        
        logger.info("llm_planner_initialized", model=model)

    async def create_plan(
        self,
        task: str,
        available_tools: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], Optional[int]]:
        """
        Create execution plan using Claude.
        
        Returns:
            (plan, prompt_version) - prompt_version is set if A/B test is active
        """
        
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
        
        # Get prompt from prompt manager (may include A/B test version)
        prompt_template, ab_version = self.prompt_manager.get_prompt("agent_planner")
        prompt = prompt_template.format(tools_text=tools_text, task=task)

        try:
            logger.debug("llm_planning_request", task=task, ab_version=ab_version)
            
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text.strip()
            
            # Clean response
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
                if response_text.startswith("json"):
                    response_text = response_text[4:].strip()
            
            plan = json.loads(response_text)
            
            logger.info("llm_plan_created", steps=len(plan), task=task, ab_version=ab_version)
            logger.debug("llm_plan_details", plan=plan)
            
            return plan, ab_version
            
        except json.JSONDecodeError as e:
            logger.error("llm_plan_parse_error", error=str(e), response=response_text)
            return [], ab_version
        except Exception as e:
            logger.error("llm_planning_failed", error=str(e))
            return [], ab_version

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost of API call."""
        input_cost = input_tokens * 0.80 / 1_000_000
        output_cost = output_tokens * 4.0 / 1_000_000
        return input_cost + output_cost

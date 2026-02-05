"""
LLM-Powered Planner using Ollama (Local)

Free, local LLM with no API costs.
"""
import json
from typing import Any, Dict, List, Optional, Tuple
import requests
from structlog import get_logger
from agentic_sdk.prompts import PromptManager, PromptStorage

logger = get_logger(__name__)


class OllamaLLMPlanner:
    """LLM-powered task planner using local Ollama."""
    
    def __init__(
        self, 
        model: str = "phi3:latest",
        base_url: str = "http://localhost:11434",
        prompt_manager: Optional[PromptManager] = None
    ):
        self.model = model
        self.base_url = base_url
        
        # Initialize prompt manager
        self.prompt_manager = prompt_manager
        if not self.prompt_manager:
            storage = PromptStorage()
            self.prompt_manager = PromptManager(storage)
        
        # Test connection
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                logger.info("ollama_planner_initialized", model=self.model)
            else:
                logger.warning("ollama_not_running", 
                             message="Run 'ollama serve' to start")
        except Exception as e:
            logger.error("ollama_connection_failed", error=str(e))
    
    async def create_plan(
        self, 
        task: str, 
        available_tools: List[Dict[str, Any]],
        ab_tester = None
    ) -> Tuple[List[Dict[str, Any]], Optional[int]]:
        """
        Create execution plan using Ollama LLM.
        
        Returns:
            (plan, ab_version) - plan is list of steps, ab_version for A/B testing
        """
        ab_version = None
        
        try:
            # Get prompt (with A/B testing if available)
            try:
                # get_prompt handles A/B testing internally via self.ab_tester
                prompt_template, ab_version = self.prompt_manager.get_prompt("agent_planner_ollama")
                logger.debug("ollama_prompt_loaded", template_len=len(prompt_template))
            except Exception as e:
                logger.error("ollama_prompt_load_failed", error=str(e))
                raise
            
            # Format tools
            tools_desc = "\n".join([
                f"- {t['name']}: {t.get('description', 'No description')}"
                for t in available_tools
            ])
            
            # Fill prompt
            full_prompt = prompt_template.format(
                task=task,
                tools_text=tools_desc
            )
            
            logger.debug("ollama_planning_request", task=task, ab_version=ab_version)
            logger.debug("ollama_prompt", prompt_len=len(full_prompt))
            
            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=120
            )
            
            logger.debug("ollama_response_status", status=response.status_code)
            
            if response.status_code != 200:
                logger.error("ollama_request_failed", 
                           status=response.status_code,
                           error=response.text)
                return [], ab_version
            
            result = response.json()
            logger.debug("ollama_full_result", keys=list(result.keys()))
            response_text = result.get("response", "")
            logger.debug("ollama_raw_response", response_len=len(response_text), response=response_text[:200])
            
            # Parse JSON plan - extract from markdown and clean
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            
            # Remove trailing commas and fix common issues
            json_str = json_str.rstrip(',')
            # Fix extra closing braces
            json_str = json_str.replace('}}}]', '}}]')
            json_str = json_str.replace('}}],', '}}]')
            
            plan = json.loads(json_str)
            
            # Handle different response formats
            if isinstance(plan, dict):
                # Try common keys
                if "steps" in plan:
                    plan = plan["steps"]
                elif "tools_used" in plan:
                    plan = plan["tools_used"]
                elif "plan" in plan:
                    plan = plan["plan"]
                else:
                    plan = []
            
            if not isinstance(plan, list):
                plan = []
            
            # Normalize plan format to match SmartAgent expectations
            normalized = []
            for step in plan:
                if isinstance(step, dict):
                    # Handle nested format from Ollama
                    if 'inputs' in step:
                        tool_data = step['inputs'].get('tool', {})
                        tool_name = tool_data.get('type') or tool_data.get('name')
                        params = step['inputs'].get('params', {})
                        normalized.append({
                            'tool': tool_name,
                            'params': params,
                            'description': step.get('name', '')
                        })
                    # Handle flat format
                    elif 'tool' in step and 'params' in step:
                        normalized.append(step)
            
            logger.info("ollama_planning_success", steps=len(normalized))
            return normalized, ab_version
            
        except Exception as e:
            logger.error("ollama_planning_failed", error=str(e))
            return [], ab_version

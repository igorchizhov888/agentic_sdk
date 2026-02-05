"""
LLM Planner Factory

Creates the appropriate LLM planner based on configuration.
Supports: Anthropic Claude, Google Gemini, Ollama (local)
"""
import os
from typing import Optional
from .llm_planner import LLMPlanner
from .llm_planner_ollama import OllamaLLMPlanner


def create_llm_planner(
    provider: str = None,
    api_key: str = None,
    model: str = None,
    prompt_manager = None
):
    """
    Create LLM planner based on provider.
    
    Args:
        provider: "anthropic", "gemini", or "ollama" (default: auto-detect)
        api_key: API key for cloud providers (not needed for ollama)
        model: Model name (optional, uses defaults)
        prompt_manager: PromptManager instance (optional)
        
    Returns:
        LLM planner instance
        
    Auto-detection priority:
    1. If provider specified, use that
    2. If ANTHROPIC_API_KEY set, use Anthropic
    3. If GEMINI_API_KEY set, use Gemini
    4. Otherwise, use Ollama (local, free)
    """
    
    if not provider:
        if api_key or os.getenv("ANTHROPIC_API_KEY"):
            provider = "anthropic"
        elif os.getenv("GEMINI_API_KEY"):
            provider = "gemini"
        else:
            provider = "ollama"
    
    provider = provider.lower()
    
    if provider == "ollama":
        return OllamaLLMPlanner(
            model=model or "llama3.2:latest",
            prompt_manager=prompt_manager
        )
    
    elif provider in ["anthropic", "claude"]:
        return LLMPlanner(
            api_key=api_key,
            model=model or "claude-haiku-4-5-20251001",
            prompt_manager=prompt_manager
        )
    
    else:
        print(f"Warning: Provider {provider} not supported, using Ollama")
        return OllamaLLMPlanner(
            model=model or "llama3.2:latest",
            prompt_manager=prompt_manager
        )

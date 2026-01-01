"""
Agentic SDK

A modular, extensible, MCP-enabled SDK for building enterprise-grade AI agents.
"""

__version__ = "0.1.0"
__author__ = "Gary"
__license__ = "Apache-2.0"

from agentic_sdk.core.interfaces.agent import IAgent, AgentConfig, AgentExecutionResult
from agentic_sdk.core.interfaces.tool import ITool, ToolSchema, ToolExecutionResult
from agentic_sdk.mcp.server import MCPServer, MCPServerConfig

__all__ = [
    "IAgent",
    "AgentConfig",
    "AgentExecutionResult",
    "ITool",
    "ToolSchema",
    "ToolExecutionResult",
    "MCPServer",
    "MCPServerConfig",
]

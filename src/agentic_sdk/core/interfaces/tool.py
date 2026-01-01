"""
Core tool interface definition.

All tools must implement this interface for type safety and MCP compatibility.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel


class ToolSchema(BaseModel):
    """Schema definition for a tool."""
    name: str
    version: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    category: str = "general"
    tags: list[str] = []
    requires_auth: bool = False
    rate_limit: Optional[int] = None
    timeout_seconds: int = 30
    idempotent: bool = False
    metadata: Dict[str, Any] = {}


class ToolExecutionContext(BaseModel):
    """Context for tool execution."""
    tool_name: str
    tool_version: str
    execution_id: UUID
    agent_id: UUID
    session_id: UUID
    user_id: Optional[str] = None
    trace_id: str
    span_id: str
    metadata: Dict[str, Any] = {}


class ToolExecutionResult(BaseModel):
    """Result of tool execution."""
    tool_name: str
    tool_version: str
    execution_id: UUID
    success: bool
    output: Any
    duration_seconds: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class ITool(ABC):
    """
    Core tool interface.
    
    All tools must implement this interface. Tools are executed
    through the MCP server, never directly by agents.
    """

    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        """Get tool schema with complete type information."""
        pass

    @abstractmethod
    async def validate_input(self, params: Dict[str, Any]) -> bool:
        """Validate input parameters."""
        pass

    @abstractmethod
    async def execute(
        self, params: Dict[str, Any], context: ToolExecutionContext
    ) -> ToolExecutionResult:
        """Execute the tool with given parameters."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if tool is healthy and operational."""
        pass

    @abstractmethod
    def get_dependencies(self) -> list[str]:
        """Get list of dependencies required by this tool."""
        pass

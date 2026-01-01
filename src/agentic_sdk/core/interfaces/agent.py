"""
Core agent interface definition.

All agents must implement this interface for MCP compatibility.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class AgentConfig(BaseModel):
    """Configuration for agent initialization."""
    name: str
    model: str
    system_prompt: str
    max_iterations: int = 10
    temperature: float = 0.7
    timeout_seconds: int = 300
    retry_policy: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}


class AgentContext(BaseModel):
    """Runtime context for agent execution."""
    agent_id: UUID
    session_id: UUID
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    trace_id: str
    parent_span_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class AgentExecutionResult(BaseModel):
    """Result of agent task execution."""
    agent_id: UUID
    session_id: UUID
    task: str
    output: str
    success: bool
    iterations: int
    tools_invoked: List[str]
    total_tokens: int
    total_cost: float
    duration_seconds: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = {}


class IAgent(ABC):
    """
    Core agent interface.
    
    Agents must use MCP server to discover and invoke tools.
    Never invoke tools directly.
    """

    @property
    @abstractmethod
    def config(self) -> AgentConfig:
        """Get agent configuration."""
        pass

    @property
    @abstractmethod
    def agent_id(self) -> UUID:
        """Get unique agent identifier."""
        pass

    @abstractmethod
    async def execute(
        self,
        task: str,
        context: Optional[AgentContext] = None,
        max_iterations: Optional[int] = None,
    ) -> AgentExecutionResult:
        """Execute a task using the agent."""
        pass

    @abstractmethod
    async def plan(self, task: str, context: AgentContext) -> List[Dict[str, Any]]:
        """Create execution plan for a task."""
        pass

    @abstractmethod
    async def reset(self) -> None:
        """Reset agent state."""
        pass

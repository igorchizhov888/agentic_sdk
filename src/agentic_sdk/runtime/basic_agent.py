"""
Basic Agent Runtime

Simple agent that can plan and execute multi-step tasks.
"""

import time
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4

from agentic_sdk.core.interfaces.agent import (
    IAgent, 
    AgentConfig, 
    AgentContext, 
    AgentExecutionResult
)
from agentic_sdk.core.interfaces.tool import ToolExecutionContext
from agentic_sdk.mcp.server import MCPServer
from structlog import get_logger

logger = get_logger(__name__)


class BasicAgent(IAgent):
    """
    Simple agent implementation.
    
    This agent:
    1. Takes a task as plain text
    2. Creates a simple plan (for now, just tries available tools)
    3. Executes tools via MCP server
    4. Returns results
    
    Future: Add LLM integration for smart planning
    """

    def __init__(self, config: AgentConfig, mcp_server: MCPServer):
        """
        Initialize agent.
        
        Args:
            config: Agent configuration
            mcp_server: MCP server instance for tool execution
        """
        self._config = config
        self._mcp = mcp_server
        self._agent_id = uuid4()
        self._iteration_count = 0

    @property
    def config(self) -> AgentConfig:
        return self._config

    @property
    def agent_id(self) -> UUID:
        return self._agent_id

    async def execute(
        self,
        task: str,
        context: Optional[AgentContext] = None,
        max_iterations: Optional[int] = None,
    ) -> AgentExecutionResult:
        """Execute a task."""
        start_time = time.time()
        
        # Create context if not provided
        if context is None:
            context = AgentContext(
                agent_id=self._agent_id,
                session_id=uuid4(),
                trace_id=f"trace-{uuid4()}",
            )

        max_iter = max_iterations or self._config.max_iterations
        tools_invoked = []
        output_parts = []
        total_tokens = 0
        success = True
        error_msg = None

        logger.info(
            "agent_execution_started",
            agent_id=str(self._agent_id),
            task=task,
            max_iterations=max_iter,
        )

        try:
            # Create execution plan
            plan = await self.plan(task, context)
            
            logger.info(
                "agent_plan_created",
                agent_id=str(self._agent_id),
                steps=len(plan),
            )

            # Execute each step in the plan
            for i, step in enumerate(plan):
                if i >= max_iter:
                    logger.warning("max_iterations_reached", iteration=i)
                    break

                self._iteration_count += 1
                
                tool_name = step["tool"]
                params = step["params"]
                
                logger.info(
                    "agent_executing_step",
                    step=i+1,
                    tool=tool_name,
                )

                # Create tool execution context
                tool_context = ToolExecutionContext(
                    tool_name=tool_name,
                    tool_version="1.0.0",  # TODO: get from registry
                    execution_id=uuid4(),
                    agent_id=self._agent_id,
                    session_id=context.session_id,
                    user_id=context.user_id,
                    trace_id=context.trace_id,
                    span_id=f"span-{i}",
                )

                # Execute via MCP
                result = await self._mcp.invoke_tool(
                    tool_name=tool_name,
                    params=params,
                    context=tool_context,
                )

                tools_invoked.append(tool_name)

                if result.success:
                    output_parts.append(f"Step {i+1}: {result.output}")
                    logger.info(
                        "agent_step_completed",
                        step=i+1,
                        success=True,
                    )
                else:
                    error_msg = f"Step {i+1} failed: {result.error}"
                    success = False
                    logger.error(
                        "agent_step_failed",
                        step=i+1,
                        error=result.error,
                    )
                    break

            # Combine output
            final_output = "\n".join(output_parts) if output_parts else "No output"

        except Exception as e:
            success = False
            error_msg = str(e)
            final_output = ""
            logger.error(
                "agent_execution_error",
                agent_id=str(self._agent_id),
                error=str(e),
            )

        duration = time.time() - start_time

        result = AgentExecutionResult(
            agent_id=self._agent_id,
            session_id=context.session_id,
            task=task,
            output=final_output,
            success=success,
            iterations=self._iteration_count,
            tools_invoked=tools_invoked,
            total_tokens=total_tokens,
            total_cost=0.0,  # TODO: calculate cost
            duration_seconds=duration,
            error=error_msg,
        )

        logger.info(
            "agent_execution_completed",
            agent_id=str(self._agent_id),
            success=success,
            duration=duration,
        )

        return result

    async def plan(self, task: str, context: AgentContext) -> List[Dict[str, Any]]:
        """
        Create execution plan.
        
        For now, this is very simple - it just returns available tools.
        Future: Use LLM to create smart plans based on task.
        """
        # Get available tools
        tools = await self._mcp.list_tools()
        
        # Simple planning: parse task for keywords
        task_lower = task.lower()
        plan = []

        # Look for file operations
        if "read" in task_lower and "file" in task_lower:
            # Extract filename (simple parsing)
            words = task.split()
            for word in words:
                if ".txt" in word or ".md" in word or ".py" in word:
                    plan.append({
                        "tool": "file_tool",
                        "params": {"file_path": word},
                        "description": f"Read {word}",
                    })
                    break

        # Look for calculations
        if any(op in task_lower for op in ["add", "subtract", "multiply", "divide", "calculate"]):
            # Simple number extraction
            import re
            numbers = re.findall(r'\d+\.?\d*', task)
            if len(numbers) >= 2:
                operation = "add"
                if "subtract" in task_lower or "-" in task:
                    operation = "subtract"
                elif "multiply" in task_lower or "*" in task or "times" in task_lower:
                    operation = "multiply"
                elif "divide" in task_lower or "/" in task:
                    operation = "divide"
                
                plan.append({
                    "tool": "calculator",
                    "params": {
                        "operation": operation,
                        "a": float(numbers[0]),
                        "b": float(numbers[1]),
                    },
                    "description": f"{operation} {numbers[0]} and {numbers[1]}",
                })

        # If no plan created, return empty (agent will fail gracefully)
        if not plan:
            logger.warning(
                "agent_no_plan_created",
                task=task,
                available_tools=len(tools),
            )

        return plan

    async def reset(self) -> None:
        """Reset agent state."""
        self._iteration_count = 0
        logger.info("agent_reset", agent_id=str(self._agent_id))

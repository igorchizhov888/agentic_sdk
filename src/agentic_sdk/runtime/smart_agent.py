"""
Smart Agent with LLM-Powered Planning and Observability

Uses Claude Haiku 4.5 for intelligent task planning with full tracing.
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
from agentic_sdk.runtime.llm_planner import LLMPlanner
from agentic_sdk.observability import AgentTracer
from structlog import get_logger

logger = get_logger(__name__)


class SmartAgent(IAgent):
    """
    Intelligent agent with LLM-powered planning and observability.
    
    Uses Claude Haiku 4.5 to:
    - Understand natural language tasks
    - Select appropriate tools intelligently
    - Create optimal execution plans
    
    Includes full observability:
    - Distributed tracing
    - Span tracking for operations
    - Metrics collection
    """

    def __init__(self, config: AgentConfig, mcp_server: MCPServer, 
                 api_key: str = None, tracer: Optional[AgentTracer] = None):
        """
        Initialize smart agent.
        
        Args:
            config: Agent configuration
            mcp_server: MCP server instance
            api_key: Anthropic API key (optional, reads from env)
            tracer: AgentTracer for observability (optional)
        """
        self._config = config
        self._mcp = mcp_server
        self._agent_id = uuid4()
        self._iteration_count = 0
        self._planner = LLMPlanner(api_key=api_key)
        self._tracer = tracer or AgentTracer()

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
        """Execute a task using LLM planning with full tracing."""
        start_time = time.time()
        
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
            "smart_agent_execution_started",
            agent_id=str(self._agent_id),
            task=task,
            planning="llm",
        )

        # Start tracing
        with self._tracer.trace_execution(
            agent_id=str(self._agent_id),
            session_id=str(context.session_id),
            task=task,
            metadata={
                "agent_name": self._config.name,
                "model": self._config.model,
                "max_iterations": max_iter
            }
        ) as trace_id:
            
            try:
                # Create execution plan using LLM - with span
                with self._tracer.start_span("llm_planning") as span:
                    span.set_attribute("model", "claude-haiku-4-5")
                    span.set_attribute("agent_id", str(self._agent_id))
                    
                    plan = await self.plan(task, context)
                    
                    span.set_attribute("plan_steps", len(plan))
                    self._tracer.record_metric("plan_steps", len(plan))
                
                logger.info(
                    "llm_plan_received",
                    agent_id=str(self._agent_id),
                    steps=len(plan),
                )

                if not plan:
                    return AgentExecutionResult(
                        agent_id=self._agent_id,
                        session_id=context.session_id,
                        task=task,
                        output="No plan could be created for this task with available tools",
                        success=False,
                        iterations=0,
                        tools_invoked=[],
                        total_tokens=0,
                        total_cost=0.0,
                        duration_seconds=time.time() - start_time,
                        error="Planning failed",
                    )

                # Execute each step - with spans
                for i, step in enumerate(plan):
                    if i >= max_iter:
                        logger.warning("max_iterations_reached", iteration=i)
                        break

                    self._iteration_count += 1
                    
                    tool_name = step["tool"]
                    params = step["params"]
                    
                    with self._tracer.start_span("tool_execution") as span:
                        span.set_attribute("tool", tool_name)
                        span.set_attribute("step", i+1)
                        span.set_attribute("params", str(params))
                        
                        logger.info(
                            "executing_planned_step",
                            step=i+1,
                            tool=tool_name,
                            description=step.get("description", ""),
                        )

                        # Create tool execution context
                        tool_context = ToolExecutionContext(
                            tool_name=tool_name,
                            tool_version="1.0.0",
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
                        
                        span.set_attribute("success", result.success)
                        if not result.success:
                            span.set_attribute("error", result.error)

                        tools_invoked.append(tool_name)
                        
                        # Record metrics
                        self._tracer.record_metric(
                            "tool_calls", 
                            1, 
                            {"tool": tool_name, "success": str(result.success)}
                        )

                        if result.success:
                            output_parts.append(f"Step {i+1} ({step.get('description', tool_name)}): {result.output}")
                        else:
                            error_msg = f"Step {i+1} failed: {result.error}"
                            success = False
                            logger.error("planned_step_failed", step=i+1, error=result.error)
                            break

                final_output = "\n".join(output_parts) if output_parts else "No output"
                
                # Record final metrics
                self._tracer.record_metric("iterations", self._iteration_count)
                self._tracer.record_metric("tools_invoked", len(tools_invoked))
                self._tracer.record_metric("success", 1.0 if success else 0.0)

            except Exception as e:
                success = False
                error_msg = str(e)
                final_output = ""
                logger.error("smart_agent_execution_error", error=str(e))

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
            total_cost=0.0,
            duration_seconds=duration,
            error=error_msg,
        )

        logger.info(
            "smart_agent_execution_completed",
            success=success,
            duration=duration,
            steps_executed=len(tools_invoked),
        )

        return result

    async def plan(self, task: str, context: AgentContext) -> List[Dict[str, Any]]:
        """Create execution plan using LLM."""
        # Get available tools from MCP
        tools = await self._mcp.list_tools()
        
        # Use LLM planner
        plan = await self._planner.create_plan(task, tools)
        
        return plan

    async def reset(self) -> None:
        """Reset agent state."""
        self._iteration_count = 0
        logger.info("smart_agent_reset", agent_id=str(self._agent_id))

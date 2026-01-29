"""
Smart Agent with LLM-Powered Planning, Observability, A/B Testing, and Memory

Uses Claude Haiku 4.5 for intelligent task planning with full tracing and memory.
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
from agentic_sdk.memory import HierarchicalMemory
from structlog import get_logger

logger = get_logger(__name__)


class SmartAgent(IAgent):
    """
    Intelligent agent with LLM-powered planning, observability, A/B testing, and memory.
    
    Uses Claude Haiku 4.5 to:
    - Understand natural language tasks
    - Select appropriate tools intelligently
    - Create optimal execution plans
    
    Includes full observability:
    - Distributed tracing
    - Span tracking for operations
    - Metrics collection
    
    Supports A/B testing:
    - Automatic prompt version selection
    - Result recording for analysis
    
    Three-level memory hierarchy:
    - L1 Working Memory: Task-scoped, volatile
    - L2 Session Memory: Session-scoped, persistent
    - L3 Long-term Memory: Cross-session, persistent
    """

    def __init__(self, config: AgentConfig, mcp_server: MCPServer, 
                 api_key: str = None, tracer: Optional[AgentTracer] = None,
                 ab_tester = None, enable_memory: bool = True,
                 user_id: str = "default"):
        """
        Initialize smart agent.
        
        Args:
            config: Agent configuration
            mcp_server: MCP server instance
            api_key: Anthropic API key (optional, reads from env)
            tracer: AgentTracer for observability (optional)
            ab_tester: ABTester for A/B testing (optional)
            enable_memory: Enable hierarchical memory (default: True)
            user_id: User ID for long-term memory (default: "default")
        """
        self._config = config
        self._mcp = mcp_server
        self._agent_id = uuid4()
        self._iteration_count = 0
        self._planner = LLMPlanner(api_key=api_key)
        self._tracer = tracer or AgentTracer()
        self._ab_tester = ab_tester
        
        # Initialize hierarchical memory
        self._enable_memory = enable_memory
        self._memory = None  # Created per session with HierarchicalMemory
        self._user_id = user_id

    @property
    def config(self) -> AgentConfig:
        return self._config

    @property
    def agent_id(self) -> UUID:
        return self._agent_id
    
    @property
    def memory(self) -> Optional[HierarchicalMemory]:
        """Access hierarchical memory (all three levels)"""
        return self._memory

    async def execute(
        self,
        task: str,
        context: Optional[AgentContext] = None,
        max_iterations: Optional[int] = None,
    ) -> AgentExecutionResult:
        """Execute a task using LLM planning with full tracing, A/B testing, and memory."""
        start_time = time.time()
        
        if context is None:
            context = AgentContext(
                agent_id=self._agent_id,
                session_id=uuid4(),
                trace_id=f"trace-{uuid4()}",
            )
        
        # Initialize hierarchical memory for this session
        if self._enable_memory:
            self._memory = HierarchicalMemory(
                user_id=self._user_id,
                session_id=str(context.session_id)
            )
            
            # Store task context
            self._memory.store("task", task, level="working")
            self._memory.store("session_id", str(context.session_id), level="working")
            self._memory.store("agent_id", str(self._agent_id), level="working")

        max_iter = max_iterations or self._config.max_iterations
        tools_invoked = []
        output_parts = []
        total_tokens = 0
        success = True
        error_msg = None
        ab_version = None

        logger.info(
            "smart_agent_execution_started",
            agent_id=str(self._agent_id),
            task=task,
            planning="llm",
            memory_enabled=self._enable_memory,
        )

        # Start tracing
        with self._tracer.trace_execution(
            agent_id=str(self._agent_id),
            session_id=str(context.session_id),
            task=task,
            metadata={
                "agent_name": self._config.name,
                "model": self._config.model,
                "max_iterations": max_iter,
                "memory_enabled": self._enable_memory,
                "user_id": self._user_id
            }
        ) as trace_id:
            
            try:
                # Create execution plan using LLM - with span
                with self._tracer.start_span("llm_planning") as span:
                    span.set_attribute("model", "claude-haiku-4-5")
                    span.set_attribute("agent_id", str(self._agent_id))
                    
                    plan, ab_version = await self.plan(task, context)
                    
                    span.set_attribute("plan_steps", len(plan))
                    if ab_version:
                        span.set_attribute("ab_version", ab_version)
                    self._tracer.record_metric("plan_steps", len(plan))
                    
                    # Store plan in working memory
                    if self._memory:
                        self._memory.store("plan", plan, level="working")
                
                logger.info(
                    "llm_plan_received",
                    agent_id=str(self._agent_id),
                    steps=len(plan),
                    ab_version=ab_version,
                )

                if not plan:
                    # Record A/B test failure if applicable
                    if self._ab_tester and ab_version:
                        self._ab_tester.record_result(
                            prompt_name="agent_planner",
                            version=ab_version,
                            trace_id=trace_id,
                            success=False,
                            duration=time.time() - start_time,
                            cost=0.0
                        )
                    
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
                        
                        # Store result in working memory
                        if self._memory and result.success:
                            self._memory.store(f"step_{i}_result", result.output, level="working")
                        
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
                
                # Store final output in memory hierarchy
                if self._memory:
                    # Working memory - for immediate use
                    self._memory.store("final_output", final_output, level="working")
                    
                    # Session memory - for conversation continuity
                    self._memory.store(f"task_{context.trace_id}", {
                        "task": task,
                        "output": final_output,
                        "success": success,
                        "timestamp": time.time()
                    }, level="session")
                    
                    # Long-term memory - store successful patterns
                    if success:
                        self._memory.store_fact(
                            f"Successfully completed: {task}",
                            confidence=0.9,
                            source="execution"
                        )
                
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

        # Record A/B test result if applicable
        if self._ab_tester and ab_version:
            self._ab_tester.record_result(
                prompt_name="agent_planner",
                version=ab_version,
                trace_id=trace_id,
                success=success,
                duration=duration,
                cost=0.0
            )
            logger.info("ab_test_result_recorded", version=ab_version, success=success)

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
            ab_version=ab_version,
            memory_summary=self._memory.get_summary() if self._memory else {},
        )

        return result

    async def plan(self, task: str, context: AgentContext) -> tuple[List[Dict[str, Any]], Optional[int]]:
        """
        Create execution plan using LLM.
        
        Returns:
            (plan, ab_version) - ab_version is set if A/B test is active
        """
        # Get available tools from MCP
        tools = await self._mcp.list_tools()
        
        # Use LLM planner (returns plan and A/B version if applicable)
        plan, ab_version = await self._planner.create_plan(task, tools)
        
        return plan, ab_version

    async def reset(self) -> None:
        """Reset agent state and clear working memory"""
        self._iteration_count = 0
        if self._memory:
            self._memory.clear_working()
        logger.info("smart_agent_reset", agent_id=str(self._agent_id))

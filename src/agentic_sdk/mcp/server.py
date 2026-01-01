"""
MCP (Model Context Protocol) Server Implementation.

The control plane for all agent operations.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from structlog import get_logger

from agentic_sdk.core.interfaces.tool import ITool, ToolExecutionContext, ToolExecutionResult

logger = get_logger(__name__)


class MCPServerConfig(BaseModel):
    """Configuration for MCP server."""
    server_id: str = Field(default_factory=lambda: str(uuid4()))
    host: str = "0.0.0.0"
    port: int = 8000
    max_concurrent_executions: int = 100
    default_timeout_seconds: int = 300
    enable_audit_logging: bool = True
    enable_rate_limiting: bool = True
    enable_caching: bool = True
    metadata: Dict[str, Any] = {}


class ToolRegistration(BaseModel):
    """Tool registration record."""
    tool_id: UUID = Field(default_factory=uuid4)
    tool_name: str
    tool_version: str
    registered_at: float = Field(default_factory=time.time)
    last_health_check: Optional[float] = None
    health_status: str = "unknown"
    invocation_count: int = 0
    error_count: int = 0
    metadata: Dict[str, Any] = {}


class MCPServer:
    """
    MCP Server - Control plane for agent operations.
    
    All tool executions flow through this server.
    """

    def __init__(self, config: Optional[MCPServerConfig] = None):
        self.config = config or MCPServerConfig()
        self._tool_registry: Dict[str, ToolRegistration] = {}
        self._tools: Dict[str, ITool] = {}
        self._running = False
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent_executions)

        logger.info(
            "mcp_server_initialized",
            server_id=self.config.server_id,
            max_concurrent=self.config.max_concurrent_executions,
        )

    async def start(self) -> None:
        """Start MCP server."""
        if self._running:
            logger.warning("mcp_server_already_running", server_id=self.config.server_id)
            return

        self._running = True
        logger.info("mcp_server_started", server_id=self.config.server_id)
        asyncio.create_task(self._health_check_loop())

    async def stop(self) -> None:
        """Stop MCP server and cleanup."""
        if not self._running:
            return

        self._running = False
        for tool_name in list(self._tools.keys()):
            await self.unregister_tool(tool_name)

        logger.info("mcp_server_stopped", server_id=self.config.server_id)

    async def register_tool(self, tool: ITool) -> ToolRegistration:
        """Register a tool with the MCP server."""
        schema = tool.schema
        tool_key = f"{schema.name}:{schema.version}"

        if tool_key in self._tools:
            raise ValueError(f"Tool {tool_key} is already registered")

        deps = tool.get_dependencies()
        logger.info(
            "tool_registration_started",
            tool=schema.name,
            version=schema.version,
            dependencies=deps,
        )

        try:
            is_healthy = await asyncio.wait_for(tool.health_check(), timeout=5.0)
            if not is_healthy:
                raise RuntimeError(f"Tool {tool_key} failed health check")
        except asyncio.TimeoutError:
            raise RuntimeError(f"Tool {tool_key} health check timed out")

        registration = ToolRegistration(
            tool_name=schema.name,
            tool_version=schema.version,
            health_status="healthy",
            last_health_check=time.time(),
        )

        self._tool_registry[tool_key] = registration
        self._tools[tool_key] = tool

        logger.info(
            "tool_registered",
            tool=schema.name,
            version=schema.version,
            tool_id=str(registration.tool_id),
        )

        return registration

    async def unregister_tool(self, tool_name: str, tool_version: str = "latest") -> None:
        """Unregister a tool from the MCP server."""
        if tool_version == "latest":
            matching_keys = [k for k in self._tools.keys() if k.startswith(f"{tool_name}:")]
            if not matching_keys:
                return
            tool_key = sorted(matching_keys)[-1]
        else:
            tool_key = f"{tool_name}:{tool_version}"

        if tool_key not in self._tools:
            logger.warning("tool_not_found_for_unregister", tool=tool_key)
            return

        del self._tools[tool_key]
        del self._tool_registry[tool_key]
        logger.info("tool_unregistered", tool=tool_key)

    async def list_tools(
        self, category: Optional[str] = None, tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """List available tools with optional filtering."""
        results = []

        for tool in self._tools.values():
            schema = tool.schema

            if category and schema.category != category:
                continue

            if tags and not any(tag in schema.tags for tag in tags):
                continue

            results.append({
                "name": schema.name,
                "version": schema.version,
                "description": schema.description,
                "category": schema.category,
                "tags": schema.tags,
            })

        return results

    async def invoke_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: ToolExecutionContext,
        tool_version: str = "latest",
    ) -> ToolExecutionResult:
        """Invoke a tool through the MCP server."""
        if tool_version == "latest":
            matching_keys = [k for k in self._tools.keys() if k.startswith(f"{tool_name}:")]
            if not matching_keys:
                raise ValueError(f"Tool {tool_name} not found")
            tool_key = sorted(matching_keys)[-1]
        else:
            tool_key = f"{tool_name}:{tool_version}"

        if tool_key not in self._tools:
            raise ValueError(f"Tool {tool_key} not found")

        tool = self._tools[tool_key]
        registration = self._tool_registry[tool_key]
        start_time = time.time()

        try:
            async with self._semaphore:
                is_valid = await tool.validate_input(params)
                if not is_valid:
                    raise ValueError(f"Invalid parameters for tool {tool_key}")

                logger.info(
                    "tool_execution_started",
                    tool=tool_key,
                    execution_id=str(context.execution_id),
                )

                result = await asyncio.wait_for(
                    tool.execute(params, context),
                    timeout=tool.schema.timeout_seconds,
                )

                duration = time.time() - start_time
                result.duration_seconds = duration
                registration.invocation_count += 1

                logger.info(
                    "tool_execution_completed",
                    tool=tool_key,
                    execution_id=str(context.execution_id),
                    success=result.success,
                    duration=duration,
                )

                return result

        except asyncio.TimeoutError:
            registration.error_count += 1
            duration = time.time() - start_time

            logger.error(
                "tool_execution_timeout",
                tool=tool_key,
                execution_id=str(context.execution_id),
            )

            return ToolExecutionResult(
                tool_name=tool_name,
                tool_version=tool.schema.version,
                execution_id=context.execution_id,
                success=False,
                output=None,
                duration_seconds=duration,
                error="Execution timed out",
            )

        except Exception as e:
            registration.error_count += 1
            duration = time.time() - start_time

            logger.error(
                "tool_execution_failed",
                tool=tool_key,
                execution_id=str(context.execution_id),
                error=str(e),
            )

            return ToolExecutionResult(
                tool_name=tool_name,
                tool_version=tool.schema.version,
                execution_id=context.execution_id,
                success=False,
                output=None,
                duration_seconds=duration,
                error=str(e),
            )

    async def _health_check_loop(self) -> None:
        """Periodic health check for all registered tools."""
        while self._running:
            await asyncio.sleep(60)

            for tool_key, tool in self._tools.items():
                try:
                    is_healthy = await asyncio.wait_for(tool.health_check(), timeout=5.0)
                    registration = self._tool_registry[tool_key]
                    registration.health_status = "healthy" if is_healthy else "unhealthy"
                    registration.last_health_check = time.time()

                    if not is_healthy:
                        logger.warning("tool_unhealthy", tool=tool_key)

                except Exception as e:
                    logger.error("tool_health_check_failed", tool=tool_key, error=str(e))
                    registration = self._tool_registry[tool_key]
                    registration.health_status = "error"

"""
HTTP Client Tool

Make HTTP requests (GET, POST, PUT, DELETE).
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
import httpx

from agentic_sdk.core.interfaces.tool import ITool, ToolSchema, ToolExecutionContext, ToolExecutionResult


class HttpRequestInput(BaseModel):
    """Input for HTTP request."""
    url: str = Field(..., description="URL to request")
    method: str = Field(default="GET", description="HTTP method: GET, POST, PUT, DELETE")
    headers: Optional[Dict[str, str]] = Field(default=None, description="HTTP headers")
    body: Optional[Dict[str, Any]] = Field(default=None, description="Request body (for POST/PUT)")
    timeout: int = Field(default=30, description="Request timeout in seconds")


class HttpResponseOutput(BaseModel):
    """Output for HTTP response."""
    status_code: int
    headers: Dict[str, str]
    body: str
    success: bool


class HttpTool(ITool):
    """Tool for making HTTP requests."""

    def __init__(self, allowed_domains: Optional[list[str]] = None):
        """
        Initialize HTTP tool.
        
        Args:
            allowed_domains: List of allowed domains (None = all allowed)
        """
        self._allowed_domains = allowed_domains

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="http_client",
            version="1.0.0",
            description="Make HTTP requests (GET, POST, PUT, DELETE)",
            input_schema=HttpRequestInput.model_json_schema(),
            output_schema=HttpResponseOutput.model_json_schema(),
            category="network",
            tags=["http", "api", "web"],
            requires_auth=False,
            rate_limit=60,
            timeout_seconds=60,
            idempotent=False,
        )

    async def validate_input(self, params: Dict[str, Any]) -> bool:
        try:
            HttpRequestInput(**params)
            return True
        except:
            return False

    async def execute(
        self, params: Dict[str, Any], context: ToolExecutionContext
    ) -> ToolExecutionResult:
        try:
            input_data = HttpRequestInput(**params)
            
            # Validate domain if restrictions exist
            if self._allowed_domains:
                from urllib.parse import urlparse
                domain = urlparse(input_data.url).netloc
                if not any(domain.endswith(allowed) for allowed in self._allowed_domains):
                    raise PermissionError(f"Domain {domain} not in allowed list")
            
            # Make request
            async with httpx.AsyncClient() as client:
                response = await client.request(
                    method=input_data.method,
                    url=input_data.url,
                    headers=input_data.headers,
                    json=input_data.body if input_data.body else None,
                    timeout=input_data.timeout,
                )
            
            output = HttpResponseOutput(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response.text,
                success=200 <= response.status_code < 300,
            )

            return ToolExecutionResult(
                tool_name=self.schema.name,
                tool_version=self.schema.version,
                execution_id=context.execution_id,
                success=True,
                output=output.model_dump(),
                duration_seconds=0.0,
            )

        except Exception as e:
            return ToolExecutionResult(
                tool_name=self.schema.name,
                tool_version=self.schema.version,
                execution_id=context.execution_id,
                success=False,
                output=None,
                duration_seconds=0.0,
                error=str(e),
            )

    async def health_check(self) -> bool:
        return True

    def get_dependencies(self) -> list[str]:
        return ["network"]

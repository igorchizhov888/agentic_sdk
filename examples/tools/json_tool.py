"""
JSON Processing Tool

Parse, query, and manipulate JSON data.
"""

import json
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from agentic_sdk.core.interfaces.tool import ITool, ToolSchema, ToolExecutionContext, ToolExecutionResult


class JsonInput(BaseModel):
    """Input for JSON operations."""
    operation: str = Field(..., description="Operation: parse, query, format, validate")
    data: str = Field(..., description="JSON string to process")
    query: Optional[str] = Field(default=None, description="JSONPath query (for query operation)")


class JsonOutput(BaseModel):
    """Output for JSON operations."""
    result: Any
    valid: bool
    message: str


class JsonTool(ITool):
    """Tool for JSON processing."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="json_processor",
            version="1.0.0",
            description="Parse, query, and manipulate JSON data",
            input_schema=JsonInput.model_json_schema(),
            output_schema=JsonOutput.model_json_schema(),
            category="data",
            tags=["json", "data", "parser"],
            requires_auth=False,
            rate_limit=1000,
            timeout_seconds=10,
            idempotent=True,
        )

    async def validate_input(self, params: Dict[str, Any]) -> bool:
        try:
            JsonInput(**params)
            return True
        except:
            return False

    async def execute(
        self, params: Dict[str, Any], context: ToolExecutionContext
    ) -> ToolExecutionResult:
        try:
            input_data = JsonInput(**params)
            
            if input_data.operation == "parse":
                result = await self._parse(input_data.data)
            elif input_data.operation == "format":
                result = await self._format(input_data.data)
            elif input_data.operation == "validate":
                result = await self._validate(input_data.data)
            else:
                raise ValueError(f"Unknown operation: {input_data.operation}")

            return ToolExecutionResult(
                tool_name=self.schema.name,
                tool_version=self.schema.version,
                execution_id=context.execution_id,
                success=result.valid,
                output=result.model_dump(),
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

    async def _parse(self, data: str) -> JsonOutput:
        """Parse JSON string."""
        try:
            parsed = json.loads(data)
            return JsonOutput(
                result=parsed,
                valid=True,
                message="JSON parsed successfully",
            )
        except json.JSONDecodeError as e:
            return JsonOutput(
                result=None,
                valid=False,
                message=f"Invalid JSON: {str(e)}",
            )

    async def _format(self, data: str) -> JsonOutput:
        """Format JSON with indentation."""
        try:
            parsed = json.loads(data)
            formatted = json.dumps(parsed, indent=2, sort_keys=True)
            return JsonOutput(
                result=formatted,
                valid=True,
                message="JSON formatted successfully",
            )
        except json.JSONDecodeError as e:
            return JsonOutput(
                result=None,
                valid=False,
                message=f"Invalid JSON: {str(e)}",
            )

    async def _validate(self, data: str) -> JsonOutput:
        """Validate JSON."""
        try:
            json.loads(data)
            return JsonOutput(
                result=True,
                valid=True,
                message="JSON is valid",
            )
        except json.JSONDecodeError as e:
            return JsonOutput(
                result=False,
                valid=False,
                message=f"Invalid JSON: {str(e)}",
            )

    async def health_check(self) -> bool:
        return True

    def get_dependencies(self) -> list[str]:
        return []

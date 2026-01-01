"""
Example: Simple Calculator Tool

Demonstrates how to implement a tool.
"""

from typing import Any, Dict
from pydantic import BaseModel, Field

from agentic_sdk.core.interfaces.tool import ITool, ToolSchema, ToolExecutionContext, ToolExecutionResult


class CalculatorInput(BaseModel):
    """Input schema for calculator tool."""
    operation: str = Field(..., description="Operation: add, subtract, multiply, divide")
    a: float = Field(..., description="First number")
    b: float = Field(..., description="Second number")


class CalculatorOutput(BaseModel):
    """Output schema for calculator tool."""
    result: float = Field(..., description="Calculation result")


class CalculatorTool(ITool):
    """Tool for basic arithmetic operations."""

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="calculator",
            version="1.0.0",
            description="Perform basic arithmetic operations",
            input_schema=CalculatorInput.model_json_schema(),
            output_schema=CalculatorOutput.model_json_schema(),
            category="math",
            tags=["calculator", "arithmetic"],
            requires_auth=False,
            rate_limit=1000,
            timeout_seconds=5,
            idempotent=True,
        )

    async def validate_input(self, params: Dict[str, Any]) -> bool:
        try:
            CalculatorInput(**params)
            return True
        except:
            return False

    async def execute(
        self, params: Dict[str, Any], context: ToolExecutionContext
    ) -> ToolExecutionResult:
        try:
            input_data = CalculatorInput(**params)
            
            if input_data.operation == "add":
                result = input_data.a + input_data.b
            elif input_data.operation == "subtract":
                result = input_data.a - input_data.b
            elif input_data.operation == "multiply":
                result = input_data.a * input_data.b
            elif input_data.operation == "divide":
                if input_data.b == 0:
                    raise ValueError("Division by zero")
                result = input_data.a / input_data.b
            else:
                raise ValueError(f"Unknown operation: {input_data.operation}")

            output = CalculatorOutput(result=result)

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
        return []

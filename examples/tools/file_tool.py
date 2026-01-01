"""
File Reader/Writer Tool

Provides file system operations for agents.
"""

import aiofiles
from pathlib import Path
from typing import Any, Dict
from pydantic import BaseModel, Field

from agentic_sdk.core.interfaces.tool import ITool, ToolSchema, ToolExecutionContext, ToolExecutionResult


class FileReadInput(BaseModel):
    """Input for file read operation."""
    file_path: str = Field(..., description="Path to file to read")
    encoding: str = Field(default="utf-8", description="File encoding")
    max_size_bytes: int = Field(default=10_000_000, description="Max file size")


class FileWriteInput(BaseModel):
    """Input for file write operation."""
    file_path: str = Field(..., description="Path to file to write")
    content: str = Field(..., description="Content to write")
    encoding: str = Field(default="utf-8", description="File encoding")
    append: bool = Field(default=False, description="Append instead of overwrite")


class FileOutput(BaseModel):
    """Output for file operations."""
    success: bool
    message: str
    content: str = ""
    size_bytes: int = 0


class FileReaderWriterTool(ITool):
    """Tool for reading and writing files."""

    def __init__(self, allowed_directories: list[str] = None):
        """
        Initialize file tool.
        
        Args:
            allowed_directories: List of allowed paths for security.
                               If None, allows all paths (use with caution).
        """
        self._allowed_dirs = allowed_directories or []

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="file_tool",
            version="1.0.0",
            description="Read and write text files with security controls",
            input_schema={
                "oneOf": [
                    FileReadInput.model_json_schema(),
                    FileWriteInput.model_json_schema(),
                ]
            },
            output_schema=FileOutput.model_json_schema(),
            category="filesystem",
            tags=["file", "io", "read", "write"],
            requires_auth=True,
            rate_limit=100,
            timeout_seconds=30,
            idempotent=False,
        )

    def _validate_path(self, file_path: str) -> Path:
        """Validate path is in allowed directories."""
        path = Path(file_path).resolve()
        
        if self._allowed_dirs:
            allowed = any(
                str(path).startswith(str(Path(allowed_dir).resolve()))
                for allowed_dir in self._allowed_dirs
            )
            if not allowed:
                raise PermissionError(
                    f"Access denied: {path} not in allowed directories"
                )
        
        return path

    async def validate_input(self, params: Dict[str, Any]) -> bool:
        try:
            # Try to parse as either read or write input
            if "content" in params:
                FileWriteInput(**params)
            else:
                FileReadInput(**params)
            return True
        except:
            return False

    async def execute(
        self, params: Dict[str, Any], context: ToolExecutionContext
    ) -> ToolExecutionResult:
        try:
            # Determine operation type
            if "content" in params:
                result = await self._write_file(params)
            else:
                result = await self._read_file(params)

            return ToolExecutionResult(
                tool_name=self.schema.name,
                tool_version=self.schema.version,
                execution_id=context.execution_id,
                success=result.success,
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

    async def _read_file(self, params: Dict[str, Any]) -> FileOutput:
        """Read a file."""
        input_data = FileReadInput(**params)
        file_path = self._validate_path(input_data.file_path)

        if not file_path.exists():
            return FileOutput(
                success=False,
                message=f"File not found: {file_path}",
            )

        file_size = file_path.stat().st_size
        if file_size > input_data.max_size_bytes:
            return FileOutput(
                success=False,
                message=f"File too large: {file_size} bytes (max: {input_data.max_size_bytes})",
            )

        async with aiofiles.open(file_path, "r", encoding=input_data.encoding) as f:
            content = await f.read()

        return FileOutput(
            success=True,
            message=f"Successfully read {file_size} bytes",
            content=content,
            size_bytes=file_size,
        )

    async def _write_file(self, params: Dict[str, Any]) -> FileOutput:
        """Write to a file."""
        input_data = FileWriteInput(**params)
        file_path = self._validate_path(input_data.file_path)

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        mode = "a" if input_data.append else "w"
        async with aiofiles.open(file_path, mode, encoding=input_data.encoding) as f:
            await f.write(input_data.content)

        size_bytes = len(input_data.content.encode(input_data.encoding))
        action = "Appended" if input_data.append else "Wrote"

        return FileOutput(
            success=True,
            message=f"{action} {size_bytes} bytes to {file_path}",
            size_bytes=size_bytes,
        )

    async def health_check(self) -> bool:
        """Check if filesystem is accessible."""
        try:
            import tempfile
            temp_dir = Path(tempfile.gettempdir())
            return temp_dir.exists() and temp_dir.is_dir()
        except:
            return False

    def get_dependencies(self) -> list[str]:
        return ["filesystem"]

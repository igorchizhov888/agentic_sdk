# Agentic SDK

Enterprise-grade SDK for building AI agents with MCP (Model Context Protocol) control plane and production-ready features.

## Features

### Core Framework
- **MCP Control Plane**: Governance and observability for all tool executions
- **Type-safe Tools**: Pydantic schemas with validation
- **Smart Agent**: LLM-powered planning with Claude Haiku 4.5
- **Basic Agent**: Keyword-based planning for simple tasks
- **Framework-independent**: Works with any AI framework
- **Async/await**: Throughout the codebase
- **Built-in Monitoring**: Health checks and structured logging

### Built-in Tools (4)
- **calculator**: Basic arithmetic operations
- **file_tool**: Read/write text files with security controls
- **http_client**: HTTP requests (GET, POST, PUT, DELETE)
- **json_processor**: Parse and manipulate JSON data

### Enterprise Features (Added January 2026)

#### 1. Prompt Management
Database-backed prompt versioning with zero-downtime deployment.
```bash
# Create new prompt version
agentic-sdk prompts create agent_planner "template..." --created-by gary

# Deploy instantly
agentic-sdk prompts activate agent_planner 3

# Rollback if needed
agentic-sdk prompts rollback agent_planner
```

**Benefits:**
- Change agent behavior without code deployment
- A/B test different prompts
- Instant rollback on issues
- Full version history

#### 2. Evaluation Framework
Automated testing with performance tracking.
```python
from agentic_sdk.eval import AgentEvaluator, TestCase

test_cases = [
    TestCase(
        id="test_1",
        task="Add 10 and 5",
        validator=lambda r: "15" in r.output
    )
]

evaluator = AgentEvaluator()
results = await evaluator.run_eval_suite(agent, test_cases, prompt_version=3)
```

**Benefits:**
- Data-driven deployment decisions
- Compare prompt versions objectively
- Track quality over time
- Prevent regressions

#### 3. Tool Registry
Auto-discovery with per-agent permissions (RBAC).
```bash
# Discover tools automatically
agentic-sdk registry discover

# Grant specific permissions
agentic-sdk registry grant my-agent calculator

# List available tools
agentic-sdk registry list --category math
```

**Benefits:**
- Add tools without code changes
- Control which agents use which tools
- Organize by category
- Dynamic loading at runtime

#### 4. Observability
Distributed tracing with full execution visibility.
```bash
# View recent traces
agentic-sdk traces list

# Show detailed trace
agentic-sdk traces show <trace-id>

# Get statistics
agentic-sdk traces stats
```

**Benefits:**
- Debug failures quickly
- Track performance metrics
- Identify bottlenecks
- Monitor costs

## Installation
```bash
# Clone repository
git clone https://github.com/igorchizhov888/agentic_sdk.git
cd agentic_sdk

# Install dependencies
pip install -e . --break-system-packages

# Set API key (for SmartAgent)
export ANTHROPIC_API_KEY="your-key-here"
```

## Quick Start

### Create a Tool
```python
from agentic_sdk.core.interfaces.tool import ITool, ToolSchema

class MyTool(ITool):
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name="my_tool",
            version="1.0.0",
            description="My custom tool",
            input_schema={...},
            output_schema={...}
        )
    
    async def execute(self, params, context):
        # Your tool logic here
        return ToolExecutionResult(...)
```

### Use with MCP Server
```python
from agentic_sdk.mcp.server import MCPServer

mcp = MCPServer()
await mcp.start()
await mcp.register_tool(MyTool())

result = await mcp.invoke_tool("my_tool", params, context)
```

### Use with Smart Agent
```python
from agentic_sdk.runtime.smart_agent import SmartAgent
from agentic_sdk.core.interfaces.agent import AgentConfig

config = AgentConfig(
    name="my_agent",
    model="claude-haiku-4-5",
    system_prompt="You are helpful",
    max_iterations=5
)

agent = SmartAgent(config, mcp)
result = await agent.execute("Calculate 150 + 200 and divide by 2")
```

### With All Enterprise Features
```python
from agentic_sdk.registry import ToolRegistry
from agentic_sdk.observability import AgentTracer

# Auto-discover and register tools
registry = ToolRegistry()
registry.auto_discover("examples/tools")

# Create tracer for observability
tracer = AgentTracer()

# Create agent with full integration
agent = SmartAgent(
    config=config,
    mcp_server=mcp,
    tracer=tracer  # Automatic tracing
)

# Execute - automatically traced with dynamic prompts
result = await agent.execute(task)

# View execution trace
traces = tracer.query_traces(limit=1)
```

## CLI Commands

### Prompts
```bash
agentic-sdk prompts list-versions <name>     # List prompt versions
agentic-sdk prompts show <name> --version 3  # Show prompt content
agentic-sdk prompts activate <name> 3        # Deploy version
agentic-sdk prompts rollback <name>          # Rollback to previous
```

### Tool Registry
```bash
agentic-sdk registry discover                # Auto-discover tools
agentic-sdk registry list                    # List all tools
agentic-sdk registry grant <agent> <tool>    # Grant permission
agentic-sdk registry show-permissions <agent># View agent tools
```

### Traces
```bash
agentic-sdk traces list                      # Recent traces
agentic-sdk traces show <trace-id>           # Detailed trace
agentic-sdk traces stats                     # Statistics
```

### Agent
```bash
agentic-sdk agent run "Calculate 10 + 5"     # Run agent task
```

### Server
```bash
agentic-sdk server start                     # Start MCP server
```

## Architecture

All tool executions flow through the MCP server for validation, access control, audit logging, rate limiting, and health monitoring.
```
SmartAgent
  ├── PromptManager (dynamic prompts from database)
  ├── LLMPlanner (uses PromptManager)
  ├── MCP Server (tool execution control plane)
  │   └── ToolRegistry (dynamic tool loading)
  └── AgentTracer (distributed tracing)
```

## Examples

See examples directory:

- `calculator_tool.py` - Basic calculator
- `file_tool.py` - File I/O with security
- `http_tool.py` - HTTP client
- `json_tool.py` - JSON processing
- `test_mcp_verbose.py` - MCP server tests
- `evaluation_example.py` - Evaluation framework
- `integration_test.py` - All systems integrated

## Development

### Run Integration Test
```bash
python3 examples/integration_test.py
```

### Run Evaluation
```bash
python3 examples/evaluation_example.py
```

### Add New Tool
1. Create tool class implementing `ITool`
2. Place in `examples/tools/`
3. Run: `agentic-sdk registry discover`

## Documentation

- [Prompt Management](PROMPT_MANAGEMENT_SUMMARY.md)
- [Evaluation Framework](EVALUATION_FRAMEWORK_SUMMARY.md)
- [Tool Registry](TOOL_REGISTRY_SUMMARY.md)
- [Observability](OBSERVABILITY_SUMMARY.md)
- [Complete Summary](COMPLETE_SDK_SUMMARY.md)

- Tool execution: 1-10ms per call
- LLM planning: 0.8-1.5s per task

## License

Apache 2.0

## Author

Igor Chizhov

## Performance

Real-world results:

- Prompt v3: 100% pass rate, 0.812s avg (23% faster than v1)
- Tool execution: 1-10ms per call
- LLM planning: 0.8-1.5s per task
- **Prompt caching: 14.9x faster (0.189ms → 0.013ms on cache hits)**

### Caching

Built-in prompt caching provides significant performance improvements:
- First load: ~0.2ms (database query)
- Subsequent loads: ~0.01ms (in-memory lookup)
- TTL: 5 minutes (configurable)
- Thread-safe with automatic eviction

## License

Apache 2.0

## Author

Igor Chizhov

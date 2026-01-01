# Agentic SDK - Architecture

## High-Level Architecture
```
┌─────────────────────────────────────────────────────────┐
│                    Client Application                    │
│                 (Your Python Code)                       │
└─────────────────────────────────────────────────────────┘
                          │
                          ├─── Create Agent
                          ├─── Pass Task
                          └─── Get Result
                          │
┌─────────────────────────────────────────────────────────┐
│                    Agent Runtime                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ Planner  │→ │ Executor │→ │  Loop    │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
                          │
                          │ All tool calls
                          ↓
┌─────────────────────────────────────────────────────────┐
│                  MCP Control Plane                       │
│  ┌─────────────┐  ┌──────────┐  ┌──────────┐          │
│  │   Tool      │  │ Validate │  │  Audit   │          │
│  │  Registry   │  │  Access  │  │   Log    │          │
│  └─────────────┘  └──────────┘  └──────────┘          │
└─────────────────────────────────────────────────────────┘
                          │
                          │ Invoke
                          ↓
┌─────────────────────────────────────────────────────────┐
│                       Tools                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │ Calculator │  │ File Tool  │  │  HTTP Tool │       │
│  └────────────┘  └────────────┘  └────────────┘       │
└─────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Client Application
Your code that uses the SDK:
```python
agent = BasicAgent(mcp_server)
result = await agent.execute("Read data.txt and sum numbers")
```

### 2. Agent Runtime (TO BE BUILT - Phase 2)
The execution engine:
- **Planner**: Breaks task into steps
- **Executor**: Runs each step
- **Loop Controller**: Manages iterations

### 3. MCP Server (COMPLETE - Phase 1)
Control plane that enforces governance:
- Validates all tool calls
- Logs every execution
- Checks permissions
- Monitors health

### 4. Tools (PARTIAL - Phase 1)
Capabilities agents can use:
- Calculator (done)
- File Reader/Writer (building now)
- HTTP Client (future)
- Database (future)

## Data Flow Example

User task: "Read numbers.txt and calculate average"
```
Step 1: Client creates agent
┌─────────┐
│ Client  │ agent = BasicAgent(mcp)
└─────────┘

Step 2: Agent plans
┌─────────────┐
│   Runtime   │ plan = [
│   Planner   │   {tool: "file_tool", action: "read"},
└─────────────┘   {tool: "calculator", action: "divide"}
                ]

Step 3: Execute via MCP
┌─────────────┐
│ MCP Server  │ → Validate → Log → Execute
└─────────────┘
        ↓
┌─────────────┐
│  File Tool  │ → Returns: "10\n20\n30"
└─────────────┘

Step 4: Next step
┌─────────────┐
│ MCP Server  │ → Validate → Log → Execute
└─────────────┘
        ↓
┌─────────────┐
│ Calculator  │ → Returns: 20.0 (average)
└─────────────┘

Step 5: Return result
┌─────────────┐
│   Runtime   │ result = "Average is 20.0"
└─────────────┘
        ↓
┌─────────────┐
│   Client    │ print(result.output)
└─────────────┘
```

## Current vs Future State

### Phase 1 (DONE)
```
Client → [gap] → MCP Server → Tools
         (no runtime yet)
```

You can:
- Create tools
- Register with MCP
- Execute tools directly

You cannot:
- Have agent plan multi-step tasks
- Have agent loop automatically
- Have agent decide which tools to use

### Phase 2 (NEXT)
```
Client → Agent Runtime → MCP Server → Tools
         (fills the gap)
```

You will be able to:
- Give agent high-level tasks
- Agent plans steps automatically
- Agent uses multiple tools
- Agent loops until done

## File Structure
```
agentic_sdk/
├── src/agentic_sdk/
│   ├── core/
│   │   └── interfaces/
│   │       ├── agent.py         # IAgent interface
│   │       └── tool.py          # ITool interface
│   │
│   ├── mcp/
│   │   └── server.py            # MCP control plane
│   │
│   ├── runtime/                 # TO BUILD - Phase 2
│   │   ├── executor.py          # Executes agent plans
│   │   ├── planner.py           # Creates execution plans
│   │   └── basic_agent.py       # First agent implementation
│   │
│   └── adapters/                # Future - Phase 4
│       ├── langchain/
│       └── llamaindex/
│
└── examples/
    └── tools/
        ├── calculator_tool.py   # Done
        └── file_tool.py         # Building now
```

## Key Design Principles

1. **MCP is the Gatekeeper**
   - ALL tool executions go through MCP
   - No backdoor tool access
   - Ensures governance

2. **Separation of Concerns**
   - Tools = Capabilities
   - Runtime = Orchestration
   - MCP = Control & Audit

3. **Framework Independence**
   - Core SDK has no external framework dependencies
   - Can add LangChain/LlamaIndex via adapters later
   - You control the abstractions

4. **Type Safety**
   - Pydantic schemas everywhere
   - Validation at every boundary
   - Clear contracts

## Next Steps

To complete Phase 2, we need to build:

1. **basic_agent.py** - Simple agent implementation
2. **executor.py** - Tool execution logic
3. **planner.py** - Task planning logic (can be simple at first)

This will connect: Client → Runtime → MCP → Tools

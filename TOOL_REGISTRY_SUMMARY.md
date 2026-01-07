# Tool Registry - Complete

## What We Built

### 1. Core Components
- ToolMetadata - Stores tool information (name, version, category, tags)
- ToolRegistryStorage - SQLite database for tools and permissions
- ToolRegistry - Main API for tool management
- CLI commands for registry operations

### 2. Features Implemented

Auto-Discovery
- Scans directories for ITool implementations
- Automatically registers tools in database
- Extracts metadata from tool schemas

Permission System
- Per-agent tool access control
- Grant/revoke permissions
- Default: all tools available unless restricted

Dynamic Loading
- Load tools by name at runtime
- Tools cached after first load
- No hardcoded tool imports needed

Category Filtering
- Filter tools by category (math, network, data, filesystem)
- Helps organize large tool collections

### 3. Current Tools Registered

calculator (v1.0.0)
- Category: math
- Operations: add, subtract, multiply, divide

file_tool (v1.0.0)
- Category: filesystem
- Read and write text files with security controls

http_client (v1.0.0)
- Category: network
- Make HTTP requests (GET, POST, PUT, DELETE)

json_processor (v1.0.0)
- Category: data
- Parse, query, and manipulate JSON data

## CLI Commands

Discover Tools
```bash
agentic-sdk registry discover --path examples/tools
```

List All Tools
```bash
agentic-sdk registry list
```

List by Category
```bash
agentic-sdk registry list --category math
```

Tool Details
```bash
agentic-sdk registry info calculator
```

Grant Permission
```bash
agentic-sdk registry grant agent-1 calculator
```

Revoke Permission
```bash
agentic-sdk registry revoke agent-1 calculator
```

Show Agent Permissions
```bash
agentic-sdk registry show-permissions agent-1
```

## Permission Examples

Example 1: Restricted Agent
```bash
# Give junior-agent only safe tools
agentic-sdk registry grant junior-agent calculator
agentic-sdk registry grant junior-agent json_processor

# Verify
agentic-sdk registry show-permissions junior-agent
# Output: calculator, json_processor
```

Example 2: Full Access Agent
```bash
# senior-agent has no restrictions
agentic-sdk registry show-permissions senior-agent
# Output: all 4 tools (default behavior)
```

Example 3: Revoke Access
```bash
# Remove dangerous tool from agent
agentic-sdk registry grant test-agent calculator
agentic-sdk registry grant test-agent file_tool
agentic-sdk registry revoke test-agent file_tool

# Verify
agentic-sdk registry show-permissions test-agent
# Output: calculator only
```

## Database Schema

Tools Table
```sql
CREATE TABLE tools (
    name TEXT UNIQUE NOT NULL,
    version TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    module_path TEXT NOT NULL,
    class_name TEXT NOT NULL,
    tags TEXT,
    enabled INTEGER DEFAULT 1,
    registered_at TEXT NOT NULL
);
```

Permissions Table
```sql
CREATE TABLE agent_tool_permissions (
    agent_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    allowed INTEGER DEFAULT 1,
    granted_at TEXT NOT NULL,
    UNIQUE(agent_id, tool_name)
);
```

## Programmatic Usage

Basic Usage
```python
from agentic_sdk.registry import ToolRegistry

registry = ToolRegistry()

# Discover tools
registry.auto_discover("examples/tools")

# List tools
tools = registry.list_tools()

# Load a tool
calc_tool = registry.load_tool("calculator")

# Check agent permissions
agent_tools = registry.get_tools_for_agent("my-agent")
```

With Permissions
```python
# Grant access
registry.storage.grant_tool_access("agent-1", "calculator")

# Revoke access
registry.storage.revoke_tool_access("agent-1", "file_tool")

# Check what agent can use
tools = registry.get_tools_for_agent("agent-1")
```

## Integration with Agent Runtime

Future enhancement - agents can query registry:
```python
class SmartAgent:
    def __init__(self, config, registry):
        self.registry = registry
        self.agent_id = config.agent_id
    
    async def get_available_tools(self):
        # Get only tools this agent can use
        tool_names = self.registry.get_tools_for_agent(self.agent_id)
        
        # Load them
        tools = []
        for name in tool_names:
            tool = self.registry.load_tool(name)
            tools.append(tool)
        
        return tools
```

## Benefits

1. Dynamic Tool Management
   - Add new tools without code changes
   - Just drop Python file in examples/tools
   - Run discovery command

2. Security
   - Control which agents use which tools
   - Prevent unauthorized tool access
   - Audit trail in database

3. Organization
   - Tools categorized by function
   - Searchable by tags
   - Version tracking

4. Scalability
   - Handles large tool libraries
   - Fast tool loading with caching
   - Database-backed for persistence

## Next Steps (Not Implemented)

1. Tool Dependencies
   - Automatically install required packages
   - Check dependencies before loading

2. Tool Versioning
   - Multiple versions of same tool
   - Gradual rollout of new versions

3. Usage Analytics
   - Track which tools are used most
   - Performance metrics per tool

4. Tool Marketplace
   - Share tools across teams
   - Import tools from registry

## Summary

Complete tool registry system with:
1. Auto-discovery from directories
2. Per-agent permission system
3. CLI commands for management
4. Dynamic tool loading
5. Category-based organization

All 4 existing tools registered and manageable via CLI or API.

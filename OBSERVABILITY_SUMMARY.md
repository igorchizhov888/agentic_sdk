# Observability System - Complete

## What We Built

### 1. Core Components
- SpanContext - Represents a timed operation within a trace
- TraceStorage - SQLite database for traces, spans, and metrics
- AgentTracer - Main API with context managers for tracing
- SmartAgent Integration - Full instrumentation of agent execution

### 2. Features Implemented

Distributed Tracing
- Trace entire agent execution from start to finish
- Hierarchical spans for sub-operations
- Unique trace IDs for correlation

Span Tracking
- LLM planning span with model and prompt version
- Tool execution spans with parameters and results
- Automatic timing and duration calculation

Metrics Collection
- Plan steps count
- Tool call count per execution
- Success/failure rates
- Iteration counts

Database Storage
- All traces persisted in SQLite
- Query by agent, time range, success status
- Full trace details with spans and metrics

### 3. Database Schema

Traces Table
```sql
CREATE TABLE traces (
    trace_id TEXT UNIQUE NOT NULL,
    agent_id TEXT NOT NULL,
    session_id TEXT,
    task TEXT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_seconds REAL,
    success INTEGER,
    error TEXT,
    metadata TEXT
);
```

Spans Table
```sql
CREATE TABLE spans (
    span_id TEXT UNIQUE NOT NULL,
    trace_id TEXT NOT NULL,
    parent_span_id TEXT,
    name TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    duration_seconds REAL,
    attributes TEXT
);
```

Metrics Table
```sql
CREATE TABLE metrics (
    trace_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    timestamp TEXT NOT NULL,
    tags TEXT
);
```

## Usage Examples

Basic Tracing
```python
from agentic_sdk.observability import AgentTracer

tracer = AgentTracer()

# Trace agent execution
with tracer.trace_execution(
    agent_id="agent-1",
    session_id="session-123",
    task="Calculate something"
) as trace_id:
    # Agent work happens here
    pass
```

With Spans
```python
# Inside trace_execution context
with tracer.start_span("llm_planning") as span:
    span.set_attribute("model", "claude-haiku-4-5")
    span.set_attribute("prompt_version", 3)
    # Do LLM planning
    
with tracer.start_span("tool_execution") as span:
    span.set_attribute("tool", "calculator")
    # Execute tool
```

Recording Metrics
```python
# Inside trace_execution context
tracer.record_metric("llm_tokens", 150, {"type": "input"})
tracer.record_metric("tool_calls", 1, {"tool": "calculator"})
tracer.record_metric("total_cost", 0.0008, {"currency": "USD"})
```

Querying Traces
```python
# Get recent traces
traces = tracer.query_traces(agent_id="agent-1", limit=10)

# Get trace details
details = tracer.get_trace_details(trace_id)
print(f"Trace: {details['trace']}")
print(f"Spans: {details['spans']}")
print(f"Metrics: {details['metrics']}")
```

## SmartAgent Integration

SmartAgent now includes automatic tracing:
```python
from agentic_sdk.runtime.smart_agent import SmartAgent
from agentic_sdk.observability import AgentTracer

tracer = AgentTracer()

agent = SmartAgent(
    config=config,
    mcp_server=mcp,
    api_key=api_key,
    tracer=tracer  # Pass tracer
)

# Execute - automatically traced
result = await agent.execute("Add 100 and 50")

# Query what happened
traces = tracer.query_traces(limit=1)
```

## What Gets Traced

Every SmartAgent Execution
1. Overall trace with task, duration, success
2. LLM planning span with model and steps
3. Tool execution spans (one per tool call)
4. Metrics: plan_steps, tool_calls, iterations, success

Example Trace Output
```
Trace: trace-abc123
  Agent: agent-1
  Task: Add 150 and 200, then divide by 2
  Duration: 1.234s
  Success: True
  
  Spans:
    - llm_planning: 0.856s
        model: claude-haiku-4-5
        plan_steps: 2
    - tool_execution: 0.123s
        tool: calculator
        step: 1
    - tool_execution: 0.089s
        tool: calculator
        step: 2
  
  Metrics:
    - plan_steps: 2
    - tool_calls: 2
    - iterations: 2
    - success: 1.0
```

## Query Examples

Recent Traces
```bash
sqlite3 traces.db "SELECT trace_id, task, duration_seconds, success FROM traces ORDER BY start_time DESC LIMIT 5;"
```

Failed Executions
```bash
sqlite3 traces.db "SELECT trace_id, task, error FROM traces WHERE success = 0 ORDER BY start_time DESC;"
```

Slowest Executions
```bash
sqlite3 traces.db "SELECT trace_id, task, duration_seconds FROM traces ORDER BY duration_seconds DESC LIMIT 10;"
```

Agent Performance
```bash
sqlite3 traces.db "SELECT agent_id, AVG(duration_seconds), COUNT(*) FROM traces GROUP BY agent_id;"
```

## Production Benefits

1. Debugging
   - See exact execution flow
   - Identify which step failed
   - Track error rates

2. Performance Monitoring
   - Identify slow operations
   - Compare LLM vs tool time
   - Track improvements over time

3. Cost Tracking
   - Record token usage
   - Track API costs
   - Optimize expensive operations

4. Usage Analytics
   - Most common tasks
   - Popular tools
   - Success patterns


## CLI Commands (Added)

The observability system includes comprehensive CLI commands for trace analysis:

### List Traces
```bash
agentic-sdk traces list                      # Recent traces
agentic-sdk traces list --agent-id <id>      # Filter by agent
agentic-sdk traces list --success            # Only successful
agentic-sdk traces list --failed             # Only failed
agentic-sdk traces list --limit 20           # Limit results
```

### Show Trace Details
```bash
agentic-sdk traces show <trace-id>
```

Shows complete trace information:
- Task and duration
- Success/failure status
- All spans with timing
- Collected metrics
- Metadata

### Statistics
```bash
agentic-sdk traces stats                     # Overall statistics
agentic-sdk traces stats --agent-id <id>     # Agent-specific
```

Displays:
- Total executions
- Success rate
- Average/min/max duration
- Most common tasks

### Example Output
```
Trace Statistics (last 9 traces):
  Total: 9
  Successful: 9 (100.0%)
  
Duration:
  Average: 0.404s
  Min: 0.100s
  Max: 1.509s
  
Most Common Tasks:
  2x: Calculate 100 + 50 and multiply by 2
  2x: Task 1
```

## Next Steps (Not Implemented)

1. Real-time Dashboard
   - Live trace visualization
   - Performance graphs
   - Alert on failures

2. OpenTelemetry Integration
   - Export to Jaeger/Zipkin
   - Integrate with APM tools
   - Distributed tracing across services

3. Automatic Anomaly Detection
   - Detect unusual patterns
   - Alert on performance degradation
   - Identify failing agents

4. Cost Attribution
   - Track costs per user/team
   - Budget alerts
   - Optimization recommendations

## Summary

Complete observability system with:
1. Distributed tracing for agent executions
2. Span tracking for sub-operations
3. Metrics collection and storage
4. SQLite persistence for all traces
5. SmartAgent fully instrumented
6. Query API for analysis

All agent executions now automatically traced and stored in traces.db for analysis and debugging.

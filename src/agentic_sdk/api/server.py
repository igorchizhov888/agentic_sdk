"""FastAPI server for AgenticSDK Dashboard"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import sys
sys.path.insert(0, '.')

from agentic_sdk.observability import AgentTracer
from agentic_sdk.prompts import PromptManager, PromptStorage
from agentic_sdk.registry import ToolRegistry

app = FastAPI(title="AgenticSDK Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "ok", "service": "AgenticSDK Dashboard API"}

@app.get("/api/traces")
def list_traces(agent_id: Optional[str] = None, limit: int = 100):
    tracer = AgentTracer()
    traces = tracer.query_traces(agent_id=agent_id, limit=limit)
    return {"traces": traces, "count": len(traces)}

@app.get("/api/traces/stats")
def trace_stats(agent_id: Optional[str] = None):
    tracer = AgentTracer()
    traces = tracer.query_traces(agent_id=agent_id, limit=1000)
    total = len(traces)
    successful = sum(1 for t in traces if t.get('success'))
    failed = total - successful
    durations = [t.get('duration_seconds', 0) for t in traces]
    avg_duration = sum(durations) / len(durations) if durations else 0
    return {
        "total_traces": total,
        "successful": successful,
        "failed": failed,
        "success_rate": successful / total if total > 0 else 0,
        "avg_duration": avg_duration
    }

@app.get("/api/traces/{trace_id}")
def get_trace(trace_id: str):
    tracer = AgentTracer()
    details = tracer.get_trace_details(trace_id)
    if not details:
        raise HTTPException(status_code=404, detail="Trace not found")
    return details

@app.get("/api/prompts")
def list_prompts():
    storage = PromptStorage()
    cursor = storage.conn.execute("SELECT DISTINCT name FROM prompts ORDER BY name")
    prompts = [row['name'] for row in cursor.fetchall()]
    return {"prompts": prompts}

@app.get("/api/prompts/{name}/versions")
def list_prompt_versions(name: str):
    storage = PromptStorage()
    manager = PromptManager(storage)
    versions = manager.list_versions(name)
    return {"versions": versions}

@app.get("/api/prompts/{name}/active")
def get_active_prompt(name: str):
    storage = PromptStorage()
    manager = PromptManager(storage)
    try:
        template, _ = manager.get_prompt(name)
        version = storage.get_active_version(name)
        return {"name": name, "version": version, "template": template}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/api/prompts/{name}/activate/{version}")
def activate_prompt(name: str, version: int):
    storage = PromptStorage()
    manager = PromptManager(storage)
    try:
        manager.activate_version(name, version)
        return {"status": "activated", "name": name, "version": version}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/tools")
def list_tools():
    registry = ToolRegistry()
    tools = registry.list_tools()
    return {"tools": [
        {
            "name": t.name,
            "version": t.version,
            "category": t.category,
            "description": t.description,
            "tags": t.tags
        } for t in tools
    ]}

@app.get("/api/tools/{tool_name}")
def get_tool(tool_name: str):
    registry = ToolRegistry()
    metadata = registry.storage.get_tool(tool_name)
    if not metadata:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {
        "name": metadata.name,
        "version": metadata.version,
        "category": metadata.category,
        "description": metadata.description,
        "tags": metadata.tags,
        "enabled": metadata.enabled
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

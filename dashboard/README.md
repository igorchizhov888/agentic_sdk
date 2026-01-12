# AgenticSDK Dashboard

Web UI for monitoring and managing AgenticSDK agents.

## Features

- Real-time trace monitoring
- Prompt version management
- Tool registry view
- Performance statistics

## Setup

Install dependencies:
```bash
npm install
```

## Running

Start API server (terminal 1):
```bash
cd ~/agentic_sdk
python3 src/agentic_sdk/api/server.py
```

Start dashboard (terminal 2):
```bash
cd ~/agentic_sdk/dashboard
npm start
```

Dashboard: http://localhost:3000
API: http://localhost:8000

## Architecture
```
React Dashboard (port 3000)
    |
    | API calls
    v
FastAPI Server (port 8000)
    |
    | queries
    v
SQLite Databases (traces.db, prompts.db, etc)
```

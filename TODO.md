# Agentic SDK - TODO List

## Phase 2: Runtime & Orchestration (Next)

### High Priority

- [ ] Implement basic Agent class
  - [ ] Task planning logic
  - [ ] Tool selection
  - [ ] Execution loop
  - [ ] Context management

- [ ] Add context persistence
  - [ ] SQLite backend
  - [ ] Save/load conversation state
  - [ ] Query context by session

- [ ] Create more tools
  - [ ] File reader/writer
  - [ ] HTTP client (GET/POST)
  - [ ] JSON parser
  - [ ] CSV processor

### Medium Priority

- [ ] CLI commands
  - [ ] `agentic-sdk server start`
  - [ ] `agentic-sdk tool list`
  - [ ] `agentic-sdk tool register <path>`

- [ ] Add retry logic
  - [ ] Exponential backoff
  - [ ] Configurable retry policy
  - [ ] Per-tool retry settings

- [ ] Caching layer
  - [ ] In-memory cache
  - [ ] Optional Redis support
  - [ ] Cache invalidation

### Low Priority

- [ ] Web UI for MCP server
  - [ ] Tool registry viewer
  - [ ] Execution logs
  - [ ] Health dashboard

- [ ] Framework adapters
  - [ ] LangChain adapter
  - [ ] LlamaIndex adapter

- [ ] Documentation
  - [ ] Architecture diagrams
  - [ ] API reference
  - [ ] Tutorial videos

## Phase 3: Production Features

- [ ] Authentication (JWT)
- [ ] Authorization (RBAC)
- [ ] Rate limiting
- [ ] Metrics export (Prometheus)
- [ ] Distributed tracing (OpenTelemetry)

## Ideas for Future

- [ ] Multi-agent workflows
- [ ] Plugin marketplace
- [ ] Visual workflow builder
- [ ] Agent templates library

---

Pick one task and start building!

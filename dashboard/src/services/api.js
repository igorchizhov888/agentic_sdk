/**
 * API Client for AgenticSDK Dashboard
 */

const API_BASE = 'http://localhost:8000';

export const api = {
  // Traces
  async getTraces(agentId = null, limit = 100) {
    const params = new URLSearchParams();
    if (agentId) params.append('agent_id', agentId);
    params.append('limit', limit);
    
    const response = await fetch(`${API_BASE}/api/traces?${params}`);
    return response.json();
  },

  async getTrace(traceId) {
    const response = await fetch(`${API_BASE}/api/traces/${traceId}`);
    return response.json();
  },

  async getTraceStats(agentId = null) {
    const params = agentId ? `?agent_id=${agentId}` : '';
    const response = await fetch(`${API_BASE}/api/traces/stats${params}`);
    return response.json();
  },

  // Prompts
  async getPrompts() {
    const response = await fetch(`${API_BASE}/api/prompts`);
    return response.json();
  },

  async getPromptVersions(name) {
    const response = await fetch(`${API_BASE}/api/prompts/${name}/versions`);
    return response.json();
  },

  async getActivePrompt(name) {
    const response = await fetch(`${API_BASE}/api/prompts/${name}/active`);
    return response.json();
  },

  async activatePrompt(name, version) {
    const response = await fetch(
      `${API_BASE}/api/prompts/${name}/activate/${version}`,
      { method: 'POST' }
    );
    return response.json();
  },

  // Tools
  async getTools() {
    const response = await fetch(`${API_BASE}/api/tools`);
    return response.json();
  },

  async getTool(name) {
    const response = await fetch(`${API_BASE}/api/tools/${name}`);
    return response.json();
  }
};

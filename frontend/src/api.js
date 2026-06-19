const API_BASE = import.meta.env.VITE_API_URL || "/api";

async function request(method, path, body) {
  const url = `${API_BASE}${path}`;
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body !== undefined) {
    opts.body = JSON.stringify(body);
  }
  const resp = await fetch(url, opts);
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`${resp.status} ${resp.statusText}: ${text}`);
  }
  return resp.json();
}

export const api = {
  health: () => request("GET", "/health"),
  listAgents: () => request("GET", "/agents"),
  listRuns: (limit = 25) => request("GET", `/runs?limit=${limit}`),
  getRun: (id) => request("GET", `/runs/${id}`),
  startRun: (payload) => request("POST", "/runs", payload),
  listJobs: () => request("GET", "/jobs"),
  getJob: (id) => request("GET", `/jobs/${id}`),
  listIssues: (status) => request("GET", status ? `/issues?status=${status}` : "/issues"),
  listDatasets: () => request("GET", "/datasets"),
  generateScenarios: (agentType, count = 20) =>
    request("GET", `/scenarios/generate?agent_type=${agentType}&count=${count}`),
  getCoverage: (agentId) => request("GET", `/coverage/${agentId}`),
  getReport: (runId) => request("GET", `/reports/${runId}`),
  evaluateRun: (runId, evaluators) =>
    request("POST", `/runs/${runId}/evaluate`, { evaluators }),
  gateRun: (runId, gates) => request("POST", `/runs/${runId}/gate`, { gates }),
};

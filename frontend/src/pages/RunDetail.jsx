import { useEffect } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api";
import { useApi } from "../hooks/useApi.js";
import { useToast } from "../components/Toast.jsx";
import { Card, CardHeader, CardTitle } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { StatusBadge } from "../components/ui/Badge";
import { Skeleton } from "../components/ui/Skeleton";
import { ErrorState } from "../components/ui/EmptyState";
import { LiveRegion } from "../components/ui/LiveRegion";
import { RichText } from "../components/RichText.jsx";
import { formatDate, formatNumber } from "../lib/utils.js";

export default function RunDetail() {
  const { id } = useParams();
  const toast = useToast();
  const {
    data: run,
    loading,
    error,
    run: fetchRun,
  } = useApi(api.getRun);

  useEffect(() => {
    fetchRun(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleEvaluate() {
    try {
      const d = await api.evaluateRun(id);
      toast(
        `Evaluated: ${d.eval_report.passed ? "passed" : "failed"}`,
        d.eval_report.passed ? "success" : "error",
      );
      await fetchRun(id);
    } catch (e) {
      toast(e.message, "error");
    }
  }

  async function handleGate() {
    try {
      const d = await api.gateRun(id);
      toast(
        `Gate ${d.gate.passed ? "passed" : "failed"}`,
        d.gate.passed ? "success" : "error",
      );
    } catch (e) {
      toast(e.message, "error");
    }
  }

  if (loading) {
    return (
      <section className="dashboard-section container">
        <Skeleton lines={8} />
      </section>
    );
  }

  if (error) {
    return (
      <section className="dashboard-section container">
        <ErrorState message={error.message} retry={() => fetchRun(id)} />
      </section>
    );
  }

  if (!run) {
    return (
      <section className="dashboard-section container">
        <p className="text-secondary">Run not found.</p>
      </section>
    );
  }

  const evalBlock = run.evaluation || {};
  const findings = evalBlock.eval_report?.findings || [];

  return (
    <section id="main" className="dashboard-section container">
      <LiveRegion message={`Run ${run.id} loaded`} />
      <header className="dashboard-header">
        <h1 className="text-2xl font-light text-primary">Run {run.id}</h1>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={handleEvaluate}>Evaluate</Button>
          <Button onClick={handleGate}>Release Gate</Button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Overview</CardTitle>
          </CardHeader>
          <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-2 text-sm">
            <dt className="text-secondary">Agent</dt>
            <dd className="text-primary">{run.agent_id}</dd>
            <dt className="text-secondary">Score</dt>
            <dd className="text-primary tabular-nums">{run.score}%</dd>
            <dt className="text-secondary">Status</dt>
            <dd><StatusBadge status={run.status} /></dd>
            <dt className="text-secondary">Scenarios</dt>
            <dd className="text-primary tabular-nums">{formatNumber(run.passed_count)}/{formatNumber(run.scenario_count)} passed</dd>
            <dt className="text-secondary">Confidence</dt>
            <dd className="text-primary tabular-nums">{Math.round((run.confidence || 0) * 100)}%</dd>
            <dt className="text-secondary">Created</dt>
            <dd className="text-primary tabular-nums">{formatDate(run.created_at)}</dd>
          </dl>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Evaluator Findings</CardTitle>
          </CardHeader>
          {findings.length === 0 && (
            <p className="text-secondary">No findings yet. Click Evaluate to run evaluators.</p>
          )}
          <ul className="space-y-2">
            {findings.slice(0, 20).map((f) => (
              <li key={f.signature} className="text-sm">
                <div className="flex items-center gap-2">
                  <StatusBadge status={f.passed ? "passed" : "failed"}>
                    {f.passed ? "passed" : "failed"}
                  </StatusBadge>
                  <span className="font-medium text-primary">{f.name}</span>
                </div>
                <RichText text={f.message} className="mt-1 text-secondary text-pretty" />
              </li>
            ))}
          </ul>
        </Card>
      </div>

      {evalBlock.gate && (
        <Card className="t-panel is-visible">
          <CardHeader>
            <CardTitle>Release Gate</CardTitle>
          </CardHeader>
          <div className="flex items-center gap-3">
            <StatusBadge status={evalBlock.gate.passed ? "passed" : "failed"}>
              {evalBlock.gate.passed ? "PASSED" : "FAILED"}
            </StatusBadge>
          </div>
          {evalBlock.gate.failures?.length > 0 && (
            <ul className="mt-3 list-disc pl-5 text-sm text-secondary">
              {evalBlock.gate.failures.map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ul>
          )}
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Scenario Results</CardTitle>
        </CardHeader>
        <div className="overflow-x-auto">
          <table className="data-table">
            <caption className="sr-only">Scenario results for run {run.id}</caption>
            <thead>
              <tr>
                <th scope="col">Name</th>
                <th scope="col">Type</th>
                <th scope="col">Score</th>
                <th scope="col">Risk</th>
                <th scope="col">Tools</th>
                <th scope="col">Latency</th>
              </tr>
            </thead>
            <tbody>
              {(run.results || []).slice(0, 100).map((r) => (
                <tr key={r.scenario_name} className="hover:bg-surface">
                  <td className="max-w-xs truncate">{r.scenario_name}</td>
                  <td>{r.scenario_type}</td>
                  <td className="tabular-nums">{r.score}%</td>
                  <td><StatusBadge status={r.risk_level} /></td>
                  <td className="max-w-xs truncate">{r.called_tools.join(", ") || "—"}</td>
                  <td className="tabular-nums">{r.latency_ms}ms</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </section>
  );
}

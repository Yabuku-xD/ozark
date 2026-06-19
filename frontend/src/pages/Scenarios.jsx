import { useEffect, useId, useState } from "react";
import { api } from "../api";
import { useApi } from "../hooks/useApi.js";
import { useToast } from "../components/Toast.jsx";
import { Card } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { StatusBadge } from "../components/ui/Badge";
import { Select, Input } from "../components/ui/Form";
import { TableSkeleton } from "../components/ui/Skeleton";
import { ErrorState } from "../components/ui/EmptyState";

const AGENT_TYPES = [
  "customer_support",
  "code_assistant",
  "data_analyst",
  "ops_controller",
  "healthcare_agent",
  "finance_agent",
  "recruiting_agent",
  "sales_agent",
];

export default function Scenarios() {
  const [agentType, setAgentType] = useState("customer_support");
  const [count, setCount] = useState(20);
  const [seed, setSeed] = useState(0);
  const toast = useToast();
  const { data, loading, error, run } = useApi(api.generateScenarios);
  const typeId = useId();
  const countId = useId();

  useEffect(() => {
    run(agentType, count);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleGenerate() {
    run(agentType, Number(count)).catch((e) => toast(e.message, "error"));
  }

  return (
    <section className="dashboard-section container">
      <header className="dashboard-header">
        <h1 className="text-2xl font-light text-primary">Scenarios</h1>
      </header>

      <Card className="flex flex-wrap items-end gap-4">
        <Select
          id={typeId}
          label="Agent type"
          value={agentType}
          onChange={(e) => {
            setAgentType(e.target.value);
            setSeed((s) => s + 1);
          }}
        >
          {AGENT_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </Select>

        <Input
          id={countId}
          label="Count"
          type="number"
          min={1}
          max={100}
          value={count}
          onChange={(e) => setCount(e.target.value)}
          className="w-24"
        />

        <Button onClick={handleGenerate} disabled={loading}>
          {loading ? "Generating…" : "Generate"}
        </Button>
      </Card>

      {error && <ErrorState message={error.message} retry={handleGenerate} />}

      {loading && !data && (
        <Card>
          <TableSkeleton rows={5} columns={5} />
        </Card>
      )}

      {data && (
        <Card className="t-panel is-visible">
          <p className="text-secondary">
            Generated <span className="tabular-nums">{data.count}</span>{" "}
            scenarios for <strong className="text-primary">{agentType}</strong>.
          </p>
          <div className="overflow-x-auto mt-3">
            <table className="data-table">
              <caption className="sr-only">Generated scenarios for {agentType}</caption>
              <thead>
                <tr>
                  <th scope="col">Prompt</th>
                  <th scope="col">Type</th>
                  <th scope="col">Difficulty</th>
                  <th scope="col">Risk</th>
                  <th scope="col">Expected tools</th>
                </tr>
              </thead>
              <tbody>
                {data.scenarios.slice(0, 100).map((s) => (
                  <tr key={`${s.name}-${seed}`} className="hover:bg-surface">
                    <td className="max-w-md truncate">{s.user_prompt?.slice(0, 80) || s.name}</td>
                    <td>{s.scenario_type}</td>
                    <td>{s.difficulty}</td>
                    <td><StatusBadge status={s.risk_level || "medium"} /></td>
                    <td className="max-w-xs truncate">{(s.expected_tools || []).join(", ") || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </section>
  );
}

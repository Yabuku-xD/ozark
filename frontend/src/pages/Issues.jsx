import { useEffect, useId, useState } from "react";
import { api } from "../api";
import { useApi } from "../hooks/useApi.js";
import { Card } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/Badge";
import { Select } from "../components/ui/Form";
import { TableSkeleton } from "../components/ui/Skeleton";
import { ErrorState, EmptyState } from "../components/ui/EmptyState";
import { formatDate } from "../lib/utils.js";

const COLUMNS = 5;

export default function Issues() {
  const [status, setStatus] = useState("");
  const { data, loading, error, run } = useApi(api.listIssues);
  const labelId = useId();

  useEffect(() => {
    run(status || undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  const issues = data?.issues || [];

  return (
    <section className="dashboard-section container">
      <header className="dashboard-header">
        <h1 className="text-2xl font-light text-primary">Issues</h1>
        <Select
          id={labelId}
          label="Filter"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="w-40"
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="closed">Closed</option>
        </Select>
      </header>

      {error && <ErrorState message={error.message} retry={() => run(status || undefined)} />}

      {loading && !data && (
        <Card>
          <TableSkeleton rows={5} columns={COLUMNS} />
        </Card>
      )}

      {!loading && issues.length === 0 && (
        <Card>
          <EmptyState
            title="No issues"
            description="Evaluator failures are grouped into issues here after a run is evaluated."
          />
        </Card>
      )}

      {issues.length > 0 && (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="data-table">
              <caption className="sr-only">Issues filtered by {status || "all statuses"}</caption>
              <thead>
                <tr>
                  <th scope="col">Title</th>
                  <th scope="col">Severity</th>
                  <th scope="col">Status</th>
                  <th scope="col">Occurrences</th>
                  <th scope="col">Last seen</th>
                </tr>
              </thead>
              <tbody>
                {issues.map((issue) => (
                  <tr key={issue.id} className="hover:bg-surface">
                    <td className="font-medium">{issue.title}</td>
                    <td><StatusBadge status={issue.severity} /></td>
                    <td>{issue.status}</td>
                    <td className="tabular-nums">{issue.occurrence_count}</td>
                    <td className="tabular-nums">{formatDate(issue.updated_at)}</td>
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

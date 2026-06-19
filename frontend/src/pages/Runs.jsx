import { Link } from "react-router-dom";
import { api } from "../api";
import { useApi } from "../hooks/useApi.js";
import { Card } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/Badge";
import { TableSkeleton } from "../components/ui/Skeleton";
import { ErrorState, EmptyState } from "../components/ui/EmptyState";
import { formatDate } from "../lib/utils.js";
import { useEffect } from "react";

const COLUMNS = 6;

export default function Runs() {
  const { data, loading, error, run } = useApi(api.listRuns);

  useEffect(() => {
    run(50);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <section className="dashboard-section container">
      <header className="dashboard-header">
        <h1 className="text-2xl font-light text-primary">Runs</h1>
      </header>

      {error && <ErrorState message={error.message} retry={() => run(50)} />}

      {loading && !data && (
        <Card>
          <TableSkeleton rows={6} columns={COLUMNS} />
        </Card>
      )}

      {!loading && data?.runs?.length === 0 && (
        <Card>
          <EmptyState
            title="No runs yet"
            description="Start a simulation run from the CLI or API to see results here."
          />
        </Card>
      )}

      {data?.runs?.length > 0 && (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="data-table">
              <caption className="sr-only">Simulation runs</caption>
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Agent</th>
                  <th scope="col">Score</th>
                  <th scope="col">Status</th>
                  <th scope="col">Summary</th>
                  <th scope="col">Created</th>
                </tr>
              </thead>
              <tbody>
                {data.runs.map((run) => (
                  <tr key={run.id} className="hover:bg-surface">
                    <td>
                      <Link to={`/runs/${run.id}`} className="font-medium">
                        {run.id}
                      </Link>
                    </td>
                    <td className="tabular-nums">{run.agent_id}</td>
                    <td className="tabular-nums">{run.score}%</td>
                    <td>
                      <StatusBadge status={run.status} />
                    </td>
                    <td className="max-w-xs truncate">{run.summary}</td>
                    <td className="tabular-nums">{formatDate(run.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {data.next_cursor && (
            <p className="mt-3 text-sm text-secondary">More runs available via cursor pagination.</p>
          )}
        </Card>
      )}
    </section>
  );
}

import { useEffect } from "react";
import { api } from "../api";
import { useApi } from "../hooks/useApi.js";
import { Card, CardHeader, CardTitle } from "../components/ui/Card";
import { TableSkeleton } from "../components/ui/Skeleton";
import { ErrorState, EmptyState } from "../components/ui/EmptyState";

const COLUMNS = 3;

export default function Agents() {
  const { data, loading, error, run } = useApi(api.listAgents);

  useEffect(() => {
    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const agents = data?.agents || [];

  return (
    <section className="dashboard-section container">
      <header className="dashboard-header">
        <h1 className="text-2xl font-light text-primary">Agents</h1>
      </header>

      {error && <ErrorState message={error.message} retry={() => run()} />}

      {loading && !data && (
        <Card>
          <TableSkeleton rows={5} columns={COLUMNS} />
        </Card>
      )}

      {!loading && agents.length === 0 && (
        <Card>
          <EmptyState
            title="No agents"
            description="Agents registered in Ozark will appear here."
          />
        </Card>
      )}

      {agents.length > 0 && (
        <Card className="overflow-hidden">
          <CardHeader>
            <CardTitle>Registered agents</CardTitle>
          </CardHeader>
          <div className="overflow-x-auto">
            <table className="data-table">
              <caption className="sr-only">Registered agents</caption>
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Name</th>
                  <th scope="col">Description</th>
                </tr>
              </thead>
              <tbody>
                {agents.map((a) => (
                  <tr key={a.id} className="hover:bg-surface">
                    <td className="font-medium">{a.id}</td>
                    <td>{a.name}</td>
                    <td className="max-w-md truncate">{a.description}</td>
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

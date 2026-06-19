import { useEffect } from "react";
import { api } from "../api";
import { useApi } from "../hooks/useApi.js";
import { Card } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/Badge";
import { TableSkeleton } from "../components/ui/Skeleton";
import { ErrorState, EmptyState } from "../components/ui/EmptyState";
import { LiveRegion } from "../components/ui/LiveRegion";
import { formatDate } from "../lib/utils.js";

const COLUMNS = 6;

export default function Jobs() {
  const { data, loading, error, run } = useApi(api.listJobs);

  useEffect(() => {
    run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const jobs = data?.jobs || [];
  const pendingCount = jobs.filter((j) => j.status === "pending" || j.status === "running").length;

  return (
    <section className="dashboard-section container">
      <LiveRegion message={pendingCount > 0 ? `${pendingCount} active jobs` : ""} />
      <header className="dashboard-header">
        <h1 className="text-2xl font-light text-primary">Jobs</h1>
        {pendingCount > 0 && (
          <StatusBadge status="running">{pendingCount} active</StatusBadge>
        )}
      </header>

      {error && <ErrorState message={error.message} retry={() => run()} />}

      {loading && !data && (
        <Card>
          <TableSkeleton rows={5} columns={COLUMNS} />
        </Card>
      )}

      {!loading && jobs.length === 0 && (
        <Card>
          <EmptyState
            title="No jobs"
            description="Background jobs will appear here when async runs are enqueued."
          />
        </Card>
      )}

      {jobs.length > 0 && (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="data-table">
              <caption className="sr-only">Background jobs</caption>
              <thead>
                <tr>
                  <th scope="col">ID</th>
                  <th scope="col">Kind</th>
                  <th scope="col">Status</th>
                  <th scope="col">Progress</th>
                  <th scope="col">Created</th>
                  <th scope="col">Finished</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-surface">
                    <td className="font-medium">{job.id}</td>
                    <td>{job.kind}</td>
                    <td><StatusBadge status={job.status} /></td>
                    <td className="tabular-nums">{job.total > 0 ? `${job.progress}/${job.total}` : "—"}</td>
                    <td className="tabular-nums">{formatDate(job.created_at)}</td>
                    <td className="tabular-nums">{job.finished_at ? formatDate(job.finished_at) : "—"}</td>
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

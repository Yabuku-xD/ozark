import { useEffect, useRef } from "react";
import { Routes, Route, NavLink } from "react-router-dom";
import { ToastProvider } from "../components/Toast.jsx";
import { api } from "../api";
import { useApi } from "../hooks/useApi.js";
import { Card, CardHeader, CardTitle } from "../components/ui/Card";
import { StatusBadge } from "../components/ui/Badge";
import { Link } from "react-router-dom";
import Runs from "./Runs";
import RunDetail from "./RunDetail";
import Jobs from "./Jobs";
import Issues from "./Issues";
import Scenarios from "./Scenarios";
import Agents from "./Agents";
import NotFound from "./NotFound";

const links = [
  { to: "/", label: "Overview", end: true },
  { to: "/runs", label: "Runs" },
  { to: "/jobs", label: "Jobs" },
  { to: "/issues", label: "Issues" },
  { to: "/scenarios", label: "Scenarios" },
  { to: "/agents", label: "Agents" },
];

function useStagger() {
  const ref = useRef(null);
  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    const items = root.querySelectorAll(".stagger-item");
    items.forEach((el) => el.classList.remove("is-visible"));
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.05, rootMargin: "0px 0px -4% 0px" },
    );
    items.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);
  return ref;
}

function Overview() {
  const { data: runsData, run: fetchRuns } = useApi(api.listRuns);
  const { data: issuesData, run: fetchIssues } = useApi(api.listIssues);
  const { data: agentsData, run: fetchAgents } = useApi(api.listAgents);
  const ref = useStagger();

  useEffect(() => {
    fetchRuns(10);
    fetchIssues();
    fetchAgents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runs = runsData?.runs || [];
  const issues = issuesData?.issues || [];
  const agents = agentsData?.agents || [];
  const openIssues = issues.filter((i) => i.status === "open");
  const avgScore = runs.length > 0
    ? Math.round(runs.reduce((sum, r) => sum + r.score, 0) / runs.length)
    : 0;

  return (
    <section className="dashboard-section container" ref={ref}>
      <div className="dashboard-header">
        <h1 className="text-2xl font-light text-primary">Ozark Dashboard</h1>
      </div>

      <div className="stats-grid">
        <div className="stat-card stagger-item">
          <div className="stat-label">Total Runs</div>
          <div className="stat-value">{runs.length}</div>
          <div className="stat-meta">Recent {runs.length} shown</div>
        </div>
        <div className="stat-card stagger-item">
          <div className="stat-label">Avg Score</div>
          <div className="stat-value">{avgScore}%</div>
          <div className="stat-meta">Across recent runs</div>
        </div>
        <div className="stat-card stagger-item">
          <div className="stat-label">Open Issues</div>
          <div className="stat-value">{openIssues.length}</div>
          <div className="stat-meta">{issues.length} total grouped</div>
        </div>
        <div className="stat-card stagger-item">
          <div className="stat-label">Registered Agents</div>
          <div className="stat-value">{agents.length}</div>
          <div className="stat-meta">Available for testing</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="stagger-item">
          <CardHeader>
            <CardTitle>Recent Runs</CardTitle>
          </CardHeader>
          {runs.length === 0 ? (
            <p className="text-secondary text-sm">
              No runs yet. Start one from the CLI:{" "}
              <code className="code-block">python ozark.py run --agent sample-support-agent --count 50</code>
            </p>
          ) : (
            <table className="data-table">
              <caption className="sr-only">Recent runs</caption>
              <thead>
                <tr>
                  <th scope="col">Run</th>
                  <th scope="col">Score</th>
                  <th scope="col">Status</th>
                </tr>
              </thead>
              <tbody>
                {runs.slice(0, 5).map((run) => (
                  <tr key={run.id}>
                    <td>
                      <Link to={`/runs/${run.id}`} className="text-accent font-medium">
                        {run.id}
                      </Link>
                    </td>
                    <td className="tabular-nums">{run.score}%</td>
                    <td><StatusBadge status={run.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        <Card className="stagger-item">
          <CardHeader>
            <CardTitle>Open Issues</CardTitle>
          </CardHeader>
          {openIssues.length === 0 ? (
            <p className="text-secondary text-sm">
              No open issues. Evaluator failures will be grouped here after runs are evaluated.
            </p>
          ) : (
            <ul className="finding-list">
              {openIssues.slice(0, 5).map((issue) => (
                <li key={issue.id} className="finding-item">
                  <div className="flex items-center gap-2">
                    <StatusBadge status={issue.severity} />
                    <span className="font-medium text-primary">{issue.title}</span>
                  </div>
                  <span className="text-tertiary text-xs tabular-nums">
                    {issue.occurrence_count} occurrences
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </section>
  );
}

function DashboardNavbar() {
  return (
    <header className="app-navbar">
      <a href="#main" className="skip-link">Skip to content</a>
      <div className="app-navbar-inner">
        <NavLink to="/" className="app-brand">
          <img src="/assets/favicon.svg" alt="" width="24" height="24" />
          <span>Ozark</span>
        </NavLink>
        <nav className="app-nav" aria-label="Dashboard">
          {links.map((l) => (
            <NavLink
              key={l.to}
              to={l.to}
              end={l.end}
              className={({ isActive }) =>
                isActive ? "app-nav-link active" : "app-nav-link"
              }
            >
              {l.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
}

export default function Dashboard() {
  return (
    <ToastProvider>
      <div className="app-shell">
        <DashboardNavbar />
        <main id="main" className="app-main">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/runs" element={<Runs />} />
            <Route path="/runs/:id" element={<RunDetail />} />
            <Route path="/jobs" element={<Jobs />} />
            <Route path="/issues" element={<Issues />} />
            <Route path="/scenarios" element={<Scenarios />} />
            <Route path="/agents" element={<Agents />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
      </div>
    </ToastProvider>
  );
}

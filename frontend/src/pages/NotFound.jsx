export default function NotFound() {
  return (
    <section className="dashboard-section container">
      <div className="empty-state">
        <div className="empty-state-icon" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M3 6h18M3 12h18M3 18h18" />
          </svg>
        </div>
        <h3>Page not found</h3>
        <p>The page you're looking for doesn't exist.</p>
      </div>
    </section>
  );
}

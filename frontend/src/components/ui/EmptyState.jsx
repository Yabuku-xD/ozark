import { Button } from "./Button";

export function EmptyState({ title, description, action, onAction }) {
  return (
    <div className="empty-state" role="status">
      <div className="empty-state-icon" aria-hidden="true">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
      </div>
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      {action && onAction && (
        <Button variant="secondary" size="sm" onClick={onAction}>{action}</Button>
      )}
    </div>
  );
}

export function ErrorState({ message, retry }) {
  return (
    <div className="error-state" role="alert">
      <div className="error-state-icon" aria-hidden="true">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <h3>Something went wrong</h3>
      <p>{message}</p>
      {retry && (
        <Button variant="secondary" size="sm" onClick={retry}>Retry</Button>
      )}
    </div>
  );
}

export function Skeleton({ className, lines = 1 }) {
  return (
    <div aria-busy="true" aria-label="Loading" className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className={`skeleton-row${className ? ` ${className}` : ""}`} />
      ))}
    </div>
  );
}

export function TableSkeleton({ rows = 5, columns = 4 }) {
  return (
    <div aria-busy="true" aria-label="Loading table" className="space-y-2">
      <div className="grid gap-2 pb-2 border-b" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: columns }).map((_, i) => (
          <div key={i} className="skeleton-row" />
        ))}
      </div>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="grid gap-2 py-2 border-b" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
          {Array.from({ length: columns }).map((_, c) => (
            <div key={c} className="skeleton-row" />
          ))}
        </div>
      ))}
    </div>
  );
}

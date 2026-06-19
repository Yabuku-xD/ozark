export function Card({ children, className, as: Component = "section" }) {
  return (
    <Component className={`surface rounded-lg p-4${className ? ` ${className}` : ""}`}>
      {children}
    </Component>
  );
}

export function CardHeader({ children }) {
  return <header className="mb-3">{children}</header>;
}

export function CardTitle({ children }) {
  return <h2 className="text-base font-semibold text-primary">{children}</h2>;
}

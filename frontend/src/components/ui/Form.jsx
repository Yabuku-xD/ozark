export function Input({ label, id, className, ...props }) {
  return (
    <div className="form-field">
      {label && <label htmlFor={id} className="form-label">{label}</label>}
      <input
        id={id}
        className={`input${className ? ` ${className}` : ""}`}
        {...props}
      />
    </div>
  );
}

export function Select({ label, id, className, children, ...props }) {
  return (
    <div className="form-field">
      {label && <label htmlFor={id} className="form-label">{label}</label>}
      <select
        id={id}
        className={`select${className ? ` ${className}` : ""}`}
        {...props}
      >
        {children}
      </select>
    </div>
  );
}

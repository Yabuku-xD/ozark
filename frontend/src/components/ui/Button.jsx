export function Button({
  children,
  variant = "primary",
  size = "md",
  className,
  disabled,
  ...props
}) {
  const variantClass = {
    primary: "btn-primary",
    secondary: "btn-secondary",
    ghost: "btn-ghost",
    danger: "btn-danger",
  };
  const sizeClass = {
    sm: "btn-sm",
    md: "",
    lg: "btn-lg",
  };
  return (
    <button
      className={`btn ${variantClass[variant] || "btn-primary"} ${sizeClass[size] || ""}${className ? ` ${className}` : ""}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}

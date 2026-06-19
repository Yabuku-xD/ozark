import { statusTone } from "../../lib/utils.js";

const toneClass = {
  success: "badge-passed",
  warning: "badge-needs_review",
  danger: "badge-failed",
  info: "badge-info",
  neutral: "badge-neutral",
};

export function Badge({ children, tone, className }) {
  const t = tone || "neutral";
  return (
    <span className={`badge ${toneClass[t] || "badge-neutral"}${className ? ` ${className}` : ""}`}>
      {children}
    </span>
  );
}

export function StatusBadge({ status, children }) {
  return <Badge tone={statusTone(status)}>{children || status}</Badge>;
}

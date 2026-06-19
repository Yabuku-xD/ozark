export function cn(...classes) {
  return classes.filter(Boolean).join(" ");
}

export function statusTone(status) {
  if (status === "passed" || status === "succeeded") return "success";
  if (status === "blocked" || status === "failed") return "danger";
  if (status === "needs_review" || status === "running" || status === "pending") return "warning";
  if (["critical", "high", "safety-critical"].includes(status)) return "danger";
  if (["medium"].includes(status)) return "warning";
  if (["low"].includes(status)) return "info";
  return "neutral";
}

export function formatDate(iso) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "short",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

export function formatNumber(n) {
  if (n === undefined || n === null) return "—";
  return Number(n).toLocaleString();
}

import { useEffect, useRef } from "react";

/** ARIA live region for accessibility announcements. */
export function LiveRegion({ message, assertive = false }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!message || !ref.current) return;
    ref.current.textContent = message;
    const id = setTimeout(() => {
      if (ref.current) ref.current.textContent = "";
    }, 1000);
    return () => clearTimeout(id);
  }, [message]);

  return (
    <div
      ref={ref}
      role="status"
      aria-live={assertive ? "assertive" : "polite"}
      aria-atomic="true"
      className="sr-only"
    />
  );
}

export function VisuallyHidden({ children }) {
  return <span className="sr-only">{children}</span>;
}

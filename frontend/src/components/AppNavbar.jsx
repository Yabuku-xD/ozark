import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useLocation } from "react-router-dom";

const links = [
  { to: "/", label: "Home", end: true },
  { to: "/runs", label: "Runs" },
  { to: "/jobs", label: "Jobs" },
  { to: "/issues", label: "Issues" },
  { to: "/scenarios", label: "Scenarios" },
  { to: "/agents", label: "Agents" },
];

export default function AppNavbar() {
  const [open, setOpen] = useState(false);
  const menuRef = useRef(null);
  const location = useLocation();
  const initialPath = useRef(location.pathname);

  useEffect(() => {
    if (location.pathname !== initialPath.current) {
      setOpen(false);
    }
  }, [location.pathname]);

  useEffect(() => {
    if (!open) return;
    function onKey(e) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <header className="app-navbar">
      <a href="#main" className="skip-link">Skip to content</a>
      <div className="app-navbar-inner">
        <Link to="/" className="app-brand">
          <img src="/assets/favicon.svg" alt="" width="24" height="24" />
          <span>Ozark</span>
        </Link>

        <nav className="app-nav hidden md:flex" aria-label="Primary">
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

        <button
          type="button"
          aria-expanded={open}
          aria-controls="mobile-nav"
          aria-label={open ? "Close navigation" : "Open navigation"}
          className="md:hidden inline-flex h-10 w-10 items-center justify-center rounded-md border border-line"
          onClick={() => setOpen((s) => !s)}
        >
          <MenuIcon open={open} />
        </button>
      </div>

      <div
        id="mobile-nav"
        ref={menuRef}
        className={`md:hidden surface border-b border-line t-dropdown ${open ? "is-open" : ""}`}
        aria-hidden={!open}
      >
        {links.map((l) => (
          <Link
            key={l.to}
            to={l.to}
            className="block px-4 py-3 text-sm text-primary hover:bg-surface"
            onClick={() => setOpen(false)}
          >
            {l.label}
          </Link>
        ))}
      </div>
    </header>
  );
}

function MenuIcon({ open }) {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" className="text-primary">
      {open ? (
        <g key="close" className="t-icon-swap">
          <line x1="4" y1="4" x2="16" y2="16" />
          <line x1="16" y1="4" x2="4" y2="16" />
        </g>
      ) : (
        <g key="open" className="t-icon-swap">
          <line x1="3" y1="6" x2="17" y2="6" />
          <line x1="3" y1="10" x2="17" y2="10" />
          <line x1="3" y1="14" x2="17" y2="14" />
        </g>
      )}
    </svg>
  );
}

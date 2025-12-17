import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import { Button } from "../components/ui/button";

const nav = [
  { to: "/", label: "Dashboard" },
  { to: "/devices", label: "Devices" },
  { to: "/schedules", label: "Schedules" },
  { to: "/history", label: "History" },
];

export function AppShell() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-full bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <Link to="/" className="text-sm font-semibold text-slate-900">
            Network Backup Manager
          </Link>
          <div className="flex items-center gap-3">
            <div className="text-xs text-slate-600">{user?.email}</div>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => void logout()}
            >
              Logout
            </Button>
          </div>
        </div>
      </header>

      <div className="mx-auto grid max-w-6xl grid-cols-1 gap-6 px-4 py-6 md:grid-cols-[200px_1fr]">
        <aside className="rounded-xl border border-slate-200 bg-white p-3">
          <nav className="flex flex-col gap-1">
            {nav.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                className={({ isActive }) =>
                  [
                    "rounded-md px-3 py-2 text-sm",
                    isActive
                      ? "bg-slate-900 text-white"
                      : "text-slate-700 hover:bg-slate-100",
                  ].join(" ")
                }
                end={n.to === "/"}
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        <main className="min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
}


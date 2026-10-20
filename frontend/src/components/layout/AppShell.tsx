import type { ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

const roleLabel: Record<string, string> = {
  parent: "Родитель",
  child: "Ребёнок",
  teen: "Подросток",
};

interface AppShellProps {
  children: ReactNode;
  navItems?: { to: string; label: string }[];
}

export default function AppShell({ children, navItems = [] }: AppShellProps) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate("/login", { replace: true });
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-logo">
          <span className="wave" aria-hidden="true" />
          Moby Family
        </div>
        <div className="app-header-right">
          {user && (
            <div className="app-header-user">
              <span className="name">{user.full_name}</span>
              <span className="role">{roleLabel[user.role] ?? user.role}</span>
            </div>
          )}
          <button type="button" className="btn btn-ghost btn-sm" onClick={handleLogout}>
            Выйти
          </button>
        </div>
      </header>
      <div className="app-body">
        {navItems.length > 0 && (
          <nav className="app-nav">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) => (isActive ? "active" : "")}
                end
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        )}
        {children}
      </div>
    </div>
  );
}

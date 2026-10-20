import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import type { Role } from "../../types";

interface ProtectedRouteProps {
  children: ReactNode;
  requireRole?: Role | Role[];
}

export default function ProtectedRoute({ children, requireRole }: ProtectedRouteProps) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="spinner-wrap">
        <div className="spinner" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requireRole) {
    const allowed = Array.isArray(requireRole) ? requireRole : [requireRole];
    if (!allowed.includes(user.role)) {
      const fallback = user.role === "parent" ? "/parent" : "/child";
      return <Navigate to={fallback} replace />;
    }
  }

  return <>{children}</>;
}

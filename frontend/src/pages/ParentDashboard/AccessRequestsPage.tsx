import { useEffect, useState } from "react";
import AppShell from "../../components/layout/AppShell";
import AccessRequestList from "../../components/access/AccessRequestList";
import { useAuth } from "../../context/AuthContext";
import * as accessApi from "../../api/accessRequests";
import type { AccessRequest } from "../../types";
import { PARENT_NAV } from "./nav";

export default function AccessRequestsPage() {
  const { user } = useAuth();
  const [requests, setRequests] = useState<AccessRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deciding, setDeciding] = useState<string | null>(null);

  useEffect(() => {
    if (!user?.family_id) return;
    let cancelled = false;
    accessApi
      .getAccessRequests(user.family_id)
      .then((data) => {
        if (!cancelled) setRequests(data);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Не удалось загрузить запросы");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user?.family_id]);

  const handleDecide = async (request: AccessRequest, decision: "approved" | "denied") => {
    setDeciding(request.id);
    setError(null);
    try {
      const updated = await accessApi.decideAccessRequest(request.id, decision);
      setRequests((prev) => prev.map((r) => (r.id === request.id ? updated : r)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось принять решение");
    } finally {
      setDeciding(null);
    }
  };

  return (
    <AppShell navItems={PARENT_NAV}>
      <h1 style={{ fontSize: 22 }}>Запросы доступа</h1>
      <div className="card">
        {loading ? (
          <div className="muted">Загрузка...</div>
        ) : (
          <AccessRequestList requests={requests} onDecide={handleDecide} deciding={deciding} />
        )}
        {error && <div className="alert alert-error">{error}</div>}
      </div>
    </AppShell>
  );
}

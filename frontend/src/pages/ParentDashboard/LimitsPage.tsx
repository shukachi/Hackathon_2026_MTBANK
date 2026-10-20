import { useEffect, useState } from "react";
import AppShell from "../../components/layout/AppShell";
import LimitEditor from "../../components/limits/LimitEditor";
import { useFamily } from "../../context/FamilyContext";
import * as limitsApi from "../../api/limits";
import type { Limit } from "../../types";
import { PARENT_NAV } from "./nav";

export default function LimitsPage() {
  const { children } = useFamily();
  const [childId, setChildId] = useState<string>(children[0]?.user.id ?? "");
  const [limits, setLimits] = useState<Limit[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (children.length > 0 && !childId) setChildId(children[0].user.id);
  }, [children, childId]);

  useEffect(() => {
    if (!childId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    limitsApi
      .getLimits(childId)
      .then((data) => {
        if (!cancelled) setLimits(data);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Не удалось загрузить лимиты");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [childId]);

  return (
    <AppShell navItems={PARENT_NAV}>
      <h1 style={{ fontSize: 22 }}>Лимиты трат</h1>

      {children.length === 0 ? (
        <div className="card empty-state">Сначала подключите ребёнка на странице «Обзор».</div>
      ) : (
        <div className="card stack">
          <div className="form-field" style={{ maxWidth: 320 }}>
            <label htmlFor="child-select">Ребёнок</label>
            <select id="child-select" value={childId} onChange={(e) => setChildId(e.target.value)}>
              {children.map((c) => (
                <option key={c.user.id} value={c.user.id}>
                  {c.user.full_name}
                </option>
              ))}
            </select>
          </div>

          {loading && <div className="muted">Загрузка лимитов...</div>}
          {error && <div className="alert alert-error">{error}</div>}
          {childId && !loading && (
            <LimitEditor
              childId={childId}
              limits={limits}
              onSaved={(limit) => setLimits((prev) => [...prev.filter((l) => l.category !== limit.category), limit])}
            />
          )}
        </div>
      )}
    </AppShell>
  );
}

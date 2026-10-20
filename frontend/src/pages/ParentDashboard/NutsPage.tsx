import { useEffect, useState } from "react";
import AppShell from "../../components/layout/AppShell";
import PointsWidget from "../../components/loyalty/PointsWidget";
import { useAuth } from "../../context/AuthContext";
import { useFamily } from "../../context/FamilyContext";
import * as loyaltyApi from "../../api/loyalty";
import type { Loyalty } from "../../types";
import { PARENT_NAV } from "./nav";

export default function NutsPage() {
  const { user } = useAuth();
  const { children } = useFamily();
  const [ownLoyalty, setOwnLoyalty] = useState<Loyalty | null>(null);
  const [childLoyalty, setChildLoyalty] = useState<Record<string, Loyalty>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    const requests: Promise<void>[] = [];

    // Свой счёт орешков родителя.
    requests.push(
      loyaltyApi
        .getLoyalty(user.id)
        .then((data) => {
          if (!cancelled) setOwnLoyalty(data);
        })
        .catch(() => {}),
    );

    // Счета орешков детей — родитель видит прогресс ребёнка.
    children.forEach((c) => {
      requests.push(
        loyaltyApi
          .getLoyalty(c.user.id)
          .then((data) => {
            if (!cancelled) setChildLoyalty((prev) => ({ ...prev, [c.user.id]: data }));
          })
          .catch(() => {}),
      );
    });

    Promise.all(requests)
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Не удалось загрузить орешки");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [user, children]);

  if (!user) return null;

  return (
    <AppShell navItems={PARENT_NAV}>
      <h1 style={{ fontSize: 22 }}>Орешки</h1>

      <div className="card">
        <div className="card-title">Мои орешки</div>
        {loading ? (
          <div className="muted">Загрузка...</div>
        ) : ownLoyalty ? (
          <PointsWidget loyalty={ownLoyalty} onConverted={setOwnLoyalty} />
        ) : (
          <div className="empty-state">Счёт орешков пока недоступен</div>
        )}
        {error && <div className="alert alert-error">{error}</div>}
      </div>

      <div className="card stack">
        <div className="card-title">Орешки детей</div>
        {children.length === 0 ? (
          <div className="empty-state">Сначала подключите ребёнка на странице «Обзор».</div>
        ) : (
          children.map((c) => {
            const loyalty = childLoyalty[c.user.id];
            return (
              <div key={c.user.id} className="stack" style={{ gap: 8, paddingBottom: 12, borderBottom: "1px solid var(--border)" }}>
                <div className="row-between">
                  <div style={{ fontWeight: 700 }}>{c.user.full_name}</div>
                  {loyalty ? (
                    <span className="badge badge-warning">
                      {loyalty.points} орешков · {loyalty.converted_byn.toFixed(2)} BYN
                    </span>
                  ) : (
                    <span className="muted">Загрузка...</span>
                  )}
                </div>
                {loyalty && loyalty.history.length > 0 && (
                  <div className="stack" style={{ gap: 4 }}>
                    {loyalty.history.slice(0, 3).map((entry, idx) => (
                      <div key={idx} className="row-between" style={{ fontSize: 13 }}>
                        <span className="muted">{entry.reason}</span>
                        <span
                          className="nut-delta"
                          style={{ fontWeight: 700, color: entry.delta >= 0 ? "var(--moby-green)" : "var(--moby-red)" }}
                        >
                          {entry.delta >= 0 ? "+" : ""}
                          {entry.delta} орешков
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      <div className="card">
        <div className="card-title">Как это работает</div>
        <div className="stack" style={{ gap: 8, fontSize: 14 }}>
          <div>
            <strong>10 орешков = 1 рубль.</strong> Орешки ребёнка и родителя копятся раздельно
            (как требует ТЗ), и каждый конвертирует их в рубли на свой счёт.
          </div>
          <div>
            <strong>Кешбэк 5%</strong> — еда, сладости, игрушки, образование, развлечения.
            Игры и подписки кешбэком не облагаются.
          </div>
          <div>
            <strong>Квесты</strong> — родитель задаёт квест и указывает награду орешками;
            ребёнок выполняет и получает орешки на свой счёт.
          </div>
        </div>
      </div>
    </AppShell>
  );
}

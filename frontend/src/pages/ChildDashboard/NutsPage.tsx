import { useEffect, useState } from "react";
import AppShell from "../../components/layout/AppShell";
import PointsWidget from "../../components/loyalty/PointsWidget";
import { useAuth } from "../../context/AuthContext";
import * as loyaltyApi from "../../api/loyalty";
import type { Loyalty } from "../../types";
import { childNav } from "./nav";

export default function NutsPage() {
  const { user } = useAuth();
  const [loyalty, setLoyalty] = useState<Loyalty | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    loyaltyApi
      .getLoyalty(user.id)
      .then((data) => {
        if (!cancelled) setLoyalty(data);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Не удалось загрузить орешки");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  if (!user) return null;

  return (
    <AppShell navItems={childNav(user.role)}>
      <h1 style={{ fontSize: 22 }}>Мои орешки</h1>

      <div className="card">
        {loading ? (
          <div className="muted">Загрузка...</div>
        ) : loyalty ? (
          <PointsWidget loyalty={loyalty} onConverted={setLoyalty} />
        ) : (
          <div className="empty-state">Счёт орешков пока недоступен</div>
        )}
        {error && <div className="alert alert-error">{error}</div>}
      </div>

      <div className="card">
        <div className="card-title">Как накопить орешки</div>
        <div className="stack" style={{ gap: 8, fontSize: 14 }}>
          <div>
            <strong>Кешбэк 5%</strong> — за покупки в семейных категориях: еда, сладости, игрушки,
            образование и развлечения. Игры и подписки кешбэком не облагаются.
          </div>
          <div>
            <strong>Квесты</strong> — за каждое выполненное задание от родителя даём орешки.
          </div>
          <div>
            <strong>10 орешков = 1 рубль</strong> — орешки можно конвертировать в рубли
            и зачислить на свой счёт в профиле.
          </div>
        </div>
      </div>
    </AppShell>
  );
}

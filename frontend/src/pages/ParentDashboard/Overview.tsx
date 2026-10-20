import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import AppShell from "../../components/layout/AppShell";
import CardView from "../../components/cards/CardView";
import TransactionList from "../../components/transactions/TransactionList";
import { useFamily } from "../../context/FamilyContext";
import * as transactionsApi from "../../api/transactions";
import type { Transaction } from "../../types";
import { PARENT_NAV } from "./nav";

export default function Overview() {
  const { children, loading: childrenLoading, error: childrenError, updateChildCard } = useFamily();
  const [transactionsByChild, setTransactionsByChild] = useState<Record<string, Transaction[]>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (children.length === 0) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    Promise.all(
      children.map(async (c) => {
        try {
          const txs = await transactionsApi.getTransactions({ user_id: c.user.id });
          return [c.user.id, txs] as const;
        } catch {
          return [c.user.id, []] as const;
        }
      }),
    )
      .then((pairs) => {
        if (cancelled) return;
        setTransactionsByChild(Object.fromEntries(pairs));
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Не удалось загрузить операции");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [children]);

  return (
    <AppShell navItems={PARENT_NAV}>
      <div className="row-between">
        <h1 style={{ fontSize: 22 }}>Семья</h1>
        <Link to="/parent/onboarding" className="btn btn-primary">
          + Подключить ребёнка
        </Link>
      </div>

      {childrenLoading ? (
        <div className="card">
          <div className="muted">Загрузка семьи...</div>
        </div>
      ) : children.length === 0 ? (
        <div className="card empty-state">
          <p>У вас пока нет подключённых детей.</p>
          <p className="muted">Нажмите «Подключить ребёнка», чтобы выпустить первую карту.</p>
        </div>
      ) : (
        <div className="grid-2">
          {children.map((c) => (
            <div key={c.user.id} className="card stack">
              <div className="row-between">
                <div>
                  <div style={{ fontWeight: 700 }}>{c.user.full_name}</div>
                  <span className="badge badge-neutral">{c.user.role === "teen" ? "Подросток" : "Ребёнок"}</span>
                </div>
              </div>
              <div className="stack" style={{ gap: 12 }}>
                {(c.cards && c.cards.length > 1 ? c.cards : [c.card]).map((card, idx) => (
                  <div key={card.id} className="stack" style={{ gap: 8 }}>
                    {c.cards && c.cards.length > 1 && (
                      <div className="row-between">
                        <strong style={{ fontSize: 13 }}>
                          {idx === 0 ? "Основная карта" : `Дополнительная карта ${idx}`}
                        </strong>
                        <span className="muted" style={{ fontSize: 13 }}>
                          {(card.balance ?? 0).toFixed(2)} BYN
                        </span>
                      </div>
                    )}
                    <CardView
                      card={card}
                      ownerName={c.user.full_name}
                      onCardUpdated={(updated) => updateChildCard(c.user.id, updated)}
                    />
                  </div>
                ))}
                {c.cards && c.cards.length > 1 && (
                  <Link to="/parent/cards" className="btn btn-secondary btn-sm" style={{ alignSelf: "flex-start" }}>
                    Управление картами
                  </Link>
                )}
              </div>
              <div>
                <div className="card-title" style={{ marginBottom: 6 }}>
                  Последние операции
                </div>
                {loading && !transactionsByChild[c.user.id] ? (
                  <div className="muted">Загрузка...</div>
                ) : (
                  <TransactionList transactions={(transactionsByChild[c.user.id] ?? []).slice(0, 5)} />
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {(error || childrenError) && <div className="alert alert-error">{error || childrenError}</div>}
    </AppShell>
  );
}

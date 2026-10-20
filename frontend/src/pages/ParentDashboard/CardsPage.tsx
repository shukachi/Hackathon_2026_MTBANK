import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import AppShell from "../../components/layout/AppShell";
import CardView from "../../components/cards/CardView";
import { useFamily } from "../../context/FamilyContext";
import * as cardsApi from "../../api/cards";
import type { Card } from "../../types";
import { PARENT_NAV } from "./nav";

export default function CardsPage() {
  const { children, updateChildCard } = useFamily();
  const [childId, setChildId] = useState<string>(children[0]?.user.id ?? "");
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [initialBalance, setInitialBalance] = useState("50");
  const [issuing, setIssuing] = useState(false);

  const [topUpAmounts, setTopUpAmounts] = useState<Record<string, string>>({});
  const [toppingUp, setToppingUp] = useState<string | null>(null);

  useEffect(() => {
    if (children.length > 0 && !childId) setChildId(children[0].user.id);
  }, [children, childId]);

  useEffect(() => {
    if (!childId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    cardsApi
      .getCardsOf(childId)
      .then((data) => {
        if (!cancelled) setCards(data);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Не удалось загрузить карты");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [childId]);

  const handleIssue = async (e: FormEvent) => {
    e.preventDefault();
    if (!childId) return;
    setIssuing(true);
    setError(null);
    setSuccess(null);
    try {
      const card = await cardsApi.issueCard({
        child_id: childId,
        balance: Number(initialBalance) || 0,
      });
      setCards((prev) => [...prev, card]);
      setSuccess(`Карта ${card.masked_number} выпущена. Баланс: ${card.balance?.toFixed(2) ?? "0.00"} BYN.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось выпустить карту");
    } finally {
      setIssuing(false);
    }
  };

  const handleTopUp = async (card: Card) => {
    const value = Number(topUpAmounts[card.id]) || 0;
    if (value <= 0) return;
    setToppingUp(card.id);
    setError(null);
    setSuccess(null);
    try {
      const updated = await cardsApi.topUpCard(card.id, value);
      setCards((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
      updateChildCard(card.user_id ?? "", updated);
      setTopUpAmounts((prev) => ({ ...prev, [card.id]: "" }));
      setSuccess(`На карту ${updated.masked_number} зачислено ${value.toFixed(2)} BYN.`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось пополнить карту");
    } finally {
      setToppingUp(null);
    }
  };

  const selectedChild = children.find((c) => c.user.id === childId);

  return (
    <AppShell navItems={PARENT_NAV}>
      <h1 style={{ fontSize: 22 }}>Карты</h1>

      {children.length === 0 ? (
        <div className="card empty-state">Сначала подключите ребёнка на странице «Обзор».</div>
      ) : (
        <div className="stack">
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

            <form onSubmit={handleIssue} className="stack" style={{ gap: 12 }}>
              <div className="card-title">Выпустить дополнительную карту</div>
              <p className="muted">
                У ребёнка может быть несколько карт — например, основная и отдельная накопительная
                под цель. Новая карта сразу получает стартовый баланс (карманные деньги).
              </p>
              <div className="form-field" style={{ maxWidth: 260 }}>
                <label htmlFor="initial-balance">Стартовый баланс карты, BYN</label>
                <input
                  id="initial-balance"
                  type="number"
                  min="0"
                  step="0.01"
                  value={initialBalance}
                  onChange={(e) => setInitialBalance(e.target.value)}
                />
              </div>
              <div>
                <button type="submit" className="btn btn-primary" disabled={issuing}>
                  {issuing ? "Выпускаем..." : `Выпустить карту для ${selectedChild?.user.full_name ?? "ребёнка"}`}
                </button>
              </div>
            </form>
          </div>

          <div className="card stack">
            <div className="card-title">Карты ребёнка</div>
            {loading ? (
              <div className="muted">Загрузка...</div>
            ) : cards.length === 0 ? (
              <div className="empty-state">У ребёнка пока нет карт</div>
            ) : (
              cards.map((card, idx) => (
                <div
                  key={card.id}
                  className="stack"
                  style={{ gap: 12, paddingBottom: 16, borderBottom: "1px solid var(--border)" }}
                >
                  <div className="row-between">
                    <strong>{idx === 0 ? "Основная карта" : `Дополнительная карта ${idx}`}</strong>
                    <span className="muted">{card.masked_number}</span>
                  </div>
                  <CardView
                    card={card}
                    showControls
                    onCardUpdated={(updated) => {
                      setCards((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
                      if (idx === 0) updateChildCard(card.user_id ?? "", updated);
                    }}
                  />
                  <div className="row">
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      placeholder="Сумма пополнения"
                      value={topUpAmounts[card.id] ?? ""}
                      onChange={(e) => setTopUpAmounts((prev) => ({ ...prev, [card.id]: e.target.value }))}
                      style={{ maxWidth: 180, border: "1px solid var(--border)", borderRadius: 8, padding: "8px 10px" }}
                    />
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      disabled={toppingUp === card.id}
                      onClick={() => handleTopUp(card)}
                    >
                      {toppingUp === card.id ? "Пополняем..." : "Пополнить баланс"}
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}
        </div>
      )}
    </AppShell>
  );
}

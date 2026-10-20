import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import AppShell from "../../components/layout/AppShell";
import CardView from "../../components/cards/CardView";
import TransactionList from "../../components/transactions/TransactionList";
import PointsWidget from "../../components/loyalty/PointsWidget";
import { useAuth } from "../../context/AuthContext";
import { useOwnCards } from "../../hooks/useOwnCards";
import * as transactionsApi from "../../api/transactions";
import * as loyaltyApi from "../../api/loyalty";
import type { Loyalty, SimulateResult, Transaction } from "../../types";
import { childNav } from "./nav";
import { CATEGORIES, categoryLabel } from "../../categories";

export default function Home() {
  const { user } = useAuth();
  const { cards, mainCard: card, setCards, loading: cardLoading, error: cardError } = useOwnCards();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loadingTx, setLoadingTx] = useState(true);
  const [txError, setTxError] = useState<string | null>(null);

  const [loyalty, setLoyalty] = useState<Loyalty | null>(null);
  const [loadingLoyalty, setLoadingLoyalty] = useState(true);

  const [selectedCardId, setSelectedCardId] = useState<string>("");
  const [amount, setAmount] = useState("10");
  const [category, setCategory] = useState<string>(CATEGORIES[0]);
  const [merchant, setMerchant] = useState("");
  const [simResult, setSimResult] = useState<SimulateResult | null>(null);
  const [simulating, setSimulating] = useState(false);
  const [simError, setSimError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    transactionsApi
      .getTransactions({ user_id: user.id })
      .then((data) => {
        if (!cancelled) setTransactions(data);
      })
      .catch((e) => {
        if (!cancelled) setTxError(e instanceof Error ? e.message : "Не удалось загрузить операции");
      })
      .finally(() => {
        if (!cancelled) setLoadingTx(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  // Счёт орешков ребёнка — виден сразу на главной.
  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    loyaltyApi
      .getLoyalty(user.id)
      .then((data) => {
        if (!cancelled) setLoyalty(data);
      })
      .catch(() => {
        // Не блокируем главную, если счёт орешков недоступен.
      })
      .finally(() => {
        if (!cancelled) setLoadingLoyalty(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  // Покупка идёт с выбранной карты, иначе — с основной.
  const activeCard = cards.find((c) => c.id === selectedCardId) ?? card;

  const handleSimulate = async (e: FormEvent) => {
    e.preventDefault();
    if (!activeCard) return;
    setSimulating(true);
    setSimError(null);
    setSimResult(null);
    try {
      const res = await transactionsApi.simulateTransaction({
        card_id: activeCard.id,
        amount: Number(amount) || 0,
        category,
        merchant: merchant || "Демо-магазин",
      });
      setSimResult(res);
      setTransactions((prev) => [res.transaction, ...prev]);

      // Карта после покупки — с новым балансом (приходит вместе с ответом).
      if (res.card) {
        setCards((prev) => prev.map((c) => (c.id === res.card!.id ? res.card! : c)));
      }

      // Кешбэк изменил баланс орешков — перезапрашиваем счёт.
      if (res.cashback_points) {
        loyaltyApi
          .getLoyalty(user!.id)
          .then((data) => setLoyalty(data))
          .catch(() => {});
      }
    } catch (e) {
      setSimError(e instanceof Error ? e.message : "Не удалось выполнить покупку");
    } finally {
      setSimulating(false);
    }
  };

  if (!user) return null;

  return (
    <AppShell navItems={childNav(user.role)}>
      <h1 style={{ fontSize: 22 }}>Привет, {user.full_name.split(" ")[0]}!</h1>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">{cards.length > 1 ? "Мои карты" : "Моя карта"}</div>
          {cardLoading ? (
            <div className="muted">Загрузка карты...</div>
          ) : cardError ? (
            <div className="alert alert-error">{cardError}</div>
          ) : cards.length === 0 ? (
            <div className="empty-state">Карта пока не привязана к профилю.</div>
          ) : (
            <div className="stack" style={{ gap: 16 }}>
              {cards.map((c, idx) => (
                <div key={c.id} className="stack" style={{ gap: 8 }}>
                  {cards.length > 1 && (
                    <div className="row-between">
                      <strong style={{ fontSize: 14 }}>
                        {idx === 0 ? "Основная карта" : `Дополнительная карта ${idx}`}
                      </strong>
                    </div>
                  )}
                  <CardView card={c} showControls={false} />
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-title">Совершить тестовую покупку</div>
          <p className="muted">Демо-функция: проверим, пройдёт ли операция по вашим лимитам.</p>
          <form className="stack" onSubmit={handleSimulate} style={{ gap: 12 }}>
            <div className="grid-2">
              <div className="form-field">
                <label htmlFor="sim-amount">Сумма, BYN</label>
                <input id="sim-amount" type="number" min="0" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} />
              </div>
              <div className="form-field">
                <label htmlFor="sim-category">Категория</label>
                <select id="sim-category" value={category} onChange={(e) => setCategory(e.target.value)}>
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {categoryLabel[c]}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            <div className="form-field">
              <label htmlFor="sim-merchant">Продавец</label>
              <input id="sim-merchant" value={merchant} onChange={(e) => setMerchant(e.target.value)} placeholder="Например, Соседний магазин" />
            </div>
            {cards.length > 1 && (
              <div className="form-field">
                <label htmlFor="sim-card">С какой карты оплачиваем</label>
                <select id="sim-card" value={activeCard?.id ?? ""} onChange={(e) => setSelectedCardId(e.target.value)}>
                  {cards.map((c, idx) => (
                    <option key={c.id} value={c.id}>
                      {idx === 0 ? "Основная" : `Дополнительная ${idx}`} — {c.masked_number} ({(c.balance ?? 0).toFixed(2)} BYN)
                    </option>
                  ))}
                </select>
              </div>
            )}
            <button type="submit" className="btn btn-primary" disabled={simulating || !activeCard}>
              {simulating ? "Оплачиваем..." : "Совершить покупку"}
            </button>
          </form>

          {simError && <div className="alert alert-error">{simError}</div>}
          {simResult && (
            <div className={`alert ${simResult.blocked ? "alert-error" : "alert-success"}`} style={{ marginTop: 12 }}>
              {!simResult.blocked ? (
                <>
                  Покупка одобрена на сумму {simResult.transaction.amount.toFixed(2)} BYN.
                  {simResult.cashback_points ? (
                    <> Кешбэк: +{simResult.cashback_points} орешков.</>
                  ) : (
                    <> По этой категории кешбэка нет.</>
                  )}
                </>
              ) : (
                <>
                  Покупка заблокирована лимитом.{" "}
                  {simResult.reason ?? "Превышен лимит по этой категории."}
                </>
              )}
              {simResult.insufficient_funds && (
                <div className="nut-warning" style={{ marginTop: 8 }}>
                  На карте не хватило средств — баланс ушёл в минус. Попросите родителя пополнить карту.
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-title">Мои орешки</div>
        {loadingLoyalty ? (
          <div className="muted">Загрузка...</div>
        ) : loyalty ? (
          <PointsWidget loyalty={loyalty} onConverted={setLoyalty} />
        ) : (
          <div className="empty-state">Счёт орешков пока недоступен</div>
        )}
      </div>

      <div className="card">
        <div className="card-title">Последние траты</div>
        {loadingTx ? <div className="muted">Загрузка...</div> : <TransactionList transactions={transactions.slice(0, 10)} />}
        {txError && <div className="alert alert-error">{txError}</div>}
      </div>
    </AppShell>
  );
}

import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import AppShell from "../../components/layout/AppShell";
import CardView from "../../components/cards/CardView";
import TransactionList from "../../components/transactions/TransactionList";
import { useAuth } from "../../context/AuthContext";
import { useOwnCard } from "../../hooks/useOwnCard";
import * as transactionsApi from "../../api/transactions";
import type { SimulateResult, Transaction } from "../../types";
import { childNav } from "./nav";
import { CATEGORIES, categoryLabel } from "../../categories";

export default function Home() {
  const { user } = useAuth();
  const { card, loading: cardLoading, error: cardError } = useOwnCard();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loadingTx, setLoadingTx] = useState(true);
  const [txError, setTxError] = useState<string | null>(null);

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

  const handleSimulate = async (e: FormEvent) => {
    e.preventDefault();
    if (!card) return;
    setSimulating(true);
    setSimError(null);
    setSimResult(null);
    try {
      const res = await transactionsApi.simulateTransaction({
        card_id: card.id,
        amount: Number(amount) || 0,
        category,
        merchant: merchant || "Демо-магазин",
      });
      setSimResult(res);
      setTransactions((prev) => [res.transaction, ...prev]);
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
          <div className="card-title">Моя карта</div>
          {cardLoading ? (
            <div className="muted">Загрузка карты...</div>
          ) : cardError ? (
            <div className="alert alert-error">{cardError}</div>
          ) : card ? (
            <CardView card={card} showControls={false} />
          ) : (
            <div className="empty-state">Карта пока не привязана к профилю.</div>
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
            <button type="submit" className="btn btn-primary" disabled={simulating || !card}>
              {simulating ? "Оплачиваем..." : "Совершить покупку"}
            </button>
          </form>

          {simError && <div className="alert alert-error">{simError}</div>}
          {simResult && (
            <div className={`alert ${simResult.blocked ? "alert-error" : "alert-success"}`} style={{ marginTop: 12 }}>
              {!simResult.blocked ? (
                <>Покупка одобрена на сумму {simResult.transaction.amount.toFixed(2)} BYN.</>
              ) : (
                <>
                  Покупка заблокирована лимитом.{" "}
                  {simResult.reason ?? "Превышен лимит по этой категории."}
                </>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-title">Последние траты</div>
        {loadingTx ? <div className="muted">Загрузка...</div> : <TransactionList transactions={transactions.slice(0, 10)} />}
        {txError && <div className="alert alert-error">{txError}</div>}
      </div>
    </AppShell>
  );
}

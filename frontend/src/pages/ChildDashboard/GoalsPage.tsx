import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import AppShell from "../../components/layout/AppShell";
import GoalProgress from "../../components/goals/GoalProgress";
import { useAuth } from "../../context/AuthContext";
import * as goalsApi from "../../api/goals";
import type { Goal } from "../../types";
import { childNav } from "./nav";

export default function GoalsPage() {
  const { user } = useAuth();
  const [goals, setGoals] = useState<Goal[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [targetAmount, setTargetAmount] = useState("100");
  const [creating, setCreating] = useState(false);

  const [contributeAmount, setContributeAmount] = useState<Record<string, string>>({});
  const [contributing, setContributing] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    goalsApi
      .getGoals(user.id)
      .then((data) => {
        if (!cancelled) setGoals(data);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Не удалось загрузить цели");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!user || !title.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const goal = await goalsApi.createGoal({ child_id: user.id, title, target_amount: Number(targetAmount) || 0 });
      setGoals((prev) => [goal, ...prev]);
      setTitle("");
      setTargetAmount("100");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать цель");
    } finally {
      setCreating(false);
    }
  };

  const handleContribute = async (goalId: string) => {
    const value = Number(contributeAmount[goalId]) || 0;
    if (value <= 0) return;
    setContributing(goalId);
    setError(null);
    try {
      const updated = await goalsApi.contributeToGoal(goalId, value);
      setGoals((prev) => prev.map((g) => (g.id === goalId ? updated : g)));
      setContributeAmount((prev) => ({ ...prev, [goalId]: "" }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось пополнить цель");
    } finally {
      setContributing(null);
    }
  };

  if (!user) return null;

  return (
    <AppShell navItems={childNav(user.role)}>
      <h1 style={{ fontSize: 22 }}>Цели накопления</h1>

      <div className="card">
        <div className="card-title">Новая цель</div>
        <form className="stack" onSubmit={handleCreate} style={{ gap: 12 }}>
          <div className="grid-2">
            <div className="form-field">
              <label htmlFor="goal-title">Название</label>
              <input id="goal-title" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Новый велосипед" required />
            </div>
            <div className="form-field">
              <label htmlFor="goal-target">Сумма цели, BYN</label>
              <input id="goal-target" type="number" min="1" value={targetAmount} onChange={(e) => setTargetAmount(e.target.value)} />
            </div>
          </div>
          <button type="submit" className="btn btn-primary" disabled={creating}>
            {creating ? "Создаём..." : "Создать цель"}
          </button>
        </form>
      </div>

      <div className="card stack">
        <div className="card-title">Мои цели</div>
        {loading ? (
          <div className="muted">Загрузка...</div>
        ) : goals.length === 0 ? (
          <div className="empty-state">Пока нет целей — создайте первую выше</div>
        ) : (
          goals.map((goal) => (
            <div key={goal.id} className="stack" style={{ gap: 10, paddingBottom: 12, borderBottom: "1px solid var(--border)" }}>
              <GoalProgress goal={goal} />
              <div className="row">
                <input
                  type="number"
                  min="1"
                  placeholder="Сумма"
                  value={contributeAmount[goal.id] ?? ""}
                  onChange={(e) => setContributeAmount((prev) => ({ ...prev, [goal.id]: e.target.value }))}
                  style={{ maxWidth: 140, border: "1px solid var(--border)", borderRadius: 8, padding: "8px 10px" }}
                />
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  disabled={contributing === goal.id}
                  onClick={() => handleContribute(goal.id)}
                >
                  Пополнить
                </button>
              </div>
            </div>
          ))
        )}
        {error && <div className="alert alert-error">{error}</div>}
      </div>
    </AppShell>
  );
}

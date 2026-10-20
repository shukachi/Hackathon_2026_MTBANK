import { useState } from "react";
import type { FormEvent } from "react";
import * as limitsApi from "../../api/limits";
import type { Limit, Period } from "../../types";
import { CATEGORIES, categoryLabel } from "../../categories";

interface LimitEditorProps {
  childId: string;
  limits: Limit[];
  onSaved?: (limit: Limit) => void;
}

export default function LimitEditor({ childId, limits, onSaved }: LimitEditorProps) {
  const [category, setCategory] = useState<string>(CATEGORIES[0]);
  const [amount, setAmount] = useState("");
  const [period, setPeriod] = useState<Period>("week");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    const numericAmount = Number(amount);
    if (!numericAmount || numericAmount <= 0) {
      setError("Укажите сумму лимита больше нуля");
      return;
    }
    setSaving(true);
    try {
      const limit = await limitsApi.upsertLimit({ child_id: childId, category, amount: numericAmount, period });
      setSuccess("Лимит сохранён");
      setAmount("");
      onSaved?.(limit);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось сохранить лимит");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="stack">
      {limits.length > 0 ? (
        <table className="simple-table">
          <thead>
            <tr>
              <th>Категория</th>
              <th>Сумма</th>
              <th>Период</th>
            </tr>
          </thead>
          <tbody>
            {limits.map((l) => (
              <tr key={l.id}>
                <td>{categoryLabel[l.category] ?? l.category}</td>
                <td>{l.amount.toFixed(2)} BYN</td>
                <td>{l.period === "week" ? "в неделю" : "в месяц"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div className="empty-state">Лимиты пока не настроены</div>
      )}

      <form onSubmit={handleSubmit} className="stack" style={{ gap: 12 }}>
        <div className="grid-2">
          <div className="form-field">
            <label htmlFor="limit-category">Категория</label>
            <select id="limit-category" value={category} onChange={(e) => setCategory(e.target.value)}>
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {categoryLabel[c]}
                </option>
              ))}
            </select>
          </div>
          <div className="form-field">
            <label htmlFor="limit-amount">Сумма, BYN</label>
            <input
              id="limit-amount"
              type="number"
              min="0"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="50"
            />
          </div>
          <div className="form-field">
            <label htmlFor="limit-period">Период</label>
            <select id="limit-period" value={period} onChange={(e) => setPeriod(e.target.value as Period)}>
              <option value="week">В неделю</option>
              <option value="month">В месяц</option>
            </select>
          </div>
        </div>
        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}
        <button type="submit" className="btn btn-primary" disabled={saving}>
          {saving ? "Сохранение..." : "Сохранить лимит"}
        </button>
      </form>
    </div>
  );
}

import { useState } from "react";
import type { FormEvent } from "react";
import AppShell from "../../components/layout/AppShell";
import { useAuth } from "../../context/AuthContext";
import * as accessApi from "../../api/accessRequests";
import { childNav } from "./nav";

const FEATURES = [
  { value: "subscriptions", label: "Подписки" },
  { value: "savings_product", label: "Накопительный продукт" },
  { value: "partner_discounts", label: "Партнёрские скидки" },
  { value: "online_shopping", label: "Онлайн-покупки без ограничений" },
];

export default function RequestAccessPage() {
  const { user } = useAuth();
  const [feature, setFeature] = useState(FEATURES[0].value);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(false);
    try {
      await accessApi.createAccessRequest(feature);
      setSuccess(true);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось отправить запрос");
    } finally {
      setSubmitting(false);
    }
  };

  if (!user) return null;

  return (
    <AppShell navItems={childNav(user.role)}>
      <h1 style={{ fontSize: 22 }}>Запросить доступ</h1>
      <div className="card" style={{ maxWidth: 420 }}>
        <p className="muted">Запрос увидит родитель и сможет одобрить или отклонить его.</p>
        <form className="stack" onSubmit={handleSubmit} style={{ gap: 12 }}>
          <div className="form-field">
            <label htmlFor="feature">Функция</label>
            <select id="feature" value={feature} onChange={(e) => setFeature(e.target.value)}>
              {FEATURES.map((f) => (
                <option key={f.value} value={f.value}>
                  {f.label}
                </option>
              ))}
            </select>
          </div>
          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">Запрос отправлен родителю!</div>}
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Отправляем..." : "Отправить запрос"}
          </button>
        </form>
      </div>
    </AppShell>
  );
}

import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [loginValue, setLoginValue] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(loginValue, password, fullName);
      navigate("/parent", { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось зарегистрироваться");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div className="auth-logo">
          <span className="wave" style={{ width: 28, height: 28, borderRadius: "50%", background: "linear-gradient(135deg, var(--moby-orange), var(--moby-blue-600))" }} />
          Moby Family
        </div>
        <p className="muted">Регистрация доступна только родителям. Профили детей создаются после входа, через онбординг.</p>

        <div className="form-field">
          <label htmlFor="full-name">Ваше имя</label>
          <input id="full-name" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
        </div>
        <div className="form-field">
          <label htmlFor="login">Логин</label>
          <input id="login" value={loginValue} onChange={(e) => setLoginValue(e.target.value)} autoComplete="username" required />
        </div>
        <div className="form-field">
          <label htmlFor="password">Пароль</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="new-password"
            required
          />
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
          {submitting ? "Создаём аккаунт..." : "Зарегистрироваться"}
        </button>

        <p className="muted" style={{ textAlign: "center" }}>
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </p>
      </form>
    </div>
  );
}

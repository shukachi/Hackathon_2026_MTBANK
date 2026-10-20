import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [loginValue, setLoginValue] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const user = await login(loginValue, password);
      navigate(user.role === "parent" ? "/parent" : "/child", { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось войти");
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
        <p className="muted">Вход для родителей, детей и подростков</p>

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
            autoComplete="current-password"
            required
          />
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
          {submitting ? "Входим..." : "Войти"}
        </button>

        <p className="muted" style={{ textAlign: "center" }}>
          Впервые здесь? <Link to="/register">Зарегистрироваться как родитель</Link>
        </p>
      </form>
    </div>
  );
}

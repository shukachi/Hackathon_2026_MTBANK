import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { apiFetch } from "../../api/client";

export default function VerifyEmailPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const email = searchParams.get("email") || "";
  const login = searchParams.get("login") || "";

  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [resending, setResending] = useState(false);

  const auth = useAuth();

  useEffect(() => {
    // Автоматическая инициализация полей из URL
    // (если страница открыта без URL-параметров — оставим пустыми)
  }, [email, login]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    if (code.length !== 6 || !/^\d{6}$/.test(code)) {
      setError("Введите 6-значный код из письма");
      setSubmitting(false);
      return;
    }

    try {
      const user = await auth.confirmRegistration(login, email, code);
      // Успешная регистрация — перенаправляем в личный кабинет родителя
      navigate("/parent", { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Неверный код верификации");
      setSubmitting(false);
    }
  };

  const handleResend = async () => {
    setError(null);
    setResending(true);
    try {
      await auth.resendVerificationCode(login, email);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось отправить код");
    } finally {
      setResending(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleVerify}>
        <div className="auth-logo">
          <span className="wave" style={{ width: 28, height: 28, borderRadius: "50%", background: "linear-gradient(135deg, var(--moby-orange), var(--moby-blue-600))" }} />
          Moby Family
        </div>

        <h2 style={{ margin: "0 0 8px 0" }}>Подтвердите e-mail</h2>
        <p className="muted" style={{ marginBottom: 16 }}>
          На адрес <strong>{email}</strong> отправлен 6-значный код подтверждения. Проверьте папку «Входящие».
        </p>

        <div className="form-field">
          <label htmlFor="code">Введите код</label>
          <input
            id="code"
            type="text"
            value={code}
            onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
            maxLength={6}
            required
            placeholder="Срок в 6 цифр"
            style={{ textAlign: "center", fontSize: "1.5rem", letterSpacing: "0.5rem" }}
          />
          {error && <div className="hint hint-error">{error}</div>}
        </div>

        <div className="option-row" style={{ marginTop: 16 }}>
          <span className="muted">Код через минуту? </span>
          <button type="button" className="link-button" onClick={handleResend} disabled={resending}>
            {resending ? "Отправляем..." : "Отправить ещё раз"}
          </button>
        </div>

        <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
          {submitting ? "Проверяем код..." : "Подтвердить код"}
        </button>

        <p className="muted" style={{ textAlign: "center", marginTop: 24 }}>
          <Link to={`/login?email=${email}`} style={{ color: "inherit" }}>
            Уже есть аккаунт? Войти
          </Link>
        </p>
      </form>
    </div>
  );
}
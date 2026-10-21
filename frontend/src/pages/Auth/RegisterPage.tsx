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
  const [confirmPassword, setConfirmPassword] = useState("");
  const [email, setEmail] = useState("");
  const [agreeToTerms, setAgreeToTerms] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const passwordMismatch = password !== confirmPassword && confirmPassword.length > 0;

  const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  const emailValid = emailRegex.test(email);
  const emailInvalid = email.length > 0 && !emailValid;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!agreeToTerms) {
      setError("Вы должны согласиться с Пользовательским соглашением для продолжения");
      return;
    }
    if (!emailValid) {
      setError("Введите корректный e-mail");
      return;
    }
    if (passwordMismatch) {
      setError("Пароли не совпадают");
      return;
    }

    setSubmitting(true);
    try {
      const result = await register(loginValue, password, confirmPassword, fullName, email);
      // Переходим на страницу верификации
      navigate(`/verify?email=${encodeURIComponent(result.email)}&login=${encodeURIComponent(loginValue)}`);
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
          <input
            id="full-name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            minLength={2}
            placeholder="Введите ваше имя"
          />
        </div>

        <div className="form-field">
          <label htmlFor="login">Логин</label>
          <input
            id="login"
            value={loginValue}
            onChange={(e) => setLoginValue(e.target.value)}
            autoComplete="username"
            required
            minLength={3}
            maxLength={32}
            placeholder="Придумайте логин"
          />
          <p className="hint">От 3 до 32 символов. Можно использовать буквы, цифры и символы _ - .</p>
        </div>

        <div className="form-field">
          <label htmlFor="email">E-mail <span className="required">*</span></label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value.toLowerCase())}
            autoComplete="email"
            required
            placeholder="email@example.com"
          />
          {emailInvalid && <p className="hint hint-error">Введите корректный e-mail (например, name@example.com)</p>}
          <p className="hint">На этот e-mail придёт 6-значный код подтверждения</p>
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
            minLength={8}
            placeholder="Не менее 8 символов"
          />
          <p className="hint">Пароль должен быть не менее 8 символов.</p>
        </div>

        <div className="form-field">
          <label htmlFor="confirm-password">Подтвердите пароль</label>
          <input
            id="confirm-password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            autoComplete="new-password"
            required
          />
          {passwordMismatch && (
            <span className="hint hint-error">Введите пароли одинаково, чтобы продолжить</span>
          )}
        </div>

        {/* Обязательный чекбокс согласия с Пользовательским соглашением */}
        <div className="form-field">
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={agreeToTerms}
              onChange={(e) => setAgreeToTerms(e.target.checked)}
              required
              style={{ marginTop: 2 }}
            />
            <span>
              Я прочитал(а) и согласен(а) с{" "}
              <Link to="/terms" className="link-inline">
                Пользовательским соглашением «Moby Family»
              </Link>
              . Регистрация возможна только при подтверждении согласия.
            </span>
          </label>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <button
          type="submit"
          className="btn btn-primary btn-block"
          disabled={submitting || !agreeToTerms || !emailValid || passwordMismatch}
        >
          {submitting ? "Отправляем код..." : "Получить код подтверждения"}
        </button>

        <p className="muted" style={{ textAlign: "center" }}>
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </p>
      </form>
    </div>
  );
}
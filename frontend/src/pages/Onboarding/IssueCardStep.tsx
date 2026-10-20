import type { OnboardingResult } from "../../types";

interface IssueCardStepProps {
  childName: string;
  age: string;
  onBack: () => void;
  onIssue: () => void;
  issuing: boolean;
  error: string | null;
  result: OnboardingResult | null;
  onFinish: () => void;
}

export default function IssueCardStep({ childName, age, onBack, onIssue, issuing, error, result, onFinish }: IssueCardStepProps) {
  if (result) {
    return (
      <div className="stack">
        <h2>Пакет выпущен!</h2>
        <div className="alert alert-error">
          Сохраните и передайте эти данные ребёнку. Пароль показывается только один раз — повторно он не будет
          отображён.
        </div>
        <div className="temp-password-box">
          <div className="muted" style={{ color: "rgba(255,255,255,0.8)" }}>
            Логин ребёнка
          </div>
          <div className="big">{result.login}</div>
          <div className="muted" style={{ color: "rgba(255,255,255,0.8)" }}>
            Временный пароль
          </div>
          <div className="big">{result.temporary_password}</div>
        </div>
        <div className="card" style={{ padding: 14 }}>
          <div className="row-between">
            <span>Карта выпущена для</span>
            <strong>{result.user.full_name}</strong>
          </div>
          <div className="row-between">
            <span>Роль</span>
            <span className="badge badge-neutral">{result.user.role === "teen" ? "Подросток" : "Ребёнок"}</span>
          </div>
        </div>
        <button type="button" className="btn btn-primary btn-block" onClick={onFinish}>
          Готово, перейти в кабинет
        </button>
      </div>
    );
  }

  return (
    <div className="stack">
      <h2>Шаг 3. Выпуск продукта</h2>
      <p className="muted">
        Будет создан профиль и карта для <strong>{childName}</strong>, {age} лет. Ребёнку автоматически присвоится
        собственный логин и временный пароль.
      </p>
      {error && <div className="alert alert-error">{error}</div>}
      <div className="row">
        <button type="button" className="btn btn-secondary" onClick={onBack} disabled={issuing}>
          Назад
        </button>
        <button type="button" className="btn btn-primary" onClick={onIssue} disabled={issuing}>
          {issuing ? "Выпускаем..." : "Выпустить карту"}
        </button>
      </div>
    </div>
  );
}

import type { FormEvent } from "react";

interface ConsentStepProps {
  childName: string;
  consent: boolean;
  onConsentChange: (value: boolean) => void;
  onBack: () => void;
  onNext: () => void;
}

export default function ConsentStep({ childName, consent, onConsentChange, onBack, onNext }: ConsentStepProps) {
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (consent) onNext();
  };

  return (
    <form className="stack" onSubmit={handleSubmit}>
      <h2>Шаг 2. Согласие законного представителя</h2>
      <p className="muted">
        Как законный представитель, вы подтверждаете согласие на открытие продукта «Moby Family» для{" "}
        <strong>{childName || "ребёнка"}</strong> и обработку его персональных данных в соответствии с правилами банка.
      </p>
      <label className="row" style={{ alignItems: "flex-start", cursor: "pointer" }}>
        <input type="checkbox" checked={consent} onChange={(e) => onConsentChange(e.target.checked)} style={{ marginTop: 4 }} />
        <span>
          Я подтверждаю согласие на оформление пакета и обработку персональных данных ребёнка. ⚠ Юридическая форма
          согласия требует финальной проверки комплаенс банка.
        </span>
      </label>
      <div className="row">
        <button type="button" className="btn btn-secondary" onClick={onBack}>
          Назад
        </button>
        <button type="submit" className="btn btn-primary" disabled={!consent}>
          Далее
        </button>
      </div>
    </form>
  );
}

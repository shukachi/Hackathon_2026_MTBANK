import type { FormEvent } from "react";

interface ChooseAgeStepProps {
  childName: string;
  age: string;
  onChildNameChange: (value: string) => void;
  onAgeChange: (value: string) => void;
  onNext: () => void;
  error?: string | null;
}

export default function ChooseAgeStep({ childName, age, onChildNameChange, onAgeChange, onNext, error }: ChooseAgeStepProps) {
  const ageNum = Number(age);
  const packageHint =
    ageNum >= 7 && ageNum <= 13
      ? "Пакет «Ребёнок 7–13»: физическая карта, карманные деньги, цель накопления, квесты."
      : ageNum >= 14 && ageNum <= 17
        ? "Пакет «Подросток 14–17»: физическая + цифровая карта, онлайн-покупки, подписки, запрос расширения прав."
        : "Введите возраст ребёнка от 7 до 17 лет, чтобы увидеть состав пакета.";

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onNext();
  };

  return (
    <form className="stack" onSubmit={handleSubmit}>
      <h2>Шаг 1. Возраст ребёнка</h2>
      <div className="form-field">
        <label htmlFor="child-name">Имя и фамилия ребёнка</label>
        <input id="child-name" value={childName} onChange={(e) => onChildNameChange(e.target.value)} required />
      </div>
      <div className="form-field">
        <label htmlFor="child-age">Возраст (7–17 лет)</label>
        <input
          id="child-age"
          type="number"
          min={7}
          max={17}
          value={age}
          onChange={(e) => onAgeChange(e.target.value)}
          required
        />
      </div>
      <div className="alert alert-info">{packageHint}</div>
      {error && <div className="alert alert-error">{error}</div>}
      <button type="submit" className="btn btn-primary btn-block">
        Далее
      </button>
    </form>
  );
}

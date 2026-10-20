import { useState } from "react";
import * as loyaltyApi from "../../api/loyalty";
import type { Loyalty } from "../../types";

interface PointsWidgetProps {
  loyalty: Loyalty;
  /** Обновляет виджет после конвертации — чтобы счётчик сразу показал новый баланс. */
  onConverted?: (updated: Loyalty) => void;
}

const FALLBACK_POINTS_PER_BYN = 10;

export default function PointsWidget({ loyalty, onConverted }: PointsWidgetProps) {
  const pointsPerByn = loyalty.points_per_byn || FALLBACK_POINTS_PER_BYN;
  const [amount, setAmount] = useState(String(pointsPerByn));
  const [converting, setConverting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const points = Number(amount) || 0;
  const isValidMultiple = points > 0 && points % pointsPerByn === 0;
  const hasEnough = points <= loyalty.points;
  const canConvert = isValidMultiple && hasEnough && !converting;

  const handleConvert = async () => {
    if (!canConvert) return;
    setConverting(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await loyaltyApi.convertPoints(points);
      onConverted?.(result.account);
      setSuccess(
        `Готово! ${result.points_spent} орешков → ${result.byn_amount.toFixed(2)} BYN. На счёте: ${result.converted_byn.toFixed(2)} BYN.`,
      );
      setAmount(String(pointsPerByn));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось конвертировать орешки");
    } finally {
      setConverting(false);
    }
  };

  return (
    <div className="stack" style={{ gap: 12 }}>
      <div className="row" style={{ gap: 16 }}>
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: "50%",
            background: "linear-gradient(135deg, var(--moby-orange), var(--moby-blue-600))",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#fff",
            fontWeight: 800,
            fontSize: 12,
            flexShrink: 0,
          }}
        >
          Moby
        </div>
        <div>
          <div style={{ fontSize: 26, fontWeight: 800 }}>
            {loyalty.points} <span style={{ fontSize: 15, fontWeight: 600 }}>орешков</span>
          </div>
          <div className="muted">На счёте: {loyalty.converted_byn.toFixed(2)} BYN</div>
        </div>
      </div>

      <div className="nut-convert">
        <div className="nut-convert-rate">
          <strong>{pointsPerByn} орешков = 1 рубль</strong>
          <span className="muted">Кэшбэк 5% в семейных категориях + награды за квесты</span>
        </div>

        <div className="nut-convert-row">
          <div className="form-field">
            <label htmlFor="nut-amount">Сколько орешков конвертировать</label>
            <input
              id="nut-amount"
              type="number"
              min={pointsPerByn}
              step={pointsPerByn}
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </div>
          <div className="nut-convert-preview">
            <span className="muted">Получите</span>
            <strong>
              {isValidMultiple ? (points / pointsPerByn).toFixed(2) : "0.00"} BYN
            </strong>
          </div>
        </div>

        {!isValidMultiple && points > 0 && (
          <div className="alert alert-info">
            Конвертировать можно кратное {pointsPerByn} орешков ({pointsPerByn} орешков = 1 рубль).
          </div>
        )}
        {isValidMultiple && !hasEnough && (
          <div className="alert alert-error">
            На счёте только {loyalty.points} орешков — не хватает {points - loyalty.points}.
          </div>
        )}

        <button
          type="button"
          className="btn btn-primary btn-block"
          onClick={handleConvert}
          disabled={!canConvert}
        >
          {converting
            ? "Конвертируем..."
            : `Конвертировать ${points > 0 ? points : pointsPerByn} орешков в рубли`}
        </button>

        {error && <div className="alert alert-error">{error}</div>}
        {success && <div className="alert alert-success">{success}</div>}
      </div>

      {loyalty.history.length > 0 && (
        <div className="stack" style={{ gap: 6 }}>
          <div className="muted" style={{ fontWeight: 600 }}>
            История начислений
          </div>
          {loyalty.history.slice(0, 6).map((entry, idx) => (
            <div key={idx} className="row-between" style={{ fontSize: 13 }}>
              <span className="muted">{entry.reason}</span>
              <span style={{ fontWeight: 700, color: entry.delta >= 0 ? "var(--moby-green)" : "var(--moby-red)" }}>
                {entry.delta >= 0 ? "+" : ""}
                {entry.delta} орешков
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

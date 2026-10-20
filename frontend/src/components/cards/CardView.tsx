import { useState } from "react";
import * as cardsApi from "../../api/cards";
import type { Card } from "../../types";

function maskNumber(card: Card): string {
  if (card.masked_number) return card.masked_number;
  return "**** **** **** " + card.id.slice(-4).padStart(4, "0");
}

const DESIGN_LABEL: Record<string, string> = {
  child: "Детская",
  teen: "Подростковая",
  adult: "Взрослая",
};

interface CardViewProps {
  card: Card;
  ownerName?: string;
  onCardUpdated?: (card: Card) => void;
  showControls?: boolean;
}

export default function CardView({ card, ownerName, onCardUpdated, showControls = true }: CardViewProps) {
  const [current, setCurrent] = useState(card);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const blocked = current.status === "blocked";

  const toggleBlock = async () => {
    setLoading(true);
    setError(null);
    try {
      const updated = blocked ? await cardsApi.unblockCard(current.id) : await cardsApi.blockCard(current.id);
      setCurrent(updated);
      onCardUpdated?.(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось изменить статус карты");
    } finally {
      setLoading(false);
    }
  };

  const balance = typeof current.balance === "number" ? current.balance : 0;

  return (
    <div className="stack">
      <div className={`card-visual${blocked ? " blocked" : ""}`}>
        <div className="row-between">
          <span className="muted" style={{ color: "rgba(255,255,255,0.8)" }}>
            {ownerName ?? "Карта"}
          </span>
          <span className={`badge ${blocked ? "badge-danger" : "badge-success"}`}>
            {blocked ? "Заблокирована" : "Активна"}
          </span>
        </div>
        <div className="card-number">{maskNumber(current)}</div>
        <div className="card-footer">
          <span>Moby Family</span>
          <span className="card-balance" style={{ fontSize: 16 }}>
            {balance.toFixed(2)} BYN
          </span>
        </div>
      </div>

      <div className="card-details">
        <div className="card-details-title">Реквизиты карты</div>
        <div className="card-details-row">
          <span className="muted">Номер карты</span>
          <strong>{maskNumber(current)}</strong>
        </div>
        <div className="card-details-row">
          <span className="muted">Доступно средств</span>
          <strong className={balance < 0 ? "card-details-negative" : "card-details-balance"}>
            {balance.toFixed(2)} BYN
          </strong>
        </div>
        <div className="card-details-row">
          <span className="muted">Статус</span>
          <span className={`badge ${blocked ? "badge-danger" : "badge-success"}`}>
            {blocked ? "Заблокирована" : "Активна"}
          </span>
        </div>
        <div className="card-details-row">
          <span className="muted">Тип карты</span>
          <span>{current.design ? (DESIGN_LABEL[current.design] ?? current.design) : "—"}</span>
        </div>
        <div className="card-details-row">
          <span className="muted">Выпущена</span>
          <span>{current.created_at ? formatDate(current.created_at) : "—"}</span>
        </div>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {showControls && (
        <button type="button" className={`btn ${blocked ? "btn-secondary" : "btn-danger"} btn-sm`} onClick={toggleBlock} disabled={loading}>
          {loading ? "Подождите..." : blocked ? "Разблокировать карту" : "Заблокировать карту"}
        </button>
      )}
    </div>
  );
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("ru-RU", { year: "numeric", month: "long", day: "numeric" });
}

import { useEffect, useMemo, useState } from "react";
import type { FormEvent } from "react";
import AppShell from "../../components/layout/AppShell";
import QrCode from "../../components/qr/QrCode";
import { useAuth } from "../../context/AuthContext";
import { useOwnCards } from "../../hooks/useOwnCards";
import * as qrApi from "../../api/qr";
import { CATEGORIES, categoryLabel } from "../../categories";
import type { Category } from "../../categories";
import type { Card } from "../../types";
import { childNav } from "./nav";

const DEFAULT_TTL = 10;

const statusLabel: Record<string, string> = {
  active: "Ожидает оплаты",
  paid: "Оплачен",
  expired: "Срок истёк",
  cancelled: "Отменён",
};

function formatLeft(ms: number): string {
  const total = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function cardName(cards: Card[], id: string): string {
  // id может прийти числом с бэкенда и строкой из состояния — сравниваем строками.
  const idx = cards.findIndex((c) => String(c.id) === String(id));
  const c = cards[idx];
  if (!c) return `Карта ${id}`;
  const prefix = idx === 0 ? "Основная" : `Дополнительная ${idx}`;
  return `${prefix} · ${last4(c.masked_number)}`.trim();
}

/** Только последние 4 цифры — полный номер не влезает в выпадающий список на телефоне. */
function last4(masked?: string): string {
  if (!masked) return "";
  const digits = masked.replace(/\D/g, "");
  return digits ? `**** ${digits.slice(-4)}` : masked;
}

export default function StepPage() {
  const { user } = useAuth();
  const { cards, setCards, loading: cardsLoading, error: cardsError } = useOwnCards();

  // --- Шаг 1: категория и карта (выбираются ДО генерации кода) ---
  const [category, setCategory] = useState<Category>("food");
  const [cardId, setCardId] = useState<string>("");
  const [amount, setAmount] = useState("");
  const [ttl, setTtl] = useState<string>(String(DEFAULT_TTL));
  const [generating, setGenerating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  // --- Шаг 2: показ QR ---
  const [created, setCreated] = useState<qrApi.CreatedQr | null>(null);
  const [qrImage, setQrImage] = useState<string>("");

  // --- История моих QR ---
  const [list, setList] = useState<qrApi.QrPayment[]>([]);
  const [listLoading, setListLoading] = useState(true);
  const [busyToken, setBusyToken] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [lastPay, setLastPay] = useState<qrApi.PayQrResult | null>(null);

  // Карта по умолчанию — основная. id приходит с бэкенда числом, держим его строкой.
  useEffect(() => {
    if (!cardId && cards.length > 0) setCardId(String(cards[0].id));
  }, [cards, cardId]);

  const loadList = () => {
    setListLoading(true);
    qrApi
      .getMyQr()
      .then(setList)
      .catch((e) => setActionError(e instanceof Error ? e.message : "Не удалось загрузить QR-коды"))
      .finally(() => setListLoading(false));
  };

  useEffect(loadList, []);

  // Обратный отсчёт до истечения активного кода.
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  const expiresAt = created ? new Date(created.expires_at).getTime() : 0;
  const leftMs = created ? expiresAt - now : 0;
  const isExpired = Boolean(created) && leftMs <= 0;

  const activeQr = useMemo(() => list.find((q) => q.status === "active") ?? null, [list]);

  const handleGenerate = async (e: FormEvent) => {
    e.preventDefault();
    if (!cardId) {
      setFormError("Выберите карту, со счёта которой будут списаны средства");
      return;
    }
    setGenerating(true);
    setFormError(null);
    setLastPay(null);
    try {
      const parsedAmount = amount.trim() === "" ? null : Number(amount);
      const res = await qrApi.generateQr({
        category,
        card_id: cardId,
        amount: parsedAmount,
        ttl_minutes: Number(ttl) || DEFAULT_TTL,
      });
      setCreated(res);
      setQrImage(res.payload);
      loadList();
    } catch (e2) {
      setFormError(e2 instanceof Error ? e2.message : "Не удалось создать QR-код");
    } finally {
      setGenerating(false);
    }
  };

  const handleCancel = async (token: string) => {
    setBusyToken(token);
    setActionError(null);
    try {
      await qrApi.cancelQr(token);
      if (created?.token === token) setCreated(null);
      loadList();
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Не удалось отменить QR-код");
    } finally {
      setBusyToken(null);
    }
  };

  // Эмуляция терминала: сканируем QR и списываем средства.
  // Сумма: если она задана в самом QR-коде — берём её, иначе — из поля формы
  // (код мог быть создан без суммы, тогда терминал её присылает).
  const handlePay = async (token: string, qrAmount?: number | null) => {
    setBusyToken(token);
    setActionError(null);
    try {
      const fallback = amount.trim() === "" ? null : Number(amount);
      const res = await qrApi.payQr(token, qrAmount != null ? qrAmount : fallback);
      setLastPay(res);
      setCreated(null);
      setAmount("");
      loadList();
      // Баланс карты изменился — обновляем карты в хедере приложения.
      if (res.card_balance_left != null) {
        setCards((prev) =>
          prev.map((c) => (String(c.id) === String(res.qr_payment.card_id) ? { ...c, balance: res.card_balance_left } : c)),
        );
      }
    } catch (e) {
      setActionError(e instanceof Error ? e.message : "Не удалось оплатить по QR-коду");
    } finally {
      setBusyToken(null);
    }
  };

  if (!user) return null;

  return (
    <AppShell navItems={childNav(user.role)}>
      <h1 style={{ fontSize: 22 }}>Step — оплата по QR</h1>
      <p className="muted">
        Выберите категорию покупки и карту, со счёта которой будут списаны деньги. Код одноразовый и
        живёт ограниченное время.
      </p>

      <div className="grid-2">
        <div className="card">
          <div className="card-title">1. Категория и карта</div>
          {cardsLoading ? (
            <div className="muted">Загрузка карт...</div>
          ) : cardsError ? (
            <div className="alert alert-error">{cardsError}</div>
          ) : cards.length === 0 ? (
            <div className="empty-state">Карта пока не привязана к профилю.</div>
          ) : (
            <form className="stack" onSubmit={handleGenerate} style={{ gap: 12 }}>
              <div className="form-field">
                <label htmlFor="qr-category">Категория покупки</label>
                <select id="qr-category" value={category} onChange={(e) => setCategory(e.target.value as Category)}>
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>
                      {categoryLabel[c]}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-field">
                <label htmlFor="qr-card">Карта для списания</label>
                <select id="qr-card" value={cardId} onChange={(e) => setCardId(e.target.value)}>
                  {cards.map((c, idx) => (
                    <option key={c.id} value={String(c.id)}>
                      {idx === 0 ? "Основная" : `Дополнительная ${idx}`} · {last4(c.masked_number)} · {(c.balance ?? 0).toFixed(2)} BYN
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid-2">
                <div className="form-field">
                  <label htmlFor="qr-amount">Сумма, BYN (необязательно)</label>
                  <input
                    id="qr-amount"
                    type="number"
                    min="0"
                    step="0.01"
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    placeholder="Спишется при оплате"
                  />
                </div>
                <div className="form-field">
                  <label htmlFor="qr-ttl">Срок действия, мин</label>
                  <input id="qr-ttl" type="number" min="1" max="120" value={ttl} onChange={(e) => setTtl(e.target.value)} />
                </div>
              </div>
              <button type="submit" className="btn btn-primary" disabled={generating || !cardId}>
                {generating ? "Создаём код..." : "Создать QR-код"}
              </button>
              {formError && <div className="alert alert-error">{formError}</div>}
            </form>
          )}
        </div>

        <div className="card">
          <div className="card-title">2. Временный QR-код</div>
          {!created ? (
            <div className="empty-state">
              {activeQr
                ? "У вас есть активный QR-код — он в списке ниже. Создайте новый, чтобы заменить его."
                : "Код появится здесь после создания."}
            </div>
          ) : (
            <div className="stack" style={{ gap: 12, alignItems: "center" }}>
              <QrCode value={qrImage} />
              <div className={`qr-timer ${isExpired ? "expired" : ""}`}>
                {isExpired ? "Срок действия истёк" : `Осталось ${formatLeft(leftMs)}`}
              </div>
              <div className="muted" style={{ textAlign: "center" }}>
                {categoryLabel[category]} · {cardName(cards, cardId)}
                {amount.trim() !== "" && ` · ${Number(amount).toFixed(2)} BYN`}
              </div>
              <div className="row" style={{ gap: 8, flexWrap: "wrap", justifyContent: "center" }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={busyToken === created.token || isExpired}
                  onClick={() => handlePay(created.token, amount.trim() !== "" ? Number(amount) : null)}
                >
                  {busyToken === created.token ? "Оплачиваем..." : "Оплатить (сканирование)"}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={busyToken === created.token}
                  onClick={() => handleCancel(created.token)}
                >
                  Отменить
                </button>
              </div>
              <div className="muted" style={{ fontSize: 12, textAlign: "center" }}>
                Код одноразовый: после оплаты или отмены он больше не сработает.
              </div>
            </div>
          )}
          {actionError && <div className="alert alert-error">{actionError}</div>}
          {lastPay && (
            <div className="alert alert-success" style={{ marginTop: 12 }}>
              Оплачено {lastPay.debited_amount.toFixed(2)} BYN. Остаток на карте:{" "}
              {lastPay.card_balance_left.toFixed(2)} BYN.
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-title">Мои QR-коды</div>
        {listLoading ? (
          <div className="muted">Загрузка...</div>
        ) : list.length === 0 ? (
          <div className="empty-state">QR-кодов пока не было</div>
        ) : (
          <div className="stack" style={{ gap: 10 }}>
            {list.map((q) => (
              <div key={q.id} className="qr-row">
                <div className="qr-row-main">
                  <div className="qr-row-title">
                    {categoryLabel[q.category] ?? q.category}
                    <span className={`badge ${q.status === "paid" ? "badge-success" : q.status === "active" ? "badge-warning" : "badge-neutral"}`}>
                      {statusLabel[q.status] ?? q.status}
                    </span>
                  </div>
                  <div className="muted" style={{ fontSize: 13 }}>
                    {cardName(cards, String(q.card_id))}

                    {q.amount != null && ` · ${q.amount.toFixed(2)} BYN`} ·{" "}
                    {new Date(q.created_at).toLocaleString("ru-RU")}
                  </div>
                </div>
                {q.status === "active" && (
                  <div className="qr-row-actions">
                    <button
                      type="button"
                      className="btn btn-primary btn-sm"
                      disabled={busyToken === q.token}
                      onClick={() => handlePay(q.token, q.amount)}
                    >
                      Оплатить
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      disabled={busyToken === q.token}
                      onClick={() => handleCancel(q.token)}
                    >
                      Отменить
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </AppShell>
  );
}

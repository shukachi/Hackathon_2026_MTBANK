import { apiFetch } from "./client";
import type { Category } from "../categories";

/** Статус временного QR-кода (совпадает с `QrPaymentStatusEnum` на бэкенде). */
export type QrStatus = "active" | "paid" | "expired" | "cancelled";

export interface QrPayment {
  id: number;
  token: string;
  user_id: number;
  card_id: number;
  category: Category;
  amount: number | null;
  status: QrStatus;
  merchant: string;
  created_at: string;
  expires_at: string;
  paid_at: string | null;
}

export interface CreatedQr {
  token: string;
  expires_at: string;
  /** Строка, которую кодируем в QR (например `moby://pay/<token>`). */
  payload: string;
  ttl_minutes: number;
}

export interface PayQrResult {
  qr_payment: QrPayment;
  transaction_id: number;
  debited_amount: number;
  card_balance_left: number;
}

export interface GenerateQrPayload {
  /** Категория покупки — выбирается до генерации кода. */
  category: Category;
  /** Карта, со счёта которой будут списаны средства. */
  card_id: string | number;
  /** Сумма может быть задана заранее, а может прийти от терминала при оплате. */
  amount?: number | null;
  ttl_minutes?: number;
}

/** Генерация временного QR-кода (только ребёнок / подросток). */
export function generateQr(payload: GenerateQrPayload): Promise<CreatedQr> {
  return apiFetch<CreatedQr>("/qr/generate", { method: "POST", body: payload });
}

/** Мои QR-коды: активные, оплаченные и истёкшие. */
export function getMyQr(): Promise<QrPayment[]> {
  return apiFetch<QrPayment[]>("/qr/my");
}

/** Отмена своего QR-кода. */
export function cancelQr(token: string): Promise<QrPayment> {
  return apiFetch<QrPayment>(`/qr/${encodeURIComponent(token)}/cancel`, { method: "POST" });
}

/**
 * Оплата по QR — эмуляция сканирования кода терминалом.
 * Если сумма не задана при генерации, она приходит здесь.
 */
export function payQr(token: string, amount?: number | null, merchant?: string): Promise<PayQrResult> {
  const body: { amount?: number; merchant?: string } = {};
  if (amount != null) body.amount = amount;
  if (merchant) body.merchant = merchant;
  return apiFetch<PayQrResult>(`/qr/${encodeURIComponent(token)}/pay`, {
    method: "POST",
    body,
  });
}

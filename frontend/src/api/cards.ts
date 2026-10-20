import { apiFetch } from "./client";
import type { Card } from "../types";

/** Все карты текущего пользователя. */
export function getMyCards(): Promise<Card[]> {
  return apiFetch<Card[]>("/cards");
}

/** Карты указанного пользователя: свои либо ребёнка из своей семьи. */
export function getCardsOf(userId: string): Promise<Card[]> {
  return apiFetch<Card[]>(`/cards?user_id=${encodeURIComponent(userId)}`);
}

export function getMyCard(): Promise<Card> {
  return apiFetch<Card>("/cards/me");
}

export function getCard(cardId: string): Promise<Card> {
  return apiFetch<Card>(`/cards/${cardId}`);
}

export interface IssueCardPayload {
  child_id: string;
  design?: "child" | "teen" | "adult";
  /** Стартовый баланс карты, BYN — карманные деньги от родителя. */
  balance?: number;
}

/** Выпуск дополнительной карты ребёнку (доступно родителю). */
export function issueCard(payload: IssueCardPayload): Promise<Card> {
  return apiFetch<Card>("/cards", { method: "POST", body: payload });
}

/** Пополнение баланса карты ребёнка (доступно родителю). */
export function topUpCard(cardId: string, amount: number): Promise<Card> {
  return apiFetch<Card>(`/cards/${cardId}/top-up`, { method: "POST", body: { amount } });
}

export function blockCard(cardId: string): Promise<Card> {
  return apiFetch<Card>(`/cards/${cardId}/block`, { method: "POST" });
}

export function unblockCard(cardId: string): Promise<Card> {
  return apiFetch<Card>(`/cards/${cardId}/unblock`, { method: "POST" });
}

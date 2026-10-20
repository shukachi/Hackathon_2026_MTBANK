import { apiFetch } from "./client";
import type { Card } from "../types";

export function getMyCard(): Promise<Card> {
  return apiFetch<Card>("/cards/me");
}

export function getCard(cardId: string): Promise<Card> {
  return apiFetch<Card>(`/cards/${cardId}`);
}

export function blockCard(cardId: string): Promise<Card> {
  return apiFetch<Card>(`/cards/${cardId}/block`, { method: "POST" });
}

export function unblockCard(cardId: string): Promise<Card> {
  return apiFetch<Card>(`/cards/${cardId}/unblock`, { method: "POST" });
}

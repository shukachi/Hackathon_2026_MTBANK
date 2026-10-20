import { apiFetch } from "./client";
import type { Limit, Period } from "../types";

export function getLimits(childId: string): Promise<Limit[]> {
  return apiFetch<Limit[]>(`/limits?child_id=${encodeURIComponent(childId)}`);
}

export interface UpsertLimitPayload {
  child_id: string;
  category: string;
  amount: number;
  period: Period;
}

export function upsertLimit(payload: UpsertLimitPayload): Promise<Limit> {
  return apiFetch<Limit>("/limits", { method: "PUT", body: payload });
}

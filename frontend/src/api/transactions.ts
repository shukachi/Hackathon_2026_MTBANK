import { apiFetch } from "./client";
import type { SimulateResult, Transaction } from "../types";

export interface TransactionsQuery {
  user_id?: string;
  category?: string;
  from?: string;
  to?: string;
}

export function getTransactions(query: TransactionsQuery = {}): Promise<Transaction[]> {
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const qs = params.toString();
  return apiFetch<Transaction[]>(`/transactions${qs ? `?${qs}` : ""}`);
}

export interface SimulatePayload {
  card_id: string;
  amount: number;
  category: string;
  merchant: string;
}

export function simulateTransaction(payload: SimulatePayload): Promise<SimulateResult> {
  return apiFetch<SimulateResult>("/transactions/simulate", { method: "POST", body: payload });
}

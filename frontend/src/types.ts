// Shared domain types mirroring the backend API contract (see plan.md, section 2.2 / 2.3).
// NOTE: the backend is being developed in parallel by another agent against the same
// contract. Fields marked optional are defensive — if the real backend omits them,
// the UI degrades gracefully instead of crashing.

export type Role = "parent" | "child" | "teen";

export interface User {
  id: string;
  login: string;
  role: Role;
  full_name: string;
  age?: number | null;
  family_id: string;
  parent_id?: string | null;
}

export interface Card {
  id: string;
  user_id?: string;
  masked_number?: string;
  status: "active" | "blocked" | string;
  balance?: number;
}

export interface OnboardingResult {
  user: User;
  login: string;
  temporary_password: string;
  card_id: string;
  card: Card;
}

export interface FamilyChild {
  user: User;
  card: Card;
}

export interface Transaction {
  id: string;
  card_id?: string;
  user_id?: string;
  amount: number;
  category: string;
  merchant?: string;
  status?: string;
  created_at: string;
}

export interface SimulateResult {
  transaction: Transaction;
  blocked: boolean;
  reason?: string | null;
  /** Сколько орешков начислено кешбэком за операцию. */
  cashback_points?: number;
}

export type Period = "week" | "month";

export interface Limit {
  id: string;
  child_id: string;
  category: string;
  amount: number;
  period: Period;
}

export interface Goal {
  id: string;
  child_id: string;
  title: string;
  target_amount: number;
  current_amount: number;
}

export interface Quest {
  id: string;
  child_id: string;
  title: string;
  description: string;
  reward_points: number;
  status: "pending" | "completed" | string;
}

export interface LoyaltyEntry {
  delta: number;
  reason: string;
  created_at: string;
}

export interface LoyaltyConversion {
  id: string;
  points_spent: number;
  byn_amount: number;
  created_at: string;
}

export interface Loyalty {
  points: number;
  /** Деньги, полученные за конвертированные орешки (1 BYN = points_per_byn орешков). */
  converted_byn: number;
  /** Курс конвертации с сервера: сколько орешков даёт 1 BYN. */
  points_per_byn: number;
  history: LoyaltyEntry[];
  conversions: LoyaltyConversion[];
}

export interface ConvertPointsResult {
  points_spent: number;
  byn_amount: number;
  points_left: number;
  converted_byn: number;
  account: Loyalty;
}

export type AccessRequestStatus = "pending" | "approved" | "denied" | string;

export interface AccessRequest {
  id: string;
  child_id: string;
  feature: string;
  status: AccessRequestStatus;
  created_at?: string;
}

export interface ChatReply {
  reply: string;
}

export interface ParentCommandPreview {
  action: string;
  parsed: {
    category: string | null;
    amount: number;
    period: Period;
  };
  preview_text: string;
}

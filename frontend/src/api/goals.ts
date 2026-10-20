import { apiFetch } from "./client";
import type { Goal } from "../types";

export function getGoals(childId: string): Promise<Goal[]> {
  return apiFetch<Goal[]>(`/goals?child_id=${encodeURIComponent(childId)}`);
}

export interface CreateGoalPayload {
  child_id: string;
  title: string;
  target_amount: number;
}

export function createGoal(payload: CreateGoalPayload): Promise<Goal> {
  return apiFetch<Goal>("/goals", { method: "POST", body: payload });
}

export function contributeToGoal(goalId: string, amount: number): Promise<Goal> {
  return apiFetch<Goal>(`/goals/${goalId}/contribute`, { method: "PATCH", body: { amount } });
}

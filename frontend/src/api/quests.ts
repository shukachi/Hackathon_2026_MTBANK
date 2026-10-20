import { apiFetch } from "./client";
import type { Quest } from "../types";

export function getQuests(childId: string): Promise<Quest[]> {
  return apiFetch<Quest[]>(`/quests?child_id=${encodeURIComponent(childId)}`);
}

export interface CreateQuestPayload {
  child_id: string;
  title: string;
  description: string;
  reward_points: number;
}

export function createQuest(payload: CreateQuestPayload): Promise<Quest> {
  return apiFetch<Quest>("/quests", { method: "POST", body: payload });
}

export function completeQuest(questId: string): Promise<Quest> {
  return apiFetch<Quest>(`/quests/${questId}/complete`, { method: "POST" });
}

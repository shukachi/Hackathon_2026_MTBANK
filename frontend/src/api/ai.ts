import { apiFetch } from "./client";
import type { ChatReply, ParentCommandPreview, Period } from "../types";

export function chat(message: string): Promise<ChatReply> {
  return apiFetch<ChatReply>("/ai/chat", { method: "POST", body: { message } });
}

export function parentCommandPreview(childId: string, text: string): Promise<ParentCommandPreview> {
  return apiFetch<ParentCommandPreview>("/ai/parent-command", { method: "POST", body: { child_id: childId, text } });
}

export interface ApplyParentCommandPayload {
  child_id: string;
  category: string | null;
  amount: number;
  period: Period;
}

export function applyParentCommand(payload: ApplyParentCommandPayload): Promise<void> {
  return apiFetch<void>("/ai/parent-command/apply", { method: "POST", body: payload });
}

import { apiFetch } from "./client";
import type { Loyalty } from "../types";

export function getLoyalty(userId: string): Promise<Loyalty> {
  return apiFetch<Loyalty>(`/loyalty/${userId}`);
}

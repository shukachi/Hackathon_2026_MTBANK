import { apiFetch } from "./client";
import type { ConvertPointsResult, Loyalty } from "../types";

export function getLoyalty(userId: string): Promise<Loyalty> {
  return apiFetch<Loyalty>(`/loyalty/${userId}`);
}

/** Конвертирует орешки в рубли: 10 орешков = 1 BYN. */
export function convertPoints(points: number): Promise<ConvertPointsResult> {
  return apiFetch<ConvertPointsResult>("/loyalty/convert", {
    method: "POST",
    body: { points },
  });
}

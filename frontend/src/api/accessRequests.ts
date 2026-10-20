import { apiFetch } from "./client";
import type { AccessRequest } from "../types";

export function createAccessRequest(feature: string): Promise<AccessRequest> {
  return apiFetch<AccessRequest>("/access-requests", { method: "POST", body: { feature } });
}

export function getAccessRequests(familyId: string): Promise<AccessRequest[]> {
  return apiFetch<AccessRequest[]>(`/access-requests?family_id=${encodeURIComponent(familyId)}`);
}

export function decideAccessRequest(id: string, decision: "approved" | "denied"): Promise<AccessRequest> {
  return apiFetch<AccessRequest>(`/access-requests/${id}/decide`, { method: "POST", body: { decision } });
}

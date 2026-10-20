import { apiFetch } from "./client";
import type { FamilyChild, OnboardingResult } from "../types";

export interface OnboardingPayload {
  child_full_name: string;
  age: number;
  consent_given: true;
}

export function onboardChild(payload: OnboardingPayload): Promise<OnboardingResult> {
  return apiFetch<OnboardingResult>("/family/onboarding", { method: "POST", body: payload });
}

export function getChildren(): Promise<FamilyChild[]> {
  return apiFetch<FamilyChild[]>("/family/children");
}

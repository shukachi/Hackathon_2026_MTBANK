import { apiFetch } from "./client";
import type { User } from "../types";

export interface LoginPayload {
  login: string;
  password: string;
}

export interface RegisterPayload {
  login: string;
  password: string;
  confirm_password: string;
  full_name: string;
}

export function register(payload: RegisterPayload): Promise<User> {
  return apiFetch<User>("/auth/register", { method: "POST", body: payload });
}

export function login(payload: LoginPayload): Promise<User> {
  return apiFetch<User>("/auth/login", { method: "POST", body: payload });
}

export function logout(): Promise<void> {
  return apiFetch<void>("/auth/logout", { method: "POST" });
}

export function me(silent = true): Promise<User> {
  return apiFetch<User>("/auth/me", { silentUnauthorized: silent });
}

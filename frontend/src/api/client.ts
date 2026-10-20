// Thin fetch wrapper used by every api/*.ts module.
// Auth is handled entirely via an httpOnly cookie set by the backend on
// login/register — we never touch localStorage, we just always send
// credentials: 'include' and let the backend read the cookie.

export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  detail?: string;

  constructor(status: number, message: string, detail?: string) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

// Fired whenever a request comes back 401 so interested parts of the app
// (AuthContext) can react (e.g. clear user state / redirect to /login).
export const UNAUTHORIZED_EVENT = "api:unauthorized";

function emitUnauthorized() {
  window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  // When true, a 401 response will not emit the global unauthorized event.
  // Useful for the initial GET /auth/me check on app load, where a 401 is
  // an expected "not logged in" state rather than a session expiry.
  silentUnauthorized?: boolean;
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, silentUnauthorized = false } = options;

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      credentials: "include",
      headers: body !== undefined ? { "Content-Type": "application/json" } : undefined,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, "Не удалось связаться с сервером. Проверьте подключение.");
  }

  if (response.status === 401) {
    if (!silentUnauthorized) emitUnauthorized();
    const detail = await safeDetail(response);
    throw new ApiError(401, "Не авторизован", detail);
  }

  if (response.status === 403) {
    const detail = await safeDetail(response);
    throw new ApiError(403, detail || "Недостаточно прав для этого действия", detail);
  }

  if (response.status === 400) {
    const detail = await safeDetail(response);
    throw new ApiError(400, detail || "Ошибка валидации данных", detail);
  }

  if (!response.ok) {
    const detail = await safeDetail(response);
    throw new ApiError(response.status, detail || `Ошибка сервера (${response.status})`, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  if (!text) return undefined as T;
  try {
    return JSON.parse(text) as T;
  } catch {
    return undefined as T;
  }
}

async function safeDetail(response: Response): Promise<string | undefined> {
  try {
    const data = await response.json();
    if (typeof data?.detail === "string") return data.detail;
    if (Array.isArray(data?.detail)) {
      return data.detail.map((d: unknown) => (typeof d === "object" && d && "msg" in d ? (d as { msg: string }).msg : String(d))).join("; ");
    }
    return undefined;
  } catch {
    return undefined;
  }
}

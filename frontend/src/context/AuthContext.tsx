import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import * as authApi from "../api/auth";
import { UNAUTHORIZED_EVENT } from "../api/client";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  error: string | null;
  login: (login: string, password: string) => Promise<User>;
  register: (login: string, password: string, confirmPassword: string, fullName: string, email: string) => Promise<authApi.RegisterStartResponse>;
  confirmRegistration: (login: string, email: string, code: string) => Promise<User>;
  resendVerificationCode: (login: string, email: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadMe = useCallback(async () => {
    try {
      const profile = await authApi.me(true);
      setUser(profile);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMe();
  }, [loadMe]);

  useEffect(() => {
    const onUnauthorized = () => setUser(null);
    window.addEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, onUnauthorized);
  }, []);

  const login = useCallback(async (loginValue: string, password: string) => {
    setError(null);
    try {
      const profile = await authApi.login({ login: loginValue, password });
      setUser(profile);
      return profile;
    } catch (e) {
      const message = e instanceof Error ? e.message : "Не удалось войти";
      setError(message);
      throw e;
    }
  }, []);

  // Шаг 1 регистрации: отправка кода верификации. Аккаунт ещё не создан.
  const register = useCallback(
    async (
      loginValue: string,
      password: string,
      confirmPassword: string,
      fullName: string,
      email: string,
    ) => {
      setError(null);
      try {
        const result = await authApi.registerStart({
          login: loginValue,
          password,
          confirm_password: confirmPassword,
          full_name: fullName,
          email,
        });
        return result;
      } catch (e) {
        const message = e instanceof Error ? e.message : "Не удалось зарегистрироваться";
        setError(message);
        throw e;
      }
    },
    [],
  );

  // Шаг 2 регистрации: подтверждение кода и завершение. Тут ставится auth-cookie.
  const confirmRegistration = useCallback(async (loginValue: string, email: string, code: string) => {
    setError(null);
    try {
      const profile = await authApi.registerConfirm({ login: loginValue, email, code });
      setUser(profile);
      return profile;
    } catch (e) {
      const message = e instanceof Error ? e.message : "Не удалось подтвердить код";
      setError(message);
      throw e;
    }
  }, []);

  const resendVerificationCode = useCallback(async (loginValue: string, email: string) => {
    setError(null);
    try {
      await authApi.resendVerificationCode({ login: loginValue, email });
    } catch (e) {
      const message = e instanceof Error ? e.message : "Не удалось отправить код повторно";
      setError(message);
      throw e;
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
    }
  }, []);

  const refresh = useCallback(async () => {
    await loadMe();
  }, [loadMe]);

  const value = useMemo<AuthContextValue>(
    () => ({ user, loading, error, login, register, confirmRegistration, resendVerificationCode, logout, refresh }),
    [user, loading, error, login, register, confirmRegistration, resendVerificationCode, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

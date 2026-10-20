import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useAuth } from "./AuthContext";
import * as familiesApi from "../api/families";
import type { Card, FamilyChild } from "../types";

interface FamilyContextValue {
  children: FamilyChild[];
  loading: boolean;
  error: string | null;
  addChild: (child: FamilyChild) => void;
  updateChildCard: (userId: string, card: Card) => void;
  refresh: () => Promise<void>;
}

const FamilyContext = createContext<FamilyContextValue | undefined>(undefined);

export function FamilyProvider({ children: reactChildren }: { children: ReactNode }) {
  const { user } = useAuth();
  const [kids, setKids] = useState<FamilyChild[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!user || user.role !== "parent") {
      setKids([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await familiesApi.getChildren();
      setKids(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось загрузить список детей");
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    load();
  }, [load]);

  const addChild = useCallback((child: FamilyChild) => {
    setKids((prev) => [...prev.filter((k) => k.user.id !== child.user.id), child]);
  }, []);

  const updateChildCard = useCallback((userId: string, card: Card) => {
    setKids((prev) => prev.map((k) => (k.user.id === userId ? { ...k, card } : k)));
  }, []);

  const value = useMemo<FamilyContextValue>(
    () => ({ children: kids, loading, error, addChild, updateChildCard, refresh: load }),
    [kids, loading, error, addChild, updateChildCard, load],
  );

  return <FamilyContext.Provider value={value}>{reactChildren}</FamilyContext.Provider>;
}

export function useFamily(): FamilyContextValue {
  const ctx = useContext(FamilyContext);
  if (!ctx) throw new Error("useFamily must be used within FamilyProvider");
  return ctx;
}

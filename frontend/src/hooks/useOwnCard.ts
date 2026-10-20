import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import * as cardsApi from "../api/cards";
import type { Card } from "../types";

// Fetches the current user's own card via GET /cards/me (child/teen only).
export function useOwnCard() {
  const { user } = useAuth();
  const [card, setCard] = useState<Card | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    cardsApi
      .getMyCard()
      .then((c) => {
        if (!cancelled) setCard(c);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Не удалось загрузить карту");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  return { card, setCard, loading, error };
}

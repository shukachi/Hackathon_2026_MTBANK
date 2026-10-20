import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import * as cardsApi from "../api/cards";
import type { Card } from "../types";

/**
 * Все карты текущего пользователя через GET /cards.
 * У ребёнка их может быть несколько (основная и дополнительные).
 */
export function useOwnCards() {
  const { user } = useAuth();
  const [cards, setCards] = useState<Card[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    cardsApi
      .getMyCards()
      .then((data) => {
        if (!cancelled) setCards(data);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Не удалось загрузить карты");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  /** Основная карта — первая выпущенная. */
  const mainCard = cards[0] ?? null;

  return { cards, mainCard, setCards, loading, error };
}

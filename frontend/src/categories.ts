// Must mirror backend's CategoryEnum exactly (backend/app/models/transaction.py).
// Using any other value here causes the backend to reject requests with 422.
export const CATEGORIES = [
  "food",
  "sweets",
  "toys",
  "games",
  "subscriptions",
  "education",
  "entertainment",
  "other",
] as const;

export type Category = (typeof CATEGORIES)[number];

export const categoryLabel: Record<string, string> = {
  food: "Еда",
  sweets: "Сладости",
  toys: "Игрушки",
  games: "Игры",
  subscriptions: "Подписки",
  education: "Образование",
  entertainment: "Развлечения",
  other: "Прочее",
};

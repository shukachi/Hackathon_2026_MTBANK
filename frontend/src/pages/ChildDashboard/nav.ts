import type { Role } from "../../types";

export function childNav(role: Role) {
  const base = [
    { to: "/child", label: "Главная" },
    { to: "/child/nuts", label: "Мои орешки" },
    { to: "/child/goals", label: "Цели" },
    { to: "/child/quests", label: "Квесты" },
    { to: "/child/step", label: "Step" },
    { to: "/child/request-access", label: "Запросить доступ" },
    { to: "/child/ai-chat", label: "Спросить AI" },
  ];
  return role === "teen" ? base : base;
}

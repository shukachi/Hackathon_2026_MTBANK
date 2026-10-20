import type { Transaction } from "../../types";
import { categoryLabel } from "../../categories";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("ru-RU", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
  } catch {
    return iso;
  }
}

interface TransactionListProps {
  transactions: Transaction[];
  emptyText?: string;
}

export default function TransactionList({ transactions, emptyText = "Пока нет операций" }: TransactionListProps) {
  if (transactions.length === 0) {
    return <div className="empty-state">{emptyText}</div>;
  }

  return (
    <table className="simple-table">
      <thead>
        <tr>
          <th>Дата</th>
          <th>Категория</th>
          <th>Продавец</th>
          <th>Сумма</th>
          {transactions.some((t) => t.status) && <th>Статус</th>}
        </tr>
      </thead>
      <tbody>
        {transactions.map((t) => (
          <tr key={t.id}>
            <td className="muted">{formatDate(t.created_at)}</td>
            <td>{categoryLabel[t.category] ?? t.category}</td>
            <td>{t.merchant ?? "—"}</td>
            <td style={{ fontWeight: 700 }}>{t.amount.toFixed(2)} BYN</td>
            {t.status && (
              <td>
                <span className={`badge ${t.status === "approved" ? "badge-success" : "badge-danger"}`}>
                  {t.status === "approved" ? "Одобрено" : "Блок по лимиту"}
                </span>
              </td>
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

import type { Transaction } from "../../types";
import { categoryLabel } from "../../categories";

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

function statusLabel(status?: string): string {
  return status === "approved" ? "Одобрено" : "Блок по лимиту";
}

interface TransactionListProps {
  transactions: Transaction[];
  emptyText?: string;
}

export default function TransactionList({ transactions, emptyText = "Пока нет операций" }: TransactionListProps) {
  if (transactions.length === 0) {
    return <div className="empty-state">{emptyText}</div>;
  }

  const showStatus = transactions.some((t) => t.status);

  return (
    <>
      {/* Десктоп: привычная таблица */}
      <table className="simple-table txn-table">
        <thead>
          <tr>
            <th>Дата</th>
            <th>Категория</th>
            <th>Продавец</th>
            <th>Сумма</th>
            {showStatus && <th>Статус</th>}
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
                    {statusLabel(t.status)}
                  </span>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>

      {/* Телефон: список карточек — таблица с 5 колонками туда не влезает */}
      <div className="txn-cards">
        {transactions.map((t) => (
          <div key={t.id} className="txn-card">
            <div className="row-between txn-card-head">
              <span className="txn-card-category">{categoryLabel[t.category] ?? t.category}</span>
              <strong className="txn-card-amount">{t.amount.toFixed(2)} BYN</strong>
            </div>
            <div className="row-between txn-card-meta">
              <span className="muted">{t.merchant ?? "—"}</span>
              <span className="muted">{formatDate(t.created_at)}</span>
            </div>
            {t.status && (
              <span className={`badge ${t.status === "approved" ? "badge-success" : "badge-danger"}`}>
                {statusLabel(t.status)}
              </span>
            )}
          </div>
        ))}
      </div>
    </>
  );
}

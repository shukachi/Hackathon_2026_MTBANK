import type { AccessRequest } from "../../types";

interface AccessRequestListProps {
  requests: AccessRequest[];
  onDecide?: (request: AccessRequest, decision: "approved" | "denied") => void;
  deciding?: string | null;
}

const statusLabel: Record<string, string> = {
  pending: "Ожидает решения",
  approved: "Одобрено",
  denied: "Отклонено",
};

export default function AccessRequestList({ requests, onDecide, deciding }: AccessRequestListProps) {
  if (requests.length === 0) {
    return <div className="empty-state">Нет запросов доступа</div>;
  }

  return (
    <div className="stack" style={{ gap: 12 }}>
      {requests.map((req) => (
        <div key={req.id} className="card" style={{ padding: 14 }}>
          <div className="row-between">
            <div>
              <div style={{ fontWeight: 700 }}>{req.feature}</div>
              <span
                className={`badge ${
                  req.status === "approved" ? "badge-success" : req.status === "denied" ? "badge-danger" : "badge-neutral"
                }`}
              >
                {statusLabel[req.status] ?? req.status}
              </span>
            </div>
            {req.status === "pending" && onDecide && (
              <div className="row">
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  disabled={deciding === req.id}
                  onClick={() => onDecide(req, "approved")}
                >
                  Одобрить
                </button>
                <button
                  type="button"
                  className="btn btn-danger btn-sm"
                  disabled={deciding === req.id}
                  onClick={() => onDecide(req, "denied")}
                >
                  Отклонить
                </button>
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

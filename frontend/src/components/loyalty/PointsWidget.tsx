import type { Loyalty } from "../../types";

interface PointsWidgetProps {
  loyalty: Loyalty;
}

export default function PointsWidget({ loyalty }: PointsWidgetProps) {
  return (
    <div className="stack" style={{ gap: 12 }}>
      <div className="row" style={{ gap: 16 }}>
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: "50%",
            background: "linear-gradient(135deg, var(--moby-orange), var(--moby-blue-600))",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#fff",
            fontWeight: 800,
            fontSize: 12,
            flexShrink: 0,
          }}
        >
          Moby
        </div>
        <div>
          <div style={{ fontSize: 26, fontWeight: 800 }}>{loyalty.points}</div>
          <div className="muted">баллов лояльности</div>
        </div>
      </div>
      {loyalty.history.length > 0 && (
        <div className="stack" style={{ gap: 6 }}>
          {loyalty.history.slice(0, 6).map((entry, idx) => (
            <div key={idx} className="row-between" style={{ fontSize: 13 }}>
              <span className="muted">{entry.reason}</span>
              <span style={{ fontWeight: 700, color: entry.delta >= 0 ? "var(--moby-green)" : "var(--moby-red)" }}>
                {entry.delta >= 0 ? "+" : ""}
                {entry.delta}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

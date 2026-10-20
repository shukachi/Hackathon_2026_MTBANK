import type { Goal } from "../../types";

interface GoalProgressProps {
  goal: Goal;
}

export default function GoalProgress({ goal }: GoalProgressProps) {
  const pct = goal.target_amount > 0 ? Math.min(100, Math.round((goal.current_amount / goal.target_amount) * 100)) : 0;

  return (
    <div className="stack" style={{ gap: 8 }}>
      <div className="row-between">
        <strong>{goal.title}</strong>
        <span className="muted">
          {goal.current_amount.toFixed(2)} / {goal.target_amount.toFixed(2)} BYN
        </span>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="muted">{pct}% накоплено</span>
    </div>
  );
}

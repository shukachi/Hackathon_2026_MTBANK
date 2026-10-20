import type { Quest } from "../../types";

interface QuestBoardProps {
  quests: Quest[];
  onComplete?: (quest: Quest) => void;
  completing?: string | null;
}

export default function QuestBoard({ quests, onComplete, completing }: QuestBoardProps) {
  if (quests.length === 0) {
    return <div className="empty-state">Пока нет квестов</div>;
  }

  return (
    <div className="stack" style={{ gap: 12 }}>
      {quests.map((quest) => {
        const done = quest.status === "completed";
        return (
          <div key={quest.id} className="card quest-card">
            <div className="quest-card-body">
              <div style={{ fontWeight: 700 }}>{quest.title}</div>
              <div className="muted">{quest.description}</div>
            </div>
            <div className="quest-card-side">
              <span className="badge badge-warning">+{quest.reward_points} орешков</span>
              {done ? (
                <span className="badge badge-success">Выполнено</span>
              ) : onComplete ? (
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={() => onComplete(quest)}
                  disabled={completing === quest.id}
                >
                  {completing === quest.id ? "Подождите..." : "Выполнить"}
                </button>
              ) : (
                <span className="badge badge-neutral">В процессе</span>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

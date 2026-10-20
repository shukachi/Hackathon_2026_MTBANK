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
          <div key={quest.id} className="card" style={{ padding: 14 }}>
            <div className="row-between">
              <div>
                <div style={{ fontWeight: 700 }}>{quest.title}</div>
                <div className="muted">{quest.description}</div>
              </div>
              <div className="stack" style={{ alignItems: "flex-end", gap: 8 }}>
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
          </div>
        );
      })}
    </div>
  );
}

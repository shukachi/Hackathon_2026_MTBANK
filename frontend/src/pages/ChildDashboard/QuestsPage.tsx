import { useEffect, useState } from "react";
import AppShell from "../../components/layout/AppShell";
import QuestBoard from "../../components/quests/QuestBoard";
import { useAuth } from "../../context/AuthContext";
import * as questsApi from "../../api/quests";
import type { Quest } from "../../types";
import { childNav } from "./nav";

export default function QuestsPage() {
  const { user } = useAuth();
  const [quests, setQuests] = useState<Quest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [completing, setCompleting] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    questsApi
      .getQuests(user.id)
      .then((data) => {
        if (!cancelled) setQuests(data);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Не удалось загрузить квесты");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [user]);

  const handleComplete = async (quest: Quest) => {
    setCompleting(quest.id);
    setError(null);
    try {
      const updated = await questsApi.completeQuest(quest.id);
      setQuests((prev) => prev.map((q) => (q.id === quest.id ? updated : q)));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось выполнить квест");
    } finally {
      setCompleting(null);
    }
  };

  if (!user) return null;

  return (
    <AppShell navItems={childNav(user.role)}>
      <h1 style={{ fontSize: 22 }}>Квесты</h1>
      <div className="card">
        {loading ? (
          <div className="muted">Загрузка...</div>
        ) : (
          <QuestBoard quests={quests} onComplete={handleComplete} completing={completing} />
        )}
        {error && <div className="alert alert-error">{error}</div>}
      </div>
    </AppShell>
  );
}

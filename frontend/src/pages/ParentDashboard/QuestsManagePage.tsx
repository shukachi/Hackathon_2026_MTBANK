import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import AppShell from "../../components/layout/AppShell";
import QuestBoard from "../../components/quests/QuestBoard";
import { useFamily } from "../../context/FamilyContext";
import * as questsApi from "../../api/quests";
import type { Quest } from "../../types";
import { PARENT_NAV } from "./nav";

export default function QuestsManagePage() {
  const { children } = useFamily();
  const [childId, setChildId] = useState<string>(children[0]?.user.id ?? "");
  const [quests, setQuests] = useState<Quest[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [reward, setReward] = useState("10");
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    if (children.length > 0 && !childId) setChildId(children[0].user.id);
  }, [children, childId]);

  useEffect(() => {
    if (!childId) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    questsApi
      .getQuests(childId)
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
  }, [childId]);

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault();
    if (!childId || !title.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const quest = await questsApi.createQuest({
        child_id: childId,
        title,
        description,
        reward_points: Number(reward) || 0,
      });
      setQuests((prev) => [quest, ...prev]);
      setTitle("");
      setDescription("");
      setReward("10");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось создать квест");
    } finally {
      setCreating(false);
    }
  };

  return (
    <AppShell navItems={PARENT_NAV}>
      <h1 style={{ fontSize: 22 }}>Квесты</h1>

      {children.length === 0 ? (
        <div className="card empty-state">Сначала подключите ребёнка на странице «Обзор».</div>
      ) : (
        <div className="stack">
          <div className="card stack">
            <div className="form-field" style={{ maxWidth: 320 }}>
              <label htmlFor="child-select">Ребёнок</label>
              <select id="child-select" value={childId} onChange={(e) => setChildId(e.target.value)}>
                {children.map((c) => (
                  <option key={c.user.id} value={c.user.id}>
                    {c.user.full_name}
                  </option>
                ))}
              </select>
            </div>

            <form onSubmit={handleCreate} className="stack" style={{ gap: 12 }}>
              <div className="card-title">Новый квест</div>
              <div className="grid-2">
                <div className="form-field">
                  <label htmlFor="quest-title">Название</label>
                  <input id="quest-title" value={title} onChange={(e) => setTitle(e.target.value)} required />
                </div>
                <div className="form-field">
                  <label htmlFor="quest-reward">Баллы награды</label>
                  <input id="quest-reward" type="number" min="0" value={reward} onChange={(e) => setReward(e.target.value)} />
                </div>
              </div>
              <div className="form-field">
                <label htmlFor="quest-description">Описание</label>
                <textarea id="quest-description" value={description} onChange={(e) => setDescription(e.target.value)} rows={2} />
              </div>
              <button type="submit" className="btn btn-primary" disabled={creating}>
                {creating ? "Создаём..." : "Создать квест"}
              </button>
            </form>
          </div>

          <div className="card">
            <div className="card-title">Квесты ребёнка</div>
            {loading ? <div className="muted">Загрузка...</div> : <QuestBoard quests={quests} />}
          </div>

          {error && <div className="alert alert-error">{error}</div>}
        </div>
      )}
    </AppShell>
  );
}

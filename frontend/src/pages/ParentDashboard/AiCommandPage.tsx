import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import AppShell from "../../components/layout/AppShell";
import { useFamily } from "../../context/FamilyContext";
import * as aiApi from "../../api/ai";
import type { ParentCommandPreview } from "../../types";
import { PARENT_NAV } from "./nav";

export default function AiCommandPage() {
  const { children } = useFamily();
  const [childId, setChildId] = useState<string>(children[0]?.user.id ?? "");
  const [text, setText] = useState("");
  const [preview, setPreview] = useState<ParentCommandPreview | null>(null);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [applying, setApplying] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (children.length > 0 && !childId) setChildId(children[0].user.id);
  }, [children, childId]);

  const handlePreview = async (e: FormEvent) => {
    e.preventDefault();
    if (!childId || !text.trim()) return;
    setLoadingPreview(true);
    setError(null);
    setSuccess(null);
    setPreview(null);
    try {
      const res = await aiApi.parentCommandPreview(childId, text);
      setPreview(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось обработать команду");
    } finally {
      setLoadingPreview(false);
    }
  };

  const handleApply = async () => {
    if (!preview || !childId) return;
    setApplying(true);
    setError(null);
    try {
      await aiApi.applyParentCommand({
        child_id: childId,
        category: preview.parsed.category,
        amount: preview.parsed.amount,
        period: preview.parsed.period,
      });
      setSuccess("Лимит применён");
      setPreview(null);
      setText("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Не удалось применить команду");
    } finally {
      setApplying(false);
    }
  };

  return (
    <AppShell navItems={PARENT_NAV}>
      <h1 style={{ fontSize: 22 }}>AI-команды</h1>

      {children.length === 0 ? (
        <div className="card empty-state">Сначала подключите ребёнка на странице «Обзор».</div>
      ) : (
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

          <form onSubmit={handlePreview} className="stack" style={{ gap: 12 }}>
            <div className="form-field">
              <label htmlFor="ai-command">Напишите команду</label>
              <input
                id="ai-command"
                value={text}
                onChange={(e) => setText(e.target.value)}
                placeholder="поставь лимит 50 рублей в неделю на сладости"
              />
            </div>
            <button type="submit" className="btn btn-primary" disabled={loadingPreview || !text.trim()}>
              {loadingPreview ? "Обрабатываем..." : "Отправить"}
            </button>
          </form>

          {error && <div className="alert alert-error">{error}</div>}
          {success && <div className="alert alert-success">{success}</div>}

          {preview && (
            <div className="alert alert-info stack" style={{ gap: 10 }}>
              <div>{preview.preview_text}</div>
              <div className="muted">
                Категория: {preview.parsed.category}, сумма: {preview.parsed.amount} BYN, период:{" "}
                {preview.parsed.period === "week" ? "в неделю" : "в месяц"}
              </div>
              <button type="button" className="btn btn-primary" onClick={handleApply} disabled={applying}>
                {applying ? "Применяем..." : "Подтвердить"}
              </button>
            </div>
          )}
        </div>
      )}
    </AppShell>
  );
}

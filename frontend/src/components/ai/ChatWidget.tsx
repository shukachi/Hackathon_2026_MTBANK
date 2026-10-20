import { useState } from "react";
import type { FormEvent } from "react";

export interface ChatMessage {
  role: "user" | "assistant";
  text: string;
}

interface ChatWidgetProps {
  messages: ChatMessage[];
  onSend: (text: string) => Promise<void> | void;
  placeholder?: string;
  sending?: boolean;
}

export default function ChatWidget({ messages, onSend, placeholder = "Напишите сообщение...", sending }: ChatWidgetProps) {
  const [draft, setDraft] = useState("");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text) return;
    setDraft("");
    await onSend(text);
  };

  return (
    <div className="stack">
      <div className="chat-window">
        {messages.length === 0 && <div className="empty-state">Начните диалог — задайте вопрос</div>}
        {messages.map((m, idx) => (
          <div key={idx} className={`chat-bubble ${m.role === "user" ? "user" : "assistant"}`}>
            {m.text}
          </div>
        ))}
        {sending && <div className="chat-bubble assistant muted">печатает...</div>}
      </div>
      <form className="chat-input-row" onSubmit={handleSubmit}>
        <input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={placeholder}
          disabled={sending}
        />
        <button type="submit" className="btn btn-primary" disabled={sending || !draft.trim()}>
          Отправить
        </button>
      </form>
    </div>
  );
}

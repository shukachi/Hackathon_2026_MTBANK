import { useState } from "react";
import AppShell from "../../components/layout/AppShell";
import ChatWidget from "../../components/ai/ChatWidget";
import type { ChatMessage } from "../../components/ai/ChatWidget";
import { useAuth } from "../../context/AuthContext";
import * as aiApi from "../../api/ai";
import { childNav } from "./nav";

export default function AiChatPage() {
  const { user } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([
    { role: "assistant", text: "Привет! Спроси меня, сколько ты потратил на игры или сладости за неделю." },
  ]);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSend = async (text: string) => {
    setMessages((prev) => [...prev, { role: "user", text }]);
    setSending(true);
    setError(null);
    try {
      const res = await aiApi.chat(text);
      setMessages((prev) => [...prev, { role: "assistant", text: res.reply }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "AI-ассистент временно недоступен");
    } finally {
      setSending(false);
    }
  };

  if (!user) return null;

  return (
    <AppShell navItems={childNav(user.role)}>
      <h1 style={{ fontSize: 22 }}>Спросить AI</h1>
      <p className="muted">Ассистент работает локально — данные о твоих тратах никуда не передаются.</p>
      <div className="card">
        <ChatWidget messages={messages} onSend={handleSend} sending={sending} placeholder="Сколько я потратил на игры?" />
        {error && <div className="alert alert-error" style={{ marginTop: 12 }}>{error}</div>}
      </div>
    </AppShell>
  );
}

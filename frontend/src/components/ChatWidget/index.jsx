import { useState } from "react";
import { MessageCircle, X } from "lucide-react";
import { chatAPI } from "../../services/api";

function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Need quick EV help? Ask here." },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const send = async () => {
    if (!input.trim() || loading) return;
    const q = input.trim();
    setInput("");
    setError("");
    setMessages((prev) => [...prev, { role: "user", text: q }, { role: "assistant", text: "" }]);
    setLoading(true);
    try {
      await chatAPI.sendStream(
        { message: q, session_id: sessionId },
        {
          onSession: (id) => setSessionId(id),
          onChunk: (chunk) => {
            setMessages((prev) => {
              const next = [...prev];
              next[next.length - 1] = { ...next[next.length - 1], text: (next[next.length - 1].text || "") + chunk };
              return next;
            });
          },
        }
      );
    } catch (e) {
      setError("Chat unavailable right now.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button className="chat-fab" type="button" onClick={() => setOpen((v) => !v)}>
        {open ? <X size={18} /> : <MessageCircle size={18} />}
      </button>
      {open && (
        <aside className="chat-widget-panel glass-card">
          <div className="chat-window" style={{ height: 260 }}>
            {messages.map((m, i) => (
              <div key={i} className={`msg ${m.role === "user" ? "user" : "bot"}`}>{m.text || (loading ? "..." : "")}</div>
            ))}
            {loading && <div className="skeleton" style={{ height: 36 }} />}
          </div>
          {error && <p style={{ color: "var(--text-muted)", marginTop: 8 }}>{error}</p>}
          <div className="input-row">
            <input className="input" value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask EV question" />
            <button className="btn btn-primary" onClick={send} disabled={loading}>Send</button>
          </div>
        </aside>
      )}
    </>
  );
}

export default ChatWidget;

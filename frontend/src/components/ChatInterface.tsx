import { useState, useRef, useEffect } from "react";
import "./ChatInterface.css";
import { chat, type ChatMessage } from "../api";

export function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const suggestions = [
    "Summarize this candidate’s experience in 5 bullets.",
    "What are the strongest technical skills shown in the resume?",
    "Is there evidence of leadership or mentorship? Quote the resume sections.",
    "Do they have hands-on experience with cloud (AWS/Azure/GCP)?",
    "What risks or gaps should I probe in an interview?",
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    setError(null);

    const userMsg: ChatMessage = { role: "user", content: q };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await chat(q, messages);
      if (res.success) {
        setMessages((prev) => [...prev, { role: "assistant", content: res.answer }]);
      } else {
        setError(res.error || "Failed to get response");
      }
    } catch {
      setError("Failed to send message");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-interface">
      {messages.length === 0 && (
        <div className="chat-suggestions">
          {suggestions.map((s) => (
            <button
              key={s}
              type="button"
              className="chip"
              onClick={() => setInput(s)}
              disabled={loading}
              title="Click to use this prompt"
            >
              {s}
            </button>
          ))}
        </div>
      )}
      <div className="chat-messages">
        {messages.length === 0 && (
          <p className="chat-placeholder">
            Ask questions about the candidate and the AI will answer based on retrieved resume context only.
            If the resume doesn’t mention something, it should say “not enough info”.
          </p>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role}`}>
            <span className="chat-role">{m.role === "user" ? "You" : "AI"}</span>
            <div className="chat-content">{m.content}</div>
          </div>
        ))}
        {loading && (
          <div className="chat-msg assistant">
            <span className="chat-role">AI</span>
            <div className="chat-content typing">...</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <form onSubmit={handleSubmit} className="chat-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your question..."
          className="chat-input"
          disabled={loading}
        />
        <button type="submit" className="btn btn-primary" disabled={loading || !input.trim()}>
          Send
        </button>
      </form>
      {error && <p className="chat-error">{error}</p>}
    </div>
  );
}

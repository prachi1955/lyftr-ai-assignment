import { useState } from "react";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

function App() {
  const [sessionId] = useState(() => crypto.randomUUID());
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const sendMessage = async () => {
    const trimmedMessage = message.trim();

    if (!trimmedMessage || loading) {
      return;
    }

    setError("");

    const userMessage = {
      role: "user",
      content: trimmedMessage,
    };

    setMessages((previous) => [...previous, userMessage]);
    setMessage("");
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: trimmedMessage,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Something went wrong");
      }

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: data.reply,
          metadata: data.metadata,
        },
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>Lyftr AI Chat</h1>
        <p>LLM chatbot with caching and automatic key failover</p>
      </header>

      <main className="chat-container">
        <div className="messages">
          {messages.length === 0 && (
            <div className="welcome">
              <h2>How can I help you?</h2>
              <p>Start a conversation with the AI assistant.</p>
            </div>
          )}

          {messages.map((item, index) => (
            <div
              key={index}
              className={`message ${item.role}`}
              data-testid={
                item.role === "assistant"
                  ? "assistant-message"
                  : undefined
              }
            >
              <div className="role">
                {item.role === "user" ? "You" : "AI"}
              </div>

              <div className="bubble">{item.content}</div>

              {item.role === "assistant" && item.metadata && (
                <div className="metadata">
                  <span data-testid="meta-source">
                    {item.metadata.resolution_source}
                  </span>

                  <span data-testid="meta-model">
                    {item.metadata.model}
                  </span>

                  <span data-testid="meta-latency">
                    {item.metadata.latency_ms} ms
                  </span>

                  <span data-testid="meta-input-tokens">
                    Input: {item.metadata.input_tokens}
                  </span>

                  <span data-testid="meta-output-tokens">
                    Output: {item.metadata.output_tokens}
                  </span>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="message assistant">
              <div className="role">AI</div>
              <div className="bubble">Thinking...</div>
            </div>
          )}
        </div>

        {error && <div className="error">{error}</div>}

        <div className="input-area">
          <textarea
            data-testid="chat-input"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            maxLength={4000}
          />

          <button
            data-testid="send-button"
            onClick={sendMessage}
            disabled={loading || !message.trim()}
          >
            {loading ? "Sending..." : "Send"}
          </button>
        </div>
      </main>
    </div>
  );
}

export default App;
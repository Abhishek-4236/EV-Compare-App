import { useState } from 'react';
import axios from 'axios';

function ChatPage() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: '👋 Hi! I\'m your India EV Assistant. Ask me anything about electric vehicles — prices, range, subsidies, comparisons!'
    }
  ]);
  const [sessionId, setSessionId] = useState(null);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { role: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post('http://localhost:8000/api/chat/', {
        message: input,
        session_id: sessionId
      });

      if (!sessionId && res.data.session_id) {
        setSessionId(res.data.session_id);
      }

      const botMsg = {
        role: 'assistant',
        text: res.data.answer,
        sources: res.data.sources
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: '❌ Sorry, something went wrong. Please try again.'
      }]);
    }
    setLoading(false);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const SUGGESTIONS = [
    "Best scooter under ₹1.2L?",
    "Compare Ather 450X vs Ola S1 Pro",
    "Which EV has longest range?",
    "FAME II subsidy for 2W?",
  ];

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>⚡ EV Chat Assistant</h1>
        <p style={styles.subtitle}>Powered by RAG — Real EV data + AI</p>
      </div>

      {/* Suggestions */}
      <div style={styles.suggestions}>
        {SUGGESTIONS.map(s => (
          <button key={s} style={styles.suggBtn}
            onClick={() => { setInput(s); }}>
            {s}
          </button>
        ))}
      </div>

      {/* Chat window */}
      <div style={styles.chatWindow}>
        {messages.map((msg, i) => (
          <div key={i} style={{
            ...styles.message,
            ...(msg.role === 'user' ? styles.userMsg : styles.botMsg)
          }}>
            <div style={styles.msgRole}>
              {msg.role === 'user' ? '👤 You' : '⚡ EV Assistant'}
            </div>
            <div style={styles.msgText}>{msg.text}</div>
            {msg.sources && msg.sources.length > 0 && (
              <div style={styles.sources}>
                <div style={styles.sourcesTitle}>📊 Based on:</div>
                {msg.sources.map((s, j) => (
                  <span key={j} style={styles.sourceTag}>
                    {s.brand} {s.model} — ₹{(s.price / 100000).toFixed(1)}L
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div style={styles.botMsg}>
            <div style={styles.msgRole}>⚡ EV Assistant</div>
            <div style={styles.msgText}>Thinking... 🤔</div>
          </div>
        )}
      </div>

      {/* Input */}
      <div style={styles.inputArea}>
        <textarea
          style={styles.input}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask about any EV... e.g. Best EV under 1 lakh with 100km range"
          rows={2}
        />
        <button
          style={styles.sendBtn}
          onClick={sendMessage}
          disabled={loading || !input.trim()}
        >
          {loading ? '...' : 'Send ➤'}
        </button>
      </div>
    </div>
  );
}

const styles = {
  container: { maxWidth: '900px', margin: '0 auto', padding: '2rem' },
  header: {
    textAlign: 'center', padding: '2rem',
    backgroundColor: '#1a1a2e', borderRadius: '12px',
    marginBottom: '1.5rem', color: 'white',
  },
  title: { fontSize: '2rem', color: '#00d4ff', margin: 0 },
  subtitle: { opacity: 0.7, marginTop: '0.5rem' },
  suggestions: {
    display: 'flex', gap: '0.8rem', flexWrap: 'wrap', marginBottom: '1rem',
  },
  suggBtn: {
    padding: '0.4rem 0.8rem', backgroundColor: '#f1f5f9',
    border: '1px solid #cbd5e1', borderRadius: '20px',
    cursor: 'pointer', fontSize: '0.85rem',
  },
  chatWindow: {
    height: '450px', overflowY: 'auto',
    border: '1px solid #e9ecef', borderRadius: '12px',
    padding: '1rem', marginBottom: '1rem',
    display: 'flex', flexDirection: 'column', gap: '1rem',
    backgroundColor: '#f8f9fa',
  },
  message: { padding: '1rem', borderRadius: '8px', maxWidth: '85%' },
  userMsg: { backgroundColor: '#1a1a2e', color: 'white', alignSelf: 'flex-end' },
  botMsg: { backgroundColor: 'white', border: '1px solid #e9ecef', alignSelf: 'flex-start' },
  msgRole: { fontSize: '0.75rem', fontWeight: 'bold', marginBottom: '0.3rem', opacity: 0.7 },
  msgText: { fontSize: '0.95rem', lineHeight: 1.5 },
  sources: { marginTop: '0.8rem', paddingTop: '0.8rem', borderTop: '1px solid #e9ecef' },
  sourcesTitle: { fontSize: '0.75rem', color: '#666', marginBottom: '0.4rem' },
  sourceTag: {
    display: 'inline-block', padding: '0.2rem 0.5rem',
    backgroundColor: '#dbeafe', borderRadius: '4px',
    fontSize: '0.75rem', marginRight: '0.4rem', marginBottom: '0.2rem',
  },
  inputArea: { display: 'flex', gap: '0.8rem' },
  input: {
    flex: 1, padding: '0.8rem', borderRadius: '8px',
    border: '1px solid #cbd5e1', fontSize: '0.95rem',
    resize: 'none', fontFamily: 'inherit',
  },
  sendBtn: {
    padding: '0 1.5rem', backgroundColor: '#00d4ff',
    color: '#1a1a2e', border: 'none', borderRadius: '8px',
    fontWeight: 'bold', cursor: 'pointer', fontSize: '1rem',
  },
};

export default ChatPage;

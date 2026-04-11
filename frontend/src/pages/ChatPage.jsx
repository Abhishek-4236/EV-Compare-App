import { useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import { chatAPI } from '../services/api';
import { Send, Bot, User, Zap, RefreshCw, Car, ChevronLeft, ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const SUGGESTIONS = [
  'Best electric car for ₹15-20L?',
  'Compare Tata Nexon EV vs MG ZS EV',
  'What is the FAME II subsidy for scooters?',
  'Fastest charging electric SUV in India?',
];

function TypingIndicator() {
  return (
    <div className="ev-msg-row bot">
      <div className="ev-avatar bot"><Bot size={16} /></div>
      <div className="ev-msg-bubble bot typing">
        <div className="typing-dots"><span></span><span></span><span></span></div>
      </div>
    </div>
  );
}

function SourceChips({ sources }) {
  if (!sources?.length) return null;
  return (
    <div className="ev-source-grid">
      {sources.slice(0, 4).map((s, i) => (
        <div key={i} className="ev-source-card">
          {s.image_url ? (
             <img src={s.image_url} alt={s.model} className="ev-source-img" />
          ) : (
             <div className="ev-source-placeholder"><Car size={14} /></div>
          )}
          <div className="ev-source-info">
            <div className="name">{s.brand} {s.model}</div>
            <div className="price">{s.price ? `₹${(s.price / 100000).toFixed(1)}L` : 'View Details'}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

function ChatMessage({ msg }) {
  const isUser = msg.role === 'user';
  return (
    <div className={`ev-msg-row ${isUser ? 'user' : 'bot'}`}>
      {!isUser && <div className="ev-avatar bot"><Bot size={16} /></div>}
      <div className={`ev-msg-bubble ${isUser ? 'user' : 'bot'}`}>
        {isUser ? (
          <p className="ev-msg-text">{msg.text}</p>
        ) : (
          <div className="ev-msg-markdown">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                table: ({ children }) => <div className="ev-table-wrap"><table className="ev-chat-table">{children}</table></div>,
                th: ({ children }) => <th>{children}</th>,
                td: ({ children }) => <td>{children}</td>,
                p: ({ children }) => <p>{children}</p>,
                strong: ({ children }) => <strong className="highlight">{children}</strong>,
              }}
            >
              {msg.text}
            </ReactMarkdown>
            <SourceChips sources={msg.sources} />
          </div>
        )}
      </div>
      {isUser && <div className="ev-avatar user"><User size={16} /></div>}
    </div>
  );
}

export default function ChatPage() {
  const [searchParams] = useSearchParams();
  const initialQ = searchParams.get('q') || '';
  const [messages, setMessages] = useState([
    { role: 'assistant', text: `Hello! I'm your **EViq Expert**. Ask me anything about EVs in India — from technical battery specs to the best budget scooter. How can I help you today?` }
  ]);
  const [sessionId, setSessionId] = useState(null);
  const [input, setInput] = useState(initialQ);
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  async function sendMessage(msgText) {
    const text = (msgText || input).trim();
    if (!text) return;
    setMessages(prev => [...prev, { role: 'user', text }]);
    setInput('');
    setLoading(true);

    try {
      setMessages(prev => [...prev, { role: 'assistant', text: '' }]);
      let collected = '';
      await chatAPI.sendStream({ message: text, session_id: sessionId }, {
        onSession: (sid) => { if (!sessionId && sid) setSessionId(sid); },
        onChunk: (chunk) => {
          collected += chunk;
          setMessages(prev => {
            const next = [...prev];
            next[next.length - 1] = { ...next[next.length - 1], text: collected };
            return next;
          });
        },
        onDone: (data) => {
          setMessages(prev => {
            const next = [...prev];
            next[next.length - 1] = { ...next[next.length - 1], sources: data?.sources };
            return next;
          });
        }
      });
    } catch (err) {
      setMessages(prev => {
        const next = [...prev];
        next[next.length - 1] = { role: 'assistant', text: 'Sorry, I encountered an issue. Let\'s try that again.' };
        return next;
      });
    }
    setLoading(false);
  }

  function clearChat() {
    setMessages([{ role: 'assistant', text: `Hello! Fresh start. How can I help you?` }]);
    setSessionId(null);
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  return (
    <div className="ev-chat-layout">
      {/* Sidebar */}
      <aside className="ev-chat-sidebar">
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={clearChat}>
            <RefreshCw size={14} /> New Chat
          </button>
        </div>
        <div className="sidebar-nav">
          <div className="label">History</div>
          <div className="nav-item active">Current Thread</div>
          <div className="nav-item disabled">EV Comparison 1</div>
          <div className="nav-item disabled">Charging Costs...</div>
        </div>
        <div className="sidebar-user">
           <User size={14} /> <span>{sessionId ? 'Active User' : 'Guest'}</span>
        </div>
      </aside>

      {/* Main Area */}
      <main className={`ev-chat-main ${messages.length <= 1 ? 'is-welcome' : ''}`}>
        <div className="ev-chat-scroll-area">
          <div className="ev-chat-content-limit">
            {messages.map((msg, i) => (
              <ChatMessage key={i} msg={msg} />
            ))}
            {loading && <TypingIndicator />}
            <div ref={chatEndRef} style={{ height: 160 }} />
          </div>
        </div>

        {/* Input Overlay */}
        <div className="ev-chat-input-sticky">
           <div className="ev-chat-input-limit">
              {!loading && messages.length <= 1 && (
                <div className="ev-suggestion-row">
                   {SUGGESTIONS.map(s => (
                     <button key={s} onClick={() => sendMessage(s)} className="suggestion-pill">{s}</button>
                   ))}
                </div>
              )}
              
              <div className="ev-input-container">
                 <textarea 
                    ref={textareaRef}
                    rows={1}
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKey}
                    placeholder="Ask EViq AI..."
                 />
                 <button className={`send-btn ${input.trim() ? 'active' : ''}`} onClick={() => sendMessage()}>
                    <Send size={18} />
                 </button>
              </div>
              <div className="disclaimer">EViq AI can make mistakes. Verify facts.</div>
           </div>
        </div>
      </main>

      <style>{`
        .ev-chat-layout {
          display: flex; height: 100vh; width: 100%;
          background: #fdfdfd; overflow: hidden;
        }

        .ev-chat-sidebar {
          width: 260px; background: #f8f8f8; border-right: 1px solid #eee;
          display: flex; flex-direction: column; padding: 16px;
        }
        @media (max-width: 768px) { .ev-chat-sidebar { display: none; } }
        
        .new-chat-btn {
          width: 100%; padding: 10px; border-radius: 8px; border: 1px solid #ddd;
          background: white; font-size: 13px; font-weight: 600; cursor: pointer;
          display: flex; align-items: center; gap: 8px;
        }
        .sidebar-nav { flex: 1; margin-top: 20px; }
        .sidebar-nav .label { font-size: 11px; font-weight: 700; color: #999; text-transform: uppercase; margin-bottom: 12px; }
        .nav-item { padding: 8px 12px; font-size: 13px; border-radius: 8px; cursor: pointer; color: #555; }
        .nav-item.active { background: #eee; font-weight: 600; color: #111; }
        .nav-item.disabled { opacity: 0.5; }
        .sidebar-user { border-top: 1px solid #eee; padding-top: 16px; display: flex; align-items: center; gap: 8px; font-size: 13px; }

        .ev-chat-main {
          flex: 1; display: flex; flex-direction: column; position: relative;
        }

        .ev-chat-scroll-area {
          flex: 1; overflow-y: auto; scrollbar-width: thin;
          padding: 60px 20px 0;
        }
        .ev-chat-content-limit { max-width: 800px; margin: 0 auto; width: 100%; }

        /* Welcome Centering Hook */
        .ev-chat-main.is-welcome .ev-chat-scroll-area {
          display: flex; align-items: center; justify-content: center; padding-top: 0;
        }
        .ev-chat-main.is-welcome .ev-chat-content-limit {
           padding-bottom: 200px;
        }

        .ev-msg-row { display: flex; gap: 16px; margin-bottom: 24px; animation: fadeIn 0.4s ease-out; }
        .ev-msg-row.user { justify-content: flex-end; }
        .ev-avatar { width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
        .ev-avatar.bot { background: #e0f2f1; color: #0ea5a4; }
        .ev-avatar.user { background: #333; color: white; }

        .ev-msg-bubble { max-width: 85%; line-height: 1.6; }
        .ev-msg-bubble.user { background: #f4f4f4; padding: 12px 20px; border-radius: 20px; color: #111; font-weight: 500; }
        .ev-msg-bubble.bot { font-size: 15px; color: #333; }
        .ev-msg-markdown p { margin-bottom: 12px; }
        .highlight { color: #0ea5a4; font-weight: 700; }

        /* Tables & Spacing */
        .ev-table-wrap { width: 100%; overflow-x: auto; margin-top: 16px; border-radius: 12px; border: 1px solid #eee; background: white; }
        .ev-chat-table { width: 100%; border-collapse: separate; border-spacing: 0; }
        .ev-chat-table th { background: #f9fafb; padding: 14px 16px; text-align: left; font-size: 13px; font-weight: 700; color: #374151; border-bottom: 1px solid #eee; }
        .ev-chat-table td { padding: 14px 16px; border-bottom: 1px solid #f3f4f6; font-size: 14px; color: #4b5563; line-height: 1.5; }
        .ev-chat-table tr:last-child td { border-bottom: none; }
        .ev-chat-table tr:hover { background: #fcfcfc; }

        .ev-chat-input-sticky {
          position: fixed; bottom: 0; left: 260px; right: 0;
          padding: 20px; background: linear-gradient(transparent, white 40%);
        }
        @media (max-width: 768px) { .ev-chat-input-sticky { left: 0; } }
        .ev-chat-input-limit { max-width: 800px; margin: 0 auto; width: 100%; }

        .ev-input-container {
          background: white; border: 1px solid #e5e7eb; border-radius: 24px;
          padding: 10px 10px 10px 20px; display: flex; align-items: flex-end; gap: 12px;
          box-shadow: 0 10px 30px rgba(0,0,0,0.05);
        }
        .ev-input-container textarea {
          flex: 1; border: none; outline: none; resize: none; max-height: 200px;
          padding: 8px 0; font-size: 15px; color: #111;
        }
        .send-btn {
          width: 40px; height: 40px; border-radius: 50%; background: #eee;
          color: white; border: none; display: flex; align-items: center; justify-content: center;
          cursor: not-allowed; transition: 0.3s;
        }
        .send-btn.active { background: #0ea5a4; cursor: pointer; transform: scale(1.05); }

        .ev-suggestion-row { display: flex; gap: 8px; margin-bottom: 12px; overflow-x: auto; scrollbar-width: none; }
        .suggestion-pill {
          white-space: nowrap; padding: 8px 16px; border-radius: 100px;
          background: white; border: 1px solid #eee; font-size: 13px; color: #666; cursor: pointer;
        }
        .disclaimer { text-align: center; font-size: 11px; color: #999; margin-top: 10px; }

        /* Helpers */
        .ev-source-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-top: 16px; }
        .ev-source-card { display: flex; gap: 10px; padding: 10px; border-radius: 12px; background: white; border: 1px solid #eee; }
        .ev-source-img { width: 44px; height: 44px; border-radius: 6px; object-fit: cover; }
        .ev-source-placeholder { width: 44px; height: 44px; background: #f0f0f0; border-radius: 6px; display: flex; align-items: center; justify-content: center; color: #aaa; }
        .ev-source-info .name { font-size: 12px; font-weight: 700; }
        .ev-source-info .price { font-size: 11px; color: #666; }

        .typing-dots span { width: 6px; height: 6px; background: #ccc; border-radius: 50%; display: inline-block; animation: bounce 1.4s infinite; margin: 0 2px; }
        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes bounce { 0%, 100% { transform: scale(1); } 50% { transform: scale(1.3); opacity: 0.5; } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
      `}</style>
    </div>
  );
}

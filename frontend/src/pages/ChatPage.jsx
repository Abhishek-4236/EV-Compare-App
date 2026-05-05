import { startTransition, useCallback, useDeferredValue, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Menu, PanelLeftClose, Sparkles } from 'lucide-react';

import { chatAPI } from '../services/api';
import useAuth from '../store/useAuth';
import ChatComposer from '../components/chat/ChatComposer';
import ChatMessage from '../components/chat/ChatMessage';
import ChatSidebar from '../components/chat/ChatSidebar';
import TypingIndicator from '../components/chat/TypingIndicator';
import {
  clearStoredChatSession,
  getStoredChatSession,
  readStoredChatSessions,
  upsertStoredChatSession,
} from '../utils/chatSessionStorage';

const INITIAL_MESSAGE = {
  role: 'assistant',
  text: "I’m **EViq Expert**. Ask me about EV recommendations, charging, TCO, subsidies, or model comparisons in the current India EV dataset.",
};

function buildSessionTitle(messages) {
  const meaningfulMessages = messages.filter(message => message.text && message !== INITIAL_MESSAGE);
  const firstUserMessage = meaningfulMessages.find(message => message.role === 'user')?.text || 'New Chat';
  return firstUserMessage.length > 44 ? `${firstUserMessage.slice(0, 44)}...` : firstUserMessage;
}

function buildLocalSession(sessionId, messages) {
  return {
    id: sessionId,
    title: buildSessionTitle(messages),
    updatedAt: new Date().toISOString(),
    messages,
  };
}

function mergeSessionLists(localSessions, remoteSessions) {
  const byId = new Map();
  [...localSessions, ...remoteSessions].forEach(session => {
    const existing = byId.get(session.id);
    if (!existing || new Date(session.updatedAt || session.created_at || 0) > new Date(existing.updatedAt || existing.created_at || 0)) {
      byId.set(session.id, session);
    }
  });

  return [...byId.values()].sort(
    (left, right) => new Date(right.updatedAt || right.created_at || 0) - new Date(left.updatedAt || left.created_at || 0)
  );
}

export default function ChatPage() {
  const [searchParams] = useSearchParams();
  const initialQ = searchParams.get('q') || '';
  const { user } = useAuth();

  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [sessionId, setSessionId] = useState(null);
  const [input, setInput] = useState(initialQ);
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [remoteSessions, setRemoteSessions] = useState([]);
  const [localSessions, setLocalSessions] = useState(() => readStoredChatSessions());
  const [streamingMessage, setStreamingMessage] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [savingSessionId, setSavingSessionId] = useState(null);
  const [deletingSessionId, setDeletingSessionId] = useState(null);
  const [hasSpeechRecognition] = useState(
    () => typeof window !== 'undefined' && Boolean(window.SpeechRecognition || window.webkitSpeechRecognition)
  );
  const isWelcomeState = messages.length <= 1;

  const deferredMessages = useDeferredValue(messages);
  const chatScrollRef = useRef(null);
  const textareaRef = useRef(null);
  const recognitionRef = useRef(null);

  const sessions = mergeSessionLists(localSessions, user ? remoteSessions : []);

  const refreshRemoteSessions = useCallback(async () => {
    if (!user) {
      setRemoteSessions([]);
      return;
    }

    try {
      const response = await chatAPI.getSessions();
      setRemoteSessions(response.data || []);
    } catch (error) {
      console.error('Could not fetch sessions', error);
    }
  }, [user]);

  useEffect(() => {
    refreshRemoteSessions();
  }, [refreshRemoteSessions]);

  useEffect(() => {
    const scrollNode = chatScrollRef.current;
    if (!scrollNode) return;

    const nextFrame = window.requestAnimationFrame(() => {
      scrollNode.scrollTo({
        top: scrollNode.scrollHeight,
        behavior: streamingMessage ? 'auto' : 'smooth',
      });
    });

    return () => window.cancelAnimationFrame(nextFrame);
  }, [messages, loading, streamingMessage]);

  useEffect(() => {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = '0px';
    textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
  }, [input]);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-IN';
    recognition.onresult = event => {
      const transcript = Array.from(event.results).map(result => result[0].transcript).join('');
      setInput(transcript);
    };
    recognition.onerror = error => {
      console.error('Speech recognition error', error);
      setIsListening(false);
    };
    recognition.onend = () => setIsListening(false);
    recognitionRef.current = recognition;
  }, []);

  useEffect(() => {
    if (!sessionId) return;
    setLocalSessions(upsertStoredChatSession(buildLocalSession(sessionId, messages.length ? messages : [INITIAL_MESSAGE])));
  }, [messages, sessionId]);

  async function loadSession(id) {
    if (id === sessionId) return;

    setSidebarOpen(false);
    setLoading(true);
    setSessionId(id);
    setStreamingMessage(null);

    const stored = getStoredChatSession(id);
    if (stored?.messages?.length) {
      setMessages(stored.messages);
    }

    try {
      const response = await chatAPI.getHistory(id);
      if (response.data && response.data.length > 0) {
        const hydrated = response.data.map((item, index, all) => {
          const retryText = item.role === 'assistant'
            ? all.slice(0, index).reverse().find(entry => entry.role === 'user')?.text
            : null;
          return { ...item, sources: item.sources || [], retryText };
        });
        setMessages(hydrated);
      } else if (!stored?.messages?.length) {
        setMessages([{ role: 'assistant', text: 'No history found for this chat yet.' }]);
      }
    } catch (error) {
      console.error(error);
      if (!stored?.messages?.length) {
        setMessages([{ role: 'assistant', text: 'Error loading history.' }]);
      }
    }

    setLoading(false);
  }

  async function sendMessage(rawText) {
    const text = (rawText || input).trim();
    if (!text || loading) return;

    const userMessage = { role: 'user', text };
    setMessages(previous => [...previous, userMessage]);
    setInput('');
    setLoading(true);
    setStreamingMessage(null);
    setSidebarOpen(false);

    try {
      let collected = '';
      let activeSessionId = sessionId;

      await chatAPI.sendStream({ message: text, session_id: sessionId }, {
        onSession: sid => {
          if (!activeSessionId && sid) {
            activeSessionId = sid;
            setSessionId(sid);
          }
        },
        onChunk: chunk => {
          collected += chunk;
          startTransition(() => {
            setStreamingMessage({ role: 'assistant', text: collected, retryText: text });
          });
        },
        onDone: data => {
          startTransition(() => {
            setMessages(previous => [
              ...previous,
              {
                role: 'assistant',
                text: collected || 'I could not generate a reply this time. Please try again.',
                sources: data?.sources || [],
                provider: data?.provider || null,
                confidence: data?.confidence || null,
                queryType: data?.query_type || null,
                userLevel: data?.user_level || null,
                retryText: text,
              },
            ]);
            setStreamingMessage(null);
          });
        },
      });

      if (user && activeSessionId) {
        setTimeout(() => {
          refreshRemoteSessions();
        }, 300);
      }
    } catch (error) {
      console.error(error);
      setStreamingMessage(null);
      setMessages(previous => [
        ...previous,
        {
          role: 'assistant',
          text: 'Sorry, I hit an issue while answering that. Try again or rephrase the request.',
          retryText: text,
        },
      ]);
    }

    setLoading(false);
  }

  function clearChat() {
    setMessages([INITIAL_MESSAGE]);
    setSessionId(null);
    setStreamingMessage(null);
    setSidebarOpen(false);
  }

  async function handleSaveSession(targetSession) {
    const targetId = targetSession?.id || sessionId;
    if (!targetId) return;

    setSavingSessionId(targetId);
    try {
      const title = targetId === sessionId
        ? buildSessionTitle(messages)
        : (targetSession?.title || 'Saved chat');

      if (user) {
        await chatAPI.saveSession(targetId, { title });
        await refreshRemoteSessions();
      }

      const localSnapshot = targetId === sessionId
        ? buildLocalSession(targetId, messages.length ? messages : [INITIAL_MESSAGE])
        : {
            ...targetSession,
            title,
            updatedAt: new Date().toISOString(),
          };
      setLocalSessions(upsertStoredChatSession(localSnapshot));
    } catch (error) {
      console.error('Could not save chat session', error);
    } finally {
      setSavingSessionId(null);
    }
  }

  async function handleDeleteSession(targetSession) {
    const targetId = targetSession?.id;
    if (!targetId) return;

    const confirmed = window.confirm('Delete this chat permanently? This will remove it from your history.');
    if (!confirmed) return;

    setDeletingSessionId(targetId);
    try {
      if (user) {
        await chatAPI.deleteSession(targetId);
        await refreshRemoteSessions();
      }

      setLocalSessions(clearStoredChatSession(targetId));

      if (targetId === sessionId) {
        clearChat();
      }
    } catch (error) {
      console.error('Could not delete chat session', error);
    } finally {
      setDeletingSessionId(null);
    }
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey && !loading) {
      event.preventDefault();
      sendMessage();
    }
  }

  function toggleListen() {
    if (!recognitionRef.current) return;
    if (isListening) {
      recognitionRef.current.stop();
      return;
    }
    recognitionRef.current.start();
    setIsListening(true);
  }

  async function handleCopy(text) {
    if (!text || !navigator.clipboard) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch (error) {
      console.error('Copy failed', error);
    }
  }

  const displayMessages = deferredMessages.map((message, index, allMessages) => ({
    ...message,
    retryText: message.retryText || (message.role === 'assistant'
      ? allMessages.slice(0, index).reverse().find(entry => entry.role === 'user')?.text
      : null),
  }));

  return (
    <div className="ev-chat-layout">
      <div className={`ev-chat-overlay ${sidebarOpen ? 'visible' : ''}`} onClick={() => setSidebarOpen(false)} />

      <ChatSidebar
        user={user}
        sessions={sessions}
        sessionId={sessionId}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onNewChat={clearChat}
        onSelectSession={loadSession}
        onSaveSession={handleSaveSession}
        onDeleteSession={handleDeleteSession}
        savingSessionId={savingSessionId}
        deletingSessionId={deletingSessionId}
      />

      <main className={`ev-chat-main ${isWelcomeState ? 'is-welcome' : ''}`}>
        <div className="ev-chat-toolbar">
          <button className="ev-chat-toolbar-btn" onClick={() => setSidebarOpen(previous => !previous)} type="button">
            {sidebarOpen ? <PanelLeftClose size={16} /> : <Menu size={16} />}
            History
          </button>
          <button className="ev-chat-toolbar-btn" onClick={clearChat} type="button">
            <Sparkles size={16} />
            New chat
          </button>
        </div>

        <div className="ev-chat-scroll-area" ref={chatScrollRef}>
          <div className="ev-chat-content-limit">
            {isWelcomeState && !loading && (
              <div className="ev-chat-welcome-panel">
                <div className="eyebrow">EViq Expert</div>
                <h1>Ask anything about EVs.</h1>
                <p>Recommendations, comparisons, charging, subsidies, and TCO in one place.</p>
              </div>
            )}

            {displayMessages
              .filter(message => !(message.role === 'assistant' && message.text === INITIAL_MESSAGE.text))
              .map((message, index) => (
              <ChatMessage
                key={`${message.role}-${index}-${message.text?.slice(0, 16)}`}
                msg={message}
                onCopy={handleCopy}
                onRetry={sendMessage}
              />
            ))}
            {streamingMessage ? <ChatMessage msg={streamingMessage} onCopy={handleCopy} onRetry={sendMessage} /> : null}
            {loading && !streamingMessage ? <TypingIndicator /> : null}
          </div>
        </div>

        <div className="ev-chat-input-sticky">
          <ChatComposer
            textareaRef={textareaRef}
            input={input}
            loading={loading}
            isListening={isListening}
            hasSpeechRecognition={hasSpeechRecognition}
            onInputChange={setInput}
            onKeyDown={handleKeyDown}
            onSubmit={sendMessage}
            onToggleListen={toggleListen}
            showSuggestions={messages.length <= 1}
          />
        </div>
      </main>

      <style>{`
        .ev-chat-layout {
          display: flex;
          min-height: calc(100vh - 64px);
          width: 100%;
          background:
            radial-gradient(circle at top left, rgba(14,165,164,0.08), transparent 28%),
            linear-gradient(180deg, var(--bg) 0%, color-mix(in srgb, var(--bg) 84%, white) 100%);
          overflow: hidden;
          position: relative;
        }

        .ev-chat-overlay {
          position: fixed;
          inset: 64px 0 0;
          background: rgba(5, 8, 18, 0.35);
          opacity: 0;
          pointer-events: none;
          transition: opacity 0.2s ease;
          z-index: 40;
        }
        .ev-chat-overlay.visible {
          opacity: 1;
          pointer-events: auto;
        }

        .ev-chat-sidebar {
          width: 300px;
          background: color-mix(in srgb, var(--bg-card) 88%, white);
          border-right: 1px solid var(--border);
          display: flex;
          flex-direction: column;
          padding: 18px;
          position: relative;
          z-index: 45;
          transition: transform 0.22s ease;
        }

        .ev-sidebar-close {
          display: none;
          position: absolute;
          top: 18px;
          right: 18px;
          width: 32px;
          height: 32px;
          border-radius: 8px;
          border: 1px solid var(--border);
          background: var(--bg-card);
          color: var(--text);
          align-items: center;
          justify-content: center;
        }

        .sidebar-header {
          display: flex;
          flex-direction: column;
          gap: 14px;
        }
        .sidebar-session-toolbar {
          display: flex;
          gap: 8px;
        }
        .sidebar-session-action {
          flex: 1;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          border-radius: 10px;
          border: 1px solid var(--border);
          background: color-mix(in srgb, var(--bg-card) 92%, white);
          color: var(--text);
          padding: 9px 12px;
          font-size: 12px;
          font-weight: 600;
        }
        .sidebar-session-action:hover:not(:disabled) {
          border-color: var(--accent);
          color: var(--accent);
        }
        .sidebar-session-action.danger:hover:not(:disabled) {
          color: #dc2626;
          border-color: #f3b5b5;
        }
        .sidebar-session-action:disabled {
          opacity: 0.55;
          cursor: not-allowed;
        }

        .ev-chat-brand-block {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .ev-chat-brand-icon {
          width: 40px;
          height: 40px;
          border-radius: 12px;
          background: var(--accent-soft);
          color: var(--accent);
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .ev-chat-brand-block strong {
          display: block;
          font-size: 14px;
          color: var(--text);
        }
        .ev-chat-brand-block span {
          display: block;
          font-size: 12px;
          color: var(--text-muted);
          margin-top: 2px;
        }

        .new-chat-btn,
        .ev-chat-toolbar-btn {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          border-radius: 12px;
          border: 1px solid var(--border);
          background: var(--bg-card);
          color: var(--text);
          padding: 11px 14px;
          font-size: 13px;
          font-weight: 600;
        }

        .sidebar-nav {
          flex: 1;
          margin-top: 20px;
          display: flex;
          flex-direction: column;
          gap: 8px;
          min-height: 0;
          overflow: auto;
        }
        .sidebar-nav .label {
          font-size: 11px;
          font-weight: 700;
          color: var(--text-muted);
          text-transform: uppercase;
          margin-bottom: 6px;
        }
        .nav-item {
          padding: 10px 12px;
          font-size: 13px;
          border-radius: 10px;
          color: var(--text-muted);
          text-align: left;
        }
        .nav-button {
          border: none;
          background: transparent;
        }
        .nav-item.active {
          background: var(--bg-muted);
          font-weight: 600;
          color: var(--text);
        }
        .nav-item.disabled {
          opacity: 0.6;
        }
        .session-history-row {
          display: flex;
          align-items: center;
          gap: 6px;
          border-radius: 12px;
        }
        .session-history-row.active {
          background: color-mix(in srgb, var(--bg-muted) 68%, white);
        }
        .session-history-select {
          flex: 1;
          min-width: 0;
        }
        .session-history-select.active {
          background: transparent;
        }
        .session-history-title {
          display: block;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .session-history-actions {
          display: flex;
          align-items: center;
          gap: 4px;
          opacity: 0;
          pointer-events: none;
          transition: opacity 0.18s ease;
          padding-right: 6px;
        }
        .session-history-row:hover .session-history-actions,
        .session-history-row.active .session-history-actions {
          opacity: 1;
          pointer-events: auto;
        }
        .session-action-btn {
          width: 28px;
          height: 28px;
          border-radius: 8px;
          border: 1px solid var(--border);
          background: var(--bg-card);
          color: var(--text-muted);
          display: inline-flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .session-action-btn:hover:not(:disabled) {
          color: var(--accent);
          border-color: var(--accent);
        }
        .session-action-btn.danger:hover:not(:disabled) {
          color: #dc2626;
          border-color: #f3b5b5;
        }
        .session-action-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .sidebar-user {
          border-top: 1px solid var(--border);
          padding-top: 12px;
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
        }
        .sidebar-user-minimal {
          margin-top: 12px;
          justify-content: space-between;
        }
        .sidebar-user-avatar {
          width: 28px;
          height: 28px;
          border-radius: 50%;
          background: var(--accent);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 11px;
          font-weight: 800;
          flex-shrink: 0;
        }
        .sidebar-user-meta {
          overflow: hidden;
          min-width: 0;
        }
        .sidebar-user-name {
          font-size: 12px;
          font-weight: 600;
          color: var(--text-muted);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .sidebar-user-email {
          font-size: 10px;
          color: var(--text-muted);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .sidebar-guest-copy {
          font-size: 12px;
          color: var(--text-muted);
          font-weight: 600;
        }
        .sidebar-login-link {
          font-size: 11px;
          color: var(--accent);
          font-weight: 700;
          text-decoration: none;
          display: flex;
          align-items: center;
          gap: 4px;
          margin-left: auto;
          padding: 6px 10px;
          border-radius: 999px;
          background: color-mix(in srgb, var(--accent-soft) 60%, white);
        }

        .ev-chat-main {
          flex: 1;
          display: flex;
          flex-direction: column;
          position: relative;
          min-width: 0;
          min-height: calc(100vh - 64px);
        }

        .ev-chat-toolbar {
          display: none;
          padding: 16px 16px 0;
          gap: 10px;
        }

        .ev-chat-scroll-area {
          flex: 1;
          overflow-y: auto;
          scrollbar-width: thin;
          padding: 28px 20px 192px;
          scroll-behavior: smooth;
          scroll-padding-bottom: 200px;
        }
        .ev-chat-content-limit {
          max-width: 860px;
          margin: 0 auto;
          width: 100%;
        }

        .ev-chat-main.is-welcome .ev-chat-scroll-area {
          padding-top: 12vh;
        }
        .ev-chat-main.is-welcome .ev-chat-content-limit {
          padding-bottom: 0;
        }

        .ev-chat-welcome-panel {
          max-width: 640px;
          margin: 0 auto 18px;
          text-align: center;
        }
        .ev-chat-welcome-panel .eyebrow {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          padding: 6px 12px;
          border-radius: 999px;
          background: var(--accent-soft);
          color: var(--accent-dark);
          font-size: 12px;
          font-weight: 700;
          margin-bottom: 14px;
        }
        .ev-chat-welcome-panel h1 {
          font-family: 'Space Grotesk', sans-serif;
          font-size: clamp(30px, 5vw, 48px);
          line-height: 1.04;
          letter-spacing: -0.8px;
          margin-bottom: 10px;
        }
        .ev-chat-welcome-panel p {
          max-width: 520px;
          margin: 0 auto;
          color: var(--text-muted);
          font-size: 14px;
          line-height: 1.65;
        }

        .ev-msg-row {
          display: flex;
          gap: 16px;
          margin-bottom: 18px;
          width: 100%;
        }
        .ev-msg-row.user {
          justify-content: flex-end;
        }
        .ev-avatar {
          width: 36px;
          height: 36px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .ev-avatar.bot {
          background: var(--accent-soft);
          color: var(--accent);
        }
        .ev-avatar.user {
          background: #20252e;
          color: white;
          box-shadow: 0 8px 18px rgba(0,0,0,0.15);
        }
        .ev-msg-bubble {
          max-width: 85%;
          line-height: 1.6;
          min-width: 0;
          overflow-wrap: anywhere;
        }
        .ev-msg-bubble.user {
          background: linear-gradient(135deg, #1f2937, #111827);
          padding: 14px 18px;
          border-radius: 20px;
          color: white;
          font-weight: 500;
          box-shadow: 0 16px 28px rgba(17,24,39,0.14);
        }
        .ev-msg-bubble.bot {
          font-size: 15px;
          color: var(--text);
        }
        .ev-msg-text,
        .ev-msg-markdown,
        .ev-msg-markdown p,
        .ev-msg-markdown li,
        .ev-msg-markdown code,
        .ev-msg-markdown strong {
          overflow-wrap: anywhere;
          word-break: break-word;
        }
        .ev-msg-markdown p {
          margin-bottom: 12px;
        }
        .ev-msg-markdown ul,
        .ev-msg-markdown ol {
          padding-left: 20px;
          margin: 0 0 12px;
        }
        .ev-msg-markdown pre {
          overflow-x: auto;
          padding: 12px 14px;
          border-radius: 12px;
          background: color-mix(in srgb, var(--bg-card) 92%, black 8%);
          margin-top: 12px;
        }
        .ev-msg-markdown code {
          font-size: 0.94em;
        }
        .highlight {
          color: var(--accent);
          font-weight: 700;
        }

        .ev-message-actions {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          margin-top: 12px;
        }
        .ev-inline-action {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 7px 12px;
          border-radius: 8px;
          background: var(--bg-card);
          border: 1px solid var(--border);
          color: var(--text-muted);
          font-size: 11px;
          font-weight: 600;
        }

        .ev-table-wrap {
          width: 100%;
          overflow-x: auto;
          margin-top: 16px;
          border-radius: 14px;
          border: 1px solid var(--border);
          background: var(--bg-card);
        }
        .ev-chat-table {
          width: 100%;
          border-collapse: separate;
          border-spacing: 0;
        }
        .ev-chat-table th {
          background: color-mix(in srgb, var(--bg-muted) 85%, white);
          padding: 14px 16px;
          text-align: left;
          font-size: 13px;
          font-weight: 700;
          color: var(--text);
          border-bottom: 1px solid var(--border);
        }
        .ev-chat-table td {
          padding: 14px 16px;
          border-bottom: 1px solid color-mix(in srgb, var(--border) 70%, white);
          font-size: 14px;
          color: var(--text-muted);
          line-height: 1.5;
        }
        .ev-chat-table tr:last-child td {
          border-bottom: none;
        }

        .ev-source-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
          gap: 12px;
          margin-top: 16px;
        }
        .ev-source-card {
          display: flex;
          gap: 10px;
          padding: 10px;
          border-radius: 12px;
          background: color-mix(in srgb, var(--bg-card) 92%, white);
          border: 1px solid var(--border);
          color: inherit;
          transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
        }
        .ev-source-card:hover {
          transform: translateY(-2px);
          border-color: var(--accent);
          box-shadow: 0 8px 24px rgba(14,165,164,0.12);
        }
        .ev-source-img {
          width: 44px;
          height: 44px;
          border-radius: 6px;
          object-fit: cover;
        }
        .ev-source-placeholder {
          width: 44px;
          height: 44px;
          background: var(--bg-muted);
          border-radius: 6px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--text-muted);
        }
        .ev-source-info .name {
          font-size: 12px;
          font-weight: 700;
          color: var(--text);
        }
        .ev-source-info .price {
          font-size: 11px;
          color: var(--text-muted);
        }
        .ev-source-info .view-hint {
          font-size: 10px;
          color: var(--accent);
          font-weight: 600;
          margin-top: 2px;
        }
        .source-match-reason {
          font-size: 10px;
          color: var(--text-muted);
          margin-top: 3px;
          text-transform: capitalize;
        }
        .ev-answer-meta {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
          margin-top: 10px;
        }
        .ev-answer-meta span {
          border: 1px solid var(--border);
          border-radius: 999px;
          color: var(--text-muted);
          font-size: 10px;
          font-weight: 700;
          padding: 4px 8px;
          text-transform: capitalize;
        }

        .typing-dots span {
          width: 6px;
          height: 6px;
          background: #ccc;
          border-radius: 50%;
          display: inline-block;
          animation: bounce 1.4s infinite;
          margin: 0 2px;
        }
        .typing-dots span:nth-child(2) {
          animation-delay: 0.2s;
        }
        .typing-dots span:nth-child(3) {
          animation-delay: 0.4s;
        }
        .typing-indicator-text {
          font-size: 13px;
          color: var(--text-muted);
          margin-bottom: 8px;
        }

        .ev-chat-input-sticky {
          position: sticky;
          bottom: 0;
          padding: 16px 20px calc(18px + env(safe-area-inset-bottom));
          background: linear-gradient(180deg, transparent 0%, color-mix(in srgb, var(--bg) 90%, white) 18%, color-mix(in srgb, var(--bg) 97%, white) 100%);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
          z-index: 20;
        }
        .ev-chat-input-limit {
          max-width: 860px;
          margin: 0 auto;
          width: 100%;
        }
        .ev-suggestion-row {
          display: flex;
          gap: 8px;
          margin-bottom: 12px;
          overflow-x: auto;
          scrollbar-width: none;
        }
        .suggestion-pill {
          white-space: nowrap;
          padding: 8px 16px;
          border-radius: 100px;
          background: color-mix(in srgb, var(--bg-card) 90%, white);
          border: 1px solid var(--border);
          font-size: 13px;
          color: var(--text-muted);
        }
        .ev-input-container {
          background: color-mix(in srgb, var(--bg-card) 94%, white);
          border: 1px solid var(--border);
          border-radius: 24px;
          padding: 10px 10px 10px 20px;
          display: flex;
          align-items: flex-end;
          gap: 12px;
          box-shadow: 0 22px 40px rgba(0,0,0,0.06);
        }
        .ev-input-container textarea {
          flex: 1;
          border: none;
          outline: none;
          resize: none;
          max-height: 200px;
          padding: 8px 0;
          font-size: 15px;
          color: var(--text);
          background: transparent;
          min-height: 24px;
        }
        .send-btn,
        .mic-btn {
          width: 42px;
          height: 42px;
          border-radius: 50%;
          border: none;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .send-btn {
          background: color-mix(in srgb, var(--bg-muted) 80%, white);
          color: var(--text-muted);
          cursor: not-allowed;
        }
        .send-btn.active {
          background: var(--accent);
          color: white;
          cursor: pointer;
          transform: translateY(-1px);
        }
        .mic-btn {
          background: transparent;
          color: var(--text-muted);
        }
        .mic-btn.active {
          color: #ef4444;
        }
        .disclaimer {
          text-align: center;
          font-size: 11px;
          color: var(--text-muted);
          margin-top: 10px;
        }

        @keyframes bounce {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.3); opacity: 0.5; }
        }

        @media (max-width: 960px) {
          .ev-chat-toolbar {
            display: flex;
          }
          .ev-chat-sidebar {
            position: fixed;
            inset: 64px auto 0 0;
            width: min(88vw, 320px);
            transform: translateX(-100%);
            box-shadow: var(--shadow-elevated);
          }
          .ev-chat-sidebar.open {
            transform: translateX(0);
          }
          .ev-sidebar-close {
            display: inline-flex;
          }
          .ev-chat-scroll-area {
            padding-top: 18px;
            padding-bottom: 184px;
          }
          .session-history-actions {
            opacity: 1;
            pointer-events: auto;
          }
        }

        @media (max-width: 640px) {
          .ev-chat-scroll-area {
            padding: 18px 14px 176px;
          }
          .ev-chat-input-sticky {
            padding: 14px;
          }
          .ev-msg-row {
            gap: 10px;
          }
          .ev-msg-bubble {
            max-width: 100%;
          }
          .ev-chat-welcome-panel h1 {
            font-size: clamp(30px, 9vw, 44px);
          }
          .ev-source-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
}

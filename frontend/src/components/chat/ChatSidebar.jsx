import { Link } from 'react-router-dom';
import { Bookmark, LogIn, RefreshCw, Sparkles, Trash2, X } from 'lucide-react';

export default function ChatSidebar({
  user,
  sessions,
  sessionId,
  isOpen,
  onClose,
  onNewChat,
  onSelectSession,
  onSaveSession,
  onDeleteSession,
  savingSessionId,
  deletingSessionId,
}) {
  const activeSession = sessions.find(session => session.id === sessionId) || null;

  return (
    <aside className={`ev-chat-sidebar ${isOpen ? 'open' : ''}`}>
      <div className="sidebar-header">
        <div className="ev-chat-brand-block">
          <div className="ev-chat-brand-icon"><Sparkles size={16} /></div>
          <div>
            <strong>EViq Expert</strong>
            <span>India EV dataset guidance</span>
          </div>
        </div>
        <button className="ev-sidebar-close" onClick={onClose} type="button">
          <X size={16} />
        </button>
        <button className="new-chat-btn" onClick={onNewChat} type="button">
          <RefreshCw size={14} /> New Chat
        </button>
        {activeSession ? (
          <div className="sidebar-session-toolbar">
            <button
              className="sidebar-session-action"
              onClick={() => onSaveSession(activeSession)}
              type="button"
              disabled={savingSessionId === activeSession.id || deletingSessionId === activeSession.id}
            >
              <Bookmark size={13} /> Save
            </button>
            <button
              className="sidebar-session-action danger"
              onClick={() => onDeleteSession(activeSession)}
              type="button"
              disabled={deletingSessionId === activeSession.id}
            >
              <Trash2 size={13} /> Delete
            </button>
          </div>
        ) : null}
      </div>

      <div className="sidebar-nav">
        <div className="label">History</div>
        <button className={`nav-item nav-button ${!sessionId ? 'active' : ''}`} onClick={onNewChat} type="button">
          New Chat
        </button>
        {sessions.length > 0 ? sessions.map(session => (
          <div key={session.id} className={`session-history-row ${sessionId === session.id ? 'active' : ''}`}>
            <button
              className={`nav-item nav-button session-history-select ${sessionId === session.id ? 'active' : ''}`}
              onClick={() => onSelectSession(session.id)}
              type="button"
            >
              <span className="session-history-title">{session.title || 'Untitled chat'}</span>
            </button>
            <div className="session-history-actions">
              <button
                className="session-action-btn"
                onClick={(event) => {
                  event.stopPropagation();
                  onSaveSession(session);
                }}
                type="button"
                title="Save chat"
                disabled={savingSessionId === session.id || deletingSessionId === session.id}
              >
                <Bookmark size={13} />
              </button>
              <button
                className="session-action-btn danger"
                onClick={(event) => {
                  event.stopPropagation();
                  onDeleteSession(session);
                }}
                type="button"
                title="Delete chat"
                disabled={deletingSessionId === session.id}
              >
                <Trash2 size={13} />
              </button>
            </div>
          </div>
        )) : (
          <div className="nav-item disabled">Your recent chats will appear here.</div>
        )}
      </div>

      <div className="sidebar-user sidebar-user-minimal">
        {user ? (
          <>
            <div className="sidebar-user-meta">
              <div className="sidebar-user-name">{user.full_name || 'User'}</div>
              <div className="sidebar-user-email">Signed in</div>
            </div>
          </>
        ) : (
          <>
            <span className="sidebar-guest-copy">Guest mode</span>
            <Link to="/login" className="sidebar-login-link">
              <LogIn size={12} /> Sign In
            </Link>
          </>
        )}
      </div>
    </aside>
  );
}

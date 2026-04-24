import { Link } from 'react-router-dom';
import { LogIn, RefreshCw, Sparkles, User, X } from 'lucide-react';

export default function ChatSidebar({
  user,
  sessions,
  sessionId,
  isOpen,
  onClose,
  onNewChat,
  onSelectSession,
}) {
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
      </div>

      <div className="sidebar-nav">
        <div className="label">History</div>
        <button className={`nav-item nav-button ${!sessionId ? 'active' : ''}`} onClick={onNewChat} type="button">
          New Chat
        </button>
        {sessions.length > 0 ? sessions.map(session => (
          <button
            key={session.id}
            className={`nav-item nav-button ${sessionId === session.id ? 'active' : ''}`}
            onClick={() => onSelectSession(session.id)}
            type="button"
          >
            {session.title || 'Untitled chat'}
          </button>
        )) : (
          <div className="nav-item disabled">Your recent chats will appear here.</div>
        )}
      </div>

      <div className="ev-chat-side-note">
        <div className="note-row"><Sparkles size={12} /> Retrieval-first EV guidance</div>
        <div className="note-row">Recommendations stay inside the current dataset and policy snapshot instead of inventing specs or prices.</div>
      </div>

      <div className="sidebar-user">
        {user ? (
          <>
            <div className="sidebar-user-avatar">{(user.full_name || user.email)[0].toUpperCase()}</div>
            <div className="sidebar-user-meta">
              <div className="sidebar-user-name">{user.full_name || 'User'}</div>
              <div className="sidebar-user-email">{user.email}</div>
            </div>
          </>
        ) : (
          <>
            <User size={14} />
            <span className="sidebar-guest-copy">Guest · local history saved in this browser</span>
            <Link to="/login" className="sidebar-login-link">
              <LogIn size={12} /> Sign In
            </Link>
          </>
        )}
      </div>
    </aside>
  );
}

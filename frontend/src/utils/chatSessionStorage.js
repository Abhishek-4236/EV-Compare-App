const STORAGE_KEY = 'eviq-chat-sessions-v1';
const STORAGE_LIMIT = 20;

export function readStoredChatSessions() {
  if (typeof window === 'undefined') return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeStoredChatSessions(sessions) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions.slice(0, STORAGE_LIMIT)));
}

export function upsertStoredChatSession(session) {
  const sessions = readStoredChatSessions().filter(item => item.id !== session.id);
  const next = [{ ...session }, ...sessions]
    .sort((a, b) => new Date(b.updatedAt || 0) - new Date(a.updatedAt || 0))
    .slice(0, STORAGE_LIMIT);
  writeStoredChatSessions(next);
  return next;
}

export function getStoredChatSession(sessionId) {
  return readStoredChatSessions().find(item => item.id === sessionId) || null;
}

export function clearStoredChatSession(sessionId) {
  const next = readStoredChatSessions().filter(item => item.id !== sessionId);
  writeStoredChatSessions(next);
  return next;
}

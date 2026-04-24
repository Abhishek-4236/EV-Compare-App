import { useState, useEffect, useRef } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import {
  Zap, Menu, X, Moon, Sun, MessageSquare, LogIn, LogOut,
  User, ChevronDown, Heart, Settings, Car, MapPin,
} from 'lucide-react';
import useAuth from '../store/useAuth';

// ── Primary links (always visible in desktop nav) ──────────────────────────
const PRIMARY_LINKS = [
  { to: '/browse',  label: 'Browse EVs' },
  { to: '/compare', label: 'Compare' },
  { to: '/chat',    label: 'AI Chat' },
];

// ── Secondary links (hidden behind "More ▾" dropdown) ──────────────────────
const MORE_LINKS = [
  { to: '/recommend',  label: '🎯 Recommend' },
  { to: '/subsidies',  label: '💰 Subsidies' },
  { to: '/tco',        label: '🧮 TCO Calculator' },
  { to: '/map',        label: '📍 Live Map' },
];

// All links (for mobile menu)
const ALL_LINKS = [...PRIMARY_LINKS, ...MORE_LINKS];

// ── "More" dropdown ─────────────────────────────────────────────────────────
function MoreDropdown() {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const close = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(o => !o)}
        className="ev-nav-link"
        style={{
          display: 'flex', alignItems: 'center', gap: 4,
          background: 'none', border: 'none', cursor: 'pointer',
          padding: '4px 2px', fontSize: 14, fontWeight: 500,
          color: 'var(--text-muted)',
        }}
      >
        More
        <ChevronDown size={14} style={{ transition: 'transform 0.2s', transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.96 }}
            transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
            style={{
              position: 'absolute', left: 0, top: 'calc(100% + 10px)',
              background: 'var(--bg-card)',
              backdropFilter: 'blur(20px)',
              border: '1px solid var(--border)',
              borderRadius: 14, padding: '6px',
              minWidth: 200,
              boxShadow: '0 16px 40px rgba(0,0,0,0.14)',
              zIndex: 200,
            }}
          >
            {MORE_LINKS.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                onClick={() => setOpen(false)}
                style={({ isActive }) => ({
                  display: 'block', padding: '9px 14px', borderRadius: 9,
                  fontSize: 13, fontWeight: 600, textDecoration: 'none',
                  color: isActive ? 'var(--accent)' : 'var(--text)',
                  background: isActive ? 'var(--accent-soft)' : 'transparent',
                  transition: 'background 0.15s',
                })}
              >
                {label}
              </NavLink>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── User account dropdown ────────────────────────────────────────────────────
function UserDropdown({ user, onLogout }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const close = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', close);
    return () => document.removeEventListener('mousedown', close);
  }, []);

  const initials = user.full_name
    ? user.full_name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase()
    : user.email[0].toUpperCase();

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          background: 'var(--accent-soft)', border: '1.5px solid var(--accent)',
          borderRadius: 99, padding: '5px 10px 5px 5px',
          cursor: 'pointer', color: 'var(--accent-dark)', transition: 'all 0.15s',
        }}
      >
        <div style={{
          width: 28, height: 28, borderRadius: '50%',
          background: 'var(--accent)', color: 'white',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 12, fontWeight: 800,
        }}>
          {initials}
        </div>
        <span style={{ fontSize: 13, fontWeight: 600, maxWidth: 100, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {user.full_name?.split(' ')[0] || 'Account'}
        </span>
        <ChevronDown size={14} style={{ transition: 'transform 0.2s', transform: open ? 'rotate(180deg)' : 'rotate(0)' }} />
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.96 }}
            transition={{ duration: 0.18, ease: [0.22, 1, 0.36, 1] }}
            style={{
              position: 'absolute', right: 0, top: 'calc(100% + 8px)',
              background: 'var(--bg-card)',
              backdropFilter: 'blur(20px)',
              WebkitBackdropFilter: 'blur(20px)',
              border: '1px solid var(--border)',
              borderRadius: 14, padding: '8px',
              minWidth: 200,
              boxShadow: '0 16px 40px rgba(0,0,0,0.16)',
              zIndex: 200,
            }}
          >
            <div style={{ padding: '8px 12px 10px', borderBottom: '1px solid var(--border)', marginBottom: 6 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)' }}>{user.full_name || 'User'}</div>
              <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 1 }}>{user.email}</div>
            </div>

            <Link
              to="/garage"
              onClick={() => setOpen(false)}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '9px 12px', borderRadius: 8, textDecoration: 'none',
                fontSize: 13, color: 'var(--text)', fontWeight: 500,
              }}
            >
              <Heart size={14} color="var(--accent)" /> My Garage
            </Link>

            {user.role === 'admin' && (
              <Link
                to="/admin"
                onClick={() => setOpen(false)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 8,
                  padding: '9px 12px', borderRadius: 8, textDecoration: 'none',
                  fontSize: 13, color: 'var(--text)', fontWeight: 500,
                }}
              >
                <Settings size={14} color="var(--accent)" /> Admin Panel
              </Link>
            )}

            <button
              onClick={() => { onLogout(); setOpen(false); }}
              style={{
                width: '100%', textAlign: 'left', padding: '9px 12px',
                borderRadius: 8, border: 'none', background: 'none', marginTop: 4,
                cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8,
                fontSize: 13, color: '#ef4444', fontWeight: 600, borderTop: '1px solid var(--border)',
              }}
            >
              <LogOut size={14} /> Sign Out
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [dark, setDark] = useState(() => localStorage.getItem('ev-theme') === 'dark');
  const [scrolled, setScrolled] = useState(false);
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const MobileMenuPanel = motion.div;

  useEffect(() => {
    const theme = dark ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ev-theme', theme);
  }, [dark]);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 18);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  function handleLogout() {
    logout();
    navigate('/');
  }

  return (
    <>
      <nav className={`ev-nav ${scrolled ? 'scrolled' : ''}`}>
        <div className="ev-nav-inner">
          {/* Brand */}
          <Link to="/" className="ev-brand">
            <Zap size={20} fill="currentColor" />
            EViq<span style={{ fontWeight: 400, fontSize: '14px', marginLeft: 2, opacity: 0.6 }}>India</span>
          </Link>

          {/* Desktop links */}
          <div className="ev-nav-links">
            {PRIMARY_LINKS.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) => `ev-nav-link ${isActive ? 'active' : ''}`}
              >
                {label}
              </NavLink>
            ))}

            {/* More dropdown */}
            <MoreDropdown />

            {/* Garage — always visible, guests redirect to login */}
            <NavLink
              to={user ? '/garage' : '/login'}
              className={({ isActive }) => `ev-nav-link ${isActive ? 'active' : ''}`}
              style={{ display: 'flex', alignItems: 'center', gap: 5 }}
            >
              <Heart size={14} />
              Garage
            </NavLink>
          </div>

          {/* Actions */}
          <div className="ev-nav-actions">
            <button
              className="ev-btn-icon ev-btn"
              onClick={() => setDark(d => !d)}
              title="Toggle dark mode"
              aria-label="Toggle dark mode"
            >
              {dark ? <Sun size={16} /> : <Moon size={16} />}
            </button>

            {user ? (
              <UserDropdown user={user} onLogout={handleLogout} />
            ) : (
              <>
                <Link to="/login" className="ev-btn ev-btn-sm" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <LogIn size={14} /> Login
                </Link>
                <Link to="/chat" className="ev-btn ev-btn-primary ev-btn-sm ev-nav-cta">
                  <MessageSquare size={14} /> Ask EViq
                </Link>
              </>
            )}

            <button
              className="ev-menu-btn"
              onClick={() => setMenuOpen(o => !o)}
              aria-label="Toggle menu"
            >
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile menu */}
      <AnimatePresence>
        {menuOpen && (
          <MobileMenuPanel
            className="ev-mobile-menu open"
            initial={{ opacity: 0, y: -14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
          >
            {ALL_LINKS.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                onClick={() => setMenuOpen(false)}
                className={({ isActive }) => `ev-mobile-link ${isActive ? 'active' : ''}`}
              >
                {label}
              </NavLink>
            ))}

            {/* Garage in mobile menu */}
            <NavLink
              to={user ? '/garage' : '/login'}
              onClick={() => setMenuOpen(false)}
              className={({ isActive }) => `ev-mobile-link ${isActive ? 'active' : ''}`}
            >
              ❤️ My Garage
            </NavLink>

            <div style={{ marginTop: '8px', padding: '0 16px', display: 'flex', flexDirection: 'column', gap: 8 }}>
              {!user && (
                <Link to="/login" className="ev-btn" style={{ justifyContent: 'center' }} onClick={() => setMenuOpen(false)}>
                  <LogIn size={14} /> Login / Sign Up
                </Link>
              )}
              {user && (
                <button className="ev-btn" style={{ justifyContent: 'center', color: '#ef4444' }} onClick={() => { handleLogout(); setMenuOpen(false); }}>
                  <LogOut size={14} /> Sign Out ({user.full_name?.split(' ')[0] || 'User'})
                </button>
              )}
              <button className="ev-btn" style={{ justifyContent: 'center' }} onClick={() => setDark(d => !d)}>
                {dark ? <><Sun size={16} /> Light Mode</> : <><Moon size={16} /> Dark Mode</>}
              </button>
            </div>
          </MobileMenuPanel>
        )}
      </AnimatePresence>
    </>
  );
}

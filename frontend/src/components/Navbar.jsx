import { useState, useEffect } from 'react';
import { Link, NavLink, useLocation } from 'react-router-dom';
import { Zap, Menu, X, Moon, Sun, GitCompare, MessageSquare } from 'lucide-react';

const NAV_LINKS = [
  { to: '/browse', label: 'Browse EVs' },
  { to: '/compare', label: 'Compare' },
  { to: '/recommend', label: 'Recommend' },
  { to: '/subsidies', label: 'Subsidies & TCO' },
  { to: '/stations', label: 'Charge Map' },
  { to: '/chat', label: 'AI Chat' },
];

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [dark, setDark] = useState(() => localStorage.getItem('ev-theme') === 'dark');
  const location = useLocation();

  useEffect(() => {
    const theme = dark ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('ev-theme', theme);
  }, [dark]);

  useEffect(() => setMenuOpen(false), [location]);

  return (
    <>
      <nav className="ev-nav">
        <div className="ev-nav-inner">
          {/* Brand */}
          <Link to="/" className="ev-brand">
            <Zap size={20} fill="currentColor" />
            EViq<span style={{ fontWeight: 400, fontSize: '14px', marginLeft: 2, opacity: 0.6 }}>India</span>
          </Link>

          {/* Desktop Links */}
          <div className="ev-nav-links">
            {NAV_LINKS.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) => `ev-nav-link ${isActive ? 'active' : ''}`}
              >
                {label}
              </NavLink>
            ))}
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
            <Link to="/compare" className="ev-btn ev-btn-primary ev-btn-sm" style={{ display: 'none' }}>
              <GitCompare size={14} /> Compare
            </Link>
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

      {/* Mobile Menu */}
      <div className={`ev-mobile-menu ${menuOpen ? 'open' : ''}`}>
        {NAV_LINKS.map(({ to, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `ev-mobile-link ${isActive ? 'active' : ''}`}
          >
            {label}
          </NavLink>
        ))}
        <div style={{ marginTop: '8px', padding: '0 16px' }}>
          <button className="ev-btn ev-btn-primary" style={{ width: '100%', justifyContent: 'center' }} onClick={() => setDark(d => !d)}>
            {dark ? <><Sun size={16} /> Light Mode</> : <><Moon size={16} /> Dark Mode</>}
          </button>
        </div>
      </div>
    </>
  );
}

import { Link } from 'react-router-dom';
import { Zap, GitFork } from 'lucide-react';

const FOOTER_LINKS = {
  'Platform': [
    { to: '/browse', label: 'Browse EVs' },
    { to: '/compare', label: 'Compare' },
    { to: '/recommend', label: 'Recommend' },
    { to: '/chat', label: 'AI Chat' },
  ],
  'Tools': [
    { to: '/subsidies', label: 'Subsidies & TCO' },
    { to: '/stations', label: 'Charge Map' },
  ],
};

export default function Footer() {
  return (
    <footer className="ev-footer">
      <div className="ev-footer-inner">
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', gap: 40, marginBottom: 40 }}>
          {/* Brand */}
          <div>
            <div className="ev-brand" style={{ marginBottom: 12 }}>
              <Zap size={18} fill="currentColor" />
              EViq<span style={{ fontWeight: 400, fontSize: '13px', marginLeft: 2, opacity: 0.6 }}>India</span>
            </div>
            <p style={{ color: 'var(--text-muted)', fontSize: 14, lineHeight: 1.7, maxWidth: 300 }}>
              India's most comprehensive EV comparison platform. Compare, calculate, and find the perfect electric vehicle for your needs.
            </p>
            <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
              <a href="https://github.com" target="_blank" rel="noreferrer" className="ev-btn ev-btn-icon" aria-label="GitHub">
                <GitFork size={16} />
              </a>
            </div>
          </div>

          {/* Links */}
          {Object.entries(FOOTER_LINKS).map(([group, links]) => (
            <div key={group}>
              <div style={{ fontWeight: 700, fontSize: 13, marginBottom: 14, color: 'var(--text)' }}>{group}</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {links.map(({ to, label }) => (
                  <Link key={to} to={to} style={{ color: 'var(--text-muted)', fontSize: 14, transition: 'color 0.15s' }}
                    onMouseEnter={e => e.target.style.color = 'var(--accent)'}
                    onMouseLeave={e => e.target.style.color = 'var(--text-muted)'}
                  >
                    {label}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
          <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>
            © 2026 EViq India — Open source EV platform for India. Built at VBIT.
          </p>
          <p style={{ color: 'var(--text-muted)', fontSize: 12 }}>
            Data sourced from industry datasets. Verify with dealers.
          </p>
        </div>
      </div>
    </footer>
  );
}

import { Link } from 'react-router-dom';
import { GitCompare, X, ChevronRight } from 'lucide-react';

export default function CompareBar({ selected, onRemove, onClear }) {
  if (selected.length === 0) return null;

  return (
    <div className="ev-floating-compare-pill">
      <div className="ev-compare-pill-content">
        <div className="ev-compare-pill-icon">
          <GitCompare size={20} />
          <span className="ev-compare-badge">{selected.length}</span>
        </div>
        
        <div className="ev-compare-selected-list">
          {selected.map(v => (
            <div key={v.id} className="ev-selected-mini-chip">
              <span className="name">{v.model}</span>
              <button onClick={() => onRemove(v.id)} className="remove-btn">
                <X size={12} />
              </button>
            </div>
          ))}
        </div>

        <div className="ev-compare-pill-actions">
          {selected.length >= 2 ? (
            <Link
              to={`/compare?ids=${selected.map(v => v.id).join(',')}`}
              className="ev-btn ev-btn-primary ev-btn-sm ev-compare-submit"
            >
              Compare Now <ChevronRight size={14} />
            </Link>
          ) : (
            <span className="ev-compare-hint">Select {2 - selected.length} more</span>
          )}
          <button className="ev-clear-all" onClick={onClear}>Clear</button>
        </div>
      </div>

      <style>{`
        .ev-floating-compare-pill {
          position: fixed;
          bottom: 24px;
          left: 50%;
          transform: translateX(-50%);
          z-index: 1000;
          width: auto;
          max-width: 90vw;
          animation: slideUp 0.4s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .ev-compare-pill-content {
          background: rgba(255, 255, 255, 0.7);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.3);
          border-radius: 100px;
          padding: 8px 12px 8px 20px;
          display: flex;
          align-items: center;
          gap: 16px;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }

        .ev-compare-pill-icon {
          position: relative;
          color: var(--accent);
          display: flex;
          align-items: center;
        }

        .ev-compare-badge {
          position: absolute;
          top: -8px;
          right: -10px;
          background: var(--accent);
          color: white;
          font-size: 10px;
          font-weight: 800;
          min-width: 18px;
          height: 18px;
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 2px solid white;
        }

        .ev-compare-selected-list {
          display: flex;
          gap: 8px;
          overflow-x: auto;
          scrollbar-width: none;
          max-width: 300px;
        }
        .ev-compare-selected-list::-webkit-scrollbar { display: none; }

        .ev-selected-mini-chip {
          background: white;
          border: 1px solid var(--border);
          padding: 4px 10px;
          border-radius: 20px;
          display: flex;
          align-items: center;
          gap: 6px;
          white-space: nowrap;
        }
        .ev-selected-mini-chip .name {
          font-size: 12px;
          font-weight: 600;
          color: var(--text);
        }
        .ev-selected-mini-chip .remove-btn {
          background: var(--bg-muted);
          border: none;
          border-radius: 50%;
          width: 16px;
          height: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          color: var(--text-muted);
        }

        .ev-compare-pill-actions {
          display: flex;
          align-items: center;
          gap: 12px;
          border-left: 1px solid var(--border);
          padding-left: 16px;
        }

        .ev-compare-submit {
          border-radius: 50px !important;
          padding: 8px 16px !important;
          font-weight: 700 !important;
          display: flex;
          align-items: center;
          gap: 4px;
        }

        .ev-compare-hint {
          font-size: 12px;
          color: var(--text-muted);
          font-weight: 600;
        }

        .ev-clear-all {
          background: none;
          border: none;
          color: var(--text-muted);
          font-size: 12px;
          font-weight: 600;
          cursor: pointer;
          text-decoration: underline;
        }

        @keyframes slideUp {
          from { transform: translate(-50%, 40px); opacity: 0; }
          to { transform: translate(-50%, 0); opacity: 1; }
        }
      `}</style>
    </div>
  );
}

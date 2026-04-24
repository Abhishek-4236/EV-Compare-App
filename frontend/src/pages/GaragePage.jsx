import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { garageAPI, vehicleAPI } from '../services/api';
import { Trash2, ArrowRight, Heart, PlusCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import useAuth from '../store/useAuth';

const MotionDiv = motion.div;

// ── Category config ──────────────────────────────────────────────────────────
const CATEGORIES = [
  { key: '2W', label: 'Bikes & Scooters', icon: '🛵', accent: '#f59e0b', bg: '#fffbeb' },
  { key: '3W', label: 'Auto Rickshaws', icon: '🛺', accent: '#3b82f6', bg: '#eff6ff' },
  { key: '4W', label: 'Cars', icon: '🚗', accent: '#10b981', bg: '#ecfdf5' },
  { key: 'Truck', label: 'Trucks', icon: '🚛', accent: '#ec4899', bg: '#fdf2f8' },
  { key: 'Bus', label: 'Buses', icon: '🚌', accent: '#8b5cf6', bg: '#f5f3ff' },
  { key: 'other', label: 'Other', icon: '⚡', accent: '#6b7280', bg: '#f9fafb' },
];

function getCategoryKey(vehicle) {
  if (!vehicle) return 'other';
  const cat = vehicle.category?.trim();
  if (['2W', '3W', '4W', 'Truck', 'Bus'].includes(cat)) return cat;
  const t = (vehicle.vehicle_type || '').toLowerCase();
  if (t.includes('truck')) return 'Truck';
  if (t.includes('bus')) return 'Bus';
  if (t.includes('auto')) return '3W';
  if (t.includes('scooter') || t.includes('bike') || t.includes('motor')) return '2W';
  return '4W';
}

// ── Guest wall ───────────────────────────────────────────────────────────────
function GuestWall() {
  return (
    <div style={{ paddingTop: 100, paddingBottom: 80, minHeight: '80vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <div style={{
        textAlign: 'center', maxWidth: 400,
        border: '1px solid var(--border)', borderRadius: 20,
        padding: '48px 40px', background: 'var(--bg-card)',
        boxShadow: '0 4px 24px rgba(0,0,0,0.06)',
      }}>
        <span style={{ fontSize: 40 }}>🔒</span>
        <h2 style={{ fontSize: 18, fontWeight: 700, margin: '14px 0 8px', color: 'var(--text)' }}>
          Sign in to view your Garage
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: 13, lineHeight: 1.65, marginBottom: 24 }}>
          Save your favourite EVs and comparisons — accessible anytime.
        </p>
        <Link to="/login" className="ev-btn ev-btn-primary ev-btn-sm" style={{ padding: '9px 28px' }}>
          Sign In
        </Link>
      </div>
    </div>
  );
}

// ── Single vehicle row inside a category ─────────────────────────────────────
function GarageRow({ item, vehiclesMap, onRemove }) {
  const ids = item.vehicle_ids.split(',').map(Number);
  const vehicles = ids.map(id => vehiclesMap[id]).filter(Boolean);
  const v = vehicles[0];
  const isComparison = vehicles.length > 1;

  return (
    <MotionDiv
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '8px 12px', background: 'var(--bg-card)',
        borderRadius: 12, border: '1px solid var(--border)',
        boxShadow: '0 2px 8px rgba(0,0,0,0.02)',
      }}
    >
      <div style={{
        width: 36, height: 36, borderRadius: 8, flexShrink: 0,
        background: 'var(--bg-muted)', display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 18, overflow: 'hidden'
      }}>
        {v?.image_url
          ? <img src={v.image_url} alt={v.model} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          : CATEGORIES.find(c => c.key === getCategoryKey(v))?.icon || '⚡'}
      </div>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 2 }}>
          <h3 style={{ fontSize: 14, fontWeight: 700, margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {item.name || (v ? `${v.brand} ${v.model}` : 'Saved Item')}
          </h3>
          {isComparison && (
            <span style={{ fontSize: 9, fontWeight: 800, background: 'var(--accent)', color: 'white', padding: '1px 6px', borderRadius: 99, textTransform: 'uppercase' }}>VS</span>
          )}
        </div>
        <div style={{ fontSize: 12, color: 'var(--text-muted)', display: 'flex', gap: 4, alignItems: 'center' }}>
          {isComparison ? (
            <span>{vehicles.map(x => x.model).join(' vs ')}</span>
          ) : (
            <>
              {v?.brand} • ₹{v ? (v.approx_price_inr / 100000).toFixed(1) : '—'}L {v?.range_km ? `• ${v.range_km} km` : ''}
            </>
          )}
        </div>
      </div>

      <Link
        to={isComparison ? `/compare?ids=${item.vehicle_ids}` : `/vehicle/${ids[0]}`}
        className="ev-btn ev-btn-sm ev-btn-primary"
        style={{ padding: '6px 12px', fontSize: 12, borderRadius: 8 }}
      >
        View
      </Link>
      <button
        onClick={() => onRemove(item.id)}
        style={{
          width: 28, height: 28, borderRadius: 6, border: 'none', background: 'transparent',
          color: 'var(--text-muted)', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: '0.2s', padding: 0
        }}
        onMouseEnter={e => { e.currentTarget.style.color = '#ef4444'; e.currentTarget.style.background = '#ef444415'; }}
        onMouseLeave={e => { e.currentTarget.style.color = 'var(--text-muted)'; e.currentTarget.style.background = 'transparent'; }}
      >
        <Trash2 size={14} />
      </button>
    </MotionDiv>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────
export default function GaragePage() {
  const [items, setItems] = useState([]);
  const [vehiclesMap, setVehiclesMap] = useState({});
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    if (user) fetchGarage();
    else setLoading(false);
  }, [user]);

  async function fetchGarage() {
    try {
      const { data } = await garageAPI.get();
      setItems(data);
      const allIds = [...new Set(data.flatMap(item => item.vehicle_ids.split(',').map(Number)))];
      const results = await Promise.all(allIds.map(id => vehicleAPI.getById(id).catch(() => null)));
      const map = {};
      results.forEach(res => { if (res?.data) map[res.data.id] = res.data; });
      setVehiclesMap(map);
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }

  async function removeItem(id) {
    try {
      await garageAPI.remove(id);
      setItems(prev => prev.filter(i => i.id !== id));
    } catch { /* ignore */ }
  }

  if (!user) return <GuestWall />;

  // Group items by category
  const grouped = {};
  items.forEach(item => {
    const firstId = Number(item.vehicle_ids.split(',')[0]);
    const v = vehiclesMap[firstId];
    const catKey = getCategoryKey(v);
    if (!grouped[catKey]) grouped[catKey] = [];
    grouped[catKey].push(item);
  });

  return (
    <div className="ev-shell">
      <MotionDiv
        initial={{ opacity: 0, y: 18 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
        className="ev-page-hero"
        style={{ marginTop: 24, marginBottom: 22 }}
      >
        <div className="ev-page-hero-copy">
          <div className="ev-section-label">PERSONAL COLLECTION</div>
          <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 'clamp(28px, 5vw, 44px)', fontWeight: 800, color: 'var(--text)', letterSpacing: '-1px', marginBottom: 8 }}>
            My Garage
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 15, lineHeight: 1.75, maxWidth: 640 }}>
            Your saved configurations, favorites, and instantly accessible comparisons in one clean space.
          </p>
        </div>
        <div className="ev-page-hero-metrics">
          <div className="ev-page-metric">
            <strong>{loading ? '...' : items.length}</strong>
            <span>saved vehicles</span>
          </div>
          <Link to="/browse" className="ev-btn ev-btn-primary" style={{ height: 48, padding: '0 24px', alignSelf: 'flex-start' }}>
            + Add EV
          </Link>
        </div>
      </MotionDiv>
      <div style={{ paddingTop: 4, marginBottom: 20 }}>

        {/* Clean small lists instead of boxes */}
        {loading ? (
          <div style={{ display: 'grid', gap: 10 }}>
            {[1, 2].map(i => <div key={i} className="ev-skeleton" style={{ height: 52, borderRadius: 12 }} />)}
          </div>

        ) : items.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 20px' }}>
            <Heart size={48} color="var(--border)" style={{ opacity: 0.5, marginBottom: 16 }} />
            <h3 style={{ fontSize: 18, marginBottom: 8 }}>Garage is empty</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>You haven't saved any vehicles yet.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
            {CATEGORIES.filter(c => grouped[c.key]?.length > 0).map(cat => (
              <div key={cat.key}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12, paddingLeft: 4 }}>
                   <span style={{ fontSize: 16 }}>{cat.icon}</span>
                   <h2 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>{cat.label}</h2>
                   <span style={{ background: 'var(--bg-muted)', padding: '2px 8px', borderRadius: 99, fontSize: 11, fontWeight: 600, color: 'var(--text-muted)' }}>
                     {grouped[cat.key].length}
                   </span>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: 12 }}>
                  <AnimatePresence>
                    {grouped[cat.key].map(item => (
                      <GarageRow key={item.id} item={item} vehiclesMap={vehiclesMap} onRemove={removeItem} />
                    ))}
                  </AnimatePresence>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

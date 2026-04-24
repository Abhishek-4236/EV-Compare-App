import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { vehicleAPI } from '../services/api';
import VehicleCard from '../components/VehicleCard';
import useCompare from '../store/useCompare';
import { X } from 'lucide-react';

const TABS = [
  { label: 'All', category: '', icon: '⚡' },
  { label: '2-Wheelers', category: '2W', icon: '🛵' },
  { label: 'Cars', category: '4W', icon: '🚗' },
  { label: '3-Wheelers', category: '3W', icon: '🛺' },
  { label: 'Trucks', category: 'Truck', icon: '🚛' },
  { label: 'Buses', category: 'Bus', icon: '🚌' },
];

const SORT_OPTIONS = [
  { value: 'overall_rating', label: 'Rating ↓' },
  { value: 'approx_price_inr', label: 'Price ↑' },
  { value: 'range_km', label: 'Range ↓' },
  { value: 'battery_kwh', label: 'Battery ↓' },
];

export default function BrowsePage() {
  const [searchParams] = useSearchParams();
  const MotionDiv = motion.div;
  const [vehicles, setVehicles] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const { compareItems, toggleCompare } = useCompare();

  const [filters, setFilters] = useState({
    category: searchParams.get('category') || '',
    sort_by: 'overall_rating',
    sort_order: 'DESC',
    max_price: 20000000,
    min_range: 0,
    page: 1,
    limit: 20,
  });

  const fetchVehicles = useCallback(async () => {
    setLoading(true);
    try {
      const params = { ...filters };
      if (!params.category) delete params.category;
      if (params.max_price >= 20000000) delete params.max_price;
      if (params.min_range <= 0) delete params.min_range;
      const res = await vehicleAPI.getAll(params);
      setVehicles(res.data.vehicles || []);
      setTotal(res.data.total || 0);
    } catch {
      setVehicles([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { fetchVehicles(); }, [fetchVehicles]);

  function setFilter(key, val) {
    setFilters(f => ({ ...f, [key]: val, page: 1 }));
  }

  function setPage(newPage) {
    setFilters(f => ({ ...f, page: newPage }));
  }

  function handleToggleCompare(id) {
    const v = vehicles.find(x => x.id === id);
    if (v) toggleCompare(v);
  }

  function isSelected(id) { return compareItems.some(x => x.id === id); }

  const activeSummary = [
    filters.category && TABS.find(tab => tab.category === filters.category)?.label,
    filters.max_price < 20000000 && `Under ₹${(filters.max_price / 100000).toFixed(1)}L`,
    filters.min_range > 0 && `${filters.min_range}+ km`,
    filters.sort_by !== 'overall_rating' && SORT_OPTIONS.find(option => option.value === filters.sort_by)?.label,
  ].filter(Boolean);

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
          <div className="ev-section-label">Browse The Catalog</div>
          <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 'clamp(28px, 5vw, 44px)', fontWeight: 800, color: 'var(--text)', letterSpacing: '-1px', marginBottom: 8 }}>
            Explore the India EV market by segment, budget, and range.
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 15, lineHeight: 1.75, maxWidth: 640 }}>
            Narrow the catalog quickly, shortlist what looks promising, and jump into compare or vehicle details without losing context.
          </p>
        </div>
        <div className="ev-page-hero-metrics">
          <div className="ev-page-metric">
            <strong>{loading ? '...' : total}</strong>
            <span>matching models</span>
          </div>
          <div className="ev-page-metric">
            <strong>{compareItems.length}</strong>
            <span>selected to compare</span>
          </div>
        </div>
      </MotionDiv>

      <div style={{ paddingTop: 4, marginBottom: 20 }}>
        <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 28, fontWeight: 800, color: 'var(--text)', letterSpacing: '-0.5px', marginBottom: 4 }}>
          Browse EVs
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 15 }}>
          {loading ? 'Loading...' : `${total} models found across all segments`}
        </p>
      </div>

      <div className="ev-tabs">
        {TABS.map(t => (
          <button
            key={t.category}
            className={`ev-tab ${filters.category === t.category ? 'active' : ''}`}
            onClick={() => setFilter('category', t.category)}
          >
            {t.icon} {t.label}
          </button>
        ))}
      </div>

      <div className="ev-filter-summary">
        <span className="label">Active filters</span>
        {activeSummary.length ? activeSummary.map(item => (
          <span key={item} className="ev-chip active">{item}</span>
        )) : <span className="empty">Showing the full catalog right now.</span>}
      </div>

      <div className="ev-filter-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: '1 1 200px' }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>Sort by:</span>
          <select
            className="ev-select"
            value={filters.sort_by}
            onChange={e => setFilter('sort_by', e.target.value)}
            style={{ flex: 1 }}
          >
            {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: '1 1 200px' }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
            Max: ₹{(filters.max_price / 100000).toFixed(0)}L
          </span>
          <input
            type="range" min={50000} max={20000000} step={50000}
            value={filters.max_price}
            onChange={e => setFilter('max_price', parseInt(e.target.value))}
            style={{ flex: 1, accentColor: 'var(--accent)' }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flex: '1 1 200px' }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
            Range ≥ {filters.min_range}km
          </span>
          <input
            type="range" min={0} max={600} step={10}
            value={filters.min_range}
            onChange={e => setFilter('min_range', parseInt(e.target.value))}
            style={{ flex: 1, accentColor: 'var(--accent)' }}
          />
        </div>

        <button
          className="ev-btn ev-btn-sm"
          onClick={() => setFilters(f => ({ ...f, max_price: 20000000, min_range: 0, sort_by: 'overall_rating', page: 1 }))}
        >
          <X size={14} /> Reset
        </button>
      </div>

      {loading ? (
        <div className="ev-grid-auto">
          {[...Array(12)].map((_, i) => (
            <div key={i} style={{ borderRadius: 14, overflow: 'hidden' }}>
              <div className="ev-skeleton" style={{ height: 160 }} />
              <div style={{ padding: 14, background: 'var(--bg-card)', border: '1px solid var(--border)', borderTop: 0, borderRadius: '0 0 14px 14px' }}>
                <div className="ev-skeleton" style={{ height: 12, width: '50%', marginBottom: 8 }} />
                <div className="ev-skeleton" style={{ height: 18, width: '40%', marginBottom: 10 }} />
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                  <div className="ev-skeleton" style={{ height: 40 }} />
                  <div className="ev-skeleton" style={{ height: 40 }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : vehicles.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '80px 20px' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🔍</div>
          <h3 style={{ fontWeight: 700, fontSize: 20, marginBottom: 8, color: 'var(--text)' }}>No EVs found</h3>
          <p style={{ color: 'var(--text-muted)', marginBottom: 20 }}>Try adjusting your filters or resetting them.</p>
          <button className="ev-btn ev-btn-primary" onClick={() => setFilters(f => ({ ...f, max_price: 20000000, min_range: 0, category: '', page: 1 }))}>
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="ev-grid-auto">
          {vehicles.map(v => (
            <VehicleCard
              key={v.id}
              vehicle={v}
              onCompareToggle={handleToggleCompare}
              isSelected={isSelected(v.id)}
            />
          ))}
        </div>
      )}

      {total > filters.limit && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 8, marginTop: 32, paddingBottom: compareItems.length > 0 ? 80 : 20 }}>
          <button className="ev-btn ev-btn-sm" disabled={filters.page <= 1} onClick={() => setPage(filters.page - 1)}>← Prev</button>
          {Array.from({ length: Math.ceil(total / filters.limit) }, (_, i) => i + 1).map(p => (
            <button
              key={p}
              className={`ev-btn ev-btn-sm ${filters.page === p ? 'ev-btn-primary' : ''}`}
              onClick={() => setPage(p)}
              style={{ minWidth: 36 }}
            >{p}</button>
          ))}
          <button className="ev-btn ev-btn-sm" disabled={filters.page * filters.limit >= total} onClick={() => setPage(filters.page + 1)}>Next →</button>
        </div>
      )}

      {/* Adding extra spacer if no pagination but compare bar is active to prevent overlapping with content */}
      {!(total > filters.limit) && compareItems.length > 0 && <div style={{ height: 80 }} />}
    </div>
  );
}

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { vehicleAPI } from '../services/api';
import VehicleCard from '../components/VehicleCard';
import CompareBar from '../components/CompareBar';
import { Search, SlidersHorizontal, X } from 'lucide-react';

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
  const [searchParams, setSearchParams] = useSearchParams();
  const [vehicles, setVehicles] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [compareItems, setCompareItems] = useState([]);
  const [showFilters, setShowFilters] = useState(false);

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
    } catch (e) {
      setVehicles([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => { fetchVehicles(); }, [fetchVehicles]);

  function setFilter(key, val) {
    setFilters(f => ({ ...f, [key]: val, page: 1 }));
  }

  function toggleCompare(id) {
    const v = vehicles.find(x => x.id === id);
    if (!v) return;
    setCompareItems(prev => {
      if (prev.find(x => x.id === id)) return prev.filter(x => x.id !== id);
      if (prev.length >= 4) return prev;
      return [...prev, v];
    });
  }

  function isSelected(id) { return compareItems.some(x => x.id === id); }

  return (
    <div className="ev-shell">
      {/* Header */}
      <div style={{ paddingTop: 32, marginBottom: 20 }}>
        <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 28, fontWeight: 800, color: 'var(--text)', letterSpacing: '-0.5px', marginBottom: 4 }}>
          Browse EVs
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: 15 }}>
          {loading ? 'Loading...' : `${total} models found across all segments`}
        </p>
      </div>

      {/* Category Tabs */}
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

      {/* Filter Bar */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 12,
        padding: '12px 16px',
        display: 'flex',
        gap: 12,
        alignItems: 'center',
        flexWrap: 'wrap',
        marginBottom: 20,
      }}>
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

      {/* Grid */}
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
              onCompareToggle={toggleCompare}
              isSelected={isSelected(v.id)}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {total > filters.limit && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 32 }}>
          <button className="ev-btn ev-btn-sm" disabled={filters.page <= 1} onClick={() => setFilter('page', filters.page - 1)}>← Prev</button>
          <span style={{ padding: '7px 14px', fontSize: 14, color: 'var(--text-muted)' }}>
            Page {filters.page} of {Math.ceil(total / filters.limit)}
          </span>
          <button className="ev-btn ev-btn-sm" disabled={filters.page * filters.limit >= total} onClick={() => setFilter('page', filters.page + 1)}>Next →</button>
        </div>
      )}

      {/* Compare Drawer */}
      <CompareBar
        selected={compareItems}
        onRemove={id => setCompareItems(prev => prev.filter(x => x.id !== id))}
        onClear={() => setCompareItems([])}
      />
    </div>
  );
}

import { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { vehicleAPI } from '../services/api';
import { ArrowLeft, Trophy, Zap, Battery, Gauge, Star, TrendingDown } from 'lucide-react';

function formatPrice(p) {
  if (!p && p !== 0) return 'N/A';
  if (p >= 10000000) return `₹${(p / 10000000).toFixed(2)}Cr`;
  if (p >= 100000) return `₹${(p / 100000).toFixed(1)}L`;
  return `₹${(p / 1000).toFixed(0)}K`;
}

const SPECS = [
  { key: 'approx_price_inr', label: 'Price', format: formatPrice, lower_is_best: true },
  { key: 'range_km', label: 'Range (km)', format: v => `${v} km`, lower_is_best: false },
  { key: 'battery_kwh', label: 'Battery (kWh)', format: v => `${Number(v).toFixed(1)} kWh`, lower_is_best: false },
  { key: 'top_speed_kmh', label: 'Top Speed', format: v => v ? `${v} kmph` : 'N/A', lower_is_best: false },
  { key: 'charging_type', label: 'Charging', format: v => v || 'N/A', lower_is_best: null },
  { key: 'charging_time_ac_hrs', label: 'AC Charge Time', format: v => v ? `${v} hrs` : 'N/A', lower_is_best: true },
  { key: 'charging_time_dc_min', label: 'DC Fast Charge', format: v => v ? `${v} min` : 'N/A', lower_is_best: true },
  { key: 'fame2_subsidy_inr', label: 'FAME II Subsidy', format: formatPrice, lower_is_best: false },
  { key: 'overall_rating', label: 'Rating', format: v => v ? `${Number(v).toFixed(1)} / 5` : 'N/A', lower_is_best: false },
  { key: 'warranty_years', label: 'Battery Warranty', format: v => v ? `${v} years` : 'N/A', lower_is_best: false },
];

function getBestIdx(vehicles, spec) {
  if (spec.lower_is_best === null) return -1;
  const vals = vehicles.map(v => {
    const val = v[spec.key];
    return val !== null && val !== undefined ? Number(val) : null;
  });
  if (vals.every(v => v === null)) return -1;
  const filtered = vals.map((v, i) => ({ v, i })).filter(x => x.v !== null);
  if (!filtered.length) return -1;
  return spec.lower_is_best
    ? filtered.reduce((a, b) => a.v < b.v ? a : b).i
    : filtered.reduce((a, b) => a.v > b.v ? a : b).i;
}

const SEGMENT_COLORS = { '2W': '#854d0e', '3W': '#1e40af', '4W': '#166534', 'Truck': '#9d174d', 'Bus': '#5b21b6' };

export default function ComparePage() {
  const [searchParams] = useSearchParams();
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const ids = searchParams.get('ids')?.split(',').map(Number).filter(Boolean);
    if (ids?.length >= 2) {
      vehicleAPI.compare(ids)
        .then(res => { setVehicles(res.data.vehicles || []); setLoading(false); })
        .catch(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  if (loading) return (
    <div className="ev-shell" style={{ paddingTop: 40, textAlign: 'center' }}>
      <div className="ev-skeleton" style={{ height: 40, maxWidth: 300, margin: '0 auto 16px' }} />
      <div className="ev-skeleton" style={{ height: 300 }} />
    </div>
  );

  if (!vehicles.length) return (
    <div className="ev-shell" style={{ paddingTop: 60, textAlign: 'center' }}>
      <div style={{ fontSize: 64, marginBottom: 16 }}>🔄</div>
      <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 26, fontWeight: 700, color: 'var(--text)', marginBottom: 12 }}>
        No Vehicles Selected
      </h2>
      <p style={{ color: 'var(--text-muted)', fontSize: 16, marginBottom: 28 }}>
        Head to Browse, select 2–4 EVs using the Compare checkbox, then hit "Compare".
      </p>
      <Link to="/browse" className="ev-btn ev-btn-primary" style={{ fontSize: 15, padding: '12px 28px' }}>
        <ArrowLeft size={16} /> Browse EVs
      </Link>
    </div>
  );

  // Best vehicle overall (highest range, lowest price ratio)
  const bestOverall = vehicles.reduce((best, v) => {
    const score = (v.range_km || 0) - (v.approx_price_inr || 0) / 100000;
    const bestScore = (best.range_km || 0) - (best.approx_price_inr || 0) / 100000;
    return score > bestScore ? v : best;
  }, vehicles[0]);

  return (
    <div className="ev-shell" style={{ paddingTop: 32 }}>
      {/* Header */}
      <div style={{ marginBottom: 24 }}>
        <Link to="/browse" className="ev-btn ev-btn-sm ev-btn-ghost" style={{ marginBottom: 16 }}>
          <ArrowLeft size={14} /> Back to Browse
        </Link>
        <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 28, fontWeight: 800, letterSpacing: '-0.5px', color: 'var(--text)', marginBottom: 4 }}>
          Side-by-Side Comparison
        </h1>
        <p style={{ color: 'var(--text-muted)' }}>Comparing {vehicles.length} EVs</p>
      </div>

      {/* Vehicle Headers */}
      <div style={{ display: 'grid', gridTemplateColumns: `160px repeat(${vehicles.length}, 1fr)`, gap: 0, marginBottom: 0 }}>
        <div />
        {vehicles.map(v => (
          <div key={v.id} className="ev-card" style={{
            padding: '20px 16px', textAlign: 'center',
            borderRadius: '14px 14px 0 0', borderBottom: 0, margin: '0 4px',
            position: 'relative',
          }}>
            {v.id === bestOverall?.id && (
              <div style={{
                position: 'absolute', top: -10, left: '50%', transform: 'translateX(-50%)',
                background: 'var(--accent)', color: 'white', borderRadius: 999,
                padding: '2px 10px', fontSize: 10, fontWeight: 700,
                display: 'flex', alignItems: 'center', gap: 4, whiteSpace: 'nowrap',
              }}>
                <Trophy size={10} /> Best Value
              </div>
            )}
            <div style={{
              width: 70, height: 70, borderRadius: 12, margin: '0 auto 10px',
              background: SEGMENT_COLORS[v.category] ? `${SEGMENT_COLORS[v.category]}18` : 'var(--bg-muted)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 36,
            }}>
              {v.category === '2W' ? '🛵' : v.category === '4W' ? '🚗' : v.category === '3W' ? '🛺' : v.category === 'Truck' ? '🚛' : '🚌'}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 2 }}>{v.brand}</div>
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 15, color: 'var(--text)', marginBottom: 4 }}>{v.model}</div>
            <div style={{ fontWeight: 800, fontSize: 18, color: 'var(--accent)' }}>{formatPrice(v.approx_price_inr)}</div>
          </div>
        ))}
      </div>

      {/* Specs Table */}
      <div style={{ overflowX: 'auto', background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: '0 0 14px 14px', marginBottom: 32 }}>
        <table className="ev-compare-table" style={{ minWidth: 600 }}>
          <tbody>
            {SPECS.map(spec => {
              const bestIdx = getBestIdx(vehicles, spec);
              return (
                <tr key={spec.key}>
                  <td style={{ background: 'var(--bg-muted)', fontWeight: 600, color: 'var(--text-muted)', fontSize: 13, width: 160, padding: '12px 16px' }}>
                    {spec.label}
                  </td>
                  {vehicles.map((v, i) => {
                    const isBest = i === bestIdx;
                    return (
                      <td key={v.id} className={isBest ? 'ev-compare-best-cell' : ''}
                        style={{ padding: '12px 16px', textAlign: 'center', minWidth: 120, fontWeight: isBest ? 700 : 400 }}>
                        <span className={isBest ? 'ev-compare-best' : ''}>{spec.format(v[spec.key])}</span>
                        {isBest && <Zap size={12} color="var(--accent)" style={{ marginLeft: 4 }} />}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Summary Cards */}
      <div style={{ marginTop: 8, marginBottom: 32 }}>
        <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 20, fontWeight: 700, color: 'var(--text)', marginBottom: 16 }}>
          Analysis
        </h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 12 }}>
          {[
            {
              label: 'Best Range',
              icon: <Zap size={20} />,
              v: vehicles.reduce((a, b) => (b.range_km || 0) > (a.range_km || 0) ? b : a),
              detail: v => `${v.range_km} km`,
            },
            {
              label: 'Best Value',
              icon: <TrendingDown size={20} />,
              v: vehicles.reduce((a, b) => (a.approx_price_inr || Infinity) < (b.approx_price_inr || Infinity) ? a : b),
              detail: v => formatPrice(v.approx_price_inr),
            },
            {
              label: 'Best Rating',
              icon: <Star size={20} />,
              v: vehicles.reduce((a, b) => (Number(b.overall_rating) || 0) > (Number(a.overall_rating) || 0) ? b : a),
              detail: v => v.overall_rating ? `${Number(v.overall_rating).toFixed(1)} / 5` : 'N/A',
            },
            {
              label: 'Biggest Battery',
              icon: <Battery size={20} />,
              v: vehicles.reduce((a, b) => (Number(b.battery_kwh) || 0) > (Number(a.battery_kwh) || 0) ? b : a),
              detail: v => `${Number(v.battery_kwh).toFixed(1)} kWh`,
            },
          ].map(({ label, icon, v, detail }) => (
            <div key={label} className="ev-card" style={{ padding: 18, display: 'flex', gap: 12, alignItems: 'flex-start' }}>
              <div style={{ width: 40, height: 40, borderRadius: 10, background: 'var(--accent-soft)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)', flexShrink: 0 }}>
                {icon}
              </div>
              <div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 2 }}>{label}</div>
                <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text)', marginBottom: 1 }}>{v.brand} {v.model}</div>
                <div style={{ color: 'var(--accent)', fontWeight: 700, fontSize: 13 }}>{detail(v)}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { vehicleAPI } from '../services/api';
import { ArrowLeft, Zap, Battery, Gauge, Star, CheckCircle, AlertCircle, GitCompare, MessageSquare, TrendingUp } from 'lucide-react';

function formatPrice(p) {
  if (!p && p !== 0) return 'N/A';
  if (p >= 10000000) return `₹${(p / 10000000).toFixed(2)}Cr`;
  if (p >= 100000) return `₹${(p / 100000).toFixed(1)}L`;
  return `₹${(p / 1000).toFixed(0)}K`;
}

const SEGMENT_EMOJI = { '2W': '🛵', '3W': '🛺', '4W': '🚗', 'Truck': '🚛', 'Bus': '🚌' };

export default function VehicleDetailPage() {
  const { id } = useParams();
  const [vehicle, setVehicle] = useState(null);
  const [subsidy, setSubsidy] = useState(null);
  const [loading, setLoading] = useState(true);
  const [subsidyState, setSubsidyState] = useState('telangana');
  const [dailyKm, setDailyKm] = useState(40);

  useEffect(() => {
    vehicleAPI.getById(id)
      .then(res => { setVehicle(res.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!vehicle) return;
    vehicleAPI.getSubsidies({ vehicle_id: vehicle.id, state: subsidyState, daily_km: dailyKm })
      .then(res => setSubsidy(res.data))
      .catch(() => setSubsidy(null));
  }, [vehicle, subsidyState, dailyKm]);

  if (loading) return (
    <div className="ev-shell" style={{ paddingTop: 40 }}>
      <div className="ev-skeleton" style={{ height: 200, borderRadius: 16, marginBottom: 20 }} />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, marginBottom: 20 }}>
        {[...Array(8)].map((_, i) => <div key={i} className="ev-skeleton" style={{ height: 80, borderRadius: 12 }} />)}
      </div>
    </div>
  );

  if (!vehicle) return (
    <div className="ev-shell" style={{ paddingTop: 60, textAlign: 'center' }}>
      <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 24, fontWeight: 700 }}>Vehicle not found</h2>
      <Link to="/browse" className="ev-btn ev-btn-primary" style={{ marginTop: 20 }}>← Browse EVs</Link>
    </div>
  );

  const SPECS = [
    { label: 'Range', value: `${vehicle.range_km} km`, icon: <Zap size={16} color="var(--accent)" /> },
    { label: 'Battery', value: `${Number(vehicle.battery_kwh).toFixed(1)} kWh`, icon: <Battery size={16} color="var(--accent)" /> },
    { label: 'Top Speed', value: vehicle.top_speed_kmh ? `${vehicle.top_speed_kmh} kmph` : 'N/A', icon: <Gauge size={16} color="var(--accent)" /> },
    { label: 'Motor', value: vehicle.motor_kw ? `${vehicle.motor_kw} kW` : 'N/A', icon: <Zap size={16} color="var(--accent)" /> },
    { label: 'Charging', value: vehicle.charging_type || 'N/A', icon: null },
    { label: 'AC Charge', value: vehicle.charging_time_ac_hrs ? `${vehicle.charging_time_ac_hrs} hrs` : 'N/A', icon: null },
    { label: 'DC Fast Charge', value: vehicle.charging_time_dc_min ? `${vehicle.charging_time_dc_min} min` : 'N/A', icon: null },
    { label: 'Warranty', value: vehicle.warranty_years ? `${vehicle.warranty_years} yrs` : 'N/A', icon: null },
    { label: 'Safety Rating', value: vehicle.safety_rating ? `${vehicle.safety_rating} stars` : 'N/A', icon: null },
    { label: 'Brakes', value: vehicle.brake_type || 'N/A', icon: null },
    { label: 'IP Rating', value: vehicle.ip_rating || 'N/A', icon: null },
    { label: 'Launch Year', value: vehicle.launch_year || 'N/A', icon: null },
  ];

  return (
    <div className="ev-shell" style={{ paddingTop: 32 }}>
      <Link to="/browse" className="ev-btn ev-btn-sm ev-btn-ghost" style={{ marginBottom: 20, display: 'inline-flex' }}>
        <ArrowLeft size={14} /> Back to Browse
      </Link>

      {/* Hero */}
      <div className="ev-card" style={{ padding: 0, marginBottom: 24, overflow: 'hidden' }}>
        <div style={{
          display: 'grid', gridTemplateColumns: '1fr 1fr', minHeight: 240,
          background: 'linear-gradient(135deg, var(--accent-soft), var(--bg-muted))',
        }}>
          {/* Vehicle visual */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 40 }}>
            <div style={{ fontSize: 120 }}>{SEGMENT_EMOJI[vehicle.category] || '⚡'}</div>
          </div>
          {/* Info */}
          <div style={{ padding: '32px 32px 32px 0', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            <div style={{ display: 'flex', gap: 8, marginBottom: 12, flexWrap: 'wrap' }}>
              <span className="ev-badge ev-badge-brand">{vehicle.category}</span>
              {vehicle.wheel_type && <span className="ev-badge ev-badge-neutral">{vehicle.wheel_type}</span>}
              <span className={`ev-badge ${vehicle.market_status === 'Available' ? 'ev-badge-success' : 'ev-badge-warn'}`}>{vehicle.market_status}</span>
              {vehicle.fame2_subsidy_inr > 0 && <span className="ev-badge ev-badge-brand">FAME II Eligible</span>}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 600, marginBottom: 4 }}>{vehicle.brand}</div>
            <h1 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 30, fontWeight: 800, color: 'var(--text)', lineHeight: 1.15, marginBottom: 12 }}>
              {vehicle.model}
            </h1>
            <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--accent)', fontFamily: "'Space Grotesk', sans-serif", marginBottom: 12 }}>
              {formatPrice(vehicle.approx_price_inr)}
            </div>
            {vehicle.overall_rating && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 16 }}>
                {[...Array(5)].map((_, i) => (
                  <Star key={i} size={18} fill={i < Math.round(vehicle.overall_rating) ? 'gold' : 'none'} color={i < Math.round(vehicle.overall_rating) ? 'gold' : 'var(--border)'} />
                ))}
                <span style={{ fontSize: 14, color: 'var(--text-muted)', marginLeft: 4 }}>{Number(vehicle.overall_rating).toFixed(1)}</span>
              </div>
            )}
            <div style={{ display: 'flex', gap: 10 }}>
              <Link to={`/compare?ids=${vehicle.id}`} className="ev-btn ev-btn-sm">
                <GitCompare size={14} /> Compare
              </Link>
              <Link to={`/chat?q=Tell me about ${vehicle.brand} ${vehicle.model}`} className="ev-btn ev-btn-sm">
                <MessageSquare size={14} /> Ask AI
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: 20, alignItems: 'start' }}>
        {/* Left column */}
        <div>
          {/* Specs Grid */}
          <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 20, fontWeight: 700, marginBottom: 14, color: 'var(--text)' }}>
            Key Specifications
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 28 }}>
            {SPECS.map(s => (
              <div key={s.label} className="ev-card" style={{ padding: '14px 16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                  {s.icon}
                  <span style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px' }}>{s.label}</span>
                </div>
                <div style={{ fontWeight: 700, fontSize: 16, color: 'var(--text)' }}>{s.value}</div>
              </div>
            ))}
          </div>

          {/* Feature flags */}
          <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 20, fontWeight: 700, marginBottom: 14, color: 'var(--text)' }}>
            Features
          </h2>
          <div className="ev-card" style={{ padding: 20, marginBottom: 24 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 10 }}>
              {[
                { label: 'Connected Features', val: vehicle.connected_features },
                { label: 'Regenerative Braking', val: vehicle.regenerative_braking },
                { label: 'Fast DC Charging', val: !!vehicle.charging_time_dc_min },
                { label: 'FAME II Eligible', val: vehicle.fame2_subsidy_inr > 0 },
              ].map(({ label, val }) => (
                <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: val ? 'var(--text)' : 'var(--text-muted)' }}>
                  {val
                    ? <CheckCircle size={16} color="var(--accent)" />
                    : <AlertCircle size={16} color="var(--border)" />
                  }
                  {label}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right column — Subsidy & TCO */}
        <div style={{ position: 'sticky', top: 80 }}>
          <div className="ev-card" style={{ padding: 20, marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }}>
              <TrendingUp size={18} color="var(--accent)" />
              <h3 style={{ fontWeight: 700, fontSize: 16, color: 'var(--text)' }}>Subsidy & TCO</h3>
            </div>

            <div style={{ marginBottom: 12 }}>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: 4 }}>YOUR STATE</label>
              <select className="ev-select" value={subsidyState} onChange={e => setSubsidyState(e.target.value)}>
                {['karnataka', 'maharashtra', 'delhi', 'gujarat', 'tamil nadu', 'telangana'].map(s => (
                  <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                ))}
              </select>
            </div>

            <div style={{ marginBottom: 16 }}>
              <label style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: 4 }}>
                DAILY KM: {dailyKm} km
              </label>
              <input type="range" min={5} max={200} step={5} value={dailyKm}
                onChange={e => setDailyKm(parseInt(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--accent)' }} />
            </div>

            {subsidy && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {[
                  { label: 'Ex-showroom Price', value: formatPrice(vehicle.approx_price_inr) },
                  { label: 'Central Subsidy (FAME)', value: `- ${formatPrice(subsidy.central_subsidy_inr)}`, color: 'var(--accent)' },
                  { label: `${subsidyState.charAt(0).toUpperCase() + subsidyState.slice(1)} State Subsidy`, value: `- ${formatPrice(subsidy.state_subsidy_inr)}`, color: 'var(--accent)' },
                  { label: 'Effective Price', value: formatPrice(vehicle.approx_price_inr - subsidy.central_subsidy_inr - subsidy.state_subsidy_inr) },
                  { label: '5-Year TCO', value: formatPrice(subsidy.tco_5year_inr), bold: true },
                ].map(row => (
                  <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: 14 }}>
                    <span style={{ color: 'var(--text-muted)' }}>{row.label}</span>
                    <span style={{ fontWeight: row.bold ? 800 : 600, color: row.color || 'var(--text)' }}>{row.value}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <Link to={`/chat?q=Tell me about ${vehicle.brand} ${vehicle.model} and its running cost`} className="ev-btn ev-btn-primary" style={{ width: '100%', justifyContent: 'center', marginBottom: 10 }}>
            <MessageSquare size={15} /> Ask about this EV
          </Link>
          <Link to="/subsidies" className="ev-btn" style={{ width: '100%', justifyContent: 'center' }}>
            Full TCO Calculator
          </Link>
        </div>
      </div>
    </div>
  );
}

import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Zap, Gauge, Battery, Star, Heart } from 'lucide-react';
import { garageAPI } from '../services/api';
import useAuth from '../store/useAuth';

const SEGMENT_COLORS = {
  '2W': { bg: '#fef9c3', color: '#854d0e', icon: '🛵' },
  '3W': { bg: '#dbeafe', color: '#1e40af', icon: '🛺' },
  '4W': { bg: '#dcfce7', color: '#166534', icon: '🚗' },
  'Truck': { bg: '#fce7f3', color: '#9d174d', icon: '🚛' },
  'Bus': { bg: '#ede9fe', color: '#5b21b6', icon: '🚌' },
};

function formatPrice(p) {
  if (!p && p !== 0) return 'N/A';
  if (p >= 10000000) return `₹${(p / 10000000).toFixed(2)}Cr`;
  if (p >= 100000) return `₹${(p / 100000).toFixed(1)}L`;
  if (p >= 1000) return `₹${(p / 1000).toFixed(0)}K`;
  return `₹${p}`;
}

function SegmentIcon({ vehicle }) {
  let cat = vehicle.category || 'other';
  if (cat === '4W' && vehicle.vehicle_type) {
    const vt = vehicle.vehicle_type.toLowerCase();
    if (vt.includes('truck') || vt.includes('commercial') || vt.includes('cargo')) {
      cat = 'Truck';
    }
  }
  const info = SEGMENT_COLORS[cat] || { bg: '#f3f4f6', color: '#374151', icon: '⚡' };
  return (
    <div style={{
      width: '100%', height: '100%',
      display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      background: info.bg, gap: 8,
    }}>
      <span style={{ fontSize: 52, lineHeight: 1 }}>{info.icon}</span>
      <span style={{ fontSize: 11, fontWeight: 600, color: info.color, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
        {cat}
      </span>
    </div>
  );
}

export default function VehicleCard({ vehicle: v, onCompareToggle, isSelected }) {
  const { user } = useAuth();
  const [saved, setSaved] = useState(false);
  const [saving, setSaving] = useState(false);

  async function handleSave(e) {
    e.preventDefault();
    e.stopPropagation();
    if (!user || saving || saved) return;
    setSaving(true);
    try {
      await garageAPI.save({ vehicle_ids: String(v.id), name: `${v.brand} ${v.model}` });
      setSaved(true);
    } catch { /* ignore — user may not be logged in */ }
    finally { setSaving(false); }
  }
  return (
    <div className="ev-vehicle-card">
      {/* Image / Segment visual */}
      <div className="ev-vehicle-card-img">
        {v.image_url
          ? <img src={v.image_url} alt={`${v.brand} ${v.model}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          : <SegmentIcon vehicle={v} />
        }
        {/* Rating badge */}
        {v.overall_rating && (
          <div style={{
            position: 'absolute', top: 10, right: 10,
            background: 'rgba(0,0,0,0.65)',
            color: 'white', borderRadius: 8,
            padding: '3px 8px', fontSize: 12, fontWeight: 600,
            display: 'flex', alignItems: 'center', gap: 3,
            backdropFilter: 'blur(8px)',
          }}>
            <Star size={11} fill="gold" color="gold" /> {Number(v.overall_rating).toFixed(1)}
          </div>
        )}
        {/* FAME badge */}
        {v.fame2_subsidy_inr > 0 && (
          <div style={{
            position: 'absolute', top: 10, left: 10,
            background: 'var(--accent)', color: 'white',
            borderRadius: 6, padding: '3px 7px', fontSize: 10, fontWeight: 700,
          }}>
            FAME II
          </div>
        )}
      </div>

      {/* Body */}
      <div className="ev-vehicle-card-body">
        <div>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, marginBottom: 2, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            {v.brand}
          </div>
          <div className="ev-vehicle-card-name">{v.model}</div>
        </div>

        <div className="ev-vehicle-card-price">{formatPrice(v.approx_price_inr)}</div>

        {/* Specs Grid */}
        <div className="ev-vehicle-card-specs">
          <div className="ev-spec-item">
            <span className="ev-spec-label"><Zap size={9} style={{ display: 'inline', marginRight: 2 }} />Range</span>
            <span className="ev-spec-value">{v.range_km} km</span>
          </div>
          <div className="ev-spec-item">
            <span className="ev-spec-label"><Battery size={9} style={{ display: 'inline', marginRight: 2 }} />Battery</span>
            <span className="ev-spec-value">{Number(v.battery_kwh).toFixed(1)} kWh</span>
          </div>
          {v.top_speed_kmh && (
            <div className="ev-spec-item">
              <span className="ev-spec-label"><Gauge size={9} style={{ display: 'inline', marginRight: 2 }} />Top Speed</span>
              <span className="ev-spec-value">{v.top_speed_kmh} kmph</span>
            </div>
          )}
          {v.charging_type && (
            <div className="ev-spec-item">
              <span className="ev-spec-label">Charging</span>
              <span className="ev-spec-value" style={{ fontSize: 11, textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                {v.charging_type}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Footer */}
      <div className="ev-vehicle-card-footer">
        <label className="ev-compare-check" onClick={e => e.stopPropagation()}>
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onCompareToggle && onCompareToggle(v.id)}
          />
          Compare
        </label>

        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {/* Save to Garage */}
          {user && (
            <button
              onClick={handleSave}
              title={saved ? 'Saved to Garage' : 'Save to Garage'}
              style={{
                width: 30, height: 30, borderRadius: 8,
                border: '1px solid var(--border)',
                background: saved ? 'var(--accent-soft)' : 'var(--bg-muted)',
                color: saved ? 'var(--accent)' : 'var(--text-muted)',
                cursor: saved ? 'default' : 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                transition: 'all 0.2s', flexShrink: 0,
              }}
            >
              <Heart size={13} fill={saved ? 'currentColor' : 'none'} />
            </button>
          )}
          <Link to={`/vehicle/${v.id}`} className="ev-btn ev-btn-sm ev-btn-primary">
            Details
          </Link>
        </div>
      </div>
    </div>
  );
}

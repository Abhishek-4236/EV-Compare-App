import { useState } from 'react';
import { vehicleAPI } from '../services/api';
import { Link } from 'react-router-dom';
import { Zap, Battery, Star, TrendingDown, ChevronRight, CheckCircle, AlertCircle, GitCompare } from 'lucide-react';
import useCompare from '../store/useCompare';

function formatPrice(p) {
  if (!p && p !== 0) return 'N/A';
  if (p >= 10000000) return `₹${(p / 10000000).toFixed(2)}Cr`;
  if (p >= 100000) return `₹${(p / 100000).toFixed(1)}L`;
  return `₹${(p / 1000).toFixed(0)}K`;
}

const STEPS = [
  { id: 'budget', label: 'Budget' },
  { id: 'segment', label: 'Segment' },
  { id: 'usage', label: 'Usage' },
  { id: 'results', label: 'Results' },
];

const SEGMENTS = [
  { value: 'scooter', label: 'Scooter / Scooty', icon: '🛵', desc: 'Daily city commute' },
  { value: 'motorcycle', label: 'Motorcycle / Bike', icon: '🏍️', desc: 'Performance riding' },
  { value: 'car', label: 'Car / SUV', icon: '🚗', desc: 'Family & highway' },
  { value: 'auto', label: '3-Wheeler / Auto', icon: '🛺', desc: 'Commercial/last-mile' },
  { value: 'truck', label: 'Truck / Cargo EV', icon: '🚛', desc: 'Heavy commercial' },
];

const BUDGET_PRESETS = [
  { label: 'Under ₹1L', value: 100000 },
  { label: '₹1–2L', value: 200000 },
  { label: '₹2–5L', value: 500000 },
  { label: '₹5–10L', value: 1000000 },
  { label: '₹10–20L', value: 2000000 },
  { label: 'Above ₹20L', value: 20000000 },
];

function ScoreBar({ score, max = 10 }) {
  const pct = Math.min(100, (score / max) * 100);
  return (
    <div style={{ height: 6, background: 'var(--bg-muted)', borderRadius: 99, overflow: 'hidden' }}>
      <div style={{ height: '100%', width: `${pct}%`, background: 'var(--accent)', borderRadius: 99, transition: 'width 0.5s' }} />
    </div>
  );
}

function ResultCard({ rec, rank, compareItems, onToggleCompare }) {
  const rankLabel = ['🥇 Best Match', '🥈 Runner-up', '🥉 Third Choice'];
  const isSelected = compareItems.some(x => x.id === rec.id);

  return (
    <div className="ev-card" style={{ padding: 0, overflow: 'hidden', transition: 'box-shadow 0.2s', boxShadow: isSelected ? '0 0 0 2px var(--accent)' : undefined }}>
      <div style={{ background: rank === 0 ? 'var(--accent-soft)' : 'var(--bg-muted)', padding: '10px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontWeight: 700, fontSize: 13, color: rank === 0 ? 'var(--accent-dark)' : 'var(--text-muted)' }}>
          {rankLabel[rank] || `#${rank + 1} Pick`}
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 500 }}>
            Score: {rec.recommend_score?.toFixed(1)}
          </span>
          {/* Compare checkbox */}
          <label
            onClick={e => e.stopPropagation()}
            style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', fontSize: 12, fontWeight: 600, color: isSelected ? 'var(--accent-dark)' : 'var(--text-muted)', userSelect: 'none' }}
          >
            <div style={{
              width: 18, height: 18, borderRadius: 4, border: `2px solid ${isSelected ? 'var(--accent)' : 'var(--border)'}`,
              background: isSelected ? 'var(--accent)' : 'transparent',
              display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.15s',
            }}
              onClick={() => onToggleCompare(rec)}
            >
              {isSelected && <span style={{ color: 'white', fontSize: 10, fontWeight: 900 }}>✓</span>}
            </div>
            <GitCompare size={13} />
            Compare
          </label>
        </div>
      </div>
      <div style={{ padding: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, marginBottom: 14 }}>
          <div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 2 }}>{rec.brand}</div>
            <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 18, fontWeight: 700, color: 'var(--text)', marginBottom: 4 }}>{rec.model}</h3>
            <div style={{ fontWeight: 800, fontSize: 20, color: 'var(--accent)' }}>{formatPrice(rec.effective_price)}</div>
            {rec.fame2_subsidy_inr > 0 && (
              <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                After subsidy (was {formatPrice(rec.approx_price_inr)})
              </div>
            )}
          </div>
          <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
            <Link to={`/vehicle/${rec.id}`} className="ev-btn ev-btn-sm">Details</Link>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 14 }}>
          {[
            { label: 'Range', value: `${rec.range_km} km` },
            { label: 'Battery', value: `${Number(rec.battery_kwh).toFixed(1)} kWh` },
            { label: 'Rating', value: rec.overall_rating ? `${Number(rec.overall_rating).toFixed(1)}/5` : 'N/A' },
          ].map(s => (
            <div key={s.label} style={{ background: 'var(--bg-muted)', borderRadius: 8, padding: '8px 10px', textAlign: 'center' }}>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', fontWeight: 600, textTransform: 'uppercase', marginBottom: 2 }}>{s.label}</div>
              <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text)' }}>{s.value}</div>
            </div>
          ))}
        </div>

        {rec.fame2_subsidy_inr > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '8px 12px', background: 'var(--accent-soft)', borderRadius: 8, fontSize: 13, color: 'var(--accent-dark)', fontWeight: 600 }}>
            <CheckCircle size={14} /> FAME II Subsidy: {formatPrice(rec.fame2_subsidy_inr)}
          </div>
        )}
      </div>
    </div>
  );
}

export default function RecommendPage() {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState({
    budget: 500000,
    segment: 'scooter',
    daily_km: 40,
    priority: 'range',
  });
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { compareItems, toggleCompare } = useCompare();

  async function submit() {
    setLoading(true);
    setError('');
    try {
      const res = await vehicleAPI.recommend({
        budget: form.budget,
        segment: form.segment,
        daily_km: form.daily_km,
        priority: form.priority,
      });
      setResults(res.data);
      setStep(3);
    } catch {
      setError('Could not fetch recommendations. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="ev-shell" style={{ paddingTop: 40, maxWidth: 760, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ textAlign: 'center', marginBottom: 40 }}>
        <div className="ev-section-label" style={{ justifyContent: 'center', display: 'flex', marginBottom: 10 }}>AI Powered</div>
        <h1 className="ev-section-title">Find Your Perfect EV</h1>
        <p className="ev-section-desc" style={{ maxWidth: 480, margin: '8px auto 0' }}>
          Answer 3 quick questions and get personalized EV recommendations with explanations.
        </p>
      </div>

      {/* Step indicator */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginBottom: 40 }}>
        {STEPS.map((s, i) => (
          <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              width: 28, height: 28, borderRadius: '50%',
              background: i <= step ? 'var(--accent)' : 'var(--bg-muted)',
              color: i <= step ? 'white' : 'var(--text-muted)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 12, fontWeight: 700, transition: 'all 0.3s',
            }}>
              {i < step ? '✓' : i + 1}
            </div>
            <span style={{ fontSize: 13, fontWeight: 500, color: i <= step ? 'var(--text)' : 'var(--text-muted)' }}>{s.label}</span>
            {i < STEPS.length - 1 && <div style={{ width: 32, height: 1, background: 'var(--border)' }} />}
          </div>
        ))}
      </div>

      {/* Step 0: Budget */}
      {step === 0 && (
        <div className="ev-card" style={{ padding: 32 }}>
          <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 22, fontWeight: 700, color: 'var(--text)', marginBottom: 6 }}>What's your budget?</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 24 }}>Choose a price range for your EV purchase.</p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10, marginBottom: 24 }}>
            {BUDGET_PRESETS.map(b => (
              <button
                key={b.value}
                className={`ev-chip ${form.budget === b.value ? 'active' : ''}`}
                style={{ padding: '12px 8px', justifyContent: 'center', fontSize: 13, fontWeight: 600 }}
                onClick={() => setForm(f => ({ ...f, budget: b.value }))}
              >
                {b.label}
              </button>
            ))}
          </div>
          <div style={{ marginBottom: 20 }}>
            <label style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: 8 }}>
              Or set custom: ₹{(form.budget / 100000).toFixed(1)}L
            </label>
            <input type="range" min={50000} max={20000000} step={50000}
              value={form.budget}
              onChange={e => setForm(f => ({ ...f, budget: parseInt(e.target.value) }))}
              style={{ width: '100%', accentColor: 'var(--accent)' }} />
          </div>
          <button className="ev-btn ev-btn-primary" style={{ width: '100%', justifyContent: 'center', padding: '13px 20px' }}
            onClick={() => setStep(1)}>
            Next: Choose Segment <ChevronRight size={16} />
          </button>
        </div>
      )}

      {/* Step 1: Segment */}
      {step === 1 && (
        <div className="ev-card" style={{ padding: 32 }}>
          <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 22, fontWeight: 700, color: 'var(--text)', marginBottom: 6 }}>What type of EV?</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 24 }}>Select the vehicle category you're interested in.</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 24 }}>
            {SEGMENTS.map(s => (
              <button
                key={s.value}
                onClick={() => setForm(f => ({ ...f, segment: s.value }))}
                style={{
                  display: 'flex', alignItems: 'center', gap: 16,
                  padding: '14px 18px', borderRadius: 12,
                  border: `2px solid ${form.segment === s.value ? 'var(--accent)' : 'var(--border)'}`,
                  background: form.segment === s.value ? 'var(--accent-soft)' : 'var(--bg-card)',
                  cursor: 'pointer', transition: 'all 0.15s', textAlign: 'left',
                }}
              >
                <span style={{ fontSize: 32 }}>{s.icon}</span>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 15, color: form.segment === s.value ? 'var(--accent-dark)' : 'var(--text)', marginBottom: 2 }}>{s.label}</div>
                  <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>{s.desc}</div>
                </div>
                {form.segment === s.value && <CheckCircle size={20} color="var(--accent)" style={{ marginLeft: 'auto' }} />}
              </button>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="ev-btn" style={{ flex: 1, justifyContent: 'center' }} onClick={() => setStep(0)}>
              ← Back
            </button>
            <button className="ev-btn ev-btn-primary" style={{ flex: 2, justifyContent: 'center', padding: '13px 20px' }}
              onClick={() => setStep(2)}>
              Next: Daily Usage <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Usage */}
      {step === 2 && (
        <div className="ev-card" style={{ padding: 32 }}>
          <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 22, fontWeight: 700, color: 'var(--text)', marginBottom: 6 }}>How do you plan to use it?</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 24 }}>This helps match the right range and charging needs.</p>

          <div style={{ marginBottom: 20 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 8 }}>
              Daily commute distance: <strong>{form.daily_km} km</strong>
            </label>
            <input type="range" min={5} max={200} step={5}
              value={form.daily_km}
              onChange={e => setForm(f => ({ ...f, daily_km: parseInt(e.target.value) }))}
              style={{ width: '100%', accentColor: 'var(--accent)' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-muted)', marginTop: 4 }}>
              <span>5 km (very short)</span><span>200 km (long distance)</span>
            </div>
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 10 }}>What matters most to you?</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
              {[
                { value: 'range', label: '🔋 Range', desc: 'Max km per charge' },
                { value: 'price', label: '💰 Value', desc: 'Lowest cost' },
                { value: 'speed', label: '⚡ Speed', desc: 'Best performance' },
              ].map(p => (
                <button
                  key={p.value}
                  onClick={() => setForm(f => ({ ...f, priority: p.value }))}
                  style={{
                    padding: '14px 10px', borderRadius: 10, cursor: 'pointer',
                    border: `2px solid ${form.priority === p.value ? 'var(--accent)' : 'var(--border)'}`,
                    background: form.priority === p.value ? 'var(--accent-soft)' : 'var(--bg-card)',
                    textAlign: 'center', transition: 'all 0.15s',
                  }}
                >
                  <div style={{ fontSize: 22, marginBottom: 4 }}>{p.label.split(' ')[0]}</div>
                  <div style={{ fontWeight: 700, fontSize: 13, color: form.priority === p.value ? 'var(--accent-dark)' : 'var(--text)', marginBottom: 2 }}>
                    {p.label.split(' ').slice(1).join(' ')}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{p.desc}</div>
                </button>
              ))}
            </div>
          </div>

          {error && <p style={{ color: '#dc2626', fontSize: 14, marginBottom: 12 }}>{error}</p>}

          <div style={{ display: 'flex', gap: 10 }}>
            <button className="ev-btn" style={{ flex: 1, justifyContent: 'center' }} onClick={() => setStep(1)}>← Back</button>
            <button className="ev-btn ev-btn-primary" style={{ flex: 2, justifyContent: 'center', padding: '13px 20px' }}
              disabled={loading} onClick={submit}>
              {loading ? 'Finding best EVs...' : '🔍 Get Recommendations'}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Results */}
      {step === 3 && results && (
        <div>
          <div style={{ textAlign: 'center', marginBottom: 28 }}>
            <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 24, fontWeight: 800, color: 'var(--text)', marginBottom: 6 }}>
              🎯 Your Top EV Picks
            </h2>
            <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 8 }}>
              Recommendations for budget {formatPrice(results.query?.budget)}, {results.query?.daily_km}km daily, {results.query?.segment} segment
            </p>
            {compareItems.length > 0 && (
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, padding: '6px 14px', background: 'var(--accent-soft)', borderRadius: 99, fontSize: 13, color: 'var(--accent-dark)', fontWeight: 600 }}>
                <GitCompare size={14} /> {compareItems.length} selected for comparison
              </div>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginBottom: 24 }}>
            {results.recommendations?.map((rec, i) => (
              <ResultCard
                key={rec.id}
                rec={rec}
                rank={i}
                compareItems={compareItems}
                onToggleCompare={toggleCompare}
              />
            ))}
          </div>

          {!results.recommendations?.length && (
            <div className="ev-card" style={{ padding: 32, textAlign: 'center' }}>
              <div style={{ fontSize: 48, marginBottom: 12 }}>😕</div>
              <h3 style={{ fontWeight: 700, fontSize: 18, marginBottom: 6 }}>No matches found</h3>
              <p style={{ color: 'var(--text-muted)' }}>Try increasing your budget or changing the segment.</p>
            </div>
          )}

          <button className="ev-btn" style={{ width: '100%', justifyContent: 'center', marginBottom: compareItems.length > 0 ? 80 : 0 }} onClick={() => { setStep(0); setResults(null); }}>
            ← Start Over
          </button>
        </div>
      )}
    </div>
  );
}

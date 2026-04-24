import { useState, useEffect } from 'react';
import { vehicleAPI } from '../services/api';
import { TrendingUp, Shield, Search, CheckCircle, Info } from 'lucide-react';

function formatPrice(p) {
  if (!p && p !== 0) return 'N/A';
  if (p >= 10000000) return `₹${(p / 10000000).toFixed(2)}Cr`;
  if (p >= 100000) return `₹${(p / 100000).toFixed(1)}L`;
  return `₹${(p / 1000).toFixed(0)}K`;
}

const STATES = [
    'andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chhattisgarh', 'goa', 'gujarat', 'haryana', 
    'himachal pradesh', 'jharkhand', 'karnataka', 'kerala', 'madhya pradesh', 'maharashtra', 'manipur', 
    'meghalaya', 'mizoram', 'nagaland', 'odisha', 'punjab', 'rajasthan', 'sikkim', 'tamil nadu', 
    'telangana', 'tripura', 'uttar pradesh', 'uttarakhand', 'west bengal', 'delhi', 'jammu and kashmir', 
    'ladakh', 'chandigarh', 'puducherry', 'andaman and nicobar', 'lakshadweep'
].sort();

const STATE_POLICIES = {
  karnataka: { roadTax: 'Waived', regFee: 'Waived', note: 'EV Policy 2017 updated under EVPOA Karnataka' },
  maharashtra: { roadTax: 'Waived', regFee: '50% waiver', note: 'MahaEV Policy 2021' },
  delhi: { roadTax: 'Waived', regFee: 'Waived', note: 'Delhi EV Policy 2020 — highest EV adoption city' },
  gujarat: { roadTax: 'Waived', regFee: 'Waived', note: 'Gujarat EV Policy 2021' },
  'tamil nadu': { roadTax: 'Waived', regFee: 'Waived', note: 'TN EV Policy 2023' },
  telangana: { roadTax: 'Waived', regFee: '50% waiver', note: 'Telangana EV & ESS Policy 2020' },
  'uttar pradesh': { roadTax: 'Waived', regFee: 'Waived', note: 'UP EV Policy 2022' },
  kerala: { roadTax: '50% waiver', regFee: 'Waived', note: 'Kerala EV Policy 2019' },
  rajasthan: { roadTax: 'Waived', regFee: 'Waived', note: 'Rajasthan EV Policy 2022' },
  odisha: { roadTax: 'Waived', regFee: 'Waived', note: 'Odisha EV Policy 2021' },
  'west bengal': { roadTax: 'Waived', regFee: 'Waived', note: 'West Bengal EV Policy 2021' },
  haryana: { roadTax: 'Waived', regFee: 'Waived', note: 'Haryana EV Policy 2022' },
  punjab: { roadTax: 'Waived', regFee: 'Waived', note: 'Punjab EV Policy 2022' },
  chandigarh: { roadTax: 'Waived', regFee: 'Waived', note: 'Chandigarh EV Policy 2022' },
};

export default function SubsidiesPage() {
  const [vehicles, setVehicles] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [state, setState] = useState('telangana');
  const [dailyKm, setDailyKm] = useState(40);
  const [electricityRate, setElectricityRate] = useState(8);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');

  useEffect(() => {
    vehicleAPI.getAll({ limit: 65, sort_by: 'overall_rating' })
      .then(res => setVehicles(res.data.vehicles || []))
      .catch(() => {});
  }, []);

  const filteredVehicles = vehicles.filter(v =>
    !search || `${v.brand} ${v.model}`.toLowerCase().includes(search.toLowerCase())
  );

  async function calculate() {
    if (!selectedVehicle) return;
    setLoading(true);
    try {
      const res = await vehicleAPI.getSubsidies({
        vehicle_id: selectedVehicle.id,
        state,
        daily_km: dailyKm,
      });
      // Augment with electricity cost override
      const annualKm = dailyKm * 365;
      const evKmCost = (electricityRate * (selectedVehicle.battery_kwh || 5)) / Math.max(selectedVehicle.range_km || 100, 1);
      const evCost5yr = evKmCost * annualKm * 5;
      const petrolCost5yr = annualKm * 5 * 6.5; // avg ₹6.5/km for petrol 2W
      setResult({ ...res.data, evCost5yr, petrolCost5yr, evKmCost: evKmCost.toFixed(2) });
    } catch {
      setResult(null);
    } finally {
      setLoading(false);
    }
  }

  const policy = STATE_POLICIES[state] || { roadTax: 'Standard Rates', regFee: 'Standard Rates', note: 'Detailed local EV policy unconfirmed. Ask dealer for exact regional tax rates.' };

  return (
    <div className="ev-shell" style={{ paddingTop: 32 }}>
      <div style={{ marginBottom: 28 }}>
        <div className="ev-section-label">Financial Planning</div>
        <h1 className="ev-section-title">Subsidies & TCO Calculator</h1>
        <p className="ev-section-desc">Real ownership cost including state subsidies, electricity, and maintenance.</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 400px', gap: 24, alignItems: 'start' }}>
        {/* Left — Inputs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {/* Vehicle Search */}
          <div className="ev-card" style={{ padding: 20 }}>
            <h3 style={{ fontWeight: 700, fontSize: 16, marginBottom: 14, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Search size={16} color="var(--accent)" /> Select Vehicle
            </h3>
            <input
              className="ev-input"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search EV model..."
              style={{ marginBottom: 10 }}
            />
            <div style={{ maxHeight: 240, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}>
              {filteredVehicles.slice(0, 20).map(v => (
                <button
                  key={v.id}
                  onClick={() => setSelectedVehicle(v)}
                  style={{
                    textAlign: 'left', padding: '10px 12px', borderRadius: 8, cursor: 'pointer',
                    border: `1px solid ${selectedVehicle?.id === v.id ? 'var(--accent)' : 'var(--border)'}`,
                    background: selectedVehicle?.id === v.id ? 'var(--accent-soft)' : 'transparent',
                    transition: 'all 0.15s',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <span style={{ fontWeight: 600, fontSize: 14, color: selectedVehicle?.id === v.id ? 'var(--accent-dark)' : 'var(--text)' }}>
                        {v.brand} {v.model}
                      </span>
                      <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 8 }}>{v.category}</span>
                    </div>
                    <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--accent)' }}>{formatPrice(v.approx_price_inr)}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Parameters */}
          <div className="ev-card" style={{ padding: 20, display: 'flex', flexDirection: 'column', gap: 16 }}>
            <h3 style={{ fontWeight: 700, fontSize: 16, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: 8 }}>
              <TrendingUp size={16} color="var(--accent)" /> Parameters
            </h3>

            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 6 }}>
                Your State
              </label>
              <select className="ev-select" value={state} onChange={e => setState(e.target.value)}>
                {STATES.map(s => (
                  <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                ))}
              </select>
              {policy.note && (
                <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <Info size={11} /> {policy.note}
                </div>
              )}
            </div>

            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
                Daily Commute: <strong>{dailyKm} km</strong>
              </label>
              <input type="range" min={5} max={200} step={5} value={dailyKm}
                onChange={e => setDailyKm(parseInt(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--accent)' }} />
            </div>

            <div>
              <label style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', display: 'block', marginBottom: 4 }}>
                Electricity Rate: <strong>₹{electricityRate}/kWh</strong>
              </label>
              <input type="range" min={4} max={15} step={0.5} value={electricityRate}
                onChange={e => setElectricityRate(parseFloat(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--accent)' }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                <span>₹4 (cheap)</span><span>₹15 (commercial)</span>
              </div>
            </div>

            <button
              className="ev-btn ev-btn-primary"
              style={{ width: '100%', justifyContent: 'center', padding: '13px 20px' }}
              onClick={calculate}
              disabled={!selectedVehicle || loading}
            >
              {loading ? 'Calculating...' : '📊 Calculate TCO'}
            </button>
          </div>

          {/* State Policy Info */}
          {policy.roadTax && (
            <div className="ev-card" style={{ padding: 20, background: 'var(--accent-soft)', border: '1px solid var(--accent)' }}>
              <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--accent-dark)', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
                <Shield size={15} /> {state.charAt(0).toUpperCase() + state.slice(1)} EV Incentives
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {[
                  `Road Tax: ${policy.roadTax}`,
                  `Registration Fees: ${policy.regFee}`,
                ].map(item => (
                  <div key={item} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--accent-dark)' }}>
                    <CheckCircle size={13} /> {item}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right — Results */}
        <div style={{ position: 'sticky', top: 80 }}>
          {!result && !selectedVehicle && (
            <div className="ev-card" style={{ padding: 40, textAlign: 'center' }}>
              <TrendingUp size={40} color="var(--border)" style={{ margin: '0 auto 16px' }} />
              <h3 style={{ fontWeight: 700, fontSize: 18, marginBottom: 8, color: 'var(--text)' }}>Calculate Your Savings</h3>
              <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>Select a vehicle and your state to see real ownership cost breakdown.</p>
            </div>
          )}

          {selectedVehicle && !result && (
            <div className="ev-card" style={{ padding: 24 }}>
              <h3 style={{ fontWeight: 700, fontSize: 17, color: 'var(--text)', marginBottom: 4 }}>
                {selectedVehicle.brand} {selectedVehicle.model}
              </h3>
              <div style={{ fontSize: 24, fontWeight: 800, color: 'var(--accent)', marginBottom: 16 }}>
                {formatPrice(selectedVehicle.approx_price_inr)}
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>Click "Calculate TCO" to see breakdown with subsidies.</p>
            </div>
          )}

          {result && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {/* Summary card */}
              <div className="ev-card" style={{ padding: 24, background: 'linear-gradient(135deg, var(--accent-soft), var(--bg-card))' }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--accent-dark)', marginBottom: 4 }}>EFFECTIVE PURCHASE PRICE</div>
                <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 32, fontWeight: 800, color: 'var(--accent)', marginBottom: 4 }}>
                  {formatPrice(selectedVehicle?.approx_price_inr - result.total_applicable_subsidies)}
                </div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                  After ₹{(result.total_applicable_subsidies / 1000).toFixed(0)}K total subsidy
                </div>
              </div>

              {/* Subsidy Breakdown */}
              <div className="ev-card" style={{ padding: 20 }}>
                <h4 style={{ fontWeight: 700, fontSize: 15, marginBottom: 14, color: 'var(--text)' }}>Subsidy Breakdown</h4>
                {[
                  { label: 'Ex-Showroom Price', value: formatPrice(selectedVehicle?.approx_price_inr) },
                  { label: 'Central Subsidy (FAME/PM E-Drive)', value: `- ${formatPrice(result.central_subsidy_inr)}`, color: 'var(--accent)' },
                  { label: `${state.charAt(0).toUpperCase() + state.slice(1)} State Subsidy`, value: `- ${formatPrice(result.state_subsidy_inr)}`, color: 'var(--accent)' },
                  { label: 'Road Tax', value: policy.roadTax === 'Waived' ? '₹0 (Waived)' : 'As applicable', color: policy.roadTax === 'Waived' ? 'var(--accent)' : undefined },
                ].map(row => (
                  <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: 14 }}>
                    <span style={{ color: 'var(--text-muted)' }}>{row.label}</span>
                    <span style={{ fontWeight: 700, color: row.color || 'var(--text)' }}>{row.value}</span>
                  </div>
                ))}
              </div>

              {/* 5-Year TCO */}
              <div className="ev-card" style={{ padding: 20 }}>
                <h4 style={{ fontWeight: 700, fontSize: 15, marginBottom: 14, color: 'var(--text)' }}>5-Year Cost of Ownership</h4>
                {[
                  { label: 'Effective Purchase Price', value: formatPrice(selectedVehicle?.approx_price_inr - result.total_applicable_subsidies) },
                  { label: `Electricity (${dailyKm}km/day × 5yr @ ₹${electricityRate}/kWh)`, value: formatPrice(Math.round(result.evCost5yr)) },
                  { label: 'Maintenance (est.)', value: '₹25K' },
                  { label: '5-Year TCO (EV)', value: formatPrice(result.tco_5year_inr), bold: true, color: 'var(--accent)' },
                ].map(row => (
                  <div key={row.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)', fontSize: 14 }}>
                    <span style={{ color: 'var(--text-muted)' }}>{row.label}</span>
                    <span style={{ fontWeight: row.bold ? 800 : 700, color: row.color || 'var(--text)' }}>{row.value}</span>
                  </div>
                ))}
                {result.evKmCost && (
                  <div style={{ marginTop: 12, padding: '10px 12px', background: 'var(--accent-soft)', borderRadius: 8, fontSize: 13, color: 'var(--accent-dark)', fontWeight: 600 }}>
                    ⚡ Running cost: ₹{result.evKmCost}/km vs ~₹6.5/km for petrol
                  </div>
                )}
              </div>

              <p style={{ fontSize: 11, color: 'var(--text-muted)', lineHeight: 1.6 }}>
                * Estimates based on industry averages. Verify with dealer for exact subsidy eligibility. Subsidies subject to change per government policy.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

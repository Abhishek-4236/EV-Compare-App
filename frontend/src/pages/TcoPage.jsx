import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Leaf, Zap, Fuel, AlertCircle, IndianRupee, MapPin } from 'lucide-react';
import { Link } from 'react-router-dom';

const MotionDiv = motion.div;

export default function TcoPage() {
  const [dailyKm, setDailyKm] = useState(40);
  const [petrolPrice, setPetrolPrice] = useState(105);
  const [petrolMlg, setPetrolMlg] = useState(15);
  
  const [electricityRate, setElectricityRate] = useState(8);
  const [evRangePerKwh, setEvRangePerKwh] = useState(7);
  
  const [petrolServiceYearly, setPetrolServiceYearly] = useState(12000);
  const [evServiceYearly, setEvServiceYearly] = useState(4000);

  const [carPriceDiff, setCarPriceDiff] = useState(300000); // e.g. EV costs 3L more upfront

  const stats = useMemo(() => {
    const daysPerYear = 330; // Commute days roughly
    const yearlyKm = dailyKm * daysPerYear;
    
    // Petrol Yearly Cost
    const petrolYearlyFuel = (yearlyKm / petrolMlg) * petrolPrice;
    const petrolYearlyTotal = petrolYearlyFuel + petrolServiceYearly;
    const petrol5Year = petrolYearlyTotal * 5;

    // EV Yearly Cost
    const evYearlyFuel = (yearlyKm / evRangePerKwh) * electricityRate;
    const evYearlyTotal = evYearlyFuel + evServiceYearly;
    const ev5Year = evYearlyTotal * 5;

    // Savings
    const yearlySavings = petrolYearlyTotal - evYearlyTotal;
    const fiveYearSavings = petrol5Year - ev5Year;
    const net5YearSavings = fiveYearSavings - carPriceDiff; // After absorbing upfront difference

    // Break even point (in years)
    const breakEvenYears = carPriceDiff / yearlySavings;

    return {
      yearlyKm,
      petrolYearlyFuel,
      evYearlyFuel,
      petrol5Year,
      ev5Year,
      yearlySavings,
      fiveYearSavings,
      net5YearSavings,
      breakEvenYears
    };
  }, [dailyKm, petrolPrice, petrolMlg, electricityRate, evRangePerKwh, petrolServiceYearly, evServiceYearly, carPriceDiff]);

  const formatRupee = (val) => new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(val);

  return (
    <div className="ev-tco-page" style={{ paddingTop: '80px', paddingBottom: '60px', minHeight: '100vh', background: 'var(--bg)' }}>
      <div className="ev-container" style={{ maxWidth: '1000px', margin: '0 auto', padding: '0 20px' }}>
        
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <h1 style={{ fontSize: 36, fontFamily: 'Space Grotesk', letterSpacing: '-1px', marginBottom: 12 }}>Total Cost of Ownership</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: 16, maxWidth: 600, margin: '0 auto' }}>
            Calculate exactly how much you'll save driving an Electric Vehicle compared to a traditional Petrol car over 5 years.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }} className="ev-tco-layout">
          
          <MotionDiv 
            initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4 }}
            className="ev-tco-controls" 
            style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 20, border: '1px solid var(--border)' }}
          >
            <h3 style={{ fontSize: 18, marginBottom: 24, display: 'flex', alignItems: 'center', gap: 8 }}><MapPin size={18} color="var(--accent)" /> Usage Metrics</h3>
            
            <div className="tco-slider-group">
              <div className="slider-header">
                <label>Daily Driving Distance</label>
                <span>{dailyKm} km</span>
              </div>
              <input type="range" min="10" max="250" value={dailyKm} onChange={e => setDailyKm(Number(e.target.value))} />
              <div className="slider-hint">Roughly {stats.yearlyKm.toLocaleString()} km per year</div>
            </div>

            <div className="tco-slider-group">
              <div className="slider-header">
                <label>EV Premium (Upfront Cost Diff)</label>
                <span>{formatRupee(carPriceDiff)}</span>
              </div>
              <input type="range" min="0" max="1000000" step="50000" value={carPriceDiff} onChange={e => setCarPriceDiff(Number(e.target.value))} />
              <div className="slider-hint">How much more expensive is the EV to buy?</div>
            </div>

            <h3 style={{ fontSize: 18, margin: '32px 0 24px', display: 'flex', alignItems: 'center', gap: 8 }}><Fuel size={18} color="#ef4444" /> Petrol Assumptions</h3>
            
            <div style={{ display: 'flex', gap: 16 }}>
              <div className="ev-input-box" style={{ flex: 1 }}>
                <label>Petrol Price (₹/L)</label>
                <input type="number" value={petrolPrice} onChange={e => setPetrolPrice(Number(e.target.value))} />
              </div>
              <div className="ev-input-box" style={{ flex: 1 }}>
                <label>Car Mileage (kmpl)</label>
                <input type="number" value={petrolMlg} onChange={e => setPetrolMlg(Number(e.target.value))} />
              </div>
            </div>
            
            <div className="ev-input-box" style={{ marginTop: 16 }}>
              <label>Yearly Maintenance (₹)</label>
              <input type="number" value={petrolServiceYearly} onChange={e => setPetrolServiceYearly(Number(e.target.value))} />
            </div>

            <h3 style={{ fontSize: 18, margin: '32px 0 24px', display: 'flex', alignItems: 'center', gap: 8 }}><Zap size={18} color="#0ea5e9" /> EV Assumptions</h3>
            
            <div style={{ display: 'flex', gap: 16 }}>
              <div className="ev-input-box" style={{ flex: 1 }}>
                <label>Electricity Rate (₹/kWh)</label>
                <input type="number" value={electricityRate} onChange={e => setElectricityRate(Number(e.target.value))} />
              </div>
              <div className="ev-input-box" style={{ flex: 1 }}>
                <label>EV Efficiency (km/kWh)</label>
                <input type="number" value={evRangePerKwh} onChange={e => setEvRangePerKwh(Number(e.target.value))} />
              </div>
            </div>
            
            <div className="ev-input-box" style={{ marginTop: 16 }}>
              <label>Yearly Maintenance (₹)</label>
              <input type="number" value={evServiceYearly} onChange={e => setEvServiceYearly(Number(e.target.value))} />
            </div>

          </MotionDiv>

          <MotionDiv 
            initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.4 }}
            className="ev-tco-results"
          >
            <div style={{ background: 'var(--accent-dark)', color: 'white', padding: 30, borderRadius: 24, marginBottom: 24, position: 'relative', overflow: 'hidden' }}>
              <div style={{ position: 'absolute', top: -30, right: -20, opacity: 0.1 }}><Leaf size={160} /></div>
              <div style={{ position: 'relative', zIndex: 2 }}>
                <div style={{ fontSize: 14, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', opacity: 0.8, marginBottom: 8 }}>Net 5-Year Savings</div>
                <div style={{ fontSize: 48, fontWeight: 700, letterSpacing: '-2px', fontFamily: 'Space Grotesk' }}>
                  {stats.net5YearSavings > 0 ? '+' : ''}{formatRupee(stats.net5YearSavings)}
                </div>
                <div style={{ fontSize: 14, opacity: 0.9, marginTop: 12 }}>
                  After absorbing the {formatRupee(carPriceDiff)} upfront EV premium.
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 16, marginBottom: 24 }}>
              <div style={{ flex: 1, background: 'color-mix(in srgb, #ef4444 8%, var(--bg-card))', border: '1px solid color-mix(in srgb, #ef4444 20%, transparent)', padding: 20, borderRadius: 16 }}>
                <div style={{ color: '#ef4444', fontSize: 12, fontWeight: 700, marginBottom: 8 }}><Fuel size={14} style={{ display: 'inline', verticalAlign: '-2px', marginRight: 4 }}/> Petrol 5Yr Cost</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text)' }}>{formatRupee(stats.petrol5Year)}</div>
              </div>
              <div style={{ flex: 1, background: 'color-mix(in srgb, #0ea5e9 8%, var(--bg-card))', border: '1px solid color-mix(in srgb, #0ea5e9 20%, transparent)', padding: 20, borderRadius: 16 }}>
                <div style={{ color: '#0ea5e9', fontSize: 12, fontWeight: 700, marginBottom: 8 }}><Zap size={14} style={{ display: 'inline', verticalAlign: '-2px', marginRight: 4 }}/> EV 5Yr Cost</div>
                <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--text)' }}>{formatRupee(stats.ev5Year)}</div>
              </div>
            </div>

            <div style={{ background: 'var(--bg-card)', padding: 24, borderRadius: 20, border: '1px solid var(--border)' }}>
              <h4 style={{ fontSize: 16, marginBottom: 20 }}>Investment Breakdown</h4>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 12, borderBottom: '1px solid var(--border)', marginBottom: 12, fontSize: 14 }}>
                <span style={{ color: 'var(--text-muted)' }}>Running Fuel Cost / Year</span>
                <span style={{ fontWeight: 600 }}>{formatRupee(stats.evYearlyFuel)} <span style={{ color: 'var(--text-muted)', fontSize: 12, fontWeight: 400 }}>(vs {formatRupee(stats.petrolYearlyFuel)})</span></span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 12, borderBottom: '1px solid var(--border)', marginBottom: 12, fontSize: 14 }}>
                <span style={{ color: 'var(--text-muted)' }}>Pure Running Savings / Year</span>
                <span style={{ fontWeight: 600, color: 'var(--accent)' }}>+{formatRupee(stats.yearlySavings)}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, alignItems: 'center' }}>
                <span style={{ color: 'var(--text-muted)' }}>Break-even Duration</span>
                <span style={{ fontWeight: 700, fontSize: 18 }}>
                  {stats.breakEvenYears < 0 ? 'Instant' : stats.breakEvenYears > 10 ? '10+ Years' : `${stats.breakEvenYears.toFixed(1)} Years`}
                </span>
              </div>
              
              {stats.breakEvenYears > 5 && (
                <div style={{ marginTop: 20, padding: 12, borderRadius: 12, background: 'color-mix(in srgb, #f59e0b 12%, transparent)', color: '#d97706', fontSize: 12, display: 'flex', gap: 8 }}>
                  <AlertCircle size={16} style={{ flexShrink: 0 }} />
                  It will take longer than 5 years to recover the premium price of the EV based on your low daily driving distance.
                </div>
              )}
            </div>

            <div style={{ marginTop: 20, textAlign: 'center' }}>
              <Link to="/browse" className="btn-primary" style={{ display: 'inline-block', width: '100%', padding: '14px', borderRadius: '12px', background: 'var(--accent)', color: 'white', textDecoration: 'none', fontWeight: 600, fontSize: 15 }}>
                Browse EVs Now
              </Link>
            </div>

          </MotionDiv>
        </div>
      </div>

      <style>{`
        .tco-slider-group { margin-bottom: 24px; }
        .tco-slider-group .slider-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 8px; }
        .tco-slider-group label { font-size: 13px; font-weight: 600; color: var(--text-muted); }
        .tco-slider-group span { font-size: 15px; font-weight: 700; color: var(--accent); }
        .tco-slider-group input[type="range"] {
          width: 100%;
          accent-color: var(--accent);
          height: 6px;
          border-radius: 4px;
          background: var(--bg-muted);
          outline: none;
          -webkit-appearance: none;
        }
        .tco-slider-group input[type="range"]::-webkit-slider-thumb {
          -webkit-appearance: none;
          width: 18px;
          height: 18px;
          border-radius: 50%;
          background: var(--accent);
          cursor: pointer;
        }
        .tco-slider-group .slider-hint { font-size: 11px; color: var(--text-muted); margin-top: 6px; }

        .ev-input-box label { display: block; font-size: 11px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; margin-bottom: 6px; }
        .ev-input-box input {
          width: 100%;
          padding: 10px 14px;
          border-radius: 10px;
          border: 1px solid var(--border);
          background: var(--bg);
          color: var(--text);
          font-size: 14px;
          font-weight: 600;
          outline: none;
          transition: border-color 0.2s;
        }
        .ev-input-box input:focus { border-color: var(--accent); }

        @media (max-width: 768px) {
          .ev-tco-layout { grid-template-columns: 1fr !important; }
        }
      `}</style>
    </div>
  );
}

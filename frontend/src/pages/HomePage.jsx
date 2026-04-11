import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { Zap, ArrowRight, GitCompare, MessageSquare, MapPin, TrendingUp, Shield, RefreshCw, Star, ChevronRight, CheckCircle } from 'lucide-react';
import { vehicleAPI } from '../services/api';
import VehicleCard from '../components/VehicleCard';
import Footer from '../components/Footer';

const SEGMENTS = [
  { label: '2-Wheelers', icon: '🛵', category: '2W', desc: 'Scooters & motorcycles', color: '#fef9c3', textColor: '#854d0e' },
  { label: 'Cars & SUVs', icon: '🚗', category: '4W', desc: 'Sedans, hatchbacks & SUVs', color: '#dcfce7', textColor: '#166534' },
  { label: '3-Wheelers', icon: '🛺', category: '3W', desc: 'Autos & cargo carriers', color: '#dbeafe', textColor: '#1e40af' },
  { label: 'Trucks', icon: '🚛', category: 'Truck', desc: 'Commercial freight EVs', color: '#fce7f3', textColor: '#9d174d' },
  { label: 'Buses', icon: '🚌', category: 'Bus', desc: 'City & intercity EVs', color: '#ede9fe', textColor: '#5b21b6' },
];

const FEATURES = [
  { icon: <GitCompare size={22} />, title: 'Side-by-Side Compare', desc: 'Compare up to 4 EVs on price, range, charging, battery, and total cost.' },
  { icon: <MessageSquare size={22} />, title: 'AI EV Assistant', desc: 'Ask in plain language. Get grounded answers from India\'s EV database.' },
  { icon: <MapPin size={22} />, title: 'Charging Map', desc: 'Find charging stations by city with live connector and speed filters.' },
  { icon: <TrendingUp size={22} />, title: 'TCO Calculator', desc: 'Calculate 5-year ownership cost including subsidies, electricity, and EMI.' },
  { icon: <Shield size={22} />, title: 'Subsidy Intelligence', desc: 'State-wise FAME II and PM E-DRIVE benefits, updated regularly.' },
  { icon: <RefreshCw size={22} />, title: 'All Segments', desc: 'EVs from scooters and autos to buses and trucks, all India-focused.' },
];

const CHAT_DEMO = [
  { role: 'bot', text: 'Hi! I\'m your India EV advisor. What are you looking for?' },
  { role: 'user', text: 'Best scooter under ₹1.2L with 100km range?' },
  { role: 'bot', text: '🛵 Top picks: Ola S1 X (₹99K), Bajaj Chetak (₹1.15L), Okaya Freedum. Ola has the best range/price ratio. Want a comparison?' },
];

const FAQ = [
  { q: 'Which segment has the most EVs in India?', a: '2-wheelers (scooters & bikes) have the largest selection with 30+ models across all budgets, from ₹60,000 to ₹2L.' },
  { q: 'Is FAME II still active?', a: 'FAME II ended in March 2024. The new PM E-Drive scheme is active with ₹10,900 Cr allocated for 2-wheelers, 3-wheelers, and e-buses.' },
  { q: 'How accurate is the TCO calculator?', a: 'TCO figures use industry-standard assumptions for electricity cost (₹8/kWh), maintenance, insurance, and battery degradation. Actual costs will vary.' },
  { q: 'Can I compare commercial EVs like trucks and buses?', a: 'Yes! EViq covers all segments including trucks, buses, and 3-wheelers — not just cars and scooters.' },
];

function FAQItem({ q, a }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="ev-card" style={{ overflow: 'hidden', cursor: 'pointer' }} onClick={() => setOpen(o => !o)}>
      <div style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16 }}>
        <span style={{ fontWeight: 600, fontSize: 15, color: 'var(--text)' }}>{q}</span>
        <ChevronRight size={18} color="var(--text-muted)" style={{ transform: open ? 'rotate(90deg)' : 'none', transition: 'transform 0.2s', flexShrink: 0 }} />
      </div>
      {open && (
        <div style={{ padding: '0 20px 16px', color: 'var(--text-muted)', fontSize: 14, lineHeight: 1.7, borderTop: '1px solid var(--border)' }}>
          <div style={{ paddingTop: 12 }}>{a}</div>
        </div>
      )}
    </div>
  );
}

export default function HomePage() {
  const [popular, setPopular] = useState([]);
  const [loadingCards, setLoadingCards] = useState(true);
  const [stats, setStats] = useState({ total: 65, segments: 5, brands: 20 });

  useEffect(() => {
    vehicleAPI.getAll({ limit: 6, sort_by: 'overall_rating', sort_order: 'DESC' })
      .then(res => {
        setPopular(res.data.vehicles || []);
        setStats(s => ({ ...s, total: res.data.total || 65 }));
      })
      .catch(() => {})
      .finally(() => setLoadingCards(false));
  }, []);

  return (
    <>
      <main className="ev-hero-gradient">
        {/* ===== HERO ===== */}
        <section style={{ maxWidth: 1280, margin: '0 auto', padding: '64px 20px 48px' }}>
          <div style={{ textAlign: 'center', marginBottom: 48 }}>
            <div className="ev-section-label" style={{ justifyContent: 'center', display: 'flex', marginBottom: 16 }}>
              <span style={{ background: 'var(--accent-soft)', padding: '4px 14px', borderRadius: 99, color: 'var(--accent-dark)', fontWeight: 700, fontSize: 12, letterSpacing: '1px' }}>
                🇮🇳 INDIA'S OPEN EV PLATFORM
              </span>
            </div>
            <h1 style={{
              fontFamily: "'Space Grotesk', sans-serif",
              fontSize: 'clamp(32px, 6vw, 60px)',
              fontWeight: 800,
              lineHeight: 1.1,
              letterSpacing: '-1.5px',
              color: 'var(--text)',
              marginBottom: 20,
            }}>
              One platform. 2-Wheelers<br />to Buses.{' '}
              <span style={{ color: 'var(--accent)' }}>Every Indian EV.</span>
            </h1>
            <p style={{ color: 'var(--text-muted)', fontSize: 18, lineHeight: 1.7, maxWidth: 560, margin: '0 auto 32px' }}>
              Compare EVs, check real subsidies, calculate ownership cost, find charging stations, and get AI guidance — all in one place.
            </p>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Link to="/browse" className="ev-btn ev-btn-primary" style={{ padding: '13px 28px', fontSize: 15 }}>
                Browse EVs <ArrowRight size={16} />
              </Link>
              <Link to="/chat" className="ev-btn" style={{ padding: '13px 28px', fontSize: 15 }}>
                <MessageSquare size={16} /> Ask AI
              </Link>
              <Link to="/compare" className="ev-btn" style={{ padding: '13px 28px', fontSize: 15 }}>
                <GitCompare size={16} /> Compare
              </Link>
            </div>
          </div>

          {/* Stats Row */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12, maxWidth: 800, margin: '0 auto' }}>
            {[
              { value: `${stats.total}+`, label: 'EV Models' },
              { value: '5', label: 'Segments' },
              { value: '6', label: 'State Subsidies' },
              { value: '₹60K–₹3Cr', label: 'Price Range' },
            ].map(s => (
              <div key={s.label} className="ev-stat-card" style={{ textAlign: 'center', padding: 16 }}>
                <div className="ev-stat-value" style={{ fontSize: 22 }}>{s.value}</div>
                <div className="ev-stat-label">{s.label}</div>
              </div>
            ))}
          </div>
        </section>

        {/* ===== BROWSE BY SEGMENT ===== */}
        <section className="ev-shell" style={{ paddingTop: 0 }}>
          <div style={{ marginBottom: 24 }}>
            <div className="ev-section-label">All Segments</div>
            <h2 className="ev-section-title">Browse by Category</h2>
            <p className="ev-section-desc">From daily commuter scooters to long-haul commercial trucks.</p>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 12 }}>
            {SEGMENTS.map(seg => (
              <Link
                key={seg.category}
                to={`/browse?category=${seg.category}`}
                className="ev-card ev-card-hover"
                style={{ padding: '20px 16px', textAlign: 'center', textDecoration: 'none', display: 'block' }}
              >
                <div style={{ fontSize: 44, marginBottom: 10 }}>{seg.icon}</div>
                <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text)', marginBottom: 4 }}>{seg.label}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.4 }}>{seg.desc}</div>
              </Link>
            ))}
          </div>
        </section>

        {/* ===== POPULAR EVs ===== */}
        <section className="ev-shell" style={{ paddingTop: 0, marginTop: 48 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
            <div>
              <div className="ev-section-label">Top Rated</div>
              <h2 className="ev-section-title">Popular EVs</h2>
            </div>
            <Link to="/browse" className="ev-btn ev-btn-sm">View all <ChevronRight size={14} /></Link>
          </div>

          {loadingCards ? (
            <div className="ev-grid-auto">
              {[...Array(6)].map((_, i) => (
                <div key={i} style={{ borderRadius: 14, overflow: 'hidden' }}>
                  <div className="ev-skeleton" style={{ height: 160 }} />
                  <div style={{ padding: 14, background: 'var(--bg-card)', border: '1px solid var(--border)', borderTop: 0, borderRadius: '0 0 14px 14px' }}>
                    <div className="ev-skeleton" style={{ height: 14, width: '60%', marginBottom: 8 }} />
                    <div className="ev-skeleton" style={{ height: 20, width: '40%', marginBottom: 12 }} />
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                      <div className="ev-skeleton" style={{ height: 40 }} />
                      <div className="ev-skeleton" style={{ height: 40 }} />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="ev-grid-auto">
              {popular.map(v => (
                <VehicleCard key={v.id} vehicle={v} />
              ))}
            </div>
          )}
        </section>

        {/* ===== FEATURES ===== */}
        <section className="ev-shell" style={{ paddingTop: 0, marginTop: 64 }}>
          <div style={{ textAlign: 'center', marginBottom: 40 }}>
            <div className="ev-section-label" style={{ justifyContent: 'center', display: 'flex' }}>Why EViq</div>
            <h2 className="ev-section-title">Better than any single EV site</h2>
          </div>
          <div className="ev-grid-3" style={{ gap: 14 }}>
            {FEATURES.map(f => (
              <div key={f.title} className="ev-card" style={{ padding: 24 }}>
                <div style={{ width: 44, height: 44, borderRadius: 12, background: 'var(--accent-soft)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)', marginBottom: 14 }}>
                  {f.icon}
                </div>
                <h3 style={{ fontWeight: 700, fontSize: 16, marginBottom: 6, color: 'var(--text)' }}>{f.title}</h3>
                <p style={{ color: 'var(--text-muted)', fontSize: 14, lineHeight: 1.6 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* ===== CTA SPLIT SECTION ===== */}
        <section className="ev-shell" style={{ paddingTop: 0, marginTop: 64 }}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            {/* AI Chat Preview */}
            <div className="ev-card" style={{ padding: 28, background: 'linear-gradient(135deg, var(--accent-soft), var(--bg-card))' }}>
              <div style={{ marginBottom: 16 }}>
                <div className="ev-section-label">Powered by AI</div>
                <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 22, fontWeight: 700, color: 'var(--text)', marginBottom: 8 }}>
                  Your EV Buying Assistant
                </h3>
                <p style={{ color: 'var(--text-muted)', fontSize: 14, lineHeight: 1.6 }}>
                  Ask in plain language, get grounded answers from our database.
                </p>
              </div>
              {/* Mini chat preview */}
              <div style={{ background: 'var(--bg-card)', borderRadius: 12, border: '1px solid var(--border)', overflow: 'hidden', marginBottom: 16 }}>
                <div style={{ padding: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {CHAT_DEMO.map((m, i) => (
                    <div key={i} style={{
                      maxWidth: '80%', padding: '8px 12px', borderRadius: 10, fontSize: 13, lineHeight: 1.5,
                      background: m.role === 'user' ? 'var(--accent)' : 'var(--bg-muted)',
                      color: m.role === 'user' ? 'white' : 'var(--text)',
                      alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
                    }}>
                      {m.text}
                    </div>
                  ))}
                </div>
              </div>
              <Link to="/chat" className="ev-btn ev-btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
                <MessageSquare size={15} /> Start EV Chat
              </Link>
            </div>

            {/* Subsidy/TCO CTA */}
            <div className="ev-card" style={{ padding: 28 }}>
              <div style={{ marginBottom: 16 }}>
                <div className="ev-section-label">Smart Calculator</div>
                <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 22, fontWeight: 700, color: 'var(--text)', marginBottom: 8 }}>
                  Real Ownership Cost
                </h3>
                <p style={{ color: 'var(--text-muted)', fontSize: 14, lineHeight: 1.6 }}>
                  State-wise subsidies + 5-year TCO. Know the real price before you buy.
                </p>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 20 }}>
                {[
                  'FAME II & PM E-Drive subsidies',
                  'State-specific road tax waivers',
                  '5-year electricity + maintenance cost',
                  'Financed vs upfront comparison',
                ].map(item => (
                  <div key={item} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 14, color: 'var(--text)' }}>
                    <CheckCircle size={16} color="var(--accent)" /> {item}
                  </div>
                ))}
              </div>
              <Link to="/subsidies" className="ev-btn ev-btn-primary" style={{ width: '100%', justifyContent: 'center' }}>
                <TrendingUp size={15} /> Calculate TCO
              </Link>
            </div>
          </div>
        </section>

        {/* ===== FAQ ===== */}
        <section className="ev-shell" style={{ paddingTop: 0, marginTop: 64 }}>
          <div style={{ textAlign: 'center', marginBottom: 32 }}>
            <div className="ev-section-label" style={{ justifyContent: 'center', display: 'flex' }}>FAQ</div>
            <h2 className="ev-section-title">Common Questions</h2>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 720, margin: '0 auto' }}>
            {FAQ.map(f => <FAQItem key={f.q} {...f} />)}
          </div>
        </section>
      </main>

      <div className="ev-shell" style={{ paddingTop: 0, paddingBottom: 0 }}>
        <Footer />
      </div>
    </>
  );
}

import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
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
const MotionDiv = motion.div;

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
  const [stats] = useState({ total: 65, segments: 5, brands: 20 });

  useEffect(() => {
    vehicleAPI.getDiverseFeatured()
      .then(res => {
        setPopular(res.data.vehicles || []);
      })
      .catch(() => {})
      .finally(() => setLoadingCards(false));
  }, []);

  return (
    <>
      <main className="ev-hero-gradient">
        <section className="ev-home-hero">
          <MotionDiv
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
            className="ev-home-hero-grid"
          >
            <div>
              <div style={{ marginBottom: 12 }}>
                <div className="ev-section-label" style={{ marginBottom: 8 }}>
                  India EV Decision Platform
                </div>
              </div>
              <h1 className="ev-home-hero-title" style={{ fontSize: 'clamp(40px, 6vw, 64px)', letterSpacing: '-1.5px', marginBottom: 12 }}>
                EV decisions, simplified.
              </h1>
              <p className="ev-home-hero-copy" style={{ fontSize: 16, marginBottom: 20 }}>
                Intelligent comparisons and AI insights for every segment—from scooters to trucks.
              </p>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 26 }}>
                <Link to="/browse" className="ev-btn ev-btn-primary" style={{ padding: '13px 28px', fontSize: 15 }}>
                  Browse EVs <ArrowRight size={16} />
                </Link>
                <Link to="/chat" className="ev-btn" style={{ padding: '13px 28px', fontSize: 15 }}>
                  <MessageSquare size={16} /> Ask AI
                </Link>
              </div>
            </div>

            <div className="ev-home-hero-panel">
              <div className="ev-home-panel-top">
                <span>Quick selection</span>
              </div>
              <div className="ev-home-panel-copy">
                <div className="ev-home-panel-card featured" style={{ padding: '20px 24px' }}>
                  <div className="eyebrow">Smart Shortlist</div>
                  <h3 style={{ fontSize: 22, lineHeight: 1.1, marginBottom: 0 }}>Find your perfect EV match in minutes.</h3>
                </div>
                <div className="ev-home-panel-stats" style={{ gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
                  {[
                    { value: `${stats.total}+`, label: 'EV models' },
                    { value: '5', label: 'Segments' },
                    { value: 'AI', label: 'Insights' },
                  ].map(item => (
                    <div key={item.label} className="ev-home-mini-stat" style={{ border: 'none', background: 'var(--bg-card)', padding: '12px 10px' }}>
                      <strong style={{ fontSize: 20 }}>{item.value}</strong>
                      <span style={{ fontSize: 10 }}>{item.label}</span>
                    </div>
                  ))}
                </div>
                <div className="ev-home-panel-card subtle" style={{ padding: '12px 20px', background: 'transparent' }}>
                  <p style={{ fontSize: 12, opacity: 0.8 }}>Pro Tip: TCO includes state-wise subsidies & road tax.</p>
                </div>
              </div>
            </div>
          </MotionDiv>

          <MotionDiv
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.55, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            style={{ maxWidth: 900, margin: '38px auto 0' }}
          >
            <div className="ev-section-label" style={{ justifyContent: 'center', display: 'flex', marginBottom: 16 }}>
              <span style={{ background: 'var(--accent-soft)', padding: '4px 14px', borderRadius: 99, color: 'var(--accent-dark)', fontWeight: 700, fontSize: 12, letterSpacing: '1px' }}>
                🇮🇳 INDIA'S OPEN EV PLATFORM
              </span>
            </div>
          </MotionDiv>

          <div className="ev-home-stat-grid">
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

        <section className="ev-shell" style={{ paddingTop: 0 }}>
          <div style={{ marginBottom: 24 }}>
            <div className="ev-section-label">All Segments</div>
            <h2 className="ev-section-title">Browse by Category</h2>
            <p className="ev-section-desc">From daily commuter scooters to long-haul commercial trucks.</p>
          </div>
          <div className="ev-home-segment-grid">
            {SEGMENTS.map(seg => (
              <Link
                key={seg.category}
                to={`/browse?category=${seg.category}`}
                className="ev-card ev-card-hover ev-home-segment-card"
              >
                <div style={{ fontSize: 44, marginBottom: 10 }}>{seg.icon}</div>
                <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text)', marginBottom: 4 }}>{seg.label}</div>
                <div style={{ fontSize: 12, color: 'var(--text-muted)', lineHeight: 1.4 }}>{seg.desc}</div>
              </Link>
            ))}
          </div>
        </section>

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

        {/* Why EViq - Minimalist version */}
        <section className="ev-shell" style={{ paddingTop: 0, marginTop: 48 }}>
          <div className="ev-card" style={{ padding: '24px 32px', background: 'var(--accent-soft)', border: 'none' }}>
            <div style={{ display: 'flex', gap: 40, flexWrap: 'wrap', justifyContent: 'center', alignItems: 'center' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontWeight: 700, fontSize: 18, color: 'var(--text)' }}>Smart Compare</div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Side-by-side specs</div>
              </div>
              <div style={{ height: 24, width: 1, background: 'var(--border)', opacity: 0.5 }} className="hidden sm:block"></div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontWeight: 700, fontSize: 18, color: 'var(--text)' }}>AI Advisor</div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Grounded answers</div>
              </div>
              <div style={{ height: 24, width: 1, background: 'var(--border)', opacity: 0.5 }} className="hidden sm:block"></div>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontWeight: 700, fontSize: 18, color: 'var(--text)' }}>Exact TCO</div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>Subsidy inclusive</div>
              </div>
            </div>
          </div>
        </section>

        <section className="ev-shell" style={{ paddingTop: 0, marginTop: 64 }}>
          <div className="ev-home-tool-grid">
            <div className="ev-card ev-home-tool-card" style={{ padding: 28, background: 'linear-gradient(135deg, var(--accent-soft), var(--bg-card))' }}>
              <div style={{ marginBottom: 16 }}>
                <div className="ev-section-label">Powered by AI</div>
                <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 22, fontWeight: 700, color: 'var(--text)', marginBottom: 8 }}>
                  Your EV Buying Assistant
                </h3>
                <p style={{ color: 'var(--text-muted)', fontSize: 14, lineHeight: 1.6 }}>
                  Ask in plain language, get grounded answers from our database.
                </p>
              </div>
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

            <div className="ev-card ev-home-tool-card" style={{ padding: 28 }}>
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

        <section className="ev-shell" style={{ paddingTop: 0, marginTop: 48 }}>
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <h2 className="ev-section-title" style={{ fontSize: 24 }}>Common Questions</h2>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxWidth: 680, margin: '0 auto' }}>
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

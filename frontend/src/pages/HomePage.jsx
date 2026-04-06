import { Link } from 'react-router-dom';

const SEGMENTS = [
  { label: '2W Scooters', emoji: '🛵', category: '2W', type: 'scooter' },
  { label: '2W Motorcycles', emoji: '🏍️', category: '2W', type: 'motorcycle' },
  { label: '4W Cars/SUVs', emoji: '🚗', category: '4W', type: '' },
  { label: '3W Vehicles', emoji: '🛺', category: '3W', type: '' },
  { label: 'Electric Buses', emoji: '🚌', category: 'Bus', type: '' },
  { label: 'EV Trucks', emoji: '🚛', category: 'Truck', type: '' },
];

function HomePage() {
  return (
    <div style={styles.container}>
      <div style={styles.hero}>
        <h1 style={styles.title}>⚡ India EV Comparison</h1>
        <p style={styles.subtitle}>
          Compare 65+ Electric Vehicles across all segments.
          Find the best EV for your budget and needs.
        </p>
        <Link to="/browse" style={styles.ctaBtn}>Browse All EVs →</Link>
      </div>

      <h2 style={styles.sectionTitle}>Browse by Segment</h2>
      <div style={styles.grid}>
        {SEGMENTS.map((seg) => (
          <Link
            key={seg.label}
            to={`/browse?category=${seg.category}`}
            style={styles.card}
          >
            <div style={styles.emoji}>{seg.emoji}</div>
            <div style={styles.cardLabel}>{seg.label}</div>
          </Link>
        ))}
      </div>

      <div style={styles.stats}>
        <div style={styles.stat}><strong>65+</strong><span>EV Models</span></div>
        <div style={styles.stat}><strong>5</strong><span>Segments</span></div>
        <div style={styles.stat}><strong>6</strong><span>States</span></div>
        <div style={styles.stat}><strong>₹59K–₹2Cr</strong><span>Price Range</span></div>
      </div>
    </div>
  );
}

const styles = {
  container: { maxWidth: '1200px', margin: '0 auto', padding: '2rem' },
  hero: {
    textAlign: 'center', padding: '4rem 2rem',
    background: 'linear-gradient(135deg, #1a1a2e, #16213e)',
    borderRadius: '16px', marginBottom: '3rem', color: 'white',
  },
  title: { fontSize: '3rem', marginBottom: '1rem', color: '#00d4ff' },
  subtitle: { fontSize: '1.2rem', marginBottom: '2rem', opacity: 0.8 },
  ctaBtn: {
    padding: '1rem 2rem', backgroundColor: '#00d4ff',
    color: '#1a1a2e', borderRadius: '8px', textDecoration: 'none',
    fontWeight: 'bold', fontSize: '1.1rem',
  },
  sectionTitle: { fontSize: '1.8rem', marginBottom: '1.5rem', color: '#1a1a2e' },
  grid: {
    display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '1.5rem', marginBottom: '3rem',
  },
  card: {
    display: 'flex', flexDirection: 'column', alignItems: 'center',
    padding: '2rem', backgroundColor: '#f8f9fa', borderRadius: '12px',
    textDecoration: 'none', color: '#1a1a2e', border: '2px solid #e9ecef',
    transition: 'transform 0.2s',
  },
  emoji: { fontSize: '3rem', marginBottom: '1rem' },
  cardLabel: { fontWeight: 'bold', fontSize: '1rem' },
  stats: {
    display: 'flex', justifyContent: 'space-around',
    padding: '2rem', backgroundColor: '#1a1a2e',
    borderRadius: '12px', color: 'white',
  },
  stat: {
    display: 'flex', flexDirection: 'column',
    alignItems: 'center', gap: '0.5rem',
    fontSize: '1.2rem',
  },
};

export default HomePage;
import { Link } from 'react-router-dom';

function formatPrice(p) {
  if (p >= 10000000) return `₹${(p / 10000000).toFixed(2)}Cr`;
  if (p >= 100000) return `₹${(p / 100000).toFixed(1)}L`;
  return `₹${(p / 1000).toFixed(0)}K`;
}

function VehicleCard({ vehicle, onCompareToggle, isSelected }) {
  return (
    <div style={{ ...styles.card, ...(isSelected ? styles.selected : {}) }}>
      <div style={styles.badge}>{vehicle.category} • {vehicle.wheel_type}</div>
      <div style={styles.body}>
        <h3 style={styles.name}>{vehicle.brand} {vehicle.model}</h3>
        <div style={styles.price}>{formatPrice(vehicle.approx_price_inr)}</div>
        <div style={styles.specs}>
          <span>🔋 {vehicle.range_km} km</span>
          <span>⚡ {vehicle.battery_kwh} kWh</span>
          <span>🏎 {vehicle.top_speed_kmh} kmph</span>
        </div>
        {vehicle.fame2_subsidy_inr > 0 && (
          <div style={styles.subsidy}>
            FAME II: -{formatPrice(vehicle.fame2_subsidy_inr)}
          </div>
        )}
        <div style={styles.actions}>
          <Link to={`/vehicle/${vehicle.id}`} style={styles.detailBtn}>
            Details
          </Link>
          <button
            style={{ ...styles.compareBtn, ...(isSelected ? styles.activeBtn : {}) }}
            onClick={() => onCompareToggle && onCompareToggle(vehicle.id)}
          >
            {isSelected ? '✓ Added' : '+ Compare'}
          </button>
        </div>
      </div>
    </div>
  );
}

const styles = {
  card: {
    border: '1px solid #e9ecef', borderRadius: '12px',
    overflow: 'hidden', backgroundColor: 'white',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
  },
  selected: { border: '2px solid #00d4ff' },
  badge: {
    padding: '0.4rem 1rem', backgroundColor: '#1a1a2e',
    color: '#00d4ff', fontSize: '0.8rem', fontWeight: 'bold',
  },
  body: { padding: '1rem' },
  name: { margin: '0 0 0.5rem', fontSize: '1.1rem' },
  price: { fontSize: '1.4rem', fontWeight: 'bold', color: '#1a1a2e', marginBottom: '0.5rem' },
  specs: { display: 'flex', gap: '0.8rem', fontSize: '0.85rem', marginBottom: '0.5rem', flexWrap: 'wrap' },
  subsidy: {
    fontSize: '0.8rem', color: '#16a34a',
    backgroundColor: '#dcfce7', padding: '0.2rem 0.5rem',
    borderRadius: '4px', marginBottom: '0.5rem', display: 'inline-block',
  },
  actions: { display: 'flex', gap: '0.5rem', marginTop: '0.8rem' },
  detailBtn: {
    padding: '0.4rem 0.8rem', backgroundColor: '#1a1a2e',
    color: 'white', borderRadius: '6px', textDecoration: 'none', fontSize: '0.85rem',
  },
  compareBtn: {
    padding: '0.4rem 0.8rem', backgroundColor: '#f1f5f9',
    border: '1px solid #cbd5e1', borderRadius: '6px',
    cursor: 'pointer', fontSize: '0.85rem',
  },
  activeBtn: { backgroundColor: '#00d4ff', color: '#1a1a2e', border: 'none' },
};

export default VehicleCard;
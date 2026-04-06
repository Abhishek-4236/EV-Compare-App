import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { vehicleAPI } from '../services/api';

function formatPrice(p) {
  if (!p) return 'N/A';
  if (p >= 10000000) return `₹${(p / 10000000).toFixed(2)}Cr`;
  if (p >= 100000) return `₹${(p / 100000).toFixed(1)}L`;
  return `₹${(p / 1000).toFixed(0)}K`;
}

function VehicleDetailPage() {
  const { id } = useParams();
  const [vehicle, setVehicle] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    vehicleAPI.getById(id).then(res => {
      setVehicle(res.data);
      setLoading(false);
    });
  }, [id]);

  if (loading) return <p style={{ padding: '2rem' }}>Loading...</p>;
  if (!vehicle) return <p style={{ padding: '2rem' }}>Vehicle not found.</p>;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div style={styles.badge}>{vehicle.category} • {vehicle.wheel_type}</div>
        <h1 style={styles.name}>{vehicle.brand} {vehicle.model}</h1>
        <div style={styles.price}>{formatPrice(vehicle.approx_price_inr)}</div>
      </div>

      <div style={styles.specGrid}>
        {[
          ['🔋 Range', `${vehicle.range_km} km`],
          ['⚡ Battery', `${vehicle.battery_kwh} kWh`],
          ['🏎 Top Speed', `${vehicle.top_speed_kmh} kmph`],
          ['🔌 Charging', vehicle.charging_type],
          ['🛡 Brakes', vehicle.brake_type || 'N/A'],
          ['📅 Launch Year', vehicle.launch_year || 'N/A'],
          ['⭐ Rating', vehicle.overall_rating || 'N/A'],
          ['🏷 Status', vehicle.market_status],
        ].map(([label, value]) => (
          <div key={label} style={styles.specCard}>
            <div style={styles.specLabel}>{label}</div>
            <div style={styles.specValue}>{value}</div>
          </div>
        ))}
      </div>

      {vehicle.fame2_subsidy_inr > 0 && (
        <div style={styles.subsidyBox}>
          <h3>💰 FAME II Subsidy Available</h3>
          <p>Central Govt Subsidy: <strong>{formatPrice(vehicle.fame2_subsidy_inr)}</strong></p>
          <p>Effective Price: <strong>{formatPrice(vehicle.approx_price_inr - vehicle.fame2_subsidy_inr)}</strong></p>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: { maxWidth: '900px', margin: '0 auto', padding: '2rem' },
  header: {
    backgroundColor: '#1a1a2e', color: 'white',
    padding: '2rem', borderRadius: '12px', marginBottom: '2rem',
  },
  badge: { color: '#00d4ff', fontSize: '0.9rem', marginBottom: '0.5rem' },
  name: { fontSize: '2.5rem', margin: '0.5rem 0' },
  price: { fontSize: '2rem', color: '#00d4ff', fontWeight: 'bold' },
  specGrid: {
    display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '1rem', marginBottom: '2rem',
  },
  specCard: {
    padding: '1rem', backgroundColor: '#f8f9fa',
    borderRadius: '8px', textAlign: 'center',
  },
  specLabel: { fontSize: '0.85rem', color: '#666', marginBottom: '0.3rem' },
  specValue: { fontSize: '1.1rem', fontWeight: 'bold' },
  subsidyBox: {
    padding: '1.5rem', backgroundColor: '#dcfce7',
    borderRadius: '8px', borderLeft: '4px solid #16a34a',
  },
};

export default VehicleDetailPage;
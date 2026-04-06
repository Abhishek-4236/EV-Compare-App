import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { vehicleAPI } from '../services/api';

function formatPrice(p) {
  if (!p) return 'N/A';
  if (p >= 10000000) return `₹${(p / 10000000).toFixed(2)}Cr`;
  if (p >= 100000) return `₹${(p / 100000).toFixed(1)}L`;
  return `₹${(p / 1000).toFixed(0)}K`;
}

function ComparePage() {
  const [searchParams] = useSearchParams();
  const [vehicles, setVehicles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const ids = searchParams.get('ids')?.split(',').map(Number);
    if (ids?.length >= 2) {
      vehicleAPI.compare(ids).then(res => {
        setVehicles(res.data.vehicles);
        setLoading(false);
      });
    } else {
      setLoading(false);
    }
  }, []);

  if (loading) return <p style={{ padding: '2rem' }}>Loading comparison...</p>;

  if (!vehicles.length) return (
    <div style={{ padding: '2rem', textAlign: 'center' }}>
      <h2>No vehicles selected</h2>
      <p>Go to <a href="/browse">Browse</a> and select 2-3 vehicles to compare.</p>
    </div>
  );

  const ROWS = [
    ['Price', v => formatPrice(v.approx_price_inr)],
    ['Range', v => `${v.range_km} km`],
    ['Battery', v => `${v.battery_kwh} kWh`],
    ['Top Speed', v => `${v.top_speed_kmh} kmph`],
    ['Charging', v => v.charging_type],
    ['Rating', v => v.overall_rating],
    ['FAME II Subsidy', v => formatPrice(v.fame2_subsidy_inr)],
    ['Value Score', v => v.value_score],
  ];

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>⚖️ Side by Side Comparison</h1>
      <div style={styles.tableWrapper}>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Spec</th>
              {vehicles.map(v => (
                <th key={v.id} style={styles.th}>
                  {v.brand} {v.model}
                  <div style={styles.category}>{v.category}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ROWS.map(([label, fn]) => (
              <tr key={label}>
                <td style={styles.label}>{label}</td>
                {vehicles.map(v => (
                  <td key={v.id} style={styles.td}>{fn(v)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const styles = {
  container: { maxWidth: '1100px', margin: '0 auto', padding: '2rem' },
  title: { fontSize: '2rem', marginBottom: '2rem' },
  tableWrapper: { overflowX: 'auto' },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: {
    padding: '1rem', backgroundColor: '#1a1a2e',
    color: 'white', textAlign: 'center', fontSize: '1rem',
  },
  category: { fontSize: '0.75rem', color: '#00d4ff', marginTop: '0.2rem' },
  label: {
    padding: '0.8rem 1rem', fontWeight: 'bold',
    backgroundColor: '#f8f9fa', borderBottom: '1px solid #e9ecef',
  },
  td: {
    padding: '0.8rem 1rem', textAlign: 'center',
    borderBottom: '1px solid #e9ecef',
  },
};

export default ComparePage;
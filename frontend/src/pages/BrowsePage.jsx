import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { vehicleAPI } from '../services/api';
import VehicleCard from '../components/VehicleCard';

function BrowsePage() {
  const [searchParams] = useSearchParams();
  const [vehicles, setVehicles] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [compareIds, setCompareIds] = useState([]);
  const [filters, setFilters] = useState({
    category: searchParams.get('category') || '',
    max_price: 20000000,
    min_range: 0,
    sort_by: 'overall_rating',
  });

  useEffect(() => {
    fetchVehicles();
  }, [filters]);

  const fetchVehicles = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.category) params.category = filters.category;
      if (filters.max_price < 20000000) params.max_price = filters.max_price;
      if (filters.min_range > 0) params.min_range = filters.min_range;
      params.sort_by = filters.sort_by;
      params.limit = 65;

      const res = await vehicleAPI.getAll(params);
      setVehicles(res.data.vehicles);
      setTotal(res.data.total);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const toggleCompare = (id) => {
    setCompareIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id)
        : prev.length < 3 ? [...prev, id] : prev
    );
  };

  return (
    <div style={styles.container}>
      <h1 style={styles.title}>Browse EVs <span style={styles.count}>({total} models)</span></h1>

      {/* Filters */}
      <div style={styles.filterBar}>
        <select value={filters.category}
          onChange={e => setFilters({ ...filters, category: e.target.value })}
          style={styles.select}>
          <option value="">All Segments</option>
          <option value="2W">2-Wheeler</option>
          <option value="3W">3-Wheeler</option>
          <option value="4W">4-Wheeler</option>
          <option value="Bus">Bus</option>
          <option value="Truck">Truck</option>
        </select>

        <select value={filters.sort_by}
          onChange={e => setFilters({ ...filters, sort_by: e.target.value })}
          style={styles.select}>
          <option value="overall_rating">Sort: Rating</option>
          <option value="approx_price_inr">Sort: Price ↑</option>
          <option value="range_km">Sort: Range ↓</option>
          <option value="battery_kwh">Sort: Battery</option>
        </select>

        <div style={styles.rangeGroup}>
          <label>Max Price: ₹{(filters.max_price / 100000).toFixed(0)}L</label>
          <input type="range" min="50000" max="20000000" step="50000"
            value={filters.max_price}
            onChange={e => setFilters({ ...filters, max_price: parseInt(e.target.value) })} />
        </div>

        <div style={styles.rangeGroup}>
          <label>Min Range: {filters.min_range} km</label>
          <input type="range" min="0" max="700" step="10"
            value={filters.min_range}
            onChange={e => setFilters({ ...filters, min_range: parseInt(e.target.value) })} />
        </div>

        <button onClick={() => setFilters({ category: '', max_price: 20000000, min_range: 0, sort_by: 'overall_rating' })}
          style={styles.resetBtn}>Reset</button>
      </div>

      {/* Compare bar */}
      {compareIds.length >= 2 && (
        <div style={styles.compareBar}>
          {compareIds.length} vehicles selected
          <a href={`/compare?ids=${compareIds.join(',')}`} style={styles.compareLink}>
            Compare Now →
          </a>
        </div>
      )}

      {/* Grid */}
      {loading ? <p>Loading EVs...</p> : (
        <div style={styles.grid}>
          {vehicles.map(v => (
            <VehicleCard key={v.id} vehicle={v}
              onCompareToggle={toggleCompare}
              isSelected={compareIds.includes(v.id)} />
          ))}
        </div>
      )}
    </div>
  );
}

const styles = {
  container: { maxWidth: '1200px', margin: '0 auto', padding: '2rem' },
  title: { fontSize: '2rem', marginBottom: '1.5rem' },
  count: { fontSize: '1rem', color: '#666', fontWeight: 'normal' },
  filterBar: {
    display: 'flex', gap: '1rem', flexWrap: 'wrap',
    alignItems: 'center', marginBottom: '2rem',
    padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px',
  },
  select: { padding: '0.5rem', borderRadius: '6px', border: '1px solid #ccc' },
  rangeGroup: { display: 'flex', flexDirection: 'column', gap: '0.2rem', fontSize: '0.85rem' },
  resetBtn: {
    padding: '0.5rem 1rem', backgroundColor: '#1a1a2e',
    color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer',
  },
  compareBar: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '1rem', backgroundColor: '#1a1a2e', color: 'white',
    borderRadius: '8px', marginBottom: '1rem',
  },
  compareLink: {
    color: '#00d4ff', fontWeight: 'bold', textDecoration: 'none',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: '1.5rem',
  },
};

export default BrowsePage;
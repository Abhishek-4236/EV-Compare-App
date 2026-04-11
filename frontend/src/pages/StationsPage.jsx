import { useState, useEffect } from 'react';
import { vehicleAPI } from '../services/api';
import { MapPin, Zap, Navigation, Info, Filter } from 'lucide-react';

// Lazy import leaflet only client-side
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix leaflet default icon issue with bundlers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom accent marker
const accentIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41], iconAnchor: [12, 41], popupAnchor: [1, -34], shadowSize: [41, 41],
});

// FALLBACK static stations (used if DB is empty)
const FALLBACK_STATIONS = [
  { id: 1, name: 'BESCOM EV Hub Koramangala', city: 'Bengaluru', lat: 12.9352, lng: 77.6245, provider: 'BESCOM', connector_types: 'CCS2, CHAdeMO', fast_charging_available: true, status: 'Operational' },
  { id: 2, name: 'Ather Grid Indiranagar', city: 'Bengaluru', lat: 12.9784, lng: 77.6408, provider: 'Ather Energy', connector_types: 'Type 2, CCS', fast_charging_available: false, status: 'Operational' },
  { id: 3, name: 'Tata Power Banjara Hills', city: 'Hyderabad', lat: 17.4128, lng: 78.4404, provider: 'Tata Power', connector_types: 'CCS2, Type 2', fast_charging_available: true, status: 'Operational' },
  { id: 4, name: 'HPCL EV Station Hitech City', city: 'Hyderabad', lat: 17.4474, lng: 78.3762, provider: 'HPCL', connector_types: 'CCS2, CHAdeMO', fast_charging_available: true, status: 'Operational' },
  { id: 5, name: 'Jio-bp Charging Andheri', city: 'Mumbai', lat: 19.1136, lng: 72.8697, provider: 'Jio-bp', connector_types: 'CCS2, Type 2', fast_charging_available: true, status: 'Operational' },
  { id: 6, name: 'MSEDCL EV Point Pune', city: 'Pune', lat: 18.5204, lng: 73.8567, provider: 'MSEDCL', connector_types: 'Type 2, AC', fast_charging_available: false, status: 'Operational' },
  { id: 7, name: 'Delhi EV Hub Saket', city: 'Delhi', lat: 28.5272, lng: 77.2188, provider: 'BSES', connector_types: 'CCS2, CHAdeMO', fast_charging_available: true, status: 'Operational' },
  { id: 8, name: 'IndianOil EV Connaught Place', city: 'Delhi', lat: 28.6315, lng: 77.2167, provider: 'IndianOil', connector_types: 'CCS2', fast_charging_available: true, status: 'Operational' },
  { id: 9, name: 'ChargeZone Chennai Central', city: 'Chennai', lat: 13.0827, lng: 80.2707, provider: 'ChargeZone', connector_types: 'CCS2, Type 2', fast_charging_available: true, status: 'Operational' },
  { id: 10, name: 'Magenta EV Hub Guindy', city: 'Chennai', lat: 13.0065, lng: 80.2207, provider: 'Magenta', connector_types: 'CCS, Type 2', fast_charging_available: false, status: 'Operational' },
];

function MapCenterSetter({ center }) {
  const map = useMap();
  useEffect(() => { if (center) map.setView(center, 13); }, [center, map]);
  return null;
}

export default function StationsPage() {
  const [city, setCity] = useState('');
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedId, setSelectedId] = useState(null);
  const [fastOnly, setFastOnly] = useState(false);
  const [mapCenter, setMapCenter] = useState([20.5937, 78.9629]); // India center

  const selected = stations.find(s => s.id === selectedId);

  async function fetchStations(cityFilter = '') {
    setLoading(true);
    try {
      const params = cityFilter ? { city: cityFilter } : undefined;
      const res = await vehicleAPI.getMapStations(params);
      const rows = res.data?.stations || [];
      const used = rows.length > 0 ? rows : FALLBACK_STATIONS.filter(s =>
        !cityFilter || s.city.toLowerCase().includes(cityFilter.toLowerCase())
      );
      setStations(used);
      if (used.length > 0) {
        setSelectedId(used[0].id);
        setMapCenter([used[0].lat, used[0].lng]);
      }
    } catch {
      const filtered = FALLBACK_STATIONS.filter(s =>
        !cityFilter || s.city.toLowerCase().includes(cityFilter.toLowerCase())
      );
      setStations(filtered);
      if (filtered.length > 0) {
        setSelectedId(filtered[0].id);
        setMapCenter([filtered[0].lat, filtered[0].lng]);
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchStations(); }, []);

  const displayStations = fastOnly ? stations.filter(s => s.fast_charging_available) : stations;

  function selectStation(s) {
    setSelectedId(s.id);
    setMapCenter([s.lat, s.lng]);
  }

  return (
    <div className="ev-shell" style={{ paddingTop: 32 }}>
      <div style={{ marginBottom: 20 }}>
        <div className="ev-section-label">India EV Network</div>
        <h1 className="ev-section-title">Charging Stations</h1>
        <p className="ev-section-desc">Find public EV charging locations across India.</p>
      </div>

      {/* Search + Filter Bar */}
      <div style={{
        background: 'var(--bg-card)', border: '1px solid var(--border)',
        borderRadius: 12, padding: '12px 16px', display: 'flex', gap: 10,
        alignItems: 'center', marginBottom: 20, flexWrap: 'wrap',
      }}>
        <MapPin size={16} color="var(--accent)" style={{ flexShrink: 0 }} />
        <input
          className="ev-input"
          style={{ flex: '1 1 200px' }}
          value={city}
          onChange={e => setCity(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && fetchStations(city.trim())}
          placeholder="Search by city (e.g. Hyderabad, Bengaluru, Delhi...)"
        />
        <button className="ev-btn ev-btn-primary ev-btn-sm" onClick={() => fetchStations(city.trim())}>Search</button>
        <button className="ev-btn ev-btn-sm" onClick={() => { setCity(''); fetchStations(''); }}>Reset</button>
        <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', cursor: 'pointer', whiteSpace: 'nowrap' }}>
          <input type="checkbox" checked={fastOnly} onChange={e => setFastOnly(e.target.checked)} style={{ accentColor: 'var(--accent)' }} />
          <Zap size={14} color={fastOnly ? 'var(--accent)' : 'var(--text-muted)'} />
          Fast charging only
        </label>
      </div>

      {loading ? (
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 16 }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {[...Array(5)].map((_, i) => <div key={i} className="ev-skeleton" style={{ height: 90, borderRadius: 12 }} />)}
          </div>
          <div className="ev-skeleton" style={{ borderRadius: 14, minHeight: 480 }} />
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: 16, alignItems: 'start' }}>
          {/* Station List */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 560, overflowY: 'auto', paddingRight: 4 }}>
            <div style={{ fontSize: 13, color: 'var(--text-muted)', fontWeight: 600, padding: '4px 2px' }}>
              {displayStations.length} station{displayStations.length !== 1 ? 's' : ''} {fastOnly ? '(fast charging)' : ''}
            </div>
            {displayStations.length === 0 ? (
              <div className="ev-card" style={{ padding: 24, textAlign: 'center' }}>
                <Info size={24} color="var(--text-muted)" style={{ margin: '0 auto 8px' }} />
                <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>
                  {fastOnly ? 'No fast charging stations found.' : 'No stations found for this city.'}
                </p>
              </div>
            ) : (
              displayStations.map(s => (
                <button
                  key={s.id}
                  onClick={() => selectStation(s)}
                  style={{
                    textAlign: 'left', background: selectedId === s.id ? 'var(--accent-soft)' : 'var(--bg-card)',
                    border: `1px solid ${selectedId === s.id ? 'var(--accent)' : 'var(--border)'}`,
                    borderRadius: 12, padding: '12px 14px', cursor: 'pointer', transition: 'all 0.15s',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                    <strong style={{ fontSize: 14, color: selectedId === s.id ? 'var(--accent-dark)' : 'var(--text)', lineHeight: 1.3 }}>{s.name}</strong>
                    {s.fast_charging_available && (
                      <span style={{ background: 'var(--accent)', color: 'white', borderRadius: 4, padding: '2px 6px', fontSize: 10, fontWeight: 700, flexShrink: 0, marginLeft: 8 }}>
                        FAST
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
                    {s.city} · {s.provider || 'Unknown'}
                  </div>
                  {s.connector_types && (
                    <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>🔌 {s.connector_types}</div>
                  )}
                </button>
              ))
            )}
          </div>

          {/* Map */}
          <div className="ev-map-wrap" style={{ height: 560, position: 'sticky', top: 80 }}>
            <MapContainer
              center={mapCenter}
              zoom={12}
              style={{ height: '100%', width: '100%' }}
              scrollWheelZoom={true}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <MapCenterSetter center={mapCenter} />
              {displayStations.map(s => (
                <Marker
                  key={s.id}
                  position={[s.lat, s.lng]}
                  icon={s.id === selectedId ? accentIcon : new L.Icon.Default()}
                  eventHandlers={{ click: () => selectStation(s) }}
                >
                  <Popup>
                    <div style={{ minWidth: 180 }}>
                      <strong style={{ fontSize: 14 }}>{s.name}</strong><br />
                      <span style={{ fontSize: 12, color: '#666' }}>{s.city} · {s.provider}</span><br />
                      {s.connector_types && <span style={{ fontSize: 12 }}>🔌 {s.connector_types}</span>}<br />
                      {s.fast_charging_available && <span style={{ color: '#0ea5a4', fontWeight: 700, fontSize: 12 }}>⚡ Fast Charging</span>}
                      <br />
                      <a href={`https://www.google.com/maps?q=${s.lat},${s.lng}`} target="_blank" rel="noreferrer"
                        style={{ color: '#0ea5a4', fontSize: 12, fontWeight: 600, display: 'block', marginTop: 4 }}>
                        Open in Google Maps →
                      </a>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          </div>
        </div>
      )}
    </div>
  );
}

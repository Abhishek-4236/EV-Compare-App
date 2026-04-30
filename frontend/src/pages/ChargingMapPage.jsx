import React, { useState, useRef, useCallback, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { BatteryCharging, Zap, Navigation, Info, Loader, AlertTriangle } from 'lucide-react';
import 'leaflet/dist/leaflet.css';

// Fix for default Leaflet marker icons not rendering properly in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Custom EV Marker Icon
const evIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

const evFastIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

// Major Indian Cities Coordinates
const CITIES = [
  { name: 'Delhi', lat: 28.6139, lng: 77.2090 },
  { name: 'Mumbai', lat: 19.0760, lng: 72.8777 },
  { name: 'Bangalore', lat: 12.9716, lng: 77.5946 },
  { name: 'Hyderabad', lat: 17.3850, lng: 78.4867 },
  { name: 'Chennai', lat: 13.0827, lng: 80.2707 },
  { name: 'Kolkata', lat: 22.5726, lng: 88.3639 },
  { name: 'Pune', lat: 18.5204, lng: 73.8567 },
  { name: 'Ahmedabad', lat: 23.0225, lng: 72.5714 },
  { name: 'Jaipur', lat: 26.9124, lng: 75.7873 },
  { name: 'Lucknow', lat: 26.8467, lng: 80.9462 },
  { name: 'Kochi', lat: 9.9312, lng: 76.2673 },
  { name: 'Chandigarh', lat: 30.7333, lng: 76.7794 },
  { name: 'Indore', lat: 22.7196, lng: 75.8577 },
  { name: 'Guwahati', lat: 26.1158, lng: 91.7086 },
];

/**
 * Handles Debounced fetching of Live Charging Nodes from OpenStreetMap!
 */
function LiveStationFetcher({ setStations, setLoading, setError, setIsZoomValid }) {
  const map = useMapEvents({
    moveend: () => {
      fetchLiveStations();
    },
    zoomend: () => {
      setIsZoomValid(map.getZoom() >= 10);
    }
  });

  const fetchTimeout = useRef(null);

  const fetchLiveStations = useCallback(async () => {
    // If zoom is too far out, don't query overpass (too much data, free API will reject)
    if (map.getZoom() < 10) return;
    
    // Debounce to prevent hammering free API while user scrolls fast
    if (fetchTimeout.current) clearTimeout(fetchTimeout.current);
    
    fetchTimeout.current = setTimeout(async () => {
      setLoading(true);
      setError(null);
      const bounds = map.getBounds();
      // Overpass Box Format: south, west, north, east
      const bbox = `${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()}`;
      
      const query = `
        [out:json][timeout:15];
        (
          node["amenity"="charging_station"](${bbox});
        );
        out body;
      `;
      
      try {
        const response = await fetch('https://overpass-api.de/api/interpreter', {
          method: 'POST',
          body: 'data=' + encodeURIComponent(query),
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        const data = await response.json();
        
        if (data && data.elements) {
          const parsed = data.elements.map(el => {
            const tags = el.tags || {};
            const isFast = tags.socket === 'type2_combo' || tags.socket === 'chademo' || Number(tags.capacity) > 22;
            return {
              id: el.id,
              lat: el.lat,
              lng: el.lon,
              name: tags.name || tags.operator || 'Public Charging Station',
              provider: tags.operator || tags.brand || 'Local Operator',
              type: isFast ? 'DC Fast Charging' : 'AC Standard',
              ports: tags.capacity || tags['socket:type2'] || tags.sockets || 'N/A',
              isFast,
            };
          });
          
          setStations(prev => {
             // Deduplicate using Map based on ID to retain existing markers
             const mapStore = new Map(prev.map(s => [s.id, s]));
             parsed.forEach(s => mapStore.set(s.id, s));
             return Array.from(mapStore.values());
          });
        }
      } catch (err) {
        console.error("Overpass API Error:", err);
        setError("Network error fetching live OpenStreetMap nodes.");
      } finally {
        setLoading(false);
      }
    }, 800); // 800ms debounce buffer
  }, [map, setStations, setLoading, setError]);

  // Initial fetch on mount if zoomed in
  useEffect(() => {
    setIsZoomValid(map.getZoom() >= 10);
    fetchLiveStations();
  }, [fetchLiveStations, map, setIsZoomValid]);

  return null;
}

// A small component to dynamically update map view based on selected city
function ChangeView({ lat, lng, zoom }) {
  const map = useMap();

  useEffect(() => {
    map.setView([lat, lng], zoom);
  }, [map, lat, lng, zoom]);

  return null;
}

export default function ChargingMapPage() {
  const [activeCity, setActiveCity] = useState(CITIES[2]); // Default Bangalore
  const [zoomLevel, setZoomLevel] = useState(11); 
  const [stations, setStations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isZoomValid, setIsZoomValid] = useState(true);
  
  const handleCitySelect = (city) => {
    setActiveCity(city);
    setZoomLevel(11); // Zoom into the city securely to trigger API fetch
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 72px)', width: '100%', position: 'relative' }}>
      
      {/* Search & Filter Overlay */}
      <div style={{
        position: 'absolute', top: 20, left: 20, zIndex: 1000,
        background: 'var(--bg-card)', padding: '20px', borderRadius: '16px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.12)', width: '320px',
        border: '1px solid var(--border)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
          <div style={{ background: 'var(--accent-soft)', color: 'var(--accent-dark)', padding: '8px', borderRadius: '10px' }}>
            {loading ? <Loader size={24} className="ev-spin" /> : <BatteryCharging size={24} />}
          </div>
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 800, margin: 0, color: 'var(--text)', display: 'flex', alignItems: 'center', gap: 6 }}>
              Live Map <span style={{ fontSize: 9, background: '#ef4444', color: 'white', padding: '2px 6px', borderRadius: 99, fontWeight: 800 }}>BETA</span>
            </h2>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{stations.length} Mapped Providers Data</span>
          </div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ fontSize: 12, fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: 8, display: 'block' }}>
            Jump to Geographic Hub
          </label>
          <div style={{ position: 'relative' }}>
            <Navigation size={14} style={{ position: 'absolute', left: 12, top: 12, color: 'var(--text-muted)' }} />
            <select 
              className="ev-select" 
              style={{ paddingLeft: 36, width: '100%' }}
              value={activeCity.name}
              onChange={(e) => handleCitySelect(CITIES.find(c => c.name === e.target.value))}
            >
              <option value="" disabled>Select a city...</option>
              {CITIES.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
            </select>
          </div>
        </div>

        {/* Live Warning Status Panels */}
        {!isZoomValid && (
          <div style={{ display: 'flex', gap: 8, fontSize: 12, color: '#f59e0b', background: '#fffbeb', padding: 12, borderRadius: 8, marginBottom: 12, border: '1px solid #fde68a' }}>
            <AlertTriangle size={16} style={{ flexShrink: 0 }} />
            <span>Zoom in closer on a city to load live charging stations. (Preventing API overload)</span>
          </div>
        )}

        {error && (
          <div style={{ display: 'flex', gap: 8, fontSize: 12, color: '#ef4444', background: '#fef2f2', padding: 12, borderRadius: 8, marginBottom: 12, border: '1px solid #fee2e2' }}>
            <AlertTriangle size={16} /> {error}
          </div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, background: 'var(--bg-muted)', padding: '12px', borderRadius: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--text)' }}>
            <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-violet.png" style={{ height: 20 }} alt="DC Fast" />
            <span style={{ flex: 1 }}>DC Fast Nodes</span>
            <span style={{ fontWeight: 700, color: 'var(--text-muted)' }}>{stations.filter(s => s.isFast).length}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: 'var(--text)' }}>
            <img src="https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png" style={{ height: 20 }} alt="AC Standard" />
            <span style={{ flex: 1 }}>AC Standard Nodes</span>
            <span style={{ fontWeight: 700, color: 'var(--text-muted)' }}>{stations.filter(s => !s.isFast).length}</span>
          </div>
          <div style={{ fontSize: 10, color: 'var(--text-muted)', marginTop: 4, textAlign: 'right' }}>
            Data: © OpenStreetMap contributors
          </div>
        </div>
      </div>

      {/* Fullscreen Map Layer */}
      <MapContainer 
        center={[activeCity.lat, activeCity.lng]}
        zoom={11} 
        style={{ width: '100%', height: '100%', zIndex: 0 }}
        zoomControl={false}
      >
        <ChangeView lat={activeCity.lat} lng={activeCity.lng} zoom={zoomLevel} />
        
        {/* API Fetcher Agent */}
        <LiveStationFetcher 
          setStations={setStations} 
          setLoading={setLoading} 
          setError={setError}
          setIsZoomValid={setIsZoomValid}
        />

        {/* OpenStreetMap Tiles */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {stations.map(station => (
          <Marker 
            key={station.id} 
            position={[station.lat, station.lng]}
            icon={station.isFast ? evFastIcon : evIcon}
          >
            <Popup className="ev-map-popup">
              <div style={{ minWidth: 200 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, borderBottom: '1px solid var(--border)', paddingBottom: 8, marginBottom: 8 }}>
                  {station.isFast ? <Zap size={16} color="#8b5cf6" /> : <BatteryCharging size={16} color="#10b981" />}
                  <h4 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--text)' }}>{station.name}</h4>
                </div>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: 12, color: 'var(--text-muted)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Operator:</span>
                    <strong style={{ color: 'var(--text)' }}>{station.provider}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Speed:</span>
                    <strong style={{ color: 'var(--text)' }}>{station.type}</strong>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>Listed Ports:</span>
                    <strong style={{ color: station.ports > 0 ? '#10b981' : 'inherit' }}>
                      {station.ports}
                    </strong>
                  </div>
                </div>

                <a 
                  href={`https://www.google.com/maps/dir/?api=1&destination=${station.lat},${station.lng}`} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style={{ 
                    marginTop: 12, width: '100%', background: 'var(--accent)', color: 'white', 
                    border: 'none', padding: '8px', borderRadius: '6px', fontSize: 12, fontWeight: 700,
                    cursor: 'pointer', display: 'block', textAlign: 'center', textDecoration: 'none'
                  }}>
                  Navigate via Maps
                </a>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}

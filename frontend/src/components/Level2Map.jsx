import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Leaf, Droplets, Sun } from 'lucide-react';
import L from 'leaflet';

// Create custom colored markers for Leaflet based on AWD State
const createIcon = (color) => {
  return new L.Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });
};

const icons = {
  wet: createIcon('blue'),
  dry: createIcon('orange'),
  unknown: createIcon('grey')
};

function Level2Map() {
  const [farmers, setFarmers] = useState([]);
  const [loading, setLoading] = useState(true);

  // Center on Maharashtra, India
  const defaultCenter = [19.7515, 75.7139]; 
  const defaultZoom = 7;

  useEffect(() => {
    const fetchMapData = async () => {
      try {
        // We use the specialized optimized endpoint created in Step 2
        const response = await fetch('http://localhost:8000/api/map/farmers');
        const data = await response.json();
        if (data.status === 'ok') {
          setFarmers(data.data);
        }
      } catch (error) {
        console.error('Failed to fetch map data:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchMapData();
  }, []);

  return (
    <div className="card" style={{ padding: '0', overflow: 'hidden' }}>
      <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', backgroundColor: 'var(--bg-secondary)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ color: '#fff' }}>Geospatial Farmer Heatmap</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '4px' }}>
            Live tracking of active fields and their current Alternate Wetting and Drying cycle states.
          </p>
        </div>
        
        <div style={{ display: 'flex', gap: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            <Droplets size={16} color="#2196F3" /> Wetting Phase (Blue)
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            <Sun size={16} color="#FF9800" /> Drying Phase (Brown)
          </div>
        </div>
      </div>

      <div className="map-container" style={{ border: 'none', borderRadius: '0', height: '650px' }}>
        {loading ? (
          <div className="loading">Loading Map Data...</div>
        ) : (
          <MapContainer 
            center={defaultCenter} 
            zoom={defaultZoom} 
            scrollWheelZoom={true} 
            style={{ height: '100%', width: '100%', background: '#0a0a0a' }}
          >
            {/* Utilize an aesthetically pleasing dark-mode basemap from CartoDB */}
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />
            
            {farmers.map(farmer => {
              // Determine which icon to use based on latest AWD state
              let markerIcon = icons.unknown;
              if (farmer.latest_state === 'Wet') markerIcon = icons.wet;
              if (farmer.latest_state === 'Dry') markerIcon = icons.dry;

              return (
                <Marker 
                  key={farmer.id} 
                  position={[farmer.lat, farmer.lng]} 
                  icon={markerIcon}
                >
                  <Popup className="dark-popup">
                    <div style={{ minWidth: '200px' }}>
                      <h4 style={{ margin: '0 0 5px 0', borderBottom: '1px solid #ccc', paddingBottom: '5px' }}>
                        {farmer.name}
                      </h4>
                      <p style={{ margin: '5px 0', fontSize: '0.9rem' }}>
                        <strong>Region:</strong> {farmer.region}
                      </p>
                      <p style={{ margin: '5px 0', fontSize: '0.9rem' }}>
                        <strong>AWD State:</strong> {farmer.latest_state}
                      </p>
                      {farmer.confidence > 0 && (
                        <p style={{ margin: '5px 0', fontSize: '0.9rem' }}>
                          <strong>Model Confidence:</strong> {(farmer.confidence * 100).toFixed(1)}%
                        </p>
                      )}
                      {farmer.last_observed && (
                        <p style={{ margin: '5px 0', fontSize: '0.8rem', color: '#666' }}>
                          Last Update: {new Date(farmer.last_observed).toLocaleString()}
                        </p>
                      )}
                    </div>
                  </Popup>
                </Marker>
              );
            })}
          </MapContainer>
        )}
      </div>
    </div>
  );
}

export default Level2Map;

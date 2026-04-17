import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';

export default function Level2Map() {
  const [farmers, setFarmers] = useState([]);

  useEffect(() => {
    const fetchFarmers = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:8000/api/dashboard/farmers');
        // Filter out farmers that don't have valid coordinates yet
        const activeFarmers = response.data.data.filter(f => f.lat !== 0 && f.lng !== 0);
        setFarmers(activeFarmers);
      } catch (error) {
        console.error("Map Data Error:", error);
      }
    };
    
    fetchFarmers();
    const interval = setInterval(fetchFarmers, 5000); 
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ marginTop: '20px' }}>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
        Live telemetry mapped via Leaflet. 
        <span style={{ color: '#00d4ff', marginLeft: '12px' }}>● Verified Edge Node</span>
      </p>
      <MapContainer 
        center={[21.1458, 79.0882]} // Default to Nagpur coordinates
        zoom={12} 
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; CARTO'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        
        {farmers.map(farmer => (
          <CircleMarker 
            key={farmer.id}
            center={[farmer.lat, farmer.lng]}
            pathOptions={{ 
              color: '#00d4ff',
              fillColor: '#00d4ff',
              fillOpacity: 0.7
            }}
            radius={10}
            weight={2}
          >
            <Popup>
              <div style={{ color: '#000', padding: '4px' }}>
                <b style={{fontSize: '1.1rem'}}>Farmer AV-{farmer.id}</b><br/>
                Coordinates: {farmer.lat.toFixed(4)}, {farmer.lng.toFixed(4)}
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}
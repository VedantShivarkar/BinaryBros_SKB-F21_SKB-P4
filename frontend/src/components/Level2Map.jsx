import React from 'react';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';

export default function Level2Map() {
  // Use mock coordinates for the heatmap demonstration
  const mockFarmers = [
    { id: 101, lat: 21.1458, lng: 79.0882, state: 'Wet' },
    { id: 102, lat: 21.1600, lng: 79.1000, state: 'Dry' },
    { id: 103, lat: 21.1300, lng: 79.0700, state: 'Wet' },
    { id: 104, lat: 21.1550, lng: 79.0500, state: 'Dry' },
  ];

  return (
    <div style={{ marginTop: '20px' }}>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '16px' }}>
        Live telemetry mapped via Leaflet. 
        <span style={{ color: '#00d4ff', marginLeft: '12px' }}>● Blue: Wet Cycle</span>
        <span style={{ color: '#ffb800', marginLeft: '12px' }}>● Brown: Dry Cycle</span>
      </p>
      <MapContainer 
        center={[21.1458, 79.0882]} 
        zoom={13} 
        scrollWheelZoom={false}
      >
        <TileLayer
          attribution='&copy; CARTO'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />
        
        {mockFarmers.map(farmer => (
          <CircleMarker 
            key={farmer.id}
            center={[farmer.lat, farmer.lng]}
            pathOptions={{ 
              color: farmer.state === 'Wet' ? '#00d4ff' : '#ffb800',
              fillColor: farmer.state === 'Wet' ? '#00d4ff' : '#ffb800',
              fillOpacity: 0.7
            }}
            radius={10}
            weight={2}
          >
            <Popup>
              <div style={{ color: '#000', padding: '4px' }}>
                <b style={{fontSize: '1.1rem'}}>Farmer #{farmer.id}</b><br/>
                AWD State: <span style={{fontWeight: 800, color: farmer.state === 'Wet' ? '#0088aa' : '#b88000'}}>{farmer.state}</span>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}

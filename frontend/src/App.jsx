import React from 'react';
import Level1Dashboard from './components/Level1Dashboard';
import Level2Map from './components/Level2Map';

function App() {
  return (
    <div>
      <header className="header">
        <h1>Amrit Vaayu dMRV</h1>
        <p className="glow-text-green">Cloud-Proof Digital Monitoring, Reporting & Verification</p>
      </header>

      <div className="dashboard-grid">
        <div className="glass-panel full-width">
          <h2>Assurance-Ready Analytics (Level 1)</h2>
          <Level1Dashboard />
        </div>
        
        <div className="glass-panel full-width">
          <h2>Farmer Geolocation & AWD Heatmap (Level 2)</h2>
          <Level2Map />
        </div>
      </div>
    </div>
  );
}

export default App;

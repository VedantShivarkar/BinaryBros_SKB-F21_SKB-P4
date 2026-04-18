import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function FarmerRegistration() {
  const [formData, setFormData] = useState({ phone: '', name: '', landSize: '' });
  const [parcels, setParcels] = useState([{ id: 1, coordinates: 'Pending...' }]);
  const [liveTelemetry, setLiveTelemetry] = useState(null);

  // Poll the SMART hardware endpoint every 3 seconds
  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        // 🚨 FORCED ABSOLUTE URL TO BYPASS CACHE & PROXY 🚨
        const res = await axios.get('http://127.0.0.1:8000/api/dashboard/live-esp32');
        if (res.data && res.data.data) {
          setLiveTelemetry(res.data.data);
          
          // Trigger the UI Alert if the hardware just minted a credit!
          if (res.data.minted_just_now) {
             alert("🌿 HARDWARE TRIGGER: Field is Dry! IoT Node automatically minted Carbon Credits to the Ledger!");
          }
        }
      } catch (error) {
        console.error("Telemetry Error:", error);
      }
    };
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleAddParcel = () => {
    setParcels([...parcels, { id: parcels.length + 1, coordinates: 'Draw on map...' }]);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.innerText;
    btn.innerText = "Syncing to Database...";
    btn.disabled = true;

    try {
      const payload = {
        name: formData.name,
        phone: formData.phone,
        landSize: parseFloat(formData.landSize)
      };

      const res = await axios.post('http://127.0.0.1:8000/api/dashboard/register', payload);
      
      if (res.data.success) {
        alert(`✅ Success! Farmer ${res.data.data.name} registered and synced to hardware ledger.`);
        setFormData({ phone: '', name: '', landSize: '' });
      }
    } catch (error) {
      console.error("Registration Error:", error);
      alert("❌ Failed to connect to the database. Check your backend terminal.");
    } finally {
      btn.innerText = originalText;
      btn.disabled = false;
    }
  };

  // Derive UI state directly from hardware pump status
  const isDry = liveTelemetry?.pump_status === 'ON';
  const stateText = isDry ? 'DRY' : 'WET';

  return (
    <div className="dashboard-grid" style={{padding: '32px 0'}}>
      <div className="full-width text-center" style={{marginBottom: '20px'}}>
        <h1 style={{fontSize: '2.5rem', fontWeight: 800}}>Farmer Command Center</h1>
        <p className="glow-text-green">Onboarding & Live Edge Node Telemetry</p>
      </div>

      {/* REGISTRATION FORM */}
      <div className="glass-panel" style={{gridColumn: 'span 1'}}>
        <h3 style={{ marginBottom: '24px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
          1. Digital Identity & Land Registry
        </h3>
        <form onSubmit={handleSubmit} style={{display: 'flex', flexDirection: 'column', gap: '16px'}}>
          <div>
            <label style={{display: 'block', marginBottom: '8px', color: 'var(--text-secondary)'}}>Full Name</label>
            <input type="text" placeholder="e.g. Ramesh Kumar" style={inputStyle} 
              onChange={e => setFormData({...formData, name: e.target.value})} required/>
          </div>
          <div>
            <label style={{display: 'block', marginBottom: '8px', color: 'var(--text-secondary)'}}>WhatsApp Number</label>
            <input type="tel" placeholder="+91 98765 43210" style={inputStyle} 
              onChange={e => setFormData({...formData, phone: e.target.value})} required/>
          </div>
          <div>
            <label style={{display: 'block', marginBottom: '8px', color: 'var(--text-secondary)'}}>Total Land Size (Acres)</label>
            <input type="number" placeholder="2.0" step="0.1" style={inputStyle} 
              onChange={e => setFormData({...formData, landSize: e.target.value})} required/>
          </div>

          <div style={{marginTop: '16px', padding: '16px', background: 'rgba(255,255,255,0.02)', borderRadius: '8px', border: '1px solid var(--border-color)'}}>
            <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px'}}>
              <h4 style={{margin: 0}}>Scattered Land Parcels</h4>
              <button type="button" onClick={handleAddParcel} style={btnStyle}>+ Add Polygon</button>
            </div>
            {parcels.map(p => (
              <div key={p.id} style={{padding: '8px', background: '#000', borderRadius: '4px', marginBottom: '8px', fontSize: '0.85rem', color: 'var(--text-secondary)'}}>
                Parcel {p.id}: {p.coordinates} 📍
              </div>
            ))}
          </div>

          <button type="submit" style={{...btnStyle, background: 'var(--accent-green)', color: '#000', padding: '12px', fontSize: '1rem', marginTop: '16px'}}>
            Generate Digital ID & Sync Hardware
          </button>
        </form>
      </div>

      {/* LIVE HARDWARE TELEMETRY */}
      <div className="glass-panel" style={{gridColumn: 'span 1'}}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
          <h3 style={{margin: 0}}>2. Live ESP32 Edge Node</h3>
          <span style={{display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: '#00ff88'}}>
            <div className="pulse-dot"></div> ACTIVE CONNECTION
          </span>
        </div>

        {liveTelemetry ? (
          <div style={{display: 'flex', flexDirection: 'column', gap: '20px'}}>
            <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px'}}>
              {/* Moisture Dial Simulation */}
              <div style={{background: '#000', padding: '24px', borderRadius: '12px', textAlign: 'center', border: '1px solid var(--border-color)'}}>
                <div style={{color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '8px', textTransform: 'uppercase'}}>Soil Moisture Status</div>
                <div style={{fontSize: '2.5rem', fontWeight: 'bold', color: !isDry ? 'var(--accent-blue)' : 'var(--accent-warning)'}}>
                  {stateText}
                </div>
                <div style={{color: 'var(--text-secondary)', fontSize: '0.8rem', marginTop: '8px'}}>
                  Raw Value: {liveTelemetry.moisture_val}
                </div>
              </div>

              {/* Pump Status */}
              <div style={{background: '#000', padding: '24px', borderRadius: '12px', textAlign: 'center', border: '1px solid var(--border-color)'}}>
                <div style={{color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '8px', textTransform: 'uppercase'}}>Irrigation Pump</div>
                <div style={{fontSize: '2rem', fontWeight: 'bold', color: isDry ? '#00ff88' : '#ff4444'}}>
                  {isDry ? 'ENGAGED' : 'STANDBY'}
                </div>
              </div>
            </div>

            <div style={{padding: '16px', background: 'rgba(0, 212, 255, 0.05)', borderRadius: '8px', border: '1px solid rgba(0, 212, 255, 0.2)'}}>
              <h4 style={{color: 'var(--accent-blue)', marginBottom: '8px'}}>System Diagnostics</h4>
              <ul style={{listStyle: 'none', padding: 0, fontSize: '0.9rem', color: 'var(--text-secondary)', lineHeight: '1.6'}}>
                <li><strong>Node ID:</strong> ESP32-WROOM-32D</li>
                <li><strong>Capacitive Calibration:</strong> Air: 2560 | Water: 1220</li>
                <li><strong>Last Sync:</strong> {new Date(liveTelemetry.timestamp).toLocaleString()}</li>
                <li><strong>Network:</strong> Cloud REST Native</li>
              </ul>
            </div>
            
            <div style={{marginTop: 'auto', textAlign: 'center', color: 'var(--text-secondary)', fontSize: '0.8rem'}}>
              Data streaming via Supabase Realtime Ledger
            </div>
          </div>
        ) : (
          <div style={{textAlign: 'center', padding: '40px', color: 'var(--text-secondary)'}}>
            Waiting for Edge Node heartbeat...
          </div>
        )}
      </div>
    </div>
  );
}

const inputStyle = {
  width: '100%',
  padding: '10px 14px',
  background: '#121212',
  border: '1px solid rgba(255,255,255,0.1)',
  borderRadius: '6px',
  color: '#fff',
  outline: 'none'
};

const btnStyle = {
  background: 'rgba(255,255,255,0.1)',
  color: '#fff',
  border: 'none',
  padding: '6px 12px',
  borderRadius: '4px',
  cursor: 'pointer',
  fontWeight: 'bold'
};
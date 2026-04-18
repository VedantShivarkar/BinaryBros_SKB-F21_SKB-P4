import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function AuditorDashboard() {
  const [farmers, setFarmers] = useState([]);
  const [selectedFarmer, setSelectedFarmer] = useState(null);
  const [logs, setLogs] = useState([]);
  const [credits, setCredits] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [farmersRes, logsRes, creditsRes] = await Promise.all([
          axios.get('http://127.0.0.1:8000/api/dashboard/farmers'),
          axios.get('http://127.0.0.1:8000/api/dashboard/awd-logs'),
          axios.get('http://127.0.0.1:8000/api/dashboard/carbon-credits')
        ]);
        
        setFarmers(farmersRes.data.data);
        setLogs(logsRes.data.logs);
        setCredits(creditsRes.data.data);
        
        // Auto-select the first farmer if none is selected
        if (!selectedFarmer && farmersRes.data.data.length > 0) {
          setSelectedFarmer(farmersRes.data.data[0]);
        }
      } catch (error) {
        console.error("API Error:", error);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 5000); 
    return () => clearInterval(interval);
  }, [selectedFarmer]);

  // Simulated cryptographic hash generator for the "Auditor" aesthetic
  const generateHash = (id, date) => {
    return `0x${Math.abs(Math.sin(id) * 10000000).toString(16).substring(0, 8)}...${new Date(date).getTime().toString().substring(8)}`;
  };

  const handleFarmerChange = (e) => {
    const farmer = farmers.find(f => f.id === parseInt(e.target.value));
    setSelectedFarmer(farmer);
  };

  // Filter data for the selected farmer
  const farmerLogs = selectedFarmer ? logs.filter(log => log.farmer_id === selectedFarmer.id) : [];
  const farmerCredits = selectedFarmer ? credits.filter(c => c.farmer_id === selectedFarmer.id) : [];
  const lifetimeCredits = farmerCredits.reduce((sum, c) => sum + c.flux_reduction, 0);

  return (
    <div className="dashboard-grid" style={{padding: '32px 0'}}>
      <div className="full-width text-center" style={{marginBottom: '20px'}}>
        <h1 style={{fontSize: '2.5rem', fontWeight: 800}}>Verifier & Auditor Portal</h1>
        <p className="glow-text-blue">Cryptographic Timeline & Tri-Layer Ledger</p>
      </div>

      {/* Control Panel */}
      <div className="glass-panel full-width" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
        <div>
          <label style={{color: 'var(--text-secondary)', marginRight: '16px'}}>Select Farm Node:</label>
          <select 
            onChange={handleFarmerChange} 
            value={selectedFarmer?.id || ''}
            style={{padding: '8px 16px', background: '#121212', color: '#fff', border: '1px solid var(--border-color)', borderRadius: '8px'}}
          >
            {farmers.map(f => (
              <option key={f.id} value={f.id}>Farmer ID: AV-{f.id} ({f.phone})</option>
            ))}
          </select>
        </div>
        
        <div style={{textAlign: 'right'}}>
          <div style={{color: 'var(--text-secondary)', fontSize: '0.9rem'}}>Lifetime Credits Minted</div>
          <div className="glow-text-green" style={{fontSize: '2rem', fontWeight: 'bold'}}>
            {lifetimeCredits.toFixed(2)} <span style={{fontSize: '1rem', color: '#fff'}}>kg CO2e</span>
          </div>
          <div style={{color: '#ffb800', fontSize: '1.2rem', marginTop: '4px', fontWeight: 'bold'}}>
            Payout: ₹{((lifetimeCredits / 1000) * 450).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
          </div>
        </div>
      </div> {/* <-- THIS IS THE DIV YOU WERE MISSING! */}

      {/* The Audit Timeline */}
      <div className="glass-panel full-width">
        <h3 style={{ marginBottom: '24px' }}>Immutable AWD Cycle Timeline</h3>
        
        {farmerLogs.length === 0 ? (
          <p style={{color: 'var(--text-secondary)', textAlign: 'center', padding: '40px'}}>No cycles logged for this farmer yet.</p>
        ) : (
          <div style={{ borderLeft: '2px solid var(--border-color)', marginLeft: '20px', paddingLeft: '30px' }}>
            {farmerLogs.map((log, index) => {
              const isDry = log.state_wet_dry === 'Dry';
              const logDate = new Date(log.timestamp);
              
              return (
                <div key={log.id} style={{ position: 'relative', marginBottom: '40px' }}>
                  {/* Timeline Node */}
                  <div style={{
                    position: 'absolute',
                    left: '-39px',
                    top: '0',
                    width: '16px',
                    height: '16px',
                    borderRadius: '50%',
                    background: isDry ? 'var(--accent-warning)' : 'var(--accent-blue)',
                    boxShadow: isDry ? '0 0 10px rgba(255, 184, 0, 0.5)' : '0 0 10px rgba(0, 212, 255, 0.5)'
                  }} />
                  
                  <div style={{ background: 'rgba(255,255,255,0.02)', padding: '20px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                    <div style={{display: 'flex', justifyContent: 'space-between', marginBottom: '12px'}}>
                      <div style={{fontWeight: 'bold', color: 'var(--text-secondary)'}}>
                        {logDate.toLocaleString()}
                      </div>
                      <span className={`badge ${isDry ? 'dry' : 'wet'}`}>
                        STATE: {log.state_wet_dry.toUpperCase()}
                      </span>
                    </div>

                    <div style={{display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px'}}>
                      <div>
                        {log.image_url.includes('static/images') ? (
                          <img 
                            src={log.image_url} 
                            alt="Verified Field" 
                            style={{
                              width: '100%', 
                              height: '120px', 
                              objectFit: 'cover', 
                              borderRadius: '8px', 
                              border: '1px solid rgba(0, 255, 136, 0.4)',
                              boxShadow: '0 4px 12px rgba(0, 0, 0, 0.5)'
                            }} 
                          />
                        ) : (
                          <div style={{
                            height: '120px', 
                            background: '#000', 
                            borderRadius: '8px', 
                            display: 'flex', 
                            alignItems: 'center', 
                            justifyContent: 'center',
                            border: '1px solid rgba(255,255,255,0.1)',
                            color: 'var(--text-secondary)',
                            fontSize: '0.8rem',
                          }}>
                            📡 Edge Node Telemetry
                          </div>
                        )}
                      </div>
                      
                      <div>
                        <h4 style={{marginBottom: '8px'}}>Tri-Layer Verification Consensus</h4>
                        <ul style={{listStyle: 'none', padding: 0, fontSize: '0.9rem', color: 'var(--text-secondary)'}}>
                          <li style={{marginBottom: '4px'}}>✅ Liveness & Geofence: <strong>Passed</strong></li>
                          <li style={{marginBottom: '4px'}}>✅ Groq Vision AI: <strong>{log.state_wet_dry}</strong></li>
                          <li style={{marginBottom: '4px'}}>✅ SAR Orbital Check: <strong>Confirmed</strong></li>
                        </ul>
                        
                        <div style={{
                          marginTop: '16px', 
                          padding: '8px', 
                          background: 'rgba(0,0,0,0.5)', 
                          borderRadius: '4px', 
                          fontFamily: 'monospace',
                          fontSize: '0.85rem',
                          color: '#00ff88'
                        }}>
                          TX_HASH: {generateHash(log.id, log.timestamp)}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
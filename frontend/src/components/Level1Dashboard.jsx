import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

export default function Level1Dashboard() {
  const generateMockSAR = () => {
    let data = [];
    const baseDate = new Date();
    baseDate.setDate(baseDate.getDate() - 30);
    for(let i=0; i<30; i++) {
        const d = new Date(baseDate);
        d.setDate(d.getDate() + i);
        const cycle = Math.sin(2 * Math.PI * i / 7);
        data.push({
            date: d.toLocaleDateString('en-US', {month: 'short', day: 'numeric'}),
            vv: -12.0 + (cycle * 2.5) + (Math.random() * 1.2 - 0.6),
            vh: -18.0 + (cycle * 1.2) + (Math.random() * 1.2 - 0.6),
        });
    }
    return data;
  };

  const [sarData] = useState(generateMockSAR());
  const [credits, setCredits] = useState([]);
  const [totals, setTotals] = useState({ farmers: 0, reduction: 0 });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const farmersRes = await axios.get('http://127.0.0.1:8000/api/dashboard/farmers');
        const creditsRes = await axios.get('http://127.0.0.1:8000/api/dashboard/carbon-credits');
        
        setTotals({
          farmers: farmersRes.data.total_farmers,
          reduction: creditsRes.data.total_flux_reduction.toFixed(1)
        });
        setCredits(creditsRes.data.data);
      } catch (error) {
        console.error("API Error:", error);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 5000); 
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ marginTop: '20px' }}>
      <div className="metrics-row">
        <div className="metric-card">
          <div className="metric-label">Total Verified Farmers</div>
          <div className="metric-value glow-text-blue">{totals.farmers}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Total Flux Reduction (kg CO2e)</div>
          <div className="metric-value glow-text-green">{totals.reduction}</div>
        </div>
      </div>

      <h3 style={{ marginBottom: '16px', marginTop: '32px' }}>Synthetic SAR Backscatter (30 Days)</h3>
      <div style={{ width: '100%', height: 350 }}>
        <ResponsiveContainer>
          <LineChart data={sarData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="date" stroke="#a0a0a5" tick={{fill: '#a0a0a5', fontSize: 12}} />
            <YAxis stroke="#a0a0a5" tick={{fill: '#a0a0a5', fontSize: 12}} domain={['auto', 'auto']} />
            <Tooltip contentStyle={{ backgroundColor: 'rgba(28,28,30,0.95)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }} itemStyle={{ color: '#fff' }} />
            <Legend />
            <Line type="monotone" dataKey="vv" name="VV Band (dB)" stroke="#00d4ff" strokeWidth={3} dot={false} activeDot={{ r: 8 }} />
            <Line type="monotone" dataKey="vh" name="VH Band (dB)" stroke="#00ff88" strokeWidth={3} dot={false} activeDot={{ r: 8 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <h3 style={{ marginBottom: '16px', marginTop: '40px' }}>Carbon Credit Ledger</h3>
      <table className="data-table">
        <thead>
          <tr>
            <th>Tx ID</th>
            <th>Farmer ID</th>
            <th>Reduction (kg)</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {credits.map(c => (
            <tr key={c.id}>
              <td style={{fontWeight: 600}}>AV-{c.id}</td>
              <td style={{color: 'var(--text-secondary)'}}>#{c.farmer_id}</td>
              <td className="glow-text-green">+{c.flux_reduction}</td>
              <td>
                <span className={`badge ${c.status === 'Verified' ? 'wet' : 'dry'}`}>{c.status}</span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
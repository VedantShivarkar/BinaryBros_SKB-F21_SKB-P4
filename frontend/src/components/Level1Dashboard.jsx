import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer } from 'recharts';

function Level1Dashboard() {
  const [credits, setCredits] = useState([]);
  const [loading, setLoading] = useState(true);

  // Generate mock synthetic SAR backscatter data for the chart roughly mimicking what the Python model outputs
  const mockSarData = Array.from({ length: 30 }).map((_, i) => {
    const awdSignal = Math.sin((i / 30) * Math.PI * 4); // basic sine wave to simulate wet/dry cycles over 30 days
    return {
      day: i + 1,
      vv_db: -15 + awdSignal * 5 + (Math.random() * 2 - 1), // VV backscatter varies between -10 to -20
      vh_db: -20 + awdSignal * 3 + (Math.random() * 1.5 - 0.75), 
    };
  });

  useEffect(() => {
    const fetchCredits = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/carbon-credits?limit=10');
        const data = await response.json();
        if (data.status === 'ok') {
          setCredits(data.data);
        }
      } catch (error) {
        console.error('Failed to fetch carbon credits:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchCredits();
  }, []);

  return (
    <>
      <div className="card" style={{ marginBottom: '2rem' }}>
        <h3 className="card-title" style={{ fontSize: '1.2rem', marginBottom: '1rem', color: '#fff' }}>
          Sentinel-1 SAR Time-Series (AWD Assurance)
        </h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem', fontSize: '0.9rem' }}>
          Synthetic Aperture Radar backscatter mimicking VV & VH polarization bands to detect Alternate Wetting and Drying cycles. Peaks indicate wet phases.
        </p>
        <div className="chart-container">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={mockSarData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="day" stroke="#b3b3b3" />
              <YAxis stroke="#b3b3b3" label={{ value: 'Backscatter (dB)', angle: -90, position: 'insideLeft', fill: '#b3b3b3' }} />
              <RechartsTooltip 
                contentStyle={{ backgroundColor: '#1e1e1e', border: '1px solid #333', borderRadius: '8px' }}
                itemStyle={{ color: '#fff' }}
              />
              <Legend />
              <Line type="monotone" dataKey="vv_db" name="VV Polarization" stroke="#00f3ff" strokeWidth={3} dot={{ r: 3 }} activeDot={{ r: 8 }} />
              <Line type="monotone" dataKey="vh_db" name="VH Polarization" stroke="#39ff14" strokeWidth={3} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="table-container">
        <div className="table-header">
          <h3 style={{ color: '#fff' }}>Verifiable Carbon Credits Ledger</h3>
        </div>
        
        {loading ? (
          <div className="loading" style={{ padding: '3rem' }}>Loading carbon credits...</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Farmer Name</th>
                <th>Methodology</th>
                <th>CH₄ Flux Reduction</th>
                <th>Credits Earned</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {credits.map((credit) => (
                <tr key={credit.id}>
                  <td style={{ fontWeight: 500 }}>{credit.Farmers?.name || 'Unknown'} <br/> <span style={{fontSize:'0.8em', color:'var(--text-muted)'}}>{credit.Farmers?.region}</span></td>
                  <td>{credit.methodology}</td>
                  <td>{credit.flux_reduction.toFixed(2)} kg CO₂e</td>
                  <td style={{ fontWeight: 600, color: 'var(--accent-neon-green)' }}>{credit.credits_earned.toFixed(2)} MCO2</td>
                  <td>
                    <span className={`badge ${credit.status.toLowerCase()}`}>
                      {credit.status}
                    </span>
                  </td>
                </tr>
              ))}
              {credits.length === 0 && (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-muted)' }}>
                    No carbon credits found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </>
  );
}

export default Level1Dashboard;

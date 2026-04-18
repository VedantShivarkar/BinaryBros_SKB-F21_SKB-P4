import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import Level2Map from './Level2Map';

export default function Level1Dashboard() {
  const [credits, setCredits] = useState([]);
  const [totals, setTotals] = useState({ farmers: 0, reduction: 0 });

  // 1. Meaningful Government Data: Cumulative Methane Reduction
  const generateReductionTrend = () => {
    let data = [];
    let currentTotal = 0;
    for(let i = 10; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const dailyMint = Math.random() * 45 + 10; // Simulated daily tons
      currentTotal += dailyMint;
      data.push({
        date: d.toLocaleDateString('en-US', {month: 'short', day: 'numeric'}),
        actual: Math.round(currentTotal),
        target: Math.round(currentTotal * 1.2) // Policy target line
      });
    }
    return data;
  };

  // 2. Meaningful Government Data: Compliance Rate
  const complianceData = [
    { name: 'Compliant (Dry Cycle Verified)', value: 82 },
    { name: 'Non-Compliant (Flooded)', value: 12 },
    { name: 'Pending Tri-Layer Review', value: 6 }
  ];
  const COLORS = ['#00ff88', '#ff4444', '#ffb800'];

  const [trendData] = useState(generateReductionTrend());

  useEffect(() => {
    const fetchData = async () => {
      try {
        const farmersRes = await axios.get('http://127.0.0.1:8000/api/dashboard/farmers');
        const creditsRes = await axios.get('http://127.0.0.1:8000/api/dashboard/carbon-credits');
        
        setTotals({
          farmers: farmersRes.data.total_farmers,
          reduction: creditsRes.data.total_flux_reduction.toFixed(1)
        });
        // Only show top 5 latest transactions for the macro view
        setCredits(creditsRes.data.data.slice(-5).reverse());
      } catch (error) {
        console.error("API Error:", error);
      }
    };
    
    fetchData();
    const interval = setInterval(fetchData, 5000); 
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="dashboard-grid" style={{padding: '32px 0'}}>
      <div className="full-width text-center" style={{marginBottom: '20px'}}>
        <h1 style={{fontSize: '2.5rem', fontWeight: 800}}>National dMRV Registry</h1>
        <p className="glow-text-green">Macro-Level Carbon Sequestration Insights</p>
      </div>

      <div className="metrics-row full-width">
        <div className="metric-card">
          <div className="metric-label">Active Verified Farms</div>
          <div className="metric-value glow-text-blue">{totals.farmers}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Total CH4 Flux Reduction (kg CO2e)</div>
          <div className="metric-value glow-text-green">{totals.reduction}</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">Market Value (₹450/Ton)</div>
          <div className="metric-value" style={{color: '#ffb800'}}>
            ₹{((totals.reduction / 1000) * 450).toLocaleString('en-IN', { maximumFractionDigits: 2 })}
          </div>
        </div>
      </div> {/* <-- THIS DIV WAS MISSING! */}

      <div className="glass-panel" style={{gridColumn: 'span 2'}}>
        <h3 style={{ marginBottom: '20px' }}>Cumulative GHG Reduction vs. State Targets</h3>
        <div style={{ height: 300 }}>
          <ResponsiveContainer>
            <AreaChart data={trendData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="colorActual" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#00ff88" stopOpacity={0.8}/>
                  <stop offset="95%" stopColor="#00ff88" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="date" stroke="#a0a0a5" tick={{fontSize: 12}} />
              <YAxis stroke="#a0a0a5" tick={{fontSize: 12}} />
              <Tooltip contentStyle={{ backgroundColor: 'rgba(28,28,30,0.95)', borderColor: 'rgba(255,255,255,0.1)' }} />
              <Legend />
              <Area type="monotone" dataKey="target" stroke="#00d4ff" fill="none" strokeDasharray="5 5" name="Policy Target (kg CO2e)" />
              <Area type="monotone" dataKey="actual" stroke="#00ff88" fillOpacity={1} fill="url(#colorActual)" name="Verified Reduction (kg CO2e)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass-panel" style={{gridColumn: 'span 1'}}>
        <h3 style={{ marginBottom: '20px', textAlign: 'center' }}>AWD Compliance Distribution</h3>
        <div style={{ height: 300 }}>
          <ResponsiveContainer>
            <PieChart>
              <Pie data={complianceData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                {complianceData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: 'rgba(28,28,30,0.95)', borderColor: 'rgba(255,255,255,0.1)' }} />
              <Legend verticalAlign="bottom" height={36} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="glass-panel full-width">
        <h3 style={{ marginBottom: '20px' }}>Geospatial Heatmap (Verified Fields)</h3>
        <Level2Map />
      </div>
    </div>
  );
}
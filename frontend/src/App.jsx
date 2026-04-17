import { useState, useEffect } from 'react';
import Level1Dashboard from './components/Level1Dashboard';
import Level2Map from './components/Level2Map';
import { Leaf, Activity, BarChart2, Map as MapIcon } from 'lucide-react';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [summaryData, setSummaryData] = useState({
    total_farmers: 0,
    total_awd_logs: 0,
    total_flux_reduction_kg: 0,
    total_credits_earned: 0
  });

  useEffect(() => {
    // Fetch summary data from FastAPI backend
    const fetchSummary = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/dashboard/summary');
        const data = await response.json();
        if (data.status === 'ok') {
          setSummaryData(data.data);
        }
      } catch (error) {
        console.error('Failed to fetch dashboard summary:', error);
      }
    };
    
    fetchSummary();
  }, []);

  return (
    <div className="app-container">
      <header className="header">
        <h1>
          <Leaf size={28} className="text-neon-green" color="#39ff14" />
          Amrit Vaayu <span style={{ color: "var(--text-secondary)", fontSize: "1.2rem", fontWeight: 400 }}>dMRV Platform</span>
        </h1>
        
        <div className="nav-tabs">
          <button 
            className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <BarChart2 size={16} style={{ display: 'inline', marginRight: '6px' }} />
            Level 1: Dashboard
          </button>
          <button 
            className={`nav-tab ${activeTab === 'map' ? 'active' : ''}`}
            onClick={() => setActiveTab('map')}
          >
            <MapIcon size={16} style={{ display: 'inline', marginRight: '6px' }} />
            Level 2: geospatial
          </button>
        </div>
      </header>

      <main className="main-content">
        {/* Global Summary Cards visible on all tabs */}
        <div className="dashboard-grid">
          <div className="card">
            <div className="card-title">
              <Activity size={16} color="var(--accent-neon-blue)" /> 
              Registered Farmers
            </div>
            <div className="card-value blue">{summaryData.total_farmers}</div>
          </div>
          
          <div className="card">
            <div className="card-title">
              <Activity size={16} color="var(--accent-warning)" /> 
              AWD Observations Logged
            </div>
            <div className="card-value warning">{summaryData.total_awd_logs}</div>
          </div>
          
          <div className="card">
            <div className="card-title">
              <Leaf size={16} color="var(--accent-neon-green)" /> 
              CH₄ Flux Reduction
            </div>
            <div className="card-value">
              {summaryData.total_flux_reduction_kg.toLocaleString()} <span style={{fontSize: "1rem", color: "var(--text-secondary)"}}>kg CO₂e</span>
            </div>
          </div>

          <div className="card">
            <div className="card-title">
              <Leaf size={16} color="var(--accent-neon-green)" /> 
              Carbon Credits Earned
            </div>
            <div className="card-value">
              {summaryData.total_credits_earned.toLocaleString()} <span style={{fontSize: "1rem", color: "var(--text-secondary)"}}>credits</span>
            </div>
          </div>
        </div>

        {/* Dynamic Tab Content */}
        {activeTab === 'dashboard' && <Level1Dashboard />}
        {activeTab === 'map' && <Level2Map />}
        
      </main>
    </div>
  );
}

export default App;

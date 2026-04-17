import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Level1Dashboard from './components/Level1Dashboard';
import AuditorDashboard from './components/AuditorDashboard';
// We will create these two in the next steps:
// import AuditorDashboard from './components/AuditorDashboard';
// import FarmerRegistration from './components/FarmerRegistration';

function Navigation() {
  const location = useLocation();
  const isActive = (path) => location.pathname === path ? 'active-link' : '';

  return (
    <nav className="top-nav">
      <div className="nav-logo">
        <span className="glow-text-green">Amrit</span> Vaayu 
      </div>
      <div className="nav-links">
        <Link to="/" className={isActive('/')}>🏦 Gov Registry</Link>
        <Link to="/auditor" className={isActive('/auditor')}>📋 Auditor View</Link>
        <Link to="/register" className={isActive('/register')}>🌾 Farmer Portal</Link>
      </div>
    </nav>
  );
}

function App() {
  return (
    <Router>
      <div className="app-container">
        <Navigation />
        <Routes>
          <Route path="/" element={<Level1Dashboard />} />
          <Route path="/auditor" element={<AuditorDashboard />} /> {/* <-- UPDATE THIS */}
          <Route path="/register" element={<div className="glass-panel" style={{margin: '32px'}}><h2>Farmer Portal (Coming Next)</h2></div>} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
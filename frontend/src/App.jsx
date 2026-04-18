import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import Level1Dashboard from './components/Level1Dashboard';
import AuditorDashboard from './components/AuditorDashboard';
import FarmerRegistration from './components/FarmerRegistration';
import FarmerMobileApp from './components/FarmerMobileApp'; // 🚨 1. NEW IMPORT HERE

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
        {/* Note: We keep the top nav for the desktop views, but the mobile app will just be a standalone page */}
        <Navigation />
        <Routes>
          <Route path="/" element={<Level1Dashboard />} />
          <Route path="/auditor" element={<AuditorDashboard />} />
          <Route path="/register" element={<FarmerRegistration />} />
          <Route path="/app" element={<FarmerMobileApp />} /> {/* 🚨 2. NEW ROUTE HERE */}
        </Routes>
      </div>
    </Router>
  );
}

export default App;
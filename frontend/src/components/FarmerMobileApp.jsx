import React, { useState } from 'react';
import axios from 'axios';

export default function FarmerMobileApp() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

   const handleCapture = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setLoading(true);
    setResult(null);

    // Try to get Native GPS
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          // Success: We got the REAL GPS coordinates!
          const { latitude, longitude } = position.coords;
          
          const formData = new FormData();
          formData.append('farmer_id', 1);
          formData.append('lat', latitude);
          formData.append('lng', longitude);
          formData.append('image', file);

          try {
            // Notice we use the relative path now! The Vite Proxy handles the rest.
            const res = await axios.post('/api/mobile-upload', formData);
            setResult(res.data);
          } catch (error) {
            setResult({ success: false, reason: 'Network connection to edge server failed.' });
          }
          setLoading(false);
        },
        (error) => {
          // Authentic rejection if they deny the prompt
          setResult({ success: false, reason: 'GPS Permission Denied. Geofence verification failed.' });
          setLoading(false);
        },
        { enableHighAccuracy: true, timeout: 10000 }
      );
    } else {
      setResult({ success: false, reason: 'Browser does not support GPS.' });
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', background: '#0a0a0a', minHeight: '100vh', color: '#fff', fontFamily: 'sans-serif' }}>
      <h2 style={{ textAlign: 'center', color: '#00ff88' }}>Amrit Vaayu Camera</h2>
      <p style={{ textAlign: 'center', color: '#888', fontSize: '0.9rem', marginBottom: '40px' }}>Secure dMRV Capture Tool</p>

      <div style={{ textAlign: 'center' }}>
        {/* The magic HTML5 attribute that opens the mobile camera */}
        <label style={{ display: 'inline-block', background: '#00ff88', color: '#000', padding: '20px 40px', borderRadius: '50px', fontSize: '1.2rem', fontWeight: 'bold', cursor: 'pointer' }}>
          📸 CAPTURE FIELD
          <input type="file" accept="image/*" capture="environment" onChange={handleCapture} style={{ display: 'none' }} />
        </label>
      </div>

      {loading && <div style={{ marginTop: '30px', textAlign: 'center', color: '#00d4ff' }}>📡 Analyzing Photo & GPS...</div>}

      {result && (
        <div style={{ marginTop: '30px', padding: '20px', borderRadius: '12px', background: result.success ? 'rgba(0, 255, 136, 0.1)' : 'rgba(255, 68, 68, 0.1)', border: `1px solid ${result.success ? '#00ff88' : '#ff4444'}` }}>
          <h3 style={{ color: result.success ? '#00ff88' : '#ff4444' }}>
            {result.success ? '✅ VERIFIED' : '❌ REJECTED'}
          </h3>
          <p style={{ marginTop: '8px' }}>{result.message || result.reason}</p>
          
          {result.success && result.state === 'DRY' && (
            <div style={{ marginTop: '16px', borderTop: '1px solid rgba(255,255,255,0.1)', paddingTop: '16px' }}>
              <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#fff' }}>+{result.credits_earned} kg CO2e</div>
              <div style={{ fontSize: '1.2rem', color: '#ffb800' }}>Payout Generated: ₹{result.money_earned}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
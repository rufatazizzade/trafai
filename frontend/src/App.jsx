
import { useState, useEffect } from 'react'
import MapComponent from './components/MapComponent'
import ControlPanel from './components/ControlPanel'
import StatsPanel from './components/StatsPanel'
import api from './api'
import { LayoutDashboard, Activity } from 'lucide-react'
import './index.css'

function App() {
  const [routeData, setRouteData] = useState(null)
  const [graph, setGraph] = useState({ nodes: [], edges: [] })

  useEffect(() => {
    const fetchGraph = () => {
      api.get('/network/layout').then(res => {
        setGraph(res.data)
      }).catch(err => console.error("Failed to load graph", err))
    };

    fetchGraph(); // Initial load

    // Poll for traffic updates
    const interval = setInterval(fetchGraph, 5000);
    return () => clearInterval(interval);
  }, [])

  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh' }}>
      {/* Sidebar */}
      <div className="glass-panel" style={{
        width: '350px',
        minWidth: '350px',
        margin: '1rem',
        padding: '1.5rem',
        display: 'flex',
        flexDirection: 'column',
        gap: '2rem',
        zIndex: 1000,
        overflowY: 'auto'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ padding: '0.5rem', background: 'var(--primary-color)', borderRadius: '8px' }}>
            <Activity color="white" size={24} />
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700 }}>TrafficAI</h1>
            <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Routing System</span>
          </div>
        </div>

        <ControlPanel onRouteComputed={setRouteData} nodes={graph.nodes} />

        {routeData && <StatsPanel data={routeData} />}

        <div style={{ marginTop: 'auto', paddingTop: '1rem', fontSize: '0.75rem', color: 'var(--text-secondary)', textAlign: 'center' }}>
          System Status: <span style={{ color: '#10b981' }}>● Online</span> | Nodes: {graph.nodes.length}
        </div>
      </div>

      {/* Map Area */}
      <div style={{ flex: 1, position: 'relative' }}>
        {/* Pass graph and routeData to MapComponent */}
        <MapComponent graph={graph} routeData={routeData} />

        {/* Floating Title */}
        <div className="glass-panel" style={{
          position: 'absolute',
          top: '1rem',
          right: '1rem',
          padding: '0.75rem 1.25rem',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem'
        }}>
          <LayoutDashboard size={16} color="var(--text-secondary)" />
          <span style={{ fontSize: '0.875rem', fontWeight: 600 }}>Urban Grid Network</span>
        </div>
      </div>
    </div>
  )
}

export default App

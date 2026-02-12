import { useState, useEffect } from 'react'
import MapComponent from './components/MapComponent'
import ControlPanel from './components/ControlPanel'
import StatsPanel from './components/StatsPanel'
import api from './api'
import { LayoutDashboard, Activity } from 'lucide-react'
import './index.css'
import { APIProvider } from '@vis.gl/react-google-maps';
import ErrorBoundary from './components/ErrorBoundary';

// Replace with your actual API Key
const API_KEY = 'AIzaSyAIgGT3GCutntPZzCKydw-dPArt-s3BdJg';

function App() {
  const [routeData, setRouteData] = useState(null)
  const [graph, setGraph] = useState({ nodes: [], edges: [] })

  useEffect(() => {
    // Optimization: Disable full graph fetching to improve performance.
    // The map will rely on Google Maps base layer.
    // We only only need to fetch route data when requested.
  }, [])

  return (
    <APIProvider apiKey={API_KEY} libraries={['places', 'marker']}>
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
          <ErrorBoundary>
            <MapComponent graph={graph} routeData={routeData} />
          </ErrorBoundary>

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
    </APIProvider>
  )
}

export default App

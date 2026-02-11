
import { useState, useEffect } from 'react'
import { Navigation, Clock, Play, MapPin } from 'lucide-react'
import api, { geocode } from '../api'

export default function ControlPanel({ onRouteComputed }) {
    const [startAddr, setStartAddr] = useState('')
    const [endAddr, setEndAddr] = useState('')
    const [time, setTime] = useState(8)
    const [loading, setLoading] = useState(false)
    const [status, setStatus] = useState('')

    const handleRoute = async () => {
        setLoading(true)
        setStatus('Geocoding addresses...')
        try {
            // 1. Geocode Start
            const startRes = await geocode(startAddr)
            const startNode = startRes.data.node_id

            // 2. Geocode End
            const endRes = await geocode(endAddr)
            const endNode = endRes.data.node_id

            setStatus('Computing optimal route...')

            // 3. Compute Route
            const res = await api.post('/route', {
                start_node: startNode.toString(),
                end_node: endNode.toString(),
                time_hour: parseInt(time)
            })

            onRouteComputed(res.data)
            setStatus('Route computed!')

        } catch (err) {
            console.error(err)
            const msg = err.response?.data?.detail || err.message
            alert("Error: " + msg)
            setStatus('Error occurred.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div className="input-group">
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-secondary)' }}>
                    <Navigation size={14} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                    Route Planning
                </label>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                    <div style={{ position: 'relative' }}>
                        <MapPin size={14} style={{ position: 'absolute', left: '10px', top: '12px', color: 'var(--text-secondary)' }} />
                        <input
                            value={startAddr}
                            onChange={e => setStartAddr(e.target.value)}
                            placeholder="Start Address (e.g. Wall St)"
                            style={{ paddingLeft: '2rem' }}
                        />
                    </div>

                    <div style={{ position: 'relative' }}>
                        <MapPin size={14} style={{ position: 'absolute', left: '10px', top: '12px', color: '#10b981' }} />
                        <input
                            value={endAddr}
                            onChange={e => setEndAddr(e.target.value)}
                            placeholder="End Address (e.g. Broadway)"
                            style={{ paddingLeft: '2rem' }}
                        />
                    </div>
                </div>
            </div>

            <div className="input-group">
                <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.875rem', fontWeight: 500, color: 'var(--text-secondary)' }}>
                    <Clock size={14} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />
                    Time of Day: {time}:00
                </label>
                <input
                    type="range"
                    min="0" max="23"
                    value={time}
                    onChange={e => setTime(e.target.value)}
                    style={{ width: '100%', accentColor: 'var(--primary-color)' }}
                />
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                    <span>00:00</span>
                    <span>12:00</span>
                    <span>23:00</span>
                </div>
            </div>

            <button
                className="btn-primary"
                onClick={handleRoute}
                disabled={loading || !startAddr || !endAddr}
                style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
            >
                {loading ? 'Processing...' : <><Play size={16} /> Compute Route</>}
            </button>

            {status && <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textAlign: 'center' }}>{status}</div>}
        </div>
    )
}

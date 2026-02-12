import { useState, useEffect } from 'react'
import { Navigation, Clock, Play, MapPin } from 'lucide-react'
import api, { geocode } from '../api'
import usePlacesAutocomplete, {
    getGeocode,
    getLatLng,
} from "use-places-autocomplete";
import { useMapsLibrary } from '@vis.gl/react-google-maps';

// Reusable Autocomplete Component
const PlacesAutocomplete = ({ setSelected, placeholder, iconColor }) => {
    // Ensure Places library is loaded before using the hook
    const placesLib = useMapsLibrary('places');
    const [enabled, setEnabled] = useState(false);

    useEffect(() => {
        if (placesLib) setEnabled(true);
    }, [placesLib]);

    if (!enabled) {
        return (
            <div style={{ position: 'relative' }}>
                <MapPin size={14} style={{ position: 'absolute', left: '10px', top: '12px', color: iconColor }} />
                <input
                    disabled
                    placeholder="Loading maps..."
                    style={{ paddingLeft: '2rem', width: '100%', boxSizing: 'border-box' }}
                />
            </div>
        )
    }

    // Only render hook when enabled
    return <PlacesAutocompleteInner setSelected={setSelected} placeholder={placeholder} iconColor={iconColor} />;
};

const PlacesAutocompleteInner = ({ setSelected, placeholder, iconColor }) => {
    const {
        ready,
        value,
        setValue,
        suggestions: { status, data },
        clearSuggestions,
    } = usePlacesAutocomplete({
        initOnMount: true,
        debounce: 300
    });

    const handleSelect = async (address) => {
        setValue(address, false);
        clearSuggestions();

        try {
            const results = await getGeocode({ address });
            const { lat, lng } = await getLatLng(results[0]);
            // Pass both address and coords
            setSelected({ address, lat, lng });
        } catch (error) {
            console.log("Error: ", error);
        }
    };

    return (
        <div style={{ position: 'relative' }}>
            <MapPin size={14} style={{ position: 'absolute', left: '10px', top: '12px', color: iconColor }} />
            <input
                value={value}
                onChange={(e) => setValue(e.target.value)}
                disabled={!ready}
                placeholder={placeholder}
                style={{ paddingLeft: '2rem', width: '100%', boxSizing: 'border-box' }}
            />
            {status === "OK" && (
                <ul style={{
                    position: 'absolute',
                    zIndex: 1000,
                    background: 'var(--panel-bg)',
                    width: '100%',
                    listStyle: 'none',
                    padding: '0.5rem',
                    margin: 0,
                    border: '1px solid var(--border-color)',
                    borderRadius: '0 0 8px 8px',
                    maxHeight: '200px',
                    overflowY: 'auto'
                }}>
                    {data.map(({ place_id, description }) => (
                        <li
                            key={place_id}
                            onClick={() => handleSelect(description)}
                            style={{
                                padding: '0.5rem',
                                cursor: 'pointer',
                                color: 'var(--text-primary)',
                                borderBottom: '1px solid var(--border-color)'
                            }}
                            className="hover:bg-gray-700"
                        >
                            {description}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}

export default function ControlPanel({ onRouteComputed }) {
    const [startLocation, setStartLocation] = useState(null)
    const [endLocation, setEndLocation] = useState(null)

    const [time, setTime] = useState(8)
    const [loading, setLoading] = useState(false)
    const [status, setStatus] = useState('')

    const handleRoute = async (e) => {
        if (e && e.preventDefault) e.preventDefault();

        if (!startLocation || !endLocation) return;

        setLoading(true)
        setStatus('Resolving nodes & Route...')
        try {
            // Updated: Pass coordinates directly. Backend determines nodes and loads graph if needed.
            const payload = {
                start_lat: startLocation.lat,
                start_lon: startLocation.lng,
                end_lat: endLocation.lat,
                end_lon: endLocation.lng,
                time_hour: parseInt(time)
            };

            setStatus('Downloading map & Computing route... (this may take a moment)')

            // 3. Compute Route via Proxy (which goes to backend)
            const res = await api.post('/route', payload)

            onRouteComputed(res.data)
            setStatus('Route computed!')

        } catch (err) {
            console.error(err)
            const msg = err.response?.data?.detail || err.message
            alert("Error: " + msg + ". Make sure backend is running.")
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
                    <PlacesAutocomplete
                        setSelected={setStartLocation}
                        placeholder="Start Address (e.g. Empire State)"
                        iconColor="var(--text-secondary)"
                    />

                    <PlacesAutocomplete
                        setSelected={setEndLocation}
                        placeholder="End Address (e.g. Times Square)"
                        iconColor="#10b981"
                    />
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
                type="button"
                className="btn-primary"
                onClick={handleRoute}
                disabled={loading || !startLocation || !endLocation}
                style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}
            >
                {loading ? 'Processing...' : <><Play size={16} /> Compute Route</>}
            </button>

            {status && <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textAlign: 'center' }}>{status}</div>}
        </div>
    )
}

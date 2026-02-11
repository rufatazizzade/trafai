
import { useEffect, useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline, CircleMarker, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import api from '../api'

// Simple component to fit map to bounds
function MapBounds({ nodes }) {
    const map = useMap();
    useEffect(() => {
        if (nodes && nodes.length > 0) {
            const lats = nodes.map(n => n.y);
            const lngs = nodes.map(n => n.x);
            // Invert Y for mapping if needed, but assuming x=lng, y=lat or similar scaling
            // Grid is small (0-4), so we might need to scale coordinates to real world or use simple CRS
            // For simplicity, let's just center.
            // Actually, (0,0) to (4, -4) is very small in LatLng. 
            // We should scale them up or use "Simple" CRS.
            // Using Simple CRS is better for grid, but TileLayer needs standard CRS.
            // Let's multiply by 0.01 degree (~1km) for valid lat/lng separation.
        }
    }, [nodes, map]);
    return null;
}

const SCALE = 0.005; // Scale grid coordinates to lat/lng degrees approx 500m

function ChangeView({ nodes }) {
    const map = useMap();
    useEffect(() => {
        if (nodes && nodes.length > 0) {
            // Find bounds
            let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
            nodes.forEach(n => {
                if (n.x < minX) minX = n.x;
                if (n.x > maxX) maxX = n.x;
                if (n.y < minY) minY = n.y;
                if (n.y > maxY) maxY = n.y;
            });
            // Convert to LatLng
            // Center is (51.505, -0.09) per getLatLng logic below
            const centerLat = 51.505;
            const centerLng = -0.09;

            const lat1 = centerLat + minY * SCALE;
            const lng1 = centerLng + minX * SCALE;
            const lat2 = centerLat + maxY * SCALE;
            const lng2 = centerLng + maxX * SCALE;

            map.fitBounds([[lat1, lng1], [lat2, lng2]], { padding: [50, 50] });
        }
    }, [nodes, map]);
    return null;
}

export default function MapComponent({ graph, routeData }) {
    // graph is passed from parent now

    // Helper to convert grid pos to LatLng
    const getLatLng = (x, y) => {
        // Center at arbitrary location (e.g., London)
        const centerLat = 51.505;
        const centerLng = -0.09;
        return [centerLat + y * SCALE, centerLng + x * SCALE];
    };

    const getNodePos = (id) => {
        const n = graph.nodes.find(n => n.id === id);
        return n ? getLatLng(n.x, n.y) : [0, 0];
    };

    return (
        <MapContainer center={[51.505, -0.09]} zoom={15} style={{ height: '100%', width: '100%', background: '#0f172a' }}>
            <ChangeView nodes={graph.nodes} />
            <TileLayer
                attribution='&copy; OpenStreetMap'
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />

            {/* Draw Network Edges */}
            {graph.edges.map((edge, i) => {
                const start = getNodePos(edge.source);
                const end = getNodePos(edge.target);

                // Color based on congestion
                const load = edge.current_flow / edge.capacity;
                let color = '#94a3b8'; // Lighter slate for better visibility on dark map
                let weight = 2;

                if (load > 0.8) { color = '#ef4444'; weight = 4; } // Red
                else if (load > 0.5) { color = '#f59e0b'; weight = 3; } // Orange

                return <Polyline key={i} positions={[start, end]} pathOptions={{ color, weight, opacity: 0.8 }} />
            })}

            {/* Draw Nodes */}
            {graph.nodes.map(node => (
                <CircleMarker
                    key={node.id}
                    center={getLatLng(node.x, node.y)}
                    radius={4}
                    pathOptions={{ color: '#3b82f6', fillColor: '#3b82f6', fillOpacity: 1 }}
                >
                    <Popup>{node.id}</Popup>
                </CircleMarker>
            ))}

            {/* Draw Computed Route */}
            {routeData && (
                <Polyline
                    positions={routeData.path.map(nodeId => getNodePos(nodeId))}
                    pathOptions={{ color: '#10b981', weight: 6, opacity: 0.9, dashArray: '10, 10' }} // Green dashed
                />
            )}
        </MapContainer>
    )
}

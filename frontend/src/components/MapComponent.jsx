import { useEffect, useState, useMemo } from 'react';
import { Map, useMap, Marker } from '@vis.gl/react-google-maps';

// Remove Map ID to avoid issues if the key doesn't support it
// const MAP_ID = 'bf51a910020fa25a'; 

function MapBounds({ nodes, routeData }) {
    const map = useMap();
    useEffect(() => {
        if (!map) return;

        try {
            const bounds = new google.maps.LatLngBounds();
            let hasPoints = false;

            // Prioritize route bounds
            if (routeData && routeData.geometry && Array.isArray(routeData.geometry)) {
                routeData.geometry.forEach(pt => {
                    if (pt && typeof pt.lat === 'number' && typeof pt.lng === 'number') {
                        bounds.extend(pt);
                        hasPoints = true;
                    }
                });
            }

            // Fallback to graph nodes
            if (!hasPoints && nodes && Array.isArray(nodes) && nodes.length > 0) {
                nodes.forEach(node => {
                    if (node && typeof node.y === 'number' && typeof node.x === 'number') {
                        bounds.extend({ lat: node.y, lng: node.x });
                        hasPoints = true;
                    }
                });
            }

            if (hasPoints) {
                console.log("Fitting bounds:", bounds);
                map.fitBounds(bounds);
            } else {
                console.log("No points to fit bounds to.");
            }
        } catch (e) {
            console.error("Error in MapBounds:", e);
        }
    }, [nodes, routeData, map]);
    return null;
}

// Polyline component using Google Maps API
function Polyline({ path, options }) {
    const map = useMap();
    const [polyline, setPolyline] = useState(null);

    useEffect(() => {
        if (!map) return;

        const line = new google.maps.Polyline({
            path,
            ...options
        });

        line.setMap(map);
        setPolyline(line);

        return () => {
            line.setMap(null);
        };
    }, [map]);

    useEffect(() => {
        if (polyline) {
            polyline.setPath(path);
            polyline.setOptions(options);
        }
    }, [polyline, path, options]);

    return null;
}

export default function MapComponent({ graph, routeData }) {

    // Default center (London)
    const defaultCenter = { lat: 51.505, lng: -0.09 };

    return (
        <div style={{ height: '100%', width: '100%' }}>
            <Map
                defaultCenter={defaultCenter}
                defaultZoom={13}
                // mapId={MAP_ID} // Removed to prevent crashes with AdvancedMarkers
                style={{ width: '100%', height: '100%' }}
                options={{
                    disableDefaultUI: false,
                    zoomControl: true,
                    mapTypeControl: false,
                    streetViewControl: false,
                    fullscreenControl: false,
                }}
            >
                <MapBounds nodes={graph.nodes} routeData={routeData} />

                {/* Draw Computed Route */}
                {routeData && (() => {
                    try {
                        let path = [];
                        if (routeData.geometry && Array.isArray(routeData.geometry) && routeData.geometry.length > 0) {
                            path = routeData.geometry;
                        }

                        if (path.length > 0) {
                            return (
                                <>
                                    <Polyline
                                        path={path}
                                        options={{
                                            strokeColor: '#10b981',
                                            strokeOpacity: 1.0,
                                            strokeWeight: 6,
                                            zIndex: 100
                                        }}
                                    />
                                    {/* Start Marker */}
                                    {path[0] && <Marker position={path[0]} title="Start" />}
                                    {/* End Marker */}
                                    {path[path.length - 1] && <Marker position={path[path.length - 1]} title="End" />}
                                </>
                            );
                        }
                    } catch (e) {
                        console.error("Error rendering route:", e);
                    }
                    return null;
                })()}

            </Map>
        </div>
    );
}

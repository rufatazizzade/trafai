import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Union

app = FastAPI(title="Google Maps Routing Proxy")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API KEY from Frontend
GOOGLE_API_KEY = "AIzaSyAIgGT3GCutntPZzCKydw-dPArt-s3BdJg"

class GeocodeRequest(BaseModel):
    address: str

class RouteRequest(BaseModel):
    # Support both ID-based (legacy matches) and Coordinate-based request
    start_node: Optional[Union[str, int]] = None
    end_node: Optional[Union[str, int]] = None
    start_lat: Optional[float] = None
    start_lon: Optional[float] = None
    end_lat: Optional[float] = None
    end_lon: Optional[float] = None
    time_hour: int = 8

def decode_polyline(polyline_str):
    """
    Decodes a Google Maps encoded polyline string into a list of dicts {'lat': ..., 'lng': ...}
    """
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}

    while index < len(polyline_str):
        for unit in ['latitude', 'longitude']:
            shift, result = 0, 0

            while True:
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break

            if (result & 1):
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']

        coordinates.append({'lat': lat / 100000.0, 'lng': lng / 100000.0})

    return coordinates

@app.get("/")
def read_root():
    return {"status": "System Operational", "mode": "Google Maps Proxy"}

@app.post("/geocode")
def geocode_address(request: GeocodeRequest):
    """
    Proxy to Google Geocoding API.
    """
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": request.address,
        "key": GOOGLE_API_KEY
    }
    
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Google API Error")
    
    data = resp.json()
    if data['status'] != 'OK':
        # Return empty/error if not found
        raise HTTPException(status_code=404, detail=f"Address not found: {data['status']}")
    
    # Extract first result
    res = data['results'][0]
    loc = res['geometry']['location']
    
    return {
        "node_id": res['place_id'], # Use place_id as ID
        "lat": loc['lat'],
        "lon": loc['lng'],
        "display_name": res['formatted_address']
    }

@app.post("/route")
def compute_route(request: RouteRequest):
    """
    Proxy to Google Directions API.
    """
    # 1. Determine Start/End coordinates
    origin = None
    destination = None
    
    if request.start_lat and request.start_lon:
        origin = f"{request.start_lat},{request.start_lon}"
    elif request.start_node:
        origin = f"place_id:{request.start_node}"
        
    if request.end_lat and request.end_lon:
        destination = f"{request.end_lat},{request.end_lon}"
    elif request.end_node:
        destination = f"place_id:{request.end_node}"
        
    if not origin or not destination:
        raise HTTPException(status_code=400, detail="Missing start or end coordinates")
        
    # 2. Call Google Directions API
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "key": GOOGLE_API_KEY,
        "mode": "driving",
        "traffic_model": "best_guess",
        "departure_time": "now" # For traffic info
    }
    
    print(f"Requesting Route: {origin} -> {destination}")
    
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Google Directions API Failed")
        
    data = resp.json()
    
    if data['status'] != 'OK':
        raise HTTPException(status_code=400, detail=f"No route found: {data['status']}")
    
    # 3. Parse and Format for Frontend
    if not data['routes']:
         raise HTTPException(status_code=404, detail="No routes found")

    route = data['routes'][0]
    leg = route['legs'][0]
    
    # Decode polyline to points
    overview_polyline = route['overview_polyline']['points']
    geometry = decode_polyline(overview_polyline)
    
    # Stats
    distance_meters = leg['distance']['value']
    duration_seconds = leg['duration']['value']
    
    return {
        "geometry": geometry,
        "stats": {
            "total_cost": duration_seconds / 60.0, # Cost in minutes
            "time_cost": duration_seconds / 60.0,
            "congestion_penalty": 0,
            "emission_cost": distance_meters * 0.0001, 
            "social_cost": 0,
            "travel_time_hours": duration_seconds / 3600.0
        },
        "path_nodes": [] # No node IDs in Google mode
    }

# Stub endpoints to preventing 404s on legacy frontend calls
@app.post("/network/init-grid")
def init_grid(rows: int = 5, cols: int = 5):
    return {"message": "Grid init disabled in Google Maps mode."}
    
class TrafficUpdate(BaseModel):
    u: str
    v: str
    current_flow: float

class TrafficUpdateList(BaseModel):
    updates: List[TrafficUpdate]

@app.post("/traffic/update")
def update_traffic(update_list: TrafficUpdateList):
    return {"updated_edges": 0}

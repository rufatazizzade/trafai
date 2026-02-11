from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
from src.graph.network import RoadNetwork
from src.routing.engine import RoutingEngine
from src.graph.osm_loader import OSMLoader

app = FastAPI(title="AI-Based Load-Balanced Routing System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Global State (In-memory for now)
network = RoadNetwork()

# Initialize with Real World Data
try:
    # Use address-based loading for better stability
    # 5km radius around Empire State Building covers Midtown and Downtown
    print("Loading OSM graph for Manhattan (5km around Empire State Bldg)...")
    G_osm = OSMLoader.load_graph_from_address("Empire State Building, New York, USA", dist=5000)
    network.load_from_osm_graph(G_osm)
    print(f"Loaded {network.graph.number_of_nodes()} nodes.")
except Exception as e:
    print(f"Failed to load OSM graph: {e}. Fallback to grid.")
    network.generate_grid_network(rows=5, cols=5)

# Background Traffic Simulation
import asyncio
import random

async def traffic_simulator():
    """
    Simulates real-time traffic updates by randomly adjusting edge flows.
    """
    while True:
        await asyncio.sleep(2) # Update every 2 seconds
        # Randomly select 10% of edges to update
        edges = list(network.graph.edges(data=True))
        if not edges: continue
        
        num_updates = max(1, len(edges) // 100)
        selected_edges = random.sample(edges, num_updates)
        
        for u, v, data in selected_edges:
            # Randomly fluctuate flow
            capacity = data.get('capacity', 1000)
            current = data.get('current_flow', 0)
            
            # Fluctuate by +/- 20% of capacity or random spike
            change = random.uniform(-0.1, 0.2) * capacity
            new_flow = max(0, min(current + change, capacity * 1.5))
            
            network.update_edge_congestion(u, v, new_flow / capacity if capacity > 0 else 1.0)
            network.graph[u][v]['current_flow'] = new_flow

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(traffic_simulator())


routing_engine = RoutingEngine(network)

class GeocodeRequest(BaseModel):
    address: str

from typing import List, Optional, Dict, Union

# ... (imports)

class RouteRequest(BaseModel):
    start_node: Union[str, int]
    end_node: Union[str, int]
    time_hour: int = 8

# ...

class TrafficUpdate(BaseModel):
    u: str
    v: str
    current_flow: float

class TrafficUpdateList(BaseModel):
    updates: List[TrafficUpdate]

@app.get("/")
def read_root():
    return {"status": "System Operational", "message": "Traffic Control AI Backend"}

@app.post("/network/init-grid")
def init_grid(rows: int = 5, cols: int = 5):
    """Re-initializes the network as a grid."""
    network.generate_grid_network(rows, cols)
    return {"message": f"Initialized {rows}x{cols} grid network."}

@app.post("/route")
def compute_route(request: RouteRequest):
    """
    Computes the load-aware optimal route.
    """
    try:
        # Resolve node types (OSM uses int, Grid uses str)
        start = request.start_node
        end = request.end_node
        
        def resolve_id(node_id):
            if node_id in network.graph:
                return node_id
            # Try converting to int if it's a string
            try:
                n_int = int(node_id)
                if n_int in network.graph:
                    return n_int
            except:
                pass
            # Try converting to str if it's an int
            n_str = str(node_id)
            if n_str in network.graph:
                return n_str
            return node_id # Return original if not found (will fail in engine)

        start = resolve_id(start)
        end = resolve_id(end)

        result = routing_engine.find_optimal_route(
            start, 
            end, 
            request.time_hour
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="No path found.")
            
        # Simulate traffic redistribution (optional, can be separate)
        # In a real system, this might happen after the user *confirms* the route.
        # For now, we assume the user takes the route.
        routing_engine.apply_traffic_update(result['path'])
        
        return {
            "path": result['path'],
            "total_cost": result['total_cost'],
            "breakdown": result['breakdown'],
            "segments": result['segments'] # Detailed segment info
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/traffic/update")
def update_traffic(update_list: TrafficUpdateList):
    """
    Updates the current flow on specific edges.
    """
    count = 0
    for update in update_list.updates:
        if network.graph.has_edge(update.u, update.v):
            network.graph[update.u][update.v]['current_flow'] = update.current_flow
            count += 1
    return {"message": f"Updated {count} edge flows."}

@app.get("/network/stats")
def get_network_stats():
    """
    Returns basic stats about the network.
    """
    return {
        "nodes": network.graph.number_of_nodes(),
        "edges": network.graph.number_of_edges(),
        "overloaded_edges": [
            (u, v, data['current_flow'], data['capacity']) 
            for u, v, data in network.graph.edges(data=True) 
            if data['current_flow'] > data['capacity']
        ]
    }

@app.get("/network/layout")
def get_network_layout():
    """
    Returns the graph structure for visualization.
    Nodes differ in position.
    """
    nodes = []
    for node, data in network.graph.nodes(data=True):
        # Default pos if not set
        pos = data.get('pos', (0, 0))
        nodes.append({"id": node, "x": pos[0], "y": pos[1]})
        
    edges = []
    for u, v, data in network.graph.edges(data=True):
        edges.append({
            "source": u, 
            "target": v, 
            "current_flow": data.get('current_flow', 0),
            "capacity": data.get('capacity', 100),
            "congestion": data.get('c', 0)
        })
        
    return {"nodes": nodes, "edges": edges}

@app.post("/geocode")
def geocode_address(request: GeocodeRequest):
    """
    Geocodes an address to a (lat, lon) and finds the nearest graph node.
    """
    try:
        import osmnx as ox
        # returns (lat, lon)
        lat, lon = ox.geocode(request.address)
        
        # Find nearest node in our graph
        node_id = OSMLoader.nearest_node(network.graph, (lat, lon))
        
        return {
            "address": request.address,
            "lat": lat,
            "lon": lon,
            "node_id": node_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Geocoding failed: {str(e)}")


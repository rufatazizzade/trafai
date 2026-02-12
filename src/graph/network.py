
import networkx as nx
import numpy as np
from typing import Dict, Tuple, List, Optional

class RoadNetwork:
    """
    Represents the urban road network as a directed weighted graph.
    Wraps networkx.DiGraph to provide domain-specific functionality.
    """
    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, node_id: str, **attrs):
        """Adds a node (intersection/endpoint) to the graph."""
        self.graph.add_node(node_id, **attrs)

    def add_road_segment(self, 
                         u: str, 
                         v: str, 
                         distance: float, 
                         speed_limit: float,
                         congestion: float = 0.0,
                         historical_load: float = 0.0,
                         accessibility: float = 1.0,
                         social_sensitivity: float = 0.0,
                         emission_coeff: float = 1.0,
                         capacity: float = 100.0,
                         geometry: Optional[List[Tuple[float, float]]] = None) -> None:
        """
        Adds a directed road segment (edge) between nodes u and v.
        """
        # Calculate free-flow travel time (hours)
        free_flow_time = distance / speed_limit if speed_limit > 0 else float('inf')
        
        self.graph.add_edge(u, v,
                            d=distance,
                            v=speed_limit,
                            c=congestion,
                            l=historical_load,
                            a=accessibility,
                            s=social_sensitivity,
                            epsilon=emission_coeff,
                            capacity=capacity,
                            free_flow_time=free_flow_time,
                            current_flow=0.0,
                            geometry=geometry)

    def get_edge_data(self, u: str, v: str) -> Dict:
        """Returns attributes of the edge u->v."""
        return self.graph.get_edge_data(u, v)

    def update_edge_congestion(self, u: str, v: str, congestion: float):
        """Updates the congestion level of a specific edge."""
        if self.graph.has_edge(u, v):
            self.graph[u][v]['c'] = congestion

    def generate_grid_network(self, rows: int, cols: int, distance: float = 1.0):
        """
        Generates a synthetic grid network for testing.
        """
        self.graph.clear()
        
        # Create grid with bidirectional edges
        for r in range(rows):
            for c in range(cols):
                node_id = f"{r},{c}"
                self.add_node(node_id, pos=(c, -r)) # For visualization context if needed
                
                # Connect to right neighbor
                if c < cols - 1:
                    neighbor_id = f"{r},{c+1}"
                    self.add_road_segment(node_id, neighbor_id, distance, speed_limit=50, social_sensitivity=np.random.random())
                    self.add_road_segment(neighbor_id, node_id, distance, speed_limit=50, social_sensitivity=np.random.random())
                
                # Connect to bottom neighbor
                if r < rows - 1:
                    neighbor_id = f"{r+1},{c}"
                    self.add_road_segment(node_id, neighbor_id, distance, speed_limit=50, social_sensitivity=np.random.random())
                    self.add_road_segment(neighbor_id, node_id, distance, speed_limit=50, social_sensitivity=np.random.random())

    def load_from_osm_graph(self, osm_graph: nx.DiGraph):
        """
        Loads the network from an OSMnx graph.
        """
        self.graph = nx.DiGraph()
        # Copy graph-level attributes (including CRS) from OSM graph
        self.graph.graph.update(osm_graph.graph)
        
        # Add nodes
        for node, data in osm_graph.nodes(data=True):
            # OSMnx uses 'y' for lat, 'x' for lon
            # We store pos as (lon, lat) to match frontend expectation (x=lon, y=lat)
            # IMPORTANT: Pass x and y explicitly as attributes or pass **data
            self.add_node(node, pos=(data.get('x'), data.get('y')), **data)

        # Add edges
        for u, v, data in osm_graph.edges(data=True):
            # Extract attributes
            # length is in meters. We might want km.
            distance_km = data.get('length', 100.0) / 1000.0
            
            # Speed limit can be a string, list, or int. Sanitize it.
            maxspeed = data.get('maxspeed', 50)
            if isinstance(maxspeed, list):
                try:
                    maxspeed = float(maxspeed[0])
                except:
                    maxspeed = 50.0
            
            try:
                 speed_limit = float(maxspeed)
            except:
                 speed_limit = 50.0

            # Sanitize lanes
            lanes = data.get('lanes', 1)
            if isinstance(lanes, list):
                try:
                    lanes = float(lanes[0])
                except:
                    lanes = 1.0
            else:
                try:
                    lanes = float(lanes)
                except:
                    lanes = 1.0
            
            capacity = lanes * 1000.0 # Rough capacity estimation

            # Extract Geometry if available
            geometry = None
            if 'geometry' in data:
                # Convert Shapely LineString to list of (lon, lat) tuples
                # Note: valid JSON response usually wants (lat, lon) eventually, 
                # but we store as (x, y) = (lon, lat) for consistency with nodes.
                # However, Google Maps expects (lat, lng). Let's store as is and convert later.
                try:
                    linestring = data['geometry']
                    # mapping: (x, y) -> (lon, lat)
                    geometry = list(linestring.coords)
                except:
                    pass

            # Default attributes
            self.add_road_segment(
                u, v, 
                distance=distance_km,
                speed_limit=speed_limit,
                capacity=capacity,
                geometry=geometry
            )

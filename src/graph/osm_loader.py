
import osmnx as ox
import networkx as nx
from typing import Tuple, Dict

class OSMLoader:
    """
    Handles downloading and processing of OpenStreetMap data.
    """
    @staticmethod
    def load_graph_from_place(place_name: str, network_type: str = 'drive') -> nx.DiGraph:
        """
        Downloads street network from OSM for a given place name.
        """
        print(f"Downloading graph for {place_name}...")
        try:
            # Download graph
            G = ox.graph_from_place(place_name, network_type=network_type)
            # Project to UTM (meters) if needed, but for lat/lon we might keep unprojected
            # However, for distance calculations, project is better.
            # But the frontend expects lat/lon (y, x). 
            # osmnx returns nodes with 'y' (lat) and 'x' (lon).
            
            # Simplified for now: just return the raw MultiDiGraph converted to DiGraph
            G_di = ox.convert.to_digraph(G, weight='length')
            
            return G_di
        except Exception as e:
            print(f"Error downloading graph: {e}")
            raise e

    @staticmethod
    def load_graph_from_address(address: str, dist: int = 1000, network_type: str = 'drive') -> nx.DiGraph:
        """
        Downloads street network from OSM around an address.
        """
        print(f"Downloading graph for {address} with dist={dist}m...")
        try:
            G = ox.graph_from_address(address, dist=dist, network_type=network_type)
            G_di = ox.convert.to_digraph(G, weight='length')
            return G_di
        except Exception as e:
            print(f"Error downloading graph from address: {e}")
            raise e

    @staticmethod
    def nearest_node(G: nx.DiGraph, point: Tuple[float, float]) -> int:
        """
        Finds the nearest node to a (lat, lon) point.
        """
        # ox.nearest_nodes takes (X, Y) i.e. (Lon, Lat)
        # return ox.nearest_nodes(G, point[1], point[0])
        # Note: osmnx 2.0+ might require specific call
        import osmnx.distance
        return osmnx.distance.nearest_nodes(G, X=point[1], Y=point[0])

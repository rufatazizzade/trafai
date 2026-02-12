
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
    def load_graph_from_bbox(north: float, south: float, east: float, west: float, network_type: str = 'drive') -> nx.DiGraph:
        """
        Downloads street network from OSM for a given bounding box.
        Uses local disk cache to avoid repeated downloads.
        """
        import os
        import hashlib
        
        # Create cache directory if not exists
        cache_dir = "cache"
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

        # Create a unique filename for this bbox
        # Round coordinates to 4 decimals to avoid float precision misses (~11m resolution)
        bbox_str = f"{north:.4f}_{south:.4f}_{east:.4f}_{west:.4f}_{network_type}"
        bbox_hash = hashlib.md5(bbox_str.encode()).hexdigest()
        cache_path = os.path.join(cache_dir, f"{bbox_hash}.graphml")

        if os.path.exists(cache_path):
            print(f"Loading graph from cache: {cache_path}")
            try:
                # Load from GraphML
                G = ox.load_graphml(filepath=cache_path)
                return ox.convert.to_digraph(G, weight='length')
            except Exception as e:
                print(f"Failed to load cache, re-downloading: {e}")
        
        print(f"Downloading graph for bbox: N={north}, S={south}, E={east}, W={west}...")
        try:
            # osmnx 2.0+ change: graph_from_bbox(bbox, ...)
            # bbox is a tuple: (north, south, east, west)
            # osmnx 2.0+ settings
            # Import settings directly to identify if they are the same object
            # Force infinite area size to disable splitting
            # Use ox.settings directly to ensure it applies
            ox.settings.max_query_area_size = 10**50 
            
            # Disable rate limit check to avoid "Pausing 60s" on DNS connection errors
            ox.settings.overpass_rate_limit = False
            ox.settings.timeout = 180 # Long timeout for big downloads
            
            # Mirror Rotation Logic
            mirrors = [
                "https://overpass.kumi.systems/api",    # Kumi (Lithuania)
                "https://overpass-api.de/api",          # Main (Germany)
                "https://api.openstreetmap.fr/oapi",    # France
                "https://overpass.nchc.org.tw/api"      # Taiwan
            ]
            
            G = None
            last_exception = None

            print(f"Starting map download. Attempting mirrors (Timeout={ox.settings.timeout}s)...")
            
            # Debug
            print(f"DEBUG: max_query_area_size = {ox.settings.max_query_area_size}")

            # Try mirrors
            for mirror_url in mirrors:
                try:
                    print(f"Trying mirror: {mirror_url} ...")
                    ox.settings.overpass_url = mirror_url
                    
                    # Attempt download
                    G = ox.graph_from_bbox(bbox=(north, south, east, west), network_type=network_type)
                    
                    print(f"Success! Downloaded from {mirror_url}")
                    break # Success, exit loop
                except Exception as e:
                    print(f"Failed to download from {mirror_url}: {e}")
                    last_exception = e
                    continue # Try next mirror

            # FALLBACK: Direct OSM API (non-overpass) if all mirrors fail
            if G is None:
                print("All Overpass mirrors failed. Attempting Direct OSM API Fallback...")
                try:
                    G = OSMLoader._download_from_osm_api(north, south, east, west, network_type)
                    print("Success! Downloaded via Direct OSM API.")
                except Exception as e:
                    print(f"Direct OSM API Fallback failed: {e}")
                    if last_exception:
                        raise last_exception
                    raise e
            
            # Save to disk
            print(f"Saving graph to cache: {cache_path}")
            ox.save_graphml(G, filepath=cache_path)
            
            G_di = ox.convert.to_digraph(G, weight='length')
            return G_di
        except Exception as e:
            print(f"Error downloading graph from bbox: {e}")
            raise e

    @staticmethod
    def _download_from_osm_api(north: float, south: float, east: float, west: float, network_type: str) -> nx.MultiDiGraph:
        """
        Download manually from api.openstreetmap.org/api/0.6/map
        This avoids Overpass entirely but is limited to 50,000 nodes.
        """
        import requests
        import tempfile
        import os
        
        # OSM API requires bbox in (left, bottom, right, top) order i.e. (west, south, east, north)
        url = f"https://api.openstreetmap.org/api/0.6/map?bbox={west},{south},{east},{north}"
        print(f"Requesting: {url}")
        
        resp = requests.get(url, timeout=60)
        if resp.status_code != 200:
            raise Exception(f"OSM API returned {resp.status_code}: {resp.text[:200]}")
        
        # Save to temp file
        fd, tmp_path = tempfile.mkstemp(suffix=".xml")
        try:
            with os.fdopen(fd, 'wb') as tmp:
                tmp.write(resp.content)
            
            print(f"Downloaded XML to {tmp_path}, parsing...")
            # Load graph from XML
            G = ox.graph_from_xml(tmp_path)
            return G
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    @staticmethod
    def nearest_node(G: nx.DiGraph, point: Tuple[float, float]) -> int:
        """
        Finds the nearest node to a (lat, lon) point.
        """
        # ox.nearest_nodes takes (X, Y) i.e. (Lon, Lat)
        # return ox.nearest_nodes(G, point[1], point[0])
        import osmnx.distance
        return osmnx.distance.nearest_nodes(G, X=point[1], Y=point[0])

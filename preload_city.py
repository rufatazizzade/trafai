import osmnx as ox
import sys
import os

# Ensure we can import from src
sys.path.append(os.getcwd())

from src.graph.osm_loader import OSMLoader

def preload_city(place_name: str):
    """
    Downloads the graph for a named place (e.g., "Prague, Czech Republic")
    and saves it to the cache using the bbox format that the engine expects.
    """
    print(f"Resolving geometry for: {place_name}...")
    try:
        # 1. Get the bounding box for the place
        gdf = ox.geocode_to_gdf(place_name)
        bbox = gdf.total_bounds # (minx, miny, maxx, maxy) -> (west, south, east, north)
        west, south, east, north = bbox
        
        print(f"Found BBox: North={north}, South={south}, East={east}, West={west}")
        
        # 2. Trigger the loader
        # This will download, process, and save to cache/hash.graphml
        print("Starting download (this replaces dynamic loading)...")
        OSMLoader.load_graph_from_bbox(north, south, east, west)
        
        print(f"\n[SUCCESS] Map for '{place_name}' has been cached!")
        print("You can now run the routing backend, and it will load this data instantly.")
        
    except Exception as e:
        print(f"\n[ERROR] Failed to preload city: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python preload_city.py \"City, Country\"")
        print("Example: python preload_city.py \"Prague, Czech Republic\"")
        sys.exit(1)
    
    place = sys.argv[1]
    preload_city(place)

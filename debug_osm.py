
import sys
import os
sys.path.append(os.getcwd())
try:
    from src.graph.osm_loader import OSMLoader
    import osmnx as ox
    print("Attempting to load graph from address...")
    # G = OSMLoader.load_graph_from_place("Wall Street, New York, USA") 
    # Let's try direct osmnx call to see if it works
    G = ox.graph_from_address("Wall Street, New York, USA", dist=2000, network_type='drive')
    print(f"Success! Nodes: {len(G.nodes)}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

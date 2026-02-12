import networkx as nx
from typing import List, Dict, Tuple
from src.graph.network import RoadNetwork
from src.models.cost import CostModel

class RoutingEngine:
    """
    Handles route computation and traffic redistribution.
    """
    def __init__(self, network: RoadNetwork):
        self.network = network
        
    def _dynamic_weight_function(self, u: str, v: str, edge_attr: Dict) -> float:
        """
        Internal wrapper to calculate edge weight for NetworkX algorithms.
        """
        # We assume a default time of day (e.g., 8 AM) for now, 
        # but this could be passed via a context or globally set.
        current_time_hour = 8 
        cost, _ = CostModel.calculate_segment_cost(edge_attr, current_time_hour)
        return cost

    def find_optimal_route(self, start_node: str, end_node: str, current_time_hour: int = 8) -> Dict:
        """
        Computes the optimal route minimizing the multi-objective cost function J.
        """
        if start_node not in self.network.graph or end_node not in self.network.graph:
            raise ValueError(f"Start ({start_node}) or End ({end_node}) node not found in network.")

        # Define weight function with captured time
        def weight_fn(u, v, d):
            cost, _ = CostModel.calculate_segment_cost(d, current_time_hour)
            return cost
            
        try:
            path = nx.dijkstra_path(self.network.graph, start_node, end_node, weight=weight_fn)
            
            # Calculate total costs and breakdown for explainability
            total_j = 0.0
            components_sum = {
                'time_cost': 0.0,
                'congestion_penalty': 0.0,
                'emission_cost': 0.0,
                'social_cost': 0.0,
                'travel_time_hours': 0.0
            }
            
            path_details = []
            
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                edge_attr = self.network.graph[u][v]
                cost, comps = CostModel.calculate_segment_cost(edge_attr, current_time_hour)
                
                total_j += cost
                for k in components_sum:
                    if k == 'travel_time_hours':
                        components_sum[k] += comps['travel_time']
                    else:
                        components_sum[k] += comps[k]
                        
                path_details.append({
                    'u': u, 'v': v, 
                    'cost': cost, 
                    'components': comps
                })

            # Construct full geometry
            full_geometry = []
            # Add start node
            if path:
                start_node_data = self.network.graph.nodes[path[0]]
                # Network stores (x, y) = (lon, lat)
                full_geometry.append({'lat': start_node_data['y'], 'lng': start_node_data['x']})

            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                edge_data = self.network.graph[u][v]
                if 'geometry' in edge_data and edge_data['geometry']:
                    # OSMnx geometry is usually (lon, lat) tuples
                    for lon, lat in edge_data['geometry']:
                         full_geometry.append({'lat': lat, 'lng': lon})
                else:
                    # Fallback to end node if no geometry
                    end_node_data = self.network.graph.nodes[v]
                    full_geometry.append({'lat': end_node_data['y'], 'lng': end_node_data['x']})
                
            return {
                'path': path,
                'total_cost': total_j,
                'breakdown': components_sum,
                'segments': path_details,
                'geometry': full_geometry
            }
            
        except nx.NetworkXNoPath:
            return None

    def apply_traffic_update(self, route: List[str]):
        """
        Redistributes traffic by incrementing flow on the chosen route.
        Simple simulation of traffic flow increase.
        """
        for i in range(len(route) - 1):
            u, v = route[i], route[i+1]
            if self.network.graph.has_edge(u, v):
                # We assume each route adds 1 unit of flow (e.g., 1 car)
                self.network.graph[u][v]['current_flow'] += 1.0

    def calculate_marginal_costs(self, route_result: Dict) -> Dict:
        """
        Extracts marginal contributions for explainability.
        Compares against a theoretical 'free flow' cost or similar baseline if needed.
        For now, returns the breakdown directly.
        """
        return route_result['breakdown']

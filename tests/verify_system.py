import sys
import os
import unittest
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.graph.network import RoadNetwork
from src.models.cost import CostModel
from src.routing.engine import RoutingEngine

class TestTrafficSystem(unittest.TestCase):
    
    def setUp(self):
        self.network = RoadNetwork()
        self.engine = RoutingEngine(self.network)
        
    def test_cost_function_behavior(self):
        """Verify cost increases with congestion."""
        edge_attrs = {'d': 10, 'v': 50, 'capacity': 100, 'current_flow': 0}
        cost_empty, _ = CostModel.calculate_segment_cost(edge_attrs)
        
        edge_attrs['current_flow'] = 120 # Overloaded
        cost_full, _ = CostModel.calculate_segment_cost(edge_attrs)
        
        print(f"Empty Cost: {cost_empty}, Overloaded Cost: {cost_full}")
        self.assertTrue(cost_full > cost_empty * 2, "Cost should increase significantly with overload")

    def test_routing_avoidance(self):
        """
        Create two paths:
        A: Short but congested
        B: Long but free
        System should choose B.
        """
        self.network.add_node("start")
        self.network.add_node("end")
        self.network.add_node("mid_A")
        self.network.add_node("mid_B")
        
        # Path A: Short (total 2km)
        self.network.add_road_segment("start", "mid_A", distance=1.0, speed_limit=50, capacity=10)
        self.network.add_road_segment("mid_A", "end", distance=1.0, speed_limit=50, capacity=10)
        
        # Path B: Long (total 10km)
        self.network.add_road_segment("start", "mid_B", distance=5.0, speed_limit=50, capacity=100)
        self.network.add_road_segment("mid_B", "end", distance=5.0, speed_limit=50, capacity=100)
        
        # Congest Path A
        self.network.update_edge_congestion("start", "mid_A", 1.5) # Forced congestion
        self.network.graph["start"]["mid_A"]['current_flow'] = 20 # 200% load
        
        route = self.engine.find_optimal_route("start", "end")
        path = route['path']
        print(f"Route chosen under congestion: {path}")
        
        self.assertIn("mid_B", path, "Router should choose longer path B to avoid severe congestion on A")

    def test_traffic_redistribution(self):
        """
        Verify that repeated routing increases flow.
        """
        self.network.generate_grid_network(rows=3, cols=3)
        start, end = "0,0", "2,2"
        
        initial_flow = self.network.get_edge_data("0,0", "0,1")['current_flow']
        
        route = self.engine.find_optimal_route(start, end)
        self.engine.apply_traffic_update(route['path'])
        
        new_flow = self.network.get_edge_data("0,0", "0,1")['current_flow']
        
        # Only if 0,0 -> 0,1 was part of the path (likely in a small grid)
        if "0,1" in route['path']:
             self.assertTrue(new_flow > initial_flow, "Traffic flow should increase after routing")

if __name__ == '__main__':
    unittest.main()

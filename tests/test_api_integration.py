
import sys
import os
import unittest
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from src.api.server import app

client = TestClient(app)

class TestApiIntegration(unittest.TestCase):
    
    def setUp(self):
        # Reset grid before each test
        client.post("/network/init-grid?rows=3&cols=3")

    def test_health_check(self):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())

    def test_routing_endpoint(self):
        """Verify /route returns a valid path."""
        payload = {
            "start_node": "0,0",
            "end_node": "2,2",
            "time_hour": 8
        }
        response = client.post("/route", json=payload)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("path", data)
        self.assertTrue(len(data["path"]) > 0)
        self.assertIn("total_cost", data)
        self.assertIn("breakdown", data)

    def test_traffic_update_endpoint(self):
        """Verify /traffic/update changes flow."""
        # 1. Update flow on edge 0,0 -> 0,1
        update_payload = {
            "updates": [
                {"u": "0,0", "v": "0,1", "current_flow": 50.0}
            ]
        }
        response = client.post("/traffic/update", json=update_payload)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Updated 1 edge flows", response.json()['message'])
        
        # 2. Check stats to confirm overloaded edge
        stats_response = client.get("/network/stats")
        self.assertEqual(stats_response.status_code, 200)
        stats = stats_response.json()
        
        # Verify edge (0,0 -> 0,1) is overloaded if capacity < 50
        # Default capacity is 100, so let's update with 150
        client.post("/traffic/update", json={
            "updates": [{"u": "0,0", "v": "0,1", "current_flow": 150.0}]
        })
        
        stats_response_2 = client.get("/network/stats")
        overloaded = stats_response_2.json().get("overloaded_edges", [])
        self.assertTrue(len(overloaded) > 0, "Should detect overloaded edge")

if __name__ == '__main__':
    unittest.main()

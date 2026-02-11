import math
from typing import Dict, Tuple

class CostModel:
    """
    Implements the physics and cost functions for the routing engine.
    """
    
    @staticmethod
    def calculate_load(current_flow: float, capacity: float) -> float:
        """
        Calculates the load factor L_e(t) = f_e(t) / C_e.
        """
        if capacity <= 0:
            return float('inf')
        return current_flow / capacity

    @staticmethod
    def get_time_dependent_weights(hour: int) -> Dict[str, float]:
        """
        Returns weights alpha, beta, gamma, delta based on time of day.
        Peak hours: 7-9 AM, 5-7 PM.
        """
        # Default weights
        weights = {
            'alpha': 1.0,  # Travel Time
            'beta': 1.0,   # Congestion
            'gamma': 0.5,  # Emission
            'delta': 0.5   # Social
        }
        
        # Peak hours adjustments
        if (7 <= hour <= 9) or (17 <= hour <= 19):
            weights['alpha'] = 1.5  # Prioritize time more
            weights['beta'] = 2.0   # Heavily penalize congestion
            
        return weights

    @staticmethod
    def calculate_segment_cost(edge_attrs: Dict, current_time_hour: int = 8) -> Tuple[float, Dict[str, float]]:
        """
        Computes the composite cost J_e and its components.
        
        Returns:
            Total cost J_e, and a dictionary of individual cost components for explainability.
        """
        weights = CostModel.get_time_dependent_weights(current_time_hour)
        
        # 1. Travel Time Cost (T_e)
        # Using simple BPR (Bureau of Public Roads) function for travel time increase with congestion
        # T = T_free * (1 + 0.15 * (flow/capacity)^4)
        distance = edge_attrs.get('d', 1.0)
        speed_limit = edge_attrs.get('v', 50.0)
        capacity = edge_attrs.get('capacity', 100.0)
        current_flow = edge_attrs.get('current_flow', 0.0)
        
        free_flow_time = distance / speed_limit if speed_limit > 0 else float('inf')
        load = CostModel.calculate_load(current_flow, capacity)
        
        # BPR-like congestion term applied to time
        congestion_factor = 1 + 0.15 * (load ** 4)
        travel_time = free_flow_time * congestion_factor
        
        cost_T = weights['alpha'] * travel_time
        
        # 2. Congestion Penalty (L_e)
        # Explicit penalty for overload beyond BPR
        penalty_L = 0.0
        if load > 1.0:
            # Exponential penalty for overloading
            penalty_L = weights['beta'] * (math.exp(load - 1.0) - 1.0) * 10 
        else:
            penalty_L = weights['beta'] * load
            
        # 3. Emission Cost (E_e)
        # E ~ distance * emission_coeff * (1 + congestion)
        emission_coeff = edge_attrs.get('epsilon', 1.0)
        raw_emission = distance * emission_coeff * (1 + 0.5 * load) # More emissions in traffic
        cost_E = weights['gamma'] * raw_emission
        
        # 4. Social Sensitivity Cost (S_e)
        social_weight = edge_attrs.get('s', 0.0)
        cost_S = weights['delta'] * social_weight * distance # Proportional to distance in sensitive area
        
        total_cost = cost_T + penalty_L + cost_E + cost_S
        
        components = {
            'time_cost': cost_T,
            'congestion_penalty': penalty_L,
            'emission_cost': cost_E,
            'social_cost': cost_S,
            'travel_time': travel_time, # Physical value
            'load': load # Physical value
        }
        
        return total_cost, components

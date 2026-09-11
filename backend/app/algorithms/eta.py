"""
ETA Calculation Engine (Phase 1 Baseline & Formula Preview)

Responsibilities:
- Haversine distance computation between resource GPS coordinates and zone epicenter.
- Speed-adjusted travel time modeling with terrain/flood penalty.
"""

import math

def calculate_haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in kilometers between two points on earth.
    """
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def estimate_eta_minutes(distance_km: float, speed_kmh: float = 35.0, delay_penalty_min: int = 0) -> int:
    """
    Estimate travel time in minutes with optional obstruction penalty.
    """
    if speed_kmh <= 0:
        speed_kmh = 30.0
    travel_time_hours = distance_km / speed_kmh
    travel_time_minutes = int(travel_time_hours * 60)
    return max(3, travel_time_minutes + delay_penalty_min)

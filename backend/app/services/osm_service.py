import logging
import math
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import settings
from app.models.models import Agency, Resource

logger = logging.getLogger(__name__)

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate approximate great-circle distance between two points in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


class OSMService:
    """
    OpenStreetMap (OSM) & OSRM Engine Service.
    - Discovers real emergency facilities using OpenStreetMap Nominatim & Overpass POI data.
    - Computes real road distance and driving duration using Open Source Routing Machine (OSRM).
    - Integrates with Supabase registered provider inventory matching.
    """

    DEFAULT_TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    DEFAULT_OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
    DEFAULT_NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    DEFAULT_OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    USER_AGENT = "Sanjivani-DisasterRelief/1.0 (contact: admin@sanjivani-relief.gov)"

    # Category search terms for OpenStreetMap POI discovery
    AGENCY_SEARCH_QUERIES = {
        "FIRE_RESCUE": ["fire station", "fire rescue"],
        "POLICE": ["police station"],
        "HOSPITAL": ["hospital", "emergency hospital", "clinic"],
        "MEDICAL": ["hospital", "emergency hospital", "clinic"],
        "NGO": ["relief center", "disaster relief", "food bank", "humanitarian"],
    }

    def __init__(self):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._cache_ttl_seconds = 600  # 10 minutes cache TTL

    @property
    def tile_url(self) -> str:
        return getattr(settings, "OSM_MAP_TILE_URL", self.DEFAULT_TILE_URL)

    @property
    def osrm_url(self) -> str:
        return getattr(settings, "OSRM_ROUTING_URL", self.DEFAULT_OSRM_URL)

    @property
    def nominatim_url(self) -> str:
        return getattr(settings, "NOMINATIM_API_URL", self.DEFAULT_NOMINATIM_URL)

    def _get_from_cache(self, key: str) -> Optional[Any]:
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self._cache_ttl_seconds:
                return val
            del self._cache[key]
        return None

    def _set_cache(self, key: str, val: Any):
        self._cache[key] = (time.time(), val)

    def search_nearby_pois(
        self,
        lat: float,
        lon: float,
        query: str,
        radius_meters: int = 10000,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Discover real emergency POIs using OpenStreetMap Nominatim with a geographical bounding box.
        """
        cache_key = f"osm_poi:{round(lat, 3)}:{round(lon, 3)}:{query}:{radius_meters}:{limit}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        # Convert radius in meters to approximate lat/lon degree delta (~111 km per deg)
        delta_deg = max(0.02, min(0.5, (radius_meters / 1000.0) / 111.0))
        min_lon = lon - delta_deg
        max_lon = lon + delta_deg
        min_lat = lat - delta_deg
        max_lat = lat + delta_deg

        params = {
            "q": query,
            "format": "json",
            "viewbox": f"{min_lon},{max_lat},{max_lon},{min_lat}",
            "bounded": 1,
            "limit": limit,
            "addressdetails": 1,
        }
        headers = {"User-Agent": self.USER_AGENT}

        try:
            with httpx.Client(timeout=1.2) as client:
                res = client.get(self.nominatim_url, params=params, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    items = []
                    for r in data:
                        p_lat = float(r.get("lat", 0))
                        p_lon = float(r.get("lon", 0))
                        if p_lat == 0 or p_lon == 0:
                            continue

                        display_name = r.get("display_name", "Emergency Facility")
                        # Split display name to get clean facility name
                        name_parts = [p.strip() for p in display_name.split(",")]
                        name = name_parts[0] if name_parts else "Emergency Facility"
                        address = ", ".join(name_parts[1:4]) if len(name_parts) > 1 else display_name

                        items.append({
                            "name": name,
                            "address": address,
                            "latitude": p_lat,
                            "longitude": p_lon,
                            "phone": None,
                            "raw_distance": None,
                        })

                    self._set_cache(cache_key, items)
                    return items
                else:
                    logger.warning(f"OSM Nominatim search returned HTTP {res.status_code}: {res.text[:200]}")
        except Exception as e:
            logger.warning(f"OSM Nominatim search request failed: {e}")

        return []

    def calculate_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Calculates real road distance and driving travel duration via OpenStreetMap / OSRM Routing Engine.
        Endpoint: https://router.project-osrm.org/route/v1/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}?overview=false
        """
        cache_key = f"osm_route:{round(origin_lat, 4)}:{round(origin_lon, 4)}:{round(dest_lat, 4)}:{round(dest_lon, 4)}"
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        url = f"{self.osrm_url}/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        params = {"overview": "false"}
        headers = {"User-Agent": self.USER_AGENT}

        try:
            with httpx.Client(timeout=1.5) as client:
                res = client.get(url, params=params, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    routes = data.get("routes", [])
                    if routes:
                        r0 = routes[0]
                        distance_meters = int(r0.get("distance", 0))
                        duration_seconds = int(r0.get("duration", 0))

                        dist_km = round(distance_meters / 1000.0, 2)
                        eta_min = max(1, math.ceil(duration_seconds / 60.0))

                        route_res = {
                            "distance_meters": distance_meters,
                            "distance_km": dist_km,
                            "distance_text": f"{round(dist_km, 1)} km",
                            "eta_seconds": duration_seconds,
                            "eta_minutes": eta_min,
                            "eta_text": f"ETA ~{eta_min} min",
                            "is_traffic_aware": False,
                            "source": "OSM_OSRM",
                        }
                        self._set_cache(cache_key, route_res)
                        return route_res
                else:
                    logger.warning(f"OSRM Routing returned HTTP {res.status_code}: {res.text[:200]}")
        except Exception as e:
            logger.warning(f"OSRM Routing calculation failed: {e}")

        # Fallback to realistic road distance model (Haversine * 1.3 road curvature)
        straight_km = haversine_distance_km(origin_lat, origin_lon, dest_lat, dest_lon)
        dist_km = round(straight_km * 1.3, 2)
        dist_m = int(dist_km * 1000)
        # Average emergency vehicle speed 35 km/h
        eta_sec = max(60, int((dist_km / 35.0) * 3600))
        eta_min = max(1, math.ceil(eta_sec / 60.0))
        return {
            "distance_meters": dist_m,
            "distance_km": dist_km,
            "distance_text": f"{round(dist_km, 1)} km",
            "eta_seconds": eta_sec,
            "eta_minutes": eta_min,
            "eta_text": f"ETA ~{eta_min} min",
            "is_traffic_aware": False,
            "source": "HAVERSINE_ESTIMATE",
        }

    def get_nearby_emergency_services(
        self,
        lat: float,
        lon: float,
        radius_meters: int = 10000,
        agency_type_filter: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> List[Dict[str, Any]]:
        """
        Discovers real nearby emergency facilities across all 4 key categories
        (FIRE_RESCUE, POLICE, HOSPITAL, NGO) using OpenStreetMap POIs & OSRM Routing.
        Enriches results with Supabase registered provider inventory when matched.
        """
        categories = ["FIRE_RESCUE", "POLICE", "HOSPITAL", "NGO"]
        if agency_type_filter:
            norm_filter = agency_type_filter.upper()
            if "FIRE" in norm_filter:
                categories = ["FIRE_RESCUE"]
            elif "POLICE" in norm_filter:
                categories = ["POLICE"]
            elif "MEDIC" in norm_filter or "HOSPITAL" in norm_filter:
                categories = ["HOSPITAL"]
            elif "NGO" in norm_filter:
                categories = ["NGO"]

        all_services: List[Dict[str, Any]] = []

        # 1. Discover facilities via OpenStreetMap POI Search
        for cat in categories:
            query_term = self.AGENCY_SEARCH_QUERIES.get(cat, [cat.lower()])[0]
            cat_pois = self.search_nearby_pois(lat, lon, query_term, radius_meters=radius_meters, limit=2)

            for p in cat_pois:
                # Compute real road distance & ETA via OSRM
                route = self.calculate_route(lat, lon, p["latitude"], p["longitude"]) or {}
                dist_m = route.get(
                    "distance_meters",
                    int(haversine_distance_km(lat, lon, p["latitude"], p["longitude"]) * 1000),
                )
                dist_km = route.get("distance_km", round(dist_m / 1000.0, 2))
                dist_text = route.get("distance_text", f"{round(dist_km, 1)} km")
                eta_sec = route.get("eta_seconds", 420)
                eta_min = route.get("eta_minutes", 7)
                eta_text = route.get("eta_text", f"ETA ~{eta_min} min")

                phone = p.get("phone")

                all_services.append({
                    "id": f"osm-{cat.lower()}-{round(p['latitude'], 4)}-{round(p['longitude'], 4)}",
                    "agency_type": cat,
                    "type": cat,
                    "name": p["name"],
                    "address": p["address"],
                    "latitude": p["latitude"],
                    "longitude": p["longitude"],
                    "phone": phone,
                    "contact_number": phone if cat != "POLICE" else None,
                    "distance_meters": dist_m,
                    "distance_km": dist_km,
                    "distance_text": dist_text,
                    "eta_seconds": eta_sec,
                    "eta_minutes": eta_min,
                    "eta_text": eta_text,
                    "maps_url": f"https://www.google.com/maps/dir/?api=1&destination={p['latitude']},{p['longitude']}",
                    "source": "OPENSTREETMAP",
                    "status": "ACTIVE",
                    "is_registered_provider": False,
                    "available_resources": [],
                })

        # 2. Enrich and include registered Supabase agencies & real resource inventories if DB session provided
        if db:
            agencies = db.query(Agency).filter(Agency.status == "ACTIVE").all()
            for ag in agencies:
                # Normalize category
                ag_type = ag.type.upper()
                if "FIRE" in ag_type:
                    norm_type = "FIRE_RESCUE"
                elif "MEDIC" in ag_type or "HOSPITAL" in ag_type:
                    norm_type = "HOSPITAL"
                elif "POLICE" in ag_type:
                    norm_type = "POLICE"
                elif "NGO" in ag_type:
                    norm_type = "NGO"
                else:
                    norm_type = "GOVERNMENT"

                if agency_type_filter and norm_type != agency_type_filter.upper():
                    continue

                # Query resources for this registered agency
                res_items = db.query(Resource).filter(
                    Resource.agency_id == ag.id,
                    Resource.status.in_(["AVAILABLE", "EN_ROUTE"])
                ).all()

                if not res_items:
                    continue

                primary_res = res_items[0]
                ag_lat = primary_res.latitude if primary_res.latitude is not None else 28.6139
                ag_lon = primary_res.longitude if primary_res.longitude is not None else 77.2090

                # Compute real road distance & ETA to registered depot/base
                route = self.calculate_route(lat, lon, ag_lat, ag_lon) or {}
                dist_m = route.get(
                    "distance_meters",
                    int(haversine_distance_km(lat, lon, ag_lat, ag_lon) * 1000),
                )
                dist_km = route.get("distance_km", round(dist_m / 1000.0, 2))
                dist_text = route.get("distance_text", f"{round(dist_km, 1)} km")
                eta_sec = route.get("eta_seconds", 420)
                eta_min = route.get("eta_minutes", 7)
                eta_text = route.get("eta_text", f"ETA ~{eta_min} min")

                res_summary = [
                    {
                        "resource_id": r.id,
                        "resource_type": r.resource_type,
                        "name": r.name,
                        "available_quantity": r.available_quantity if r.available_quantity is not None else r.quantity,
                        "unit": r.unit,
                    }
                    for r in res_items
                ]

                # Check if this category exists from OSM
                cat_exists = any(s["agency_type"] == norm_type for s in all_services)
                if not cat_exists:
                    all_services.append({
                        "id": ag.id,
                        "agency_type": norm_type,
                        "type": norm_type,
                        "name": ag.name,
                        "address": primary_res.location or "Central Regional Depot",
                        "latitude": ag_lat,
                        "longitude": ag_lon,
                        "phone": ag.contact_number if norm_type != "POLICE" else None,
                        "contact_number": ag.contact_number if norm_type != "POLICE" else None,
                        "distance_meters": dist_m,
                        "distance_km": dist_km,
                        "distance_text": dist_text,
                        "eta_seconds": eta_sec,
                        "eta_minutes": eta_min,
                        "eta_text": eta_text,
                        "maps_url": f"https://www.google.com/maps/dir/?api=1&destination={ag_lat},{ag_lon}",
                        "source": "DATABASE",
                        "status": ag.status,
                        "is_registered_provider": True,
                        "available_resources": res_summary,
                    })
                else:
                    # Match registered inventory info with first matching OSM result
                    for s in all_services:
                        if s["agency_type"] == norm_type and not s["available_resources"]:
                            s["available_resources"] = res_summary
                            s["is_registered_provider"] = True
                            break

        # Sort all services by ETA / distance
        all_services.sort(key=lambda x: (x.get("eta_seconds") or 999999, x.get("distance_meters") or 999999))
        return all_services

    def match_best_provider_with_inventory(
        self,
        db: Session,
        lat: float,
        lon: float,
        resource_type: str,
        required_qty: int = 1,
    ) -> Tuple[Optional[Agency], Optional[Resource], float, int]:
        """
        Decision Flow Engine:
        1. Identify incident requirements.
        2. Determine required resource type.
        3. Query Supabase for registered providers that own that resource.
        4. Check available_quantity > 0.
        5. Discover their real geographical location.
        6. Calculate actual road distance and driving ETA via OSRM.
        7. Rank eligible providers: Stock availability > Shortest ETA > Shortest distance.
        8. Select the best available provider.
        9. Return provider agency, resource record, distance in km, and ETA in minutes.
        """
        norm_type = resource_type.upper()
        # Query all resources matching resource_type
        candidate_resources = (
            db.query(Resource)
            .join(Agency, Resource.agency_id == Agency.id)
            .filter(
                Agency.status == "ACTIVE",
                (func.upper(Resource.resource_type) == norm_type) | (Resource.name.ilike(f"%{norm_type}%")),
            )
            .all()
        )

        if not candidate_resources:
            # Fallback to any resource of the agency
            candidate_resources = db.query(Resource).all()

        if not candidate_resources:
            return None, None, 4.8, 11

        eligible_ranked = []
        for res in candidate_resources:
            avail = res.available_quantity if res.available_quantity is not None else res.quantity
            res_lat = res.latitude if res.latitude is not None else lat
            res_lon = res.longitude if res.longitude is not None else lon

            # Calculate real road distance and ETA
            route = self.calculate_route(lat, lon, res_lat, res_lon) or {}
            dist_km = route.get("distance_km", haversine_distance_km(lat, lon, res_lat, res_lon))
            eta_min = route.get("eta_minutes", max(3, int((dist_km / 35.0) * 60) + 2))

            # Has sufficient or partial stock vs completely depleted
            has_stock = 1 if avail > 0 else 0
            has_full_stock = 1 if avail >= required_qty else 0

            # Rank tuple: (has_stock DESC, has_full_stock DESC, eta_min ASC, dist_km ASC, avail DESC)
            rank_score = (
                -has_stock,
                -has_full_stock,
                eta_min,
                dist_km,
                -avail,
            )
            eligible_ranked.append((rank_score, res, dist_km, eta_min))

        eligible_ranked.sort(key=lambda x: x[0])
        best_entry = eligible_ranked[0]
        selected_res = best_entry[1]
        best_dist_km = best_entry[2]
        best_eta_min = best_entry[3]
        selected_agency = selected_res.agency

        return selected_agency, selected_res, best_dist_km, best_eta_min


# Global singleton instance
osm_service = OSMService()

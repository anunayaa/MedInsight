"""
Facility Recommender — Recommends nearby hospitals, clinics, or gyms/wellness centres
based on patient lab results and location.
"""

import os
import math
import logging
import requests
from typing import Dict, List, Any, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Overpass API mirrors for query reliability and fallback
OVERPASS_MIRRORS = [
    "https://overpass.osm.ch/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter"
]
# Nominatim API endpoint for geocoding
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Target tests for gyms/fitness (metabolic/lifestyle flags)
METABOLIC_TESTS = {
    "glucose",
    "fasting glucose",
    "postprandial glucose",
    "hba1c",
    "ldl",
    "triglycerides",
    "total cholesterol",
}


def geolocate_by_ip() -> Optional[Dict[str, Any]]:
    """
    Attempt to geolocate the server's public IP address using ipapi.co.
    Returns a dict with status, latitude, longitude, city, country, or None on failure.
    Note: This reflects the server's IP (or the user's if running locally).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    endpoints = [
        "https://ipapi.co/json/",
        "https://ip-api.com/json/?fields=status,lat,lon,city,country,zip",
    ]
    for url in endpoints:
        try:
            response = requests.get(url, headers=headers, timeout=8)
            if response.status_code == 200:
                data = response.json()
                # ipapi.co format
                if "latitude" in data and "longitude" in data:
                    if data.get("error"):
                        continue
                    return {
                        "status": "success",
                        "source": "ip",
                        "latitude": float(data["latitude"]),
                        "longitude": float(data["longitude"]),
                        "city": data.get("city", "Unknown City"),
                        "country": data.get("country_name", ""),
                        "zip": data.get("postal", ""),
                    }
                # ip-api.com format
                elif data.get("status") == "success" and "lat" in data:
                    return {
                        "status": "success",
                        "source": "ip",
                        "latitude": float(data["lat"]),
                        "longitude": float(data["lon"]),
                        "city": data.get("city", "Unknown City"),
                        "country": data.get("country", ""),
                        "zip": data.get("zip", ""),
                    }
        except Exception as e:
            logger.warning(f"IP geolocation via {url} failed: {e}")
    return None


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on the Earth in kilometers."""
    R = 6371.0  # Earth radius in kilometers

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 2)


def geocode_address(query: str) -> Optional[Tuple[float, float, str]]:
    """
    Geocode a city name or postal code using OpenStreetMap Nominatim.
    Returns (lat, lon, display_name) or None if not found.
    """
    if not query or not query.strip():
        return None
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    params = {
        "q": query.strip(),
        "format": "json",
        "limit": 1
    }
    try:
        response = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                display_name = data[0]["display_name"]
                return lat, lon, display_name
    except Exception as e:
        logger.error(f"Geocoding failed for '{query}': {e}")
    
    return None


class FacilityRecommender:
    """Handles logic for detecting recommendations needs and querying nearby services."""

    @staticmethod
    def check_recommendations_needed(comparison_results: Dict[str, Any]) -> Tuple[bool, bool]:
        """
        Analyze lab results to decide if hospitals/clinics and/or gyms are recommended.
        
        Returns:
            (recommend_hospitals, recommend_gyms)
        """
        recommend_hospitals = False
        recommend_gyms = False

        results = comparison_results.get("results", [])
        for r in results:
            name_lower = r.get("name", "").lower()
            status = r.get("status", "")

            # Hospital/clinic: any CRITICAL LOW, CRITICAL HIGH, or HIGH
            if status in ("CRITICAL LOW", "CRITICAL HIGH", "HIGH"):
                recommend_hospitals = True

            # Gym/fitness: metabolic test that is HIGH or CRITICAL HIGH
            if name_lower in METABOLIC_TESTS and status in ("HIGH", "CRITICAL HIGH"):
                recommend_gyms = True

        return recommend_hospitals, recommend_gyms

    def search_nearby(
        self, lat: float, lon: float, radius_km: float = 5.0, search_hospitals: bool = True, search_gyms: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Query nearby hospitals/clinics and/or gyms.
        Checks for GOOGLE_PLACES_API_KEY env variable first; falls back to Overpass API.
        """
        google_key = os.getenv("GOOGLE_PLACES_API_KEY")
        
        hospitals = []
        gyms = []
        
        logger.info(f"Starting facility search at ({lat}, {lon}), radius={radius_km}km, search_hospitals={search_hospitals}, search_gyms={search_gyms}")

        if google_key:
            logger.info("Using Google Places API for nearby search.")
            if search_hospitals:
                hospitals = self._search_google_places(lat, lon, radius_km, "hospital", google_key)
                logger.info(f"Google Places hospital search returned {len(hospitals)} results")
                # Fallback to clinic / doctor if hospitals are few
                if len(hospitals) < 3:
                    clinics = self._search_google_places(lat, lon, radius_km, "doctor", google_key)
                    logger.info(f"Google Places clinic/doctor search returned {len(clinics)} results")
                    hospitals.extend(clinics)
                    # Deduplicate by name + address
                    seen = set()
                    deduped = []
                    for h in hospitals:
                        key = (h["name"].lower(), h["address"].lower())
                        if key not in seen:
                            seen.add(key)
                            deduped.append(h)
                    hospitals = deduped
            
            if search_gyms:
                gyms = self._search_google_places(lat, lon, radius_km, "gym", google_key)
                logger.info(f"Google Places gym search returned {len(gyms)} results")
        else:
            logger.info("Using OpenStreetMap Overpass API for nearby search.")
            if search_hospitals:
                hospitals = self._search_overpass(lat, lon, radius_km, "hospital")
                logger.info(f"Overpass hospital search returned {len(hospitals)} results")
            if search_gyms:
                gyms = self._search_overpass(lat, lon, radius_km, "gym")
                logger.info(f"Overpass gym search returned {len(gyms)} results")

        # Sort by distance and limit to top 5
        hospitals = sorted(hospitals, key=lambda x: x["distance_km"])[:5]
        gyms = sorted(gyms, key=lambda x: x["distance_km"])[:5]
        
        logger.info(f"Final results: {len(hospitals)} hospitals, {len(gyms)} gyms")

        return {
            "hospitals": hospitals,
            "gyms": gyms
        }

    def _search_google_places(
        self, lat: float, lon: float, radius_km: float, place_type: str, api_key: str
    ) -> List[Dict[str, Any]]:
        """Search nearby places using Google Places API."""
        url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
        radius_meters = int(radius_km * 1000)
        params = {
            "location": f"{lat},{lon}",
            "radius": radius_meters,
            "type": place_type,
            "key": api_key
        }
        
        results = []
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("results", []):
                    item_lat = item["geometry"]["location"]["lat"]
                    item_lon = item["geometry"]["location"]["lng"]
                    dist = haversine(lat, lon, item_lat, item_lon)
                    
                    results.append({
                        "name": item.get("name", "Unknown Facility"),
                        "address": item.get("vicinity", "Address not specified"),
                        "distance_km": dist,
                        "rating": item.get("rating"),
                        "phone": "N/A",  # Google requires Place Details API call for phone number
                        "lat": item_lat,
                        "lon": item_lon,
                        "directions_url": f"https://www.google.com/maps/dir/?api=1&destination={item_lat},{item_lon}"
                    })
        except Exception as e:
            logger.error(f"Google Places search failed for type '{place_type}': {e}")
            
        return results

    def _search_overpass(self, lat: float, lon: float, radius_km: float, facility_type: str) -> List[Dict[str, Any]]:
        """Search nearby places using OSM Overpass API mirrors with waterfall fallback."""
        radius_meters = int(radius_km * 1000)
        
        if facility_type == "hospital":
            # Search for hospital, clinic, doctors
            amenity_filter = 'node["amenity"~"hospital|clinic|doctors"](around:{radius},{lat},{lon}); way["amenity"~"hospital|clinic|doctors"](around:{radius},{lat},{lon}); relation["amenity"~"hospital|clinic|doctors"](around:{radius},{lat},{lon});'
        else:
            # Search for fitness centre or gym
            amenity_filter = 'node["leisure"="fitness_centre"](around:{radius},{lat},{lon}); way["leisure"="fitness_centre"](around:{radius},{lat},{lon}); relation["leisure"="fitness_centre"](around:{radius},{lat},{lon}); node["amenity"="gym"](around:{radius},{lat},{lon}); way["amenity"="gym"](around:{radius},{lat},{lon}); relation["amenity"="gym"](around:{radius},{lat},{lon});'
            
        query = f"""
        [out:json][timeout:25];
        (
          {amenity_filter.format(radius=radius_meters, lat=lat, lon=lon)}
        );
        out center;
        """
        
        results = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        
        logger.info(f"Starting Overpass search for {facility_type} at ({lat}, {lon}), radius {radius_meters}m")
        
        for url in OVERPASS_MIRRORS:
            try:
                logger.info(f"Querying Overpass mirror: {url}")
                response = requests.post(url, data={"data": query}, headers=headers, timeout=15)
                logger.info(f"Overpass response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    elements = data.get("elements", [])
                    logger.info(f"Overpass returned {len(elements)} elements for {facility_type}")
                    
                    for element in elements:
                        tags = element.get("tags", {})
                        item_lat = element.get("lat") or element.get("center", {}).get("lat")
                        item_lon = element.get("lon") or element.get("center", {}).get("lon")
                        
                        if not item_lat or not item_lon:
                            continue
                            
                        dist = haversine(lat, lon, item_lat, item_lon)
                        
                        # Try to build a clean address
                        addr_parts = []
                        if "addr:housenumber" in tags:
                            addr_parts.append(tags["addr:housenumber"])
                        if "addr:street" in tags:
                            addr_parts.append(tags["addr:street"])
                        if "addr:suburb" in tags:
                            addr_parts.append(tags["addr:suburb"])
                        if "addr:city" in tags:
                            addr_parts.append(tags["addr:city"])
                        
                        if addr_parts:
                            address = ", ".join(addr_parts)
                        elif "addr:full" in tags:
                            address = tags["addr:full"]
                        else:
                            address = tags.get("operator", "") or "Address not specified"
                            if address == "Address not specified" and "amenity" in tags:
                                address = f"Local {tags['amenity'].title()}"

                        name = tags.get("name")
                        if not name:
                            # Fallback name
                            amenity = tags.get("amenity") or tags.get("leisure") or facility_type
                            name = f"Unnamed {amenity.replace('_', ' ').title()}"

                        phone = tags.get("phone") or tags.get("contact:phone") or "N/A"
                        
                        results.append({
                            "name": name,
                            "address": address,
                            "distance_km": dist,
                            "rating": None,  # OSM doesn't have ratings
                            "phone": phone,
                            "lat": item_lat,
                            "lon": item_lon,
                            "directions_url": f"https://www.google.com/maps/dir/?api=1&destination={item_lat},{item_lon}"
                        })
                    
                    logger.info(f"Successfully processed {len(results)} {facility_type} results from {url}")
                    # Break the waterfall loop if we successfully got a response from a working mirror
                    break
                else:
                    logger.warning(f"Overpass mirror {url} returned status code {response.status_code}")
            except Exception as e:
                logger.warning(f"Overpass query to mirror {url} failed: {e}")
        
        logger.info(f"Overpass search for {facility_type} complete: {len(results)} results found")        
        return results

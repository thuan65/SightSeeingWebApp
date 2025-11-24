"""
Navigation System - GraphHopper Backend (Local Python Execution)
---------------------------------------------------------------

This version is simplified for direct Python execution.

Usage:
    1. Open this file in VSCode, PyCharm, or IDLE.
    2. Replace 'YOUR_KEY_HERE' below with your actual GraphHopper API key.
    3. Press Run (or F5) to execute.
    4. Output:
        - Distance (m)
        - Time (ms)
        - A 'route.geojson' file (viewable on https://geojson.io)
"""

import json
import requests
from GetCoordinates import get_address_coordinates, get_user_coordinates
import os

# --- SETUP ---
GH_KEY = "510b2242-84d4-45c2-97fa-baa242e6a4b7" 
TIMEOUT = 15


def gh_route_hosted(start: tuple[float, float],
                    end: tuple[float, float],
                    profile: str = "car") -> dict:
    """Send route request to GraphHopper Directions API."""
    if not GH_KEY:
        raise SystemExit("GraphHopper API key is missing. Set GH_KEY at the top of the file.")
    url = "https://graphhopper.com/api/1/route"
    params = [
        ("point", f"{start[0]},{start[1]}"),
        ("point", f"{end[0]},{end[1]}"),
        ("profile", profile),
        ("points_encoded", "false"),
        ("key", GH_KEY)
    ]
    r = requests.get(url, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def to_geojson_linestring(path_json: dict) -> dict:
    """Convert GraphHopper path JSON to GeoJSON LineString."""
    coords = path_json["points"]["coordinates"]
    return {"type": "LineString", "coordinates": coords}


if __name__ == "__main__":
    print("Fetching coordinates...")

    start = get_user_coordinates()  # your current location (via IP)
    end = get_address_coordinates("Hồ Chí Minh, Việt Nam")

    if not all(start) or not all(end):
        raise SystemExit("Failed to retrieve start/end coordinates.")

    print("Requesting route from GraphHopper...")
    data = gh_route_hosted(start, end, profile="car")

    path = data["paths"][0]
    distance_m = path["distance"]
    time_ms = path["time"]
    geojson = to_geojson_linestring(path)

    print(f"Distance: {distance_m:.1f} m")
    print(f"Estimated Time: {time_ms / 60000:.1f} minutes")

    feature = {
        "type": "Feature",
        "geometry": geojson,
        "properties": {"distance_m": distance_m, "time_ms": time_ms}
    }

    output_path = os.path.join("static", "route.geojson")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": [feature]}, f, ensure_ascii=False, indent=2)

    print(f"✅ Route saved as '{output_path}'. You can open http://127.0.0.1:5000/map to view it in your Flask app.")

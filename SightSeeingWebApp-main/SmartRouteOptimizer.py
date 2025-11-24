"""
Smart Route Optimizer (3 stops) - resilient & API-thrifty

This module optimizes the visiting order of 3 stops while minimizing calls to
the GraphHopper Directions API. It is designed to be drop-in compatible with
your existing backend.

Key features:
- Retries with exponential backoff + jitter on HTTP 429 / 5xx.
- On-disk JSON cache for each leg (A->B) to reduce repeated API calls.
- In-process memoization so permutations do not refetch the same leg.
- Negative caching (store None) for failing legs to avoid hammering the API.

Environment variables:
- GH_KEY: GraphHopper API key (required).
- TRAVEL_MODE: "car" | "bike" | "foot" (default: "car").
- RETURN_TO_START: "true" | "false" (default: "false").
- GH_TIMEOUT: request timeout seconds (default: 15).
- GH_MAX_RETRIES: max retries on 429/5xx (default: 6).
- GH_BACKOFF_BASE: base backoff seconds (default: 0.6).
- GH_BACKOFF_CAP: max backoff seconds cap (default: 8.0).

Outputs:
- Prints the best order, distance, and time.
- Saves a GeoJSON file "best_route.geojson" for quick visualization.
"""

from __future__ import annotations
import os
import json
import time
import random
import itertools
from typing import Tuple, List, Dict, Optional

import requests

# Import your existing helpers (unchanged)
from GetCoordinates import get_address_coordinates, get_user_coordinates

# ------------------------ Configuration ------------------------

GH_KEY = "510b2242-84d4-45c2-97fa-baa242e6a4b7"
TRAVEL_MODE = os.getenv("TRAVEL_MODE", "car")       # car | bike | foot
RETURN_TO_START = os.getenv("RETURN_TO_START", "false").lower() == "true"

TIMEOUT = int(os.getenv("GH_TIMEOUT", "15"))
MAX_RETRIES = int(os.getenv("GH_MAX_RETRIES", "6"))
BACKOFF_BASE = float(os.getenv("GH_BACKOFF_BASE", "0.6"))
BACKOFF_CAP = float(os.getenv("GH_BACKOFF_CAP", "8.0"))  # seconds

# Keep the original 3 default stops (you can still replace them at runtime)
ADDRESSES = [
    "Nguyễn Văn Cừ, Hồ Chí Minh, Việt Nam",
    "Sư Vạn Hạnh, Hồ Chí Minh, Việt Nam",
    "Quận 1, Hồ Chí Minh, Việt Nam"
]

# ------------------------ Simple JSON cache ------------------------

import threading
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
os.makedirs(CACHE_DIR, exist_ok=True)
ROUTE_CACHE = os.path.join(CACHE_DIR, "route_cache.json")
_cache_lock = threading.Lock()

def _json_load(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _json_save(path: str, data: dict) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)

def _cache_get(key: str):
    with _cache_lock:
        d = _json_load(ROUTE_CACHE)
        return d.get(key)

def _cache_set(key: str, value):
    with _cache_lock:
        d = _json_load(ROUTE_CACHE)
        # prune if huge
        if len(d) > 5000:
            drop_n = max(1, len(d) // 5)  # drop ~20% oldest
            for _ in range(drop_n):
                try:
                    d.pop(next(iter(d)))
                except StopIteration:
                    break
        d[key] = value
        _json_save(ROUTE_CACHE, d)

def _hash_key(*parts) -> str:
    import hashlib
    s = "|".join(str(p) for p in parts)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

# ------------------------ Routing core ------------------------

def gh_route(start: Tuple[float, float], end: Tuple[float, float], profile: str) -> Optional[Dict]:
    """
    Fetch a route leg from GraphHopper, with caching and retries.
    Returns the raw JSON (or None if no path).
    """
    if not GH_KEY:
        raise SystemExit("Missing GH_KEY. Set environment variable GH_KEY = <your_graphhopper_key>.")

    key = _hash_key("gh", round(start[0], 6), round(start[1], 6),
                         round(end[0], 6),   round(end[1], 6), profile)
    cached = _cache_get(key)
    if cached is not None:  # may be None (negative cache)
        return cached

    url = "https://graphhopper.com/api/1/route"
    params = [
        ("point", f"{start[0]},{start[1]}"),
        ("point", f"{end[0]},{end[1]}"),
        ("profile", profile),
        ("points_encoded", "false"),
        ("key", GH_KEY),
    ]

    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, params=params, timeout=TIMEOUT)
            # Retry on rate limiting / transient server errors
            if r.status_code in (429, 500, 502, 503, 504):
                wait = min(BACKOFF_CAP, BACKOFF_BASE * (2 ** attempt)) + random.uniform(0.05, 0.35)
                time.sleep(wait)
                continue
            r.raise_for_status()
            data = r.json()
            if not data.get("paths"):
                _cache_set(key, None)  # negative cache
                return None
            _cache_set(key, data)
            return data
        except requests.exceptions.RequestException:
            # Transient network issues -> small backoff and retry
            time.sleep(0.25 + 0.25 * attempt)

    # Give up for now; negative cache to prevent hot loops
    _cache_set(key, None)
    return None

def _extract_path(path_json: Dict) -> Dict:
    """Extract minimal path info."""
    return {
        "distance": path_json["distance"],           # meters
        "time": path_json["time"],                   # milliseconds
        "coords": path_json["points"]["coordinates"] # [[lon, lat], ...]
    }

# In-process memo to avoid duplicate legs across permutations
_leg_memo: dict = {}
def route_leg(a: Tuple[float, float], b: Tuple[float, float], profile: str):
    k = (round(a[0], 6), round(a[1], 6), round(b[0], 6), round(b[1], 6), profile)
    if k in _leg_memo:
        return _leg_memo[k]
    data = gh_route(a, b, profile)
    if data and "paths" in data and data["paths"]:
        leg = _extract_path(data["paths"][0])
        _leg_memo[k] = leg
        return leg
    _leg_memo[k] = None
    return None

def _stitch(coords_list: List[List[List[float]]]) -> List[List[float]]:
    """Concatenate segments and skip duplicate vertices at the joints."""
    out = []
    for i, seg in enumerate(coords_list):
        out.extend(seg if i == 0 else seg[1:])
    return out

def optimize_three_stops(start: Tuple[float, float],
                         stops: List[Tuple[float, float]],
                         profile: str,
                         return_to_start: bool = False):
    """
    Try all permutations of the 3 stops, sum distances, and pick the shortest.
    Returns a dict with best order, distance, time, and merged coordinates.
    """
    best_total = float("inf")
    best = None
    for perm in itertools.permutations(stops, 3):
        order = [start, *perm]
        total_dist = 0.0
        total_time = 0
        all_coords = []
        feasible = True

        for i in range(len(order) - 1):
            leg = route_leg(order[i], order[i + 1], profile)
            if not leg:
                feasible = False
                break
            total_dist += leg["distance"]
            total_time += leg["time"]
            all_coords.append(leg["coords"])

        if not feasible:
            continue

        if return_to_start:
            back = route_leg(order[-1], start, profile)
            if not back:
                feasible = False
            else:
                total_dist += back["distance"]
                total_time += back["time"]
                all_coords.append(back["coords"])

        if not feasible:
            continue

        if total_dist < best_total:
            best_total = total_dist
            best = {
                "perm": perm,
                "distance": total_dist,
                "time": total_time,
                "coords": _stitch(all_coords)
            }
    return best

def _fmt_coord(c: Tuple[float, float]) -> str:
    return f"({c[0]:.6f}, {c[1]:.6f})"

# ------------------------ CLI entrypoint ------------------------

def main():
    print("Fetching current coordinates (approx via IP)...")
    start = get_user_coordinates()
    if not all(start):
        raise SystemExit("Failed to get user coordinates.")

    print("Fetching geocodes for 3 addresses (cached)...")
    s1 = get_address_coordinates(ADDRESSES[0])
    s2 = get_address_coordinates(ADDRESSES[1])
    s3 = get_address_coordinates(ADDRESSES[2])
    if not all(s1) or not all(s2) or not all(s3):
        raise SystemExit("Failed to geocode one of the addresses.")

    print("Fetching optimal visiting order (memoized legs)...")
    best = optimize_three_stops(start, [s1, s2, s3], TRAVEL_MODE, RETURN_TO_START)
    if not best:
        raise SystemExit("No feasible route found (API limits or connectivity).")

    order = [start, *best["perm"]]
    if RETURN_TO_START:
        order.append(start)

    print("\n=== RESULT ===")
    for i, p in enumerate(order, 1):
        print(f"{i}. {_fmt_coord(p)}")
    print(f"Total distance: {best['distance']:.1f} m")
    print(f"Total time: {best['time']/60000:.1f} minutes")
    print(f"Mode: {TRAVEL_MODE} | Return to start: {RETURN_TO_START}")

    # Export a handy GeoJSON to visualize the shape at https://geojson.io
    feature = {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": best["coords"]},
        "properties": {
            "distance_m": best["distance"],
            "time_ms": best["time"],
            "mode": TRAVEL_MODE,
            "return_to_start": RETURN_TO_START,
            "stops": ADDRESSES,
        },
    }
    with open("best_route.geojson", "w", encoding="utf-8") as f:
        json.dump({"type": "FeatureCollection", "features": [feature]}, f, ensure_ascii=False, indent=2)
    print("Saved best_route.geojson (open on https://geojson.io).")

if __name__ == "__main__":
    main()

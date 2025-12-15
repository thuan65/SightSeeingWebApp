"""
Module to check if coordinates are within Vietnam territory
OPTIMIZED VERSION - Smart waypoint selection to avoid API overload
"""

import json
import os
import math

# --- CONFIGURATION ---
try:
    from .config import get_geojson_path, VIETNAM_BBOX
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("⚠️ config.py not found, using default configuration")

try:
    from shapely.geometry import Point, shape, Polygon
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    print("⚠️ Warning: Shapely not installed. using basic ray-casting algorithm.")

# Global variable to store geometry
VIETNAM_GEOMETRY = None

# --- HARDCODED FALLBACK POLYGON ---
VN_POLYGON_FALLBACK = [
    (21.5, 108.0), (20.8, 106.8), (20.0, 106.0), (19.0, 105.5),
    (17.5, 106.5), (16.5, 107.5), (16.0, 108.2), (15.0, 109.0),
    (13.0, 109.5), (11.5, 109.0), (10.5, 107.5), (10.3, 107.0),
    (8.5, 104.5),  (10.0, 104.0), (10.5, 104.5),
    (10.9, 105.0), (11.0, 106.0),
    (11.5, 106.5), (12.0, 107.0), (13.0, 107.5), (14.0, 107.5),
    (15.0, 107.5), (16.0, 107.0), (17.0, 106.0), (18.0, 105.0),
    (19.0, 104.0), (20.0, 103.5), (21.0, 103.0), (22.5, 102.5),
    (23.4, 105.0), (23.0, 106.0), (22.0, 107.0)
]

def load_vietnam_boundary():
    """Load Vietnam boundary from GeoJSON file"""
    global VIETNAM_GEOMETRY
    if VIETNAM_GEOMETRY is not None: return VIETNAM_GEOMETRY
    if not SHAPELY_AVAILABLE: return None

    possible_paths = [
        'templates/geoBoundaries-VNM-ADM0_simplified.geojson',
        'geoBoundaries-VNM-ADM0_simplified.geojson',
        os.path.join(os.path.dirname(__file__), 'templates', 'geoBoundaries-VNM-ADM0_simplified.geojson'),
    ]
    if CONFIG_AVAILABLE: possible_paths.insert(0, get_geojson_path())

    geojson_path = None
    for path in possible_paths:
        if path and os.path.exists(path):
            geojson_path = path
            break

    if geojson_path:
        try:
            with open(geojson_path, 'r', encoding='utf-8') as f:
                geojson_data = json.load(f)
            if 'features' in geojson_data and len(geojson_data['features']) > 0:
                feature = geojson_data['features'][0]
                VIETNAM_GEOMETRY = shape(feature['geometry'])
                print(f"✓ Loaded Vietnam boundary from {geojson_path}")
                return VIETNAM_GEOMETRY
        except Exception as e:
            print(f"⚠️ Error loading GeoJSON: {e}")

    return None

if SHAPELY_AVAILABLE: load_vietnam_boundary()

def is_point_in_polygon(lat, lon, polygon):
    """Ray-casting algorithm for fallback checks"""
    num_vertices = len(polygon)
    inside = False
    p1 = polygon[0]
    for i in range(1, num_vertices + 1):
        p2 = polygon[i % num_vertices]
        if min(p1[1], p2[1]) < lon <= max(p1[1], p2[1]):
            if lat <= max(p1[0], p2[0]):
                if p1[1] != p2[1]:
                    xinters = (lon - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1]) + p1[0]
                if p1[0] == p2[0] or lat <= xinters:
                    inside = not inside
        p1 = p2
    return inside

def is_in_vietnam(lat, lon):
    """Check if coordinates are within Vietnam"""
    if SHAPELY_AVAILABLE and VIETNAM_GEOMETRY:
        point = Point(lon, lat)
        return VIETNAM_GEOMETRY.contains(point)

    if not (8.0 <= lat <= 23.5 and 102.0 <= lon <= 110.0):
        return False

    return is_point_in_polygon(lat, lon, VN_POLYGON_FALLBACK)

def check_route_in_vietnam(coordinates):
    """Check if route goes through foreign countries"""
    if not coordinates:
        return {'is_valid': True, 'percentage_outside': 0, 'warning': ''}

    outside_points = 0
    total_points = len(coordinates)

    step = 5 if total_points > 200 else 1
    checked_points = 0

    for i in range(0, total_points, step):
        lon, lat = coordinates[i][0], coordinates[i][1]
        checked_points += 1
        if not is_in_vietnam(lat, lon):
            outside_points += 1

    percentage_outside = (outside_points / checked_points * 100) if checked_points > 0 else 0
    is_valid = percentage_outside < 5

    warning = ""
    if not is_valid:
        warning = f"⚠️ Warning: Route crosses borders ({percentage_outside:.1f}% outside VN)"

    return {
        'is_valid': is_valid,
        'outside_points': outside_points,
        'total_points': total_points,
        'percentage_outside': percentage_outside,
        'warning': warning
    }

# --- OPTIMIZED BACKBONE WAYPOINTS ---
# Reduced set of KEY cities only
VIETNAM_BACKBONE = [
    (21.0285, 105.8542),  # Hanoi (0)
    (18.6761, 105.6815),  # Vinh (1)
    (16.4637, 107.5909),  # Hue (2)
    (15.1205, 108.8048),  # Quang Ngai (3)
    (12.2388, 109.1967),  # Nha Trang (4)
    (10.7769, 106.7009),  # HCMC (5)
    (10.0452, 105.7469)   # Can Tho (6)
]

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate approximate distance between two points"""
    return math.sqrt((lat1 - lat2)**2 + (lon1 - lon2)**2)

def get_vietnam_waypoints(start_lat, start_lon, end_lat, end_lon, max_waypoints=3):
    """
    OPTIMIZED: Smart selection of backbone waypoints

    Strategy:
    1. Only use waypoints if distance > threshold
    2. Limit maximum number of waypoints (default 3)
    3. Select evenly distributed points along the route

    Args:
        max_waypoints: Maximum number of waypoints to add (default 3)
    """

    # 1. Calculate total distance
    total_distance = calculate_distance(start_lat, start_lon, end_lat, end_lon)

    # 2. If route is short (<2 degrees ~220km), no waypoints needed
    if total_distance < 2.0:
        print(f"  ℹ️ Short route ({total_distance:.2f}°), no waypoints needed")
        return []

    # 3. Find closest backbone indices
    def get_closest_index(lat, lon):
        min_dist = float('inf')
        idx = -1
        for i, (b_lat, b_lon) in enumerate(VIETNAM_BACKBONE):
            dist = calculate_distance(lat, lon, b_lat, b_lon)
            if dist < min_dist:
                min_dist = dist
                idx = i
        return idx, min_dist

    start_idx, start_dist = get_closest_index(start_lat, start_lon)
    end_idx, end_dist = get_closest_index(end_lat, end_lon)

    if start_idx == -1 or end_idx == -1:
        return []

    # 4. Get backbone segment
    if start_idx < end_idx:
        segment = list(range(start_idx, end_idx + 1))
    else:
        segment = list(range(end_idx, start_idx + 1))[::-1]

    # 5. Filter out start and end if they're too close
    filtered_segment = []
    for idx in segment:
        b_lat, b_lon = VIETNAM_BACKBONE[idx]
        d_start = calculate_distance(b_lat, b_lon, start_lat, start_lon)
        d_end = calculate_distance(b_lat, b_lon, end_lat, end_lon)

        # Only keep if reasonably far from both start and end (>0.3 degrees ~33km)
        if d_start > 0.3 and d_end > 0.3:
            filtered_segment.append(idx)

    # 6. If too many waypoints, select evenly distributed ones
    if len(filtered_segment) > max_waypoints:
        # Use step to select evenly distributed points
        step = len(filtered_segment) / (max_waypoints + 1)
        selected_indices = [filtered_segment[int(i * step)] for i in range(1, max_waypoints + 1)]
        filtered_segment = selected_indices

    # 7. Convert indices to coordinates
    waypoints = [VIETNAM_BACKBONE[idx] for idx in filtered_segment]

    print(f"  ➜ Selected {len(waypoints)}/{len(VIETNAM_BACKBONE)} waypoints for {total_distance:.2f}° route")

    return waypoints


def is_route_crossing_border(start_lat, start_lon, end_lat, end_lon):
    """
    Quick check: Does the direct line between start and end likely cross borders?

    Returns:
        bool: True if route likely crosses Laos/Cambodia border
    """

    # Simple heuristic: Check if route goes through central Vietnam danger zones
    # These coordinates roughly define the area near Laos/Cambodia borders

    avg_lat = (start_lat + end_lat) / 2
    avg_lon = (start_lon + end_lon) / 2

    # If route passes through Central Highlands near western border (105-107 lon, 14-18 lat)
    # This is where routes might cut through Laos
    if 14.0 <= avg_lat <= 18.0 and 105.0 <= avg_lon <= 107.0:
        # Additional check: Is this a long North-South route?
        lat_diff = abs(start_lat - end_lat)
        if lat_diff > 3.0:  # More than ~330km latitude difference
            print("  ⚠️ Route likely crosses western border region")
            return True

    return False
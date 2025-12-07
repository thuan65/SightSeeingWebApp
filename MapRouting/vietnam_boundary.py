"""
Module to check if coordinates are within Vietnam territory
Uses Shapely with MultiPolygon from official GeoJSON file
"""

import json
import os

try:
    from .config import get_geojson_path, VIETNAM_BBOX
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    print("⚠️ config.py not found, using default configuration")

try:
    from shapely.geometry import Point, shape
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    print("⚠️ Warning: Shapely not installed. Run: pip install shapely")

# Global variable to store geometry
VIETNAM_GEOMETRY = None

def load_vietnam_boundary():
    """
    Load Vietnam boundary from GeoJSON file

    Returns:
        Shapely geometry object or None
    """
    global VIETNAM_GEOMETRY

    if VIETNAM_GEOMETRY is not None:
        return VIETNAM_GEOMETRY

    if not SHAPELY_AVAILABLE:
        return None

    # Find GeoJSON file
    if CONFIG_AVAILABLE:
        geojson_path = get_geojson_path()
    else:
        # Fallback: manual search
        possible_paths = [
            'templates/geoBoundaries-VNM-ADM0_simplified.geojson',
            'geoBoundaries-VNM-ADM0_simplified.geojson',
            '../templates/geoBoundaries-VNM-ADM0_simplified.geojson',
            os.path.join(os.path.dirname(__file__), 'templates', 'geoBoundaries-VNM-ADM0_simplified.geojson'),
        ]

        geojson_path = None
        for path in possible_paths:
            if os.path.exists(path):
                geojson_path = path
                break

    if geojson_path is None:
        print(f"⚠️ GeoJSON file not found!")
        print(f"   Place 'geoBoundaries-VNM-ADM0_simplified.geojson' in 'templates/' directory")
        return None

    try:
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)

        # Get geometry from first feature
        if 'features' in geojson_data and len(geojson_data['features']) > 0:
            feature = geojson_data['features'][0]
            VIETNAM_GEOMETRY = shape(feature['geometry'])
            print(f"✓ Loaded Vietnam boundary from {geojson_path}")
            print(f"  Geometry type: {VIETNAM_GEOMETRY.geom_type}")
            print(f"  Number of polygons: {len(list(VIETNAM_GEOMETRY.geoms)) if VIETNAM_GEOMETRY.geom_type == 'MultiPolygon' else 1}")
            return VIETNAM_GEOMETRY
        else:
            print("⚠️ No features found in GeoJSON")
            return None

    except Exception as e:
        print(f"⚠️ Error loading GeoJSON: {e}")
        return None

# Initialize geometry when importing module
if SHAPELY_AVAILABLE:
    load_vietnam_boundary()

def is_in_vietnam(lat, lon):
    """
    Check if coordinates are within Vietnam (using Shapely)

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        bool: True if within Vietnam
    """
    if not SHAPELY_AVAILABLE:
        # Fallback: use simple bounding box
        if CONFIG_AVAILABLE:
            bbox = VIETNAM_BBOX
            return (bbox['lat_min'] <= lat <= bbox['lat_max'] and
                   bbox['lon_min'] <= lon <= bbox['lon_max'])
        else:
            return (8.5 <= lat <= 23.4 and 102.1 <= lon <= 109.5)

    if VIETNAM_GEOMETRY is None:
        # Try to load again
        load_vietnam_boundary()
        if VIETNAM_GEOMETRY is None:
            # Fallback if can't load
            if CONFIG_AVAILABLE:
                bbox = VIETNAM_BBOX
                return (bbox['lat_min'] <= lat <= bbox['lat_max'] and
                       bbox['lon_min'] <= lon <= bbox['lon_max'])
            else:
                return (8.5 <= lat <= 23.4 and 102.1 <= lon <= 109.5)

    point = Point(lon, lat)  # Shapely uses (lon, lat)
    return VIETNAM_GEOMETRY.contains(point)

def check_route_in_vietnam(coordinates):
    """
    Check if route goes through foreign countries

    Args:
        coordinates: List of coordinates [[lon, lat], [lon, lat], ...] (GraphHopper format)

    Returns:
        dict: {
            'is_valid': bool,
            'outside_points': int,
            'total_points': int,
            'percentage_outside': float,
            'warning': str,
            'outside_coords': list
        }
    """
    if not coordinates:
        return {
            'is_valid': True,
            'outside_points': 0,
            'total_points': 0,
            'percentage_outside': 0.0,
            'warning': '',
            'outside_coords': []
        }

    outside_points = 0
    outside_coords = []

    for coord in coordinates:
        lon, lat = coord[0], coord[1]

        if not is_in_vietnam(lat, lon):
            outside_points += 1
            outside_coords.append((lat, lon))

    total_points = len(coordinates)
    percentage_outside = (outside_points / total_points * 100) if total_points > 0 else 0

    # Warning threshold: >3% of points outside
    is_valid = percentage_outside < 3

    warning = ""
    if not is_valid:
        warning = f"⚠️ Warning: Route goes through foreign countries ({outside_points}/{total_points} points = {percentage_outside:.1f}%)"

    return {
        'is_valid': is_valid,
        'outside_points': outside_points,
        'total_points': total_points,
        'percentage_outside': percentage_outside,
        'warning': warning,
        'outside_coords': outside_coords[:5]  # Save max 5 points for debugging
    }

def get_vietnam_waypoints(start_lat, start_lon, end_lat, end_lon):
    """
    Suggest intermediate points to pass through Vietnam territory

    Args:
        start_lat, start_lon: Starting point
        end_lat, end_lon: Ending point

    Returns:
        list: List of waypoints [(lat, lon), ...]
    """
    waypoints = []

    # Determine region
    def get_region(lat):
        if lat >= 16.0:
            return 'north'
        elif lat >= 12.0:
            return 'central'
        else:
            return 'south'

    start_region = get_region(start_lat)
    end_region = get_region(end_lat)

    # If traveling from North to South (or vice versa)
    if start_region != end_region:
        if start_region == 'north' and end_region == 'south':
            # North → South: Through Vinh, Da Nang, Nha Trang
            waypoints.extend([
                (18.6761, 105.6815),  # Vinh
                (16.0544, 108.2022),  # Da Nang
                (12.2388, 109.1967),  # Nha Trang
            ])
        elif start_region == 'south' and end_region == 'north':
            # South → North: Reverse
            waypoints.extend([
                (12.2388, 109.1967),  # Nha Trang
                (16.0544, 108.2022),  # Da Nang
                (18.6761, 105.6815),  # Vinh
            ])
        elif start_region == 'north' and end_region == 'central':
            # North → Central: Through Vinh
            waypoints.append((18.6761, 105.6815))
        elif start_region == 'south' and end_region == 'central':
            # South → Central: Through Nha Trang
            waypoints.append((12.2388, 109.1967))
        elif start_region == 'central' and end_region == 'north':
            # Central → North: Through Vinh
            waypoints.append((18.6761, 105.6815))
        elif start_region == 'central' and end_region == 'south':
            # Central → South: Through Nha Trang
            waypoints.append((12.2388, 109.1967))

    return waypoints

if __name__ == "__main__":
    print("=== Test coordinate checking with GeoJSON data ===")

    if not SHAPELY_AVAILABLE:
        print("⚠️ Shapely not installed!")
        print("Run: pip install shapely")
        exit(1)

    if VIETNAM_GEOMETRY is None:
        print("⚠️ Cannot load GeoJSON file!")
        exit(1)

    test_coords = [
        (21.0285, 105.8542, "Hanoi"),
        (16.0544, 108.2022, "Da Nang"),
        (10.7769, 106.7009, "HCMC"),
        (12.2388, 109.1967, "Nha Trang"),
        (11.5564, 104.9282, "Phnom Penh - Cambodia"),
        (17.9757, 102.6331, "Vientiane - Laos"),
        (22.8000, 105.0000, "China border"),
        (10.3, 105.1, "Can Tho"),
        (21.5, 103.0, "Dien Bien Phu"),
    ]

    print(f"\nUsing geometry from GeoJSON: {VIETNAM_GEOMETRY.geom_type}")

    for lat, lon, name in test_coords:
        in_vn = is_in_vietnam(lat, lon)
        status = "✓ Inside VN" if in_vn else "✗ Outside VN"

        print(f"{name:30s}: ({lat:7.4f}, {lon:8.4f}) - {status}")

    # Test route check
    print("\n\n=== Test route checking ===")

    # Create fake route going through Cambodia
    fake_route = []
    for i in range(20):
        lat = 21.0 - (i * 0.6)  # From North to South
        lon = 105.8 - (i * 0.1)  # Shifting West (through Laos/Cambodia)
        fake_route.append([lon, lat])

    result = check_route_in_vietnam(fake_route)
    print(f"Total points: {result['total_points']}")
    print(f"Points outside VN: {result['outside_points']}")
    print(f"Percentage: {result['percentage_outside']:.1f}%")
    print(f"Valid: {result['is_valid']}")
    if result['warning']:
        print(result['warning'])

    # Test waypoints
    print("\n\n=== Test waypoint suggestions ===")
    waypoints = get_vietnam_waypoints(21.0285, 105.8542, 10.7769, 106.7009)
    print(f"Hanoi → HCMC: {len(waypoints)} waypoints")
    for i, (lat, lon) in enumerate(waypoints, 1):
        print(f"  {i}. ({lat:.4f}, {lon:.4f})")
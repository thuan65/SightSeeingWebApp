"""
Configuration file for Vietnam Routing System
"""

import os

# ==================== FILE PATHS ====================

# Project root directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Templates directory
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')

# GeoJSON file path
GEOJSON_FILE = 'templates/geoBoundaries-VNM-ADM0_simplified.geojson'

# Possible GeoJSON file paths
GEOJSON_PATHS = [
    os.path.join(TEMPLATES_DIR, GEOJSON_FILE),
    os.path.join(BASE_DIR, GEOJSON_FILE),
    os.path.join(BASE_DIR, '..', 'templates', GEOJSON_FILE),
]

# ==================== API CONFIGURATION ====================

# GraphHopper API
GRAPHHOPPER_API = "https://graphhopper.com/api/1/route"
GRAPHHOPPER_API_KEY = "510b2242-84d4-45c2-97fa-baa242e6a4b7"

# API Timeout (seconds)
API_TIMEOUT = 15

# Maximum retry attempts
MAX_RETRIES = 3

# ==================== ROUTING CONFIGURATION ====================

# Warning threshold (% of points outside Vietnam)
WARNING_THRESHOLD = 3.0  # < 3% = Safe
DANGER_THRESHOLD = 10.0  # > 10% = Danger

# Maximum waypoints
MAX_WAYPOINTS = 10

# Default vehicle
DEFAULT_VEHICLE = 'car'

# ==================== STRATEGIC WAYPOINTS ====================

# Major cities as waypoints
MAJOR_CITIES = {
    'hanoi': (21.0285, 105.8542),
    'hai_phong': (20.8449, 106.6881),
    'vinh': (18.6761, 105.6815),
    'dong_ha': (16.8163, 107.1004),
    'da_nang': (16.0544, 108.2022),
    'hoi_an': (15.8801, 108.3380),
    'quy_nhon': (13.7563, 109.2177),
    'nha_trang': (12.2388, 109.1967),
    'da_lat': (11.9404, 108.4583),
    'ho_chi_minh': (10.7769, 106.7009),
    'can_tho': (10.0340, 105.7218),
}

# Regional waypoints
REGIONAL_WAYPOINTS = {
    'north_to_central': [
        MAJOR_CITIES['vinh'],
        MAJOR_CITIES['dong_ha'],
    ],
    'central_to_south': [
        MAJOR_CITIES['da_nang'],
        MAJOR_CITIES['quy_nhon'],
        MAJOR_CITIES['nha_trang'],
    ],
    'north_to_south': [
        MAJOR_CITIES['vinh'],
        MAJOR_CITIES['da_nang'],
        MAJOR_CITIES['quy_nhon'],
        MAJOR_CITIES['nha_trang'],
    ],
}

# ==================== GEO BOUNDARIES ====================

# Vietnam bounding box (lat_min, lat_max, lon_min, lon_max)
VIETNAM_BBOX = {
    'lat_min': 8.5,
    'lat_max': 23.4,
    'lon_min': 102.1,
    'lon_max': 109.5
}

# Regional divisions
REGIONS = {
    'north': {'lat_min': 16.0, 'lat_max': 23.4},  # Northern region
    'central': {'lat_min': 12.0, 'lat_max': 16.0},  # Central region
    'south': {'lat_min': 8.5, 'lat_max': 12.0},  # Southern region
}

# ==================== MULTI-POINT ROUTING ====================

# Maximum destinations
MAX_DESTINATIONS = 4

# Optimize order by default
OPTIMIZE_ORDER_DEFAULT = True

# ==================== LOGGING ====================

# Show detailed logs
VERBOSE = True

# Show debug information
DEBUG = False


# ==================== HELPER FUNCTIONS ====================

def get_geojson_path():
    """
    Find GeoJSON file path

    Returns:
        str: File path or None if not found
    """
    for path in GEOJSON_PATHS:
        if os.path.exists(path):
            return path
    return None


def get_region(lat):
    """
    Determine region based on latitude

    Args:
        lat: Latitude

    Returns:
        str: 'north', 'central', or 'south'
    """
    if lat >= REGIONS['north']['lat_min']:
        return 'north'
    elif lat >= REGIONS['central']['lat_min']:
        return 'central'
    else:
        return 'south'


def is_in_bbox(lat, lon):
    """
    Check if coordinates are within Vietnam bounding box

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        bool: True if within bounding box
    """
    return (
            VIETNAM_BBOX['lat_min'] <= lat <= VIETNAM_BBOX['lat_max'] and
            VIETNAM_BBOX['lon_min'] <= lon <= VIETNAM_BBOX['lon_max']
    )


def print_config():
    """Print current configuration"""
    print("=" * 60)
    print("VIETNAM ROUTING SYSTEM - CONFIGURATION")
    print("=" * 60)

    print(f"\n📁 Paths:")
    print(f"   Base dir: {BASE_DIR}")
    print(f"   Templates: {TEMPLATES_DIR}")

    geojson_path = get_geojson_path()
    if geojson_path:
        print(f"   GeoJSON: ✓ {geojson_path}")
    else:
        print(f"   GeoJSON: ✗ Not found")

    print(f"\n🌐 API:")
    print(f"   GraphHopper: {GRAPHHOPPER_API}")
    print(f"   Timeout: {API_TIMEOUT}s")
    print(f"   Max retries: {MAX_RETRIES}")

    print(f"\n⚙️ Routing:")
    print(f"   Warning threshold: {WARNING_THRESHOLD}%")
    print(f"   Danger threshold: {DANGER_THRESHOLD}%")
    print(f"   Max waypoints: {MAX_WAYPOINTS}")
    print(f"   Default vehicle: {DEFAULT_VEHICLE}")

    print(f"\n🏙️ Major cities: {len(MAJOR_CITIES)}")
    for name, (lat, lon) in list(MAJOR_CITIES.items())[:3]:
        print(f"   - {name:15s}: ({lat:.4f}, {lon:.4f})")
    if len(MAJOR_CITIES) > 3:
        print(f"   ... and {len(MAJOR_CITIES) - 3} more cities")

    print(f"\n📊 Multi-point:")
    print(f"   Max destinations: {MAX_DESTINATIONS}")
    print(f"   Optimize by default: {OPTIMIZE_ORDER_DEFAULT}")

    print(f"\n🔧 Debug:")
    print(f"   Verbose: {VERBOSE}")
    print(f"   Debug: {DEBUG}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    print_config()

    # Test GeoJSON path
    print("\n🔍 Testing GeoJSON path...")
    geojson_path = get_geojson_path()

    if geojson_path:
        print(f"✓ File found: {geojson_path}")

        # Check file size
        file_size = os.path.getsize(geojson_path)
        print(f"  Size: {file_size / 1024:.2f} KB")
    else:
        print("✗ GeoJSON file not found!")
        print("\nPaths tried:")
        for path in GEOJSON_PATHS:
            exists = "✓" if os.path.exists(path) else "✗"
            print(f"  {exists} {path}")
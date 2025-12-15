import requests
from .vietnam_boundary import (
    check_route_in_vietnam,
    get_vietnam_waypoints,
    is_in_vietnam,
    is_route_crossing_border
)

GRAPHHOPPER_API = "https://graphhopper.com/api/1/route"
API_KEY = "510b2242-84d4-45c2-97fa-baa242e6a4b7"


def get_route(start_lat, start_lon, end_lat, end_lon, vehicle='car', max_retries=1):
    """
    OPTIMIZED: Find route with smart waypoint selection

    Strategy:
    1. Try direct route first
    2. If invalid AND route likely crosses border, use LIMITED waypoints
    3. Smart selection of max 3 waypoints to avoid API overload
    """

    # --- 1. Try Direct Route ---
    print("🔍 Attempt 1: Direct Route...")
    params = {
        'point': [f"{start_lat},{start_lon}", f"{end_lat},{end_lon}"],
        'vehicle': vehicle,
        'locale': 'vi',
        'instructions': 'true',
        'calc_points': 'true',
        'points_encoded': 'false',
        'key': API_KEY
    }

    direct_route = _fetch_route(params)

    # If direct route is valid, use it
    if direct_route and direct_route['vietnam_check']['is_valid']:
        print("✓ Direct route is valid.")
        return direct_route

    # --- 2. Smart Decision: Do we REALLY need waypoints? ---
    # Only use waypoints if route likely crosses borders
    if not is_route_crossing_border(start_lat, start_lon, end_lat, end_lon):
        print("ℹ️ Route unlikely to cross borders. Using direct route.")
        return direct_route if direct_route else None

    # --- 3. Apply OPTIMIZED Backbone Strategy ---
    print("⚠️ Route may cross borders. Applying SMART waypoint strategy...")

    # Get LIMITED waypoints (max 3)
    backbone_waypoints = get_vietnam_waypoints(
        start_lat, start_lon,
        end_lat, end_lon,
        max_waypoints=3  # CRITICAL: Limit to 3 waypoints max
    )

    if not backbone_waypoints:
        print("ℹ️ No waypoints needed or available.")
        return direct_route

    print(f"  ➜ Using {len(backbone_waypoints)} strategic waypoints")

    # Build path with limited waypoints
    all_points = [(start_lat, start_lon)] + backbone_waypoints + [(end_lat, end_lon)]
    point_params = [f"{lat},{lon}" for lat, lon in all_points]

    params['point'] = point_params
    backbone_route = _fetch_route(params)

    if backbone_route:
        # Compare routes
        if not direct_route or backbone_route['vietnam_check']['percentage_outside'] < \
                direct_route['vietnam_check']['percentage_outside']:
            print("✓ Optimized backbone route selected.")
            backbone_route['method'] = 'coastal_backbone'
            backbone_route['waypoints'] = backbone_waypoints
            backbone_route['waypoint_count'] = len(backbone_waypoints)
            return backbone_route

    # --- 4. Fallback ---
    print("⚠️ Returning direct route (best effort).")
    return direct_route


def _fetch_route(params):
    """Helper to call API and parse response"""
    try:
        print(f"  📡 API Call: {len(params.get('point', []))} points")

        response = requests.get(GRAPHHOPPER_API, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        if 'paths' in data and len(data['paths']) > 0:
            path = data['paths'][0]
            coordinates = path['points']['coordinates']
            route_check = check_route_in_vietnam(coordinates)

            return {
                'coordinates': coordinates,
                'distance': path['distance'],
                'time': path['time'],
                'instructions': path.get('instructions', []),
                'bbox': path.get('bbox', []),
                'vietnam_check': route_check,
                'method': 'direct'
            }
        else:
            print("  ❌ API returned no paths")

    except requests.exceptions.Timeout:
        print("  ❌ API Timeout (too many waypoints?)")
    except requests.exceptions.RequestException as e:
        print(f"  ❌ API Error: {e}")
    except Exception as e:
        print(f"  ❌ Unexpected Error: {e}")

    return None
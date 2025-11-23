import requests
from vietnam_boundary import check_route_in_vietnam, get_vietnam_waypoints, is_in_vietnam

GRAPHHOPPER_API = "https://graphhopper.com/api/1/route"
API_KEY = "510b2242-84d4-45c2-97fa-baa242e6a4b7"


def get_strategic_waypoints(start_lat, start_lon, end_lat, end_lon):
    """
    Create strategic waypoints based on geographic regions

    Args:
        start_lat, start_lon: Starting point coordinates
        end_lat, end_lon: Ending point coordinates

    Returns:
        list: List of waypoints [(lat, lon), ...]
    """
    waypoints = []

    # Check if start and end points are within Vietnam
    start_in_vn = is_in_vietnam(start_lat, start_lon)
    end_in_vn = is_in_vietnam(end_lat, end_lon)

    if not start_in_vn or not end_in_vn:
        print(f"⚠️ Warning: {'Start' if not start_in_vn else 'End'} point is outside Vietnam")
        return []

    # Calculate latitude distance
    lat_diff = abs(end_lat - start_lat)
    lon_diff = abs(end_lon - start_lon)

    # If distance is too far (>5 degrees), add waypoints
    if lat_diff > 5:
        # Get basic waypoints from old function
        basic_waypoints = get_vietnam_waypoints(start_lat, start_lon, end_lat, end_lon)

        # Add additional waypoints for border provinces
        if start_lat > 20 and end_lat < 12:
            # From far North to far South - follow coastal route
            waypoints.extend([
                (20.8449, 106.6881),  # Hai Phong
                (18.6761, 105.6815),  # Vinh
                (17.4739, 106.6234),  # Dong Ha
                (16.0544, 108.2022),  # Da Nang
                (13.7563, 109.2177),  # Quy Nhon
                (12.2388, 109.1967),  # Nha Trang
                (11.9404, 108.4583),  # Da Lat
            ])
        else:
            waypoints.extend(basic_waypoints)

    # If crossing Southwest region (high risk of entering Cambodia)
    elif start_lon < 105.0 or end_lon < 105.0:
        # Southwest region - near Cambodia
        if 10.0 <= start_lat <= 12.0 or 10.0 <= end_lat <= 12.0:
            waypoints.append((10.7769, 106.7009))  # HCMC (safe point)

    # If crossing Northwest region (risk of entering Laos)
    elif start_lon < 105.0 and start_lat > 18.0:
        waypoints.append((21.0285, 105.8542))  # Hanoi (safe point)

    return waypoints


def get_route(start_lat, start_lon, end_lat, end_lon, vehicle='car', max_retries=3):
    """
    Find route from start point to end point
    (Automatically adds waypoints if needed to stay within Vietnam)

    Args:
        start_lat: Start latitude
        start_lon: Start longitude
        end_lat: End latitude
        end_lon: End longitude
        vehicle: Vehicle type (car, bike, foot)
        max_retries: Maximum retry attempts

    Returns:
        dict: Route information or None if failed
    """

    # Try 1: Find direct route
    print("🔍 Finding direct route...")
    params = {
        'point': [f"{start_lat},{start_lon}", f"{end_lat},{end_lon}"],
        'vehicle': vehicle,
        'locale': 'vi',
        'instructions': 'true',
        'calc_points': 'true',
        'points_encoded': 'false',
        'key': API_KEY
    }

    try:
        response = requests.get(GRAPHHOPPER_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'paths' in data and len(data['paths']) > 0:
            path = data['paths'][0]
            coordinates = path['points']['coordinates']
            route_check = check_route_in_vietnam(coordinates)

            # If route OK (< 5% outside VN), return immediately
            if route_check['percentage_outside'] < 5:
                print(f"✓ Found direct route ({route_check['percentage_outside']:.1f}% outside VN)")
                return {
                    'coordinates': coordinates,
                    'distance': path['distance'],
                    'time': path['time'],
                    'instructions': path.get('instructions', []),
                    'bbox': path.get('bbox', []),
                    'vietnam_check': route_check,
                    'used_waypoints': False,
                    'method': 'direct'
                }

            # Route not good - save for comparison
            print(f"⚠️ Direct route has {route_check['percentage_outside']:.1f}% outside VN")
            best_route = {
                'coordinates': coordinates,
                'distance': path['distance'],
                'time': path['time'],
                'instructions': path.get('instructions', []),
                'bbox': path.get('bbox', []),
                'vietnam_check': route_check,
                'used_waypoints': False,
                'method': 'direct'
            }
            best_percentage = route_check['percentage_outside']

        else:
            print("⚠️ No direct route found")
            best_route = None
            best_percentage = 100

    except requests.exceptions.RequestException as e:
        print(f"❌ Error finding direct route: {e}")
        best_route = None
        best_percentage = 100

    # Try 2: Find route with strategic waypoints
    print("\n🔍 Trying with strategic waypoints...")
    waypoints = get_strategic_waypoints(start_lat, start_lon, end_lat, end_lon)

    if waypoints:
        print(f"  Using {len(waypoints)} waypoints")

        # Create point list: start → waypoint1 → waypoint2 → ... → end
        all_points = [(start_lat, start_lon)] + waypoints + [(end_lat, end_lon)]
        point_params = [f"{lat},{lon}" for lat, lon in all_points]

        params['point'] = point_params

        try:
            response = requests.get(GRAPHHOPPER_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'paths' in data and len(data['paths']) > 0:
                path = data['paths'][0]
                coordinates = path['points']['coordinates']
                route_check = check_route_in_vietnam(coordinates)

                print(f"  Result: {route_check['percentage_outside']:.1f}% outside VN")

                # If new route is significantly better (>10% improvement or <5%)
                if route_check['percentage_outside'] < best_percentage - 10 or route_check['percentage_outside'] < 5:
                    print(f"✓ Route with waypoints is better!")
                    return {
                        'coordinates': coordinates,
                        'distance': path['distance'],
                        'time': path['time'],
                        'instructions': path.get('instructions', []),
                        'bbox': path.get('bbox', []),
                        'vietnam_check': route_check,
                        'used_waypoints': True,
                        'waypoints': waypoints,
                        'method': 'strategic_waypoints'
                    }
                else:
                    print(f"  Route with waypoints doesn't improve significantly")

        except requests.exceptions.RequestException as e:
            print(f"  Error trying waypoints: {e}")
    else:
        print("  No waypoints needed for this route")

    # Try 3: Find route with denser waypoints (if still have retries)
    if best_percentage > 10 and max_retries > 1:
        print("\n🔍 Trying with denser waypoints...")

        # Create denser waypoint grid
        dense_waypoints = []
        lat_steps = int(abs(end_lat - start_lat) / 2) + 1

        for i in range(1, lat_steps):
            interp_lat = start_lat + (end_lat - start_lat) * i / lat_steps
            interp_lon = start_lon + (end_lon - start_lon) * i / lat_steps

            # Check if point is in Vietnam
            if is_in_vietnam(interp_lat, interp_lon):
                dense_waypoints.append((interp_lat, interp_lon))

        if len(dense_waypoints) > 0 and len(dense_waypoints) <= 5:
            print(f"  Using {len(dense_waypoints)} interpolated waypoints")

            all_points = [(start_lat, start_lon)] + dense_waypoints + [(end_lat, end_lon)]
            point_params = [f"{lat},{lon}" for lat, lon in all_points]
            params['point'] = point_params

            try:
                response = requests.get(GRAPHHOPPER_API, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()

                if 'paths' in data and len(data['paths']) > 0:
                    path = data['paths'][0]
                    coordinates = path['points']['coordinates']
                    route_check = check_route_in_vietnam(coordinates)

                    print(f"  Result: {route_check['percentage_outside']:.1f}% outside VN")

                    if route_check['percentage_outside'] < best_percentage:
                        print(f"✓ Route with dense waypoints is better!")
                        return {
                            'coordinates': coordinates,
                            'distance': path['distance'],
                            'time': path['time'],
                            'instructions': path.get('instructions', []),
                            'bbox': path.get('bbox', []),
                            'vietnam_check': route_check,
                            'used_waypoints': True,
                            'waypoints': dense_waypoints,
                            'method': 'dense_waypoints'
                        }

            except requests.exceptions.RequestException as e:
                print(f"  Error trying dense waypoints: {e}")

    # Return best route found (may have warnings)
    if best_route:
        print(
            f"\n➜ Using best route: {best_route['method']} ({best_route['vietnam_check']['percentage_outside']:.1f}% outside VN)")
        return best_route

    print("\n❌ No suitable route found")
    return None


def format_distance(meters):
    """Convert meters to km or m"""
    if meters >= 1000:
        return f"{meters / 1000:.2f} km"
    return f"{int(meters)} m"


def format_time(milliseconds):
    """Convert milliseconds to hours:minutes"""
    minutes = milliseconds / 1000 / 60
    hours = int(minutes // 60)
    mins = int(minutes % 60)

    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


if __name__ == "__main__":
    print("=" * 60)
    print("TEST ROUTING WITH ACCURATE BOUNDARIES")
    print("=" * 60)

    # Test 1: Short route within same city
    print("\n\n### Test 1: Hanoi → Hoan Kiem Lake ###")
    route = get_route(21.0285, 105.8542, 21.0288, 105.8526, 'car')

    if route:
        print(f"\n📊 Result:")
        print(f"  Distance: {format_distance(route['distance'])}")
        print(f"  Time: {format_time(route['time'])}")
        print(f"  Points: {len(route['coordinates'])}")
        print(f"  Method: {route['method']}")
        if route['vietnam_check']['warning']:
            print(f"  {route['vietnam_check']['warning']}")

    # Test 2: Long North-South route
    print("\n\n### Test 2: Hanoi → HCMC ###")
    route = get_route(21.0285, 105.8542, 10.7769, 106.7009, 'car')

    if route:
        print(f"\n📊 Result:")
        print(f"  Distance: {format_distance(route['distance'])}")
        print(f"  Time: {format_time(route['time'])}")
        print(f"  Points: {len(route['coordinates'])}")
        print(f"  Method: {route['method']}")
        if route.get('used_waypoints'):
            print(f"  ✓ Used {len(route['waypoints'])} waypoints")
        if route['vietnam_check']['warning']:
            print(f"  {route['vietnam_check']['warning']}")

    # Test 3: Dangerous route (near Cambodia)
    print("\n\n### Test 3: Can Tho → An Giang (near border) ###")
    route = get_route(10.0340, 105.7218, 10.5216, 105.1258, 'car')

    if route:
        print(f"\n📊 Result:")
        print(f"  Distance: {format_distance(route['distance'])}")
        print(f"  Time: {format_time(route['time'])}")
        print(f"  Points: {len(route['coordinates'])}")
        print(f"  Method: {route['method']}")
        if route.get('used_waypoints'):
            print(f"  ✓ Used {len(route['waypoints'])} waypoints")
        if route['vietnam_check']['warning']:
            print(f"  {route['vietnam_check']['warning']}")
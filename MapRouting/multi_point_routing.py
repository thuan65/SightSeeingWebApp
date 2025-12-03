import requests
from itertools import permutations
from vietnam_boundary import check_route_in_vietnam, is_in_vietnam, get_vietnam_waypoints

GRAPHHOPPER_API = "https://graphhopper.com/api/1/route"
API_KEY = "510b2242-84d4-45c2-97fa-baa242e6a4b7"


def get_strategic_waypoints_for_segment(start_lat, start_lon, end_lat, end_lon):
    """
    Generate strategic waypoints for a route segment to keep it within Vietnam

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
        print(f"  ⚠️ Warning: {'Start point' if not start_in_vn else 'End point'} is outside Vietnam")
        return []

    # Calculate distance
    lat_diff = abs(end_lat - start_lat)
    lon_diff = abs(end_lon - start_lon)

    # If distance is far (>3 degrees latitude), add waypoints
    if lat_diff > 3:
        basic_waypoints = get_vietnam_waypoints(start_lat, start_lon, end_lat, end_lon)
        waypoints.extend(basic_waypoints)

    # If passing through Southwest region (risk of entering Cambodia)
    elif start_lon < 105.5 or end_lon < 105.5:
        if 9.5 <= start_lat <= 11.5 or 9.5 <= end_lat <= 11.5:
            # Add safe point: HCMC
            waypoints.append((10.7769, 106.7009))

    # If passing through Northwest region (risk of entering Laos)
    elif start_lon < 105.5 and start_lat > 18.0:
        # Add safe point: Hanoi
        waypoints.append((21.0285, 105.8542))

    return waypoints


def get_route_with_boundary_check(points, vehicle='car', max_retries=2):
    """
    Calculate route with boundary checking and auto-add waypoints if needed

    Args:
        points: List of points [(lat, lon), ...]
        vehicle: Vehicle type
        max_retries: Maximum number of retries

    Returns:
        dict: Route information or None
    """
    if len(points) < 2:
        return None

    # Try 1: Direct route
    point_params = [f"{lat},{lon}" for lat, lon in points]

    params = {
        'point': point_params,
        'vehicle': vehicle,
        'locale': 'vi',
        'instructions': 'true',
        'calc_points': 'true',
        'points_encoded': 'false',
        'key': API_KEY
    }

    try:
        response = requests.get(GRAPHHOPPER_API, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if 'paths' in data and len(data['paths']) > 0:
            path = data['paths'][0]
            coordinates = path['points']['coordinates']
            route_check = check_route_in_vietnam(coordinates)

            # If route is OK (<5% outside VN), return immediately
            if route_check['percentage_outside'] < 5:
                return {
                    'coordinates': coordinates,
                    'distance': path['distance'],
                    'time': path['time'],
                    'instructions': path.get('instructions', []),
                    'vietnam_check': route_check,
                    'method': 'direct'
                }

            # Route not good - save for comparison
            print(f"  ⚠️ Direct route has {route_check['percentage_outside']:.1f}% outside VN")
            best_route = {
                'coordinates': coordinates,
                'distance': path['distance'],
                'time': path['time'],
                'instructions': path.get('instructions', []),
                'vietnam_check': route_check,
                'method': 'direct'
            }
            best_percentage = route_check['percentage_outside']
        else:
            best_route = None
            best_percentage = 100

    except requests.exceptions.RequestException as e:
        print(f"  ❌ Error finding direct route: {e}")
        best_route = None
        best_percentage = 100

    # Try 2: Add strategic waypoints for each segment
    if best_percentage > 5 and max_retries > 0:
        print(f"  🔄 Trying with strategic waypoints...")

        enhanced_points = [points[0]]  # Starting point

        # Add waypoints between segments
        for i in range(len(points) - 1):
            start_lat, start_lon = points[i]
            end_lat, end_lon = points[i + 1]

            # Get waypoints for this segment
            segment_waypoints = get_strategic_waypoints_for_segment(
                start_lat, start_lon, end_lat, end_lon
            )

            if segment_waypoints:
                print(f"    Segment {i + 1}: Added {len(segment_waypoints)} waypoints")
                enhanced_points.extend(segment_waypoints)

            # Add destination point of this segment
            enhanced_points.append((end_lat, end_lon))

        # If waypoints were added, try new route
        if len(enhanced_points) > len(points):
            point_params = [f"{lat},{lon}" for lat, lon in enhanced_points]
            params['point'] = point_params

            try:
                response = requests.get(GRAPHHOPPER_API, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()

                if 'paths' in data and len(data['paths']) > 0:
                    path = data['paths'][0]
                    coordinates = path['points']['coordinates']
                    route_check = check_route_in_vietnam(coordinates)

                    print(f"    Result: {route_check['percentage_outside']:.1f}% outside VN")

                    # If new route is significantly better
                    if route_check['percentage_outside'] < best_percentage - 5:
                        print(f"  ✅ Route with waypoints is better!")
                        return {
                            'coordinates': coordinates,
                            'distance': path['distance'],
                            'time': path['time'],
                            'instructions': path.get('instructions', []),
                            'vietnam_check': route_check,
                            'method': 'strategic_waypoints',
                            'waypoints_added': len(enhanced_points) - len(points)
                        }

            except requests.exceptions.RequestException as e:
                print(f"    Error trying waypoints: {e}")

    # Return best route found
    if best_route:
        return best_route

    return None


def get_route_distance(points, vehicle='car'):
    """
    Calculate distance for a route through multiple points
    (Limited to Vietnam territory)

    Args:
        points: List of points [(lat, lon), ...]
        vehicle: Vehicle type

    Returns:
        dict: Route information or None
    """
    # Check if all points are within Vietnam
    points_in_vn = []
    for i, (lat, lon) in enumerate(points):
        in_vn = is_in_vietnam(lat, lon)
        points_in_vn.append(in_vn)
        if not in_vn:
            print(f"⚠️ Point {i + 1} ({lat:.4f}, {lon:.4f}) is outside Vietnam")

    # If there are points outside VN, warn
    if not all(points_in_vn):
        outside_count = len([x for x in points_in_vn if not x])
        print(f"⚠️ Warning: {outside_count}/{len(points)} points outside Vietnam")

    # Use function with boundary check
    return get_route_with_boundary_check(points, vehicle)


def find_shortest_route_multi_points(start_lat, start_lon, destinations, vehicle='car', optimize=True):
    """
    Find route through multiple points (1-4 points) with Vietnam territory limit

    Args:
        start_lat: Start latitude
        start_lon: Start longitude
        destinations: List of destination points [{'lat': x, 'lon': y, 'name': '...'}, ...]
        vehicle: Vehicle type
        optimize: Whether to optimize point order

    Returns:
        dict: Best route information
    """
    if not destinations:
        print("❌ No destinations")
        return None

    if len(destinations) > 4:
        print(f"⚠️ Only support up to 4 destinations (current: {len(destinations)})")
        return None

    # Check starting point
    if not is_in_vietnam(start_lat, start_lon):
        print(f"⚠️ Starting point ({start_lat:.4f}, {start_lon:.4f}) is outside Vietnam")

    # Check destination points
    dest_points = []
    for i, d in enumerate(destinations):
        lat, lon = d['lat'], d['lon']
        name = d.get('name', f'Point {i + 1}')

        if not is_in_vietnam(lat, lon):
            print(f"⚠️ {name} ({lat:.4f}, {lon:.4f}) is outside Vietnam")

        dest_points.append((lat, lon))

    # If only 1 destination, no need to optimize
    if len(dest_points) == 1:
        print("🔍 Finding route to 1 destination...")
        points = [(start_lat, start_lon)] + dest_points
        route = get_route_distance(points, vehicle)

        if route:
            route['order'] = [0, 1]
            route['ordered_destinations'] = destinations

            # Add safety level information
            if route['vietnam_check']['percentage_outside'] < 3:
                route['safety_level'] = 'safe'
            elif route['vietnam_check']['percentage_outside'] < 10:
                route['safety_level'] = 'warning'
            else:
                route['safety_level'] = 'danger'

        return route

    # If not optimizing, just find route in order
    if not optimize:
        print(f"🔍 Finding route through {len(dest_points)} points (no optimization)...")
        points = [(start_lat, start_lon)] + dest_points
        route = get_route_distance(points, vehicle)

        if route:
            route['order'] = list(range(len(destinations) + 1))
            route['ordered_destinations'] = destinations

            if route['vietnam_check']['percentage_outside'] < 3:
                route['safety_level'] = 'safe'
            elif route['vietnam_check']['percentage_outside'] < 10:
                route['safety_level'] = 'warning'
            else:
                route['safety_level'] = 'danger'

        return route

    # Optimize destination order
    print(f"🔍 Optimizing order for {len(dest_points)} points...")

    best_route = None
    best_distance = float('inf')
    best_order = None
    best_percentage_outside = 100

    total_perms = 1
    for i in range(1, len(dest_points) + 1):
        total_perms *= i

    print(f"  Total permutations: {total_perms}")

    perm_count = 0
    for perm in permutations(range(len(dest_points))):
        perm_count += 1

        # Create point order: start -> dest[perm[0]] -> dest[perm[1]] -> ...
        ordered_points = [(start_lat, start_lon)]
        for idx in perm:
            ordered_points.append(dest_points[idx])

        route = get_route_distance(ordered_points, vehicle)

        if route:
            distance = route['distance']
            percentage_outside = route['vietnam_check']['percentage_outside']

            # Prioritize safer routes (less outside VN)
            # If safety is similar, choose shorter route
            is_better = False

            if percentage_outside < 3 and best_percentage_outside < 3:
                # Both safe -> choose shorter route
                is_better = distance < best_distance
            elif percentage_outside < best_percentage_outside:
                # New route is safer
                is_better = True
            elif percentage_outside == best_percentage_outside:
                # Same safety -> choose shorter route
                is_better = distance < best_distance

            if is_better:
                best_distance = distance
                best_route = route
                best_order = [0] + [idx + 1 for idx in perm]
                best_percentage_outside = percentage_outside

                # Reorder destinations according to best order
                ordered_dests = [destinations[idx] for idx in perm]
                best_route['ordered_destinations'] = ordered_dests
                best_route['order'] = best_order

                print(
                    f"  ✅ Permutation {perm_count}/{total_perms}: {format_distance(distance)}, {percentage_outside:.1f}% outside VN")

    if best_route:
        # Add safety assessment
        if best_route['vietnam_check']['percentage_outside'] < 3:
            best_route['safety_level'] = 'safe'
            print(f"\n✅ Safe route: {format_distance(best_route['distance'])}")
        elif best_route['vietnam_check']['percentage_outside'] < 10:
            best_route['safety_level'] = 'warning'
            print(
                f"\n⚠️ Warning route: {format_distance(best_route['distance'])}, {best_route['vietnam_check']['percentage_outside']:.1f}% outside VN")
        else:
            best_route['safety_level'] = 'danger'
            print(
                f"\n⚠️ Dangerous route: {format_distance(best_route['distance'])}, {best_route['vietnam_check']['percentage_outside']:.1f}% outside VN")

        # Display waypoint information if available
        if best_route.get('method') == 'strategic_waypoints':
            print(f"  📍 Added {best_route.get('waypoints_added', 0)} waypoints to keep route in VN")

    return best_route


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
    print("TEST MULTI-POINT ROUTING WITH VIETNAM TERRITORY LIMIT")
    print("=" * 60)

    # Test 1: 3 points in HCMC
    print("\n\n### Test 1: Tour of 3 points in HCMC ###")
    start_lat, start_lon = 10.7769, 106.7009

    destinations = [
        {'lat': 10.7624, 'lon': 106.6822, 'name': 'Ben Thanh Market'},
        {'lat': 10.7721, 'lon': 106.6988, 'name': 'Notre Dame Cathedral'},
        {'lat': 10.7877, 'lon': 106.7018, 'name': 'Independence Palace'}
    ]

    result = find_shortest_route_multi_points(start_lat, start_lon, destinations, 'car')

    if result:
        print(f"\n📊 Result:")
        print(f"  Distance: {format_distance(result['distance'])}")
        print(f"  Time: {format_time(result['time'])}")
        print(f"  Optimal order: {result['order']}")
        print(f"  Safety level: {result['safety_level']}")
        print(f"  Method: {result.get('method', 'unknown')}")

        if result['vietnam_check']['warning']:
            print(f"  {result['vietnam_check']['warning']}")

        print(f"\n  Point order:")
        print(f"    0. Starting point")
        for i, dest in enumerate(result['ordered_destinations'], 1):
            print(f"    {i}. {dest.get('name', f'Point {i}')}")

    # Test 2: Central region tour (may cross border)
    print("\n\n### Test 2: Tour of 4 points in Central region ###")
    start_lat, start_lon = 16.0544, 108.2022  # Da Nang

    destinations = [
        {'lat': 16.4637, 'lon': 107.5909, 'name': 'Hue'},
        {'lat': 15.8801, 'lon': 108.3380, 'name': 'Hoi An'},
        {'lat': 15.5709, 'lon': 108.0200, 'name': 'Tam Ky'},
        {'lat': 14.3545, 'lon': 108.0059, 'name': 'Kon Tum'}
    ]

    result = find_shortest_route_multi_points(start_lat, start_lon, destinations, 'car')

    if result:
        print(f"\n📊 Result:")
        print(f"  Distance: {format_distance(result['distance'])}")
        print(f"  Time: {format_time(result['time'])}")
        print(f"  Optimal order: {result['order']}")
        print(f"  Safety level: {result['safety_level']}")
        print(f"  Method: {result.get('method', 'unknown')}")

        if result['vietnam_check']['warning']:
            print(f"  {result['vietnam_check']['warning']}")

        print(f"\n  Point order:")
        print(f"    0. Da Nang (starting point)")
        for i, dest in enumerate(result['ordered_destinations'], 1):
            print(f"    {i}. {dest.get('name', f'Point {i}')}")

    # Test 3: Dangerous route (near Cambodia border)
    print("\n\n### Test 3: Route near Cambodia border ###")
    start_lat, start_lon = 10.0340, 105.7218  # Can Tho

    destinations = [
        {'lat': 10.5216, 'lon': 105.1258, 'name': 'An Giang'},
        {'lat': 10.3800, 'lon': 105.4350, 'name': 'Chau Doc'}
    ]

    result = find_shortest_route_multi_points(start_lat, start_lon, destinations, 'car')

    if result:
        print(f"\n📊 Result:")
        print(f"  Distance: {format_distance(result['distance'])}")
        print(f"  Time: {format_time(result['time'])}")
        print(f"  Optimal order: {result['order']}")
        print(f"  Safety level: {result['safety_level']}")
        print(f"  Method: {result.get('method', 'unknown')}")

        if result['vietnam_check']['warning']:
            print(f"  {result['vietnam_check']['warning']}")

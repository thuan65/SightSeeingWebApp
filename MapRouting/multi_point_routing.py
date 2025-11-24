import requests
from itertools import permutations
from vietnam_boundary import check_route_in_vietnam, is_in_vietnam

GRAPHHOPPER_API = "https://graphhopper.com/api/1/route"
API_KEY = "510b2242-84d4-45c2-97fa-baa242e6a4b7"


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

    # If there are points outside VN, may not find route
    if not all(points_in_vn):
        outside_count = len([x for x in points_in_vn if not x])
        print(f"⚠️ Warning: {outside_count}/{len(points)} points outside Vietnam")

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

            return {
                'coordinates': coordinates,
                'distance': path['distance'],
                'time': path['time'],
                'instructions': path.get('instructions', []),
                'vietnam_check': route_check
            }
        else:
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Error calling GraphHopper API: {e}")
        return None


def find_shortest_route_multi_points(start_lat, start_lon, destinations, vehicle='car', optimize=True):
    """
    Find route through multiple points (1-4 points)

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

    # If not optimizing, just find one route in order
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
            # If percentage_outside is similar, choose shorter route
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
                    f"  ✓ Permutation {perm_count}/{total_perms}: {format_distance(distance)}, {percentage_outside:.1f}% outside VN")

    if best_route:
        # Add safety assessment
        if best_route['vietnam_check']['percentage_outside'] < 3:
            best_route['safety_level'] = 'safe'
            print(f"\n✓ Safe route: {format_distance(best_route['distance'])}")
        elif best_route['vietnam_check']['percentage_outside'] < 10:
            best_route['safety_level'] = 'warning'
            print(
                f"\n⚠️ Warning route: {format_distance(best_route['distance'])}, {best_route['vietnam_check']['percentage_outside']:.1f}% outside VN")
        else:
            best_route['safety_level'] = 'danger'
            print(
                f"\n⚠️ Dangerous route: {format_distance(best_route['distance'])}, {best_route['vietnam_check']['percentage_outside']:.1f}% outside VN")

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
    print("TEST MULTI-POINT ROUTING WITH ACCURATE BOUNDARIES")
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

        if result['vietnam_check']['warning']:
            print(f"  {result['vietnam_check']['warning']}")

        print(f"\n  Point order:")
        print(f"    0. Starting point")
        for i, dest in enumerate(result['ordered_destinations'], 1):
            print(f"    {i}. {dest.get('name', f'Point {i}')}")

    # Test 2: Central region tour
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

        if result['vietnam_check']['warning']:
            print(f"  {result['vietnam_check']['warning']}")

        print(f"\n  Point order:")
        print(f"    0. Da Nang (starting point)")
        for i, dest in enumerate(result['ordered_destinations'], 1):
            print(f"    {i}. {dest.get('name', f'Point {i}')}")
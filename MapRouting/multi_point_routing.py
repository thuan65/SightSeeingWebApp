import requests
from itertools import permutations
from .vietnam_boundary import (
    check_route_in_vietnam,
    is_in_vietnam,
    get_vietnam_waypoints,
    is_route_crossing_border
)

GRAPHHOPPER_API = "https://graphhopper.com/api/1/route"
API_KEY = "510b2242-84d4-45c2-97fa-baa242e6a4b7"


def find_shortest_route_multi_points(start_lat, start_lon, destinations, vehicle='car'):
    """
    OPTIMIZED: Find optimal route through multiple points

    Strategy:
    1. Limit waypoints per segment to avoid API overload
    2. Smart selection based on segment length
    3. Maximum 2 waypoints per segment (instead of unlimited)
    """
    if not destinations:
        return None

    num_dests = len(destinations)
    indices = range(num_dests)

    best_route = None
    min_distance = float('inf')

    print(f"🔄 Optimizing route for {num_dests} destinations...")

    # Try all permutations
    for perm_idx, perm in enumerate(permutations(indices)):
        print(f"  Testing permutation {perm_idx + 1}...")

        # Build list of all points for this permutation
        api_points = []
        current_lat, current_lon = start_lat, start_lon

        # Add Start Point
        api_points.append(f"{start_lat},{start_lon}")

        total_waypoints_added = 0

        # Loop through destinations in this order
        for dest_idx in perm:
            dest = destinations[dest_idx]
            d_lat, d_lon = dest['lat'], dest['lon']

            # --- OPTIMIZED: Smart waypoint decision for each segment ---
            segment_needs_waypoints = is_route_crossing_border(
                current_lat, current_lon, d_lat, d_lon
            )

            if segment_needs_waypoints:
                # Get LIMITED waypoints (max 2 per segment)
                waypoints = get_vietnam_waypoints(
                    current_lat, current_lon,
                    d_lat, d_lon,
                    max_waypoints=2  # CRITICAL: Max 2 waypoints per segment
                )

                if waypoints:
                    for wp in waypoints:
                        api_points.append(f"{wp[0]},{wp[1]}")
                        total_waypoints_added += 1

            # Add destination point
            api_points.append(f"{d_lat},{d_lon}")

            # Update current position
            current_lat, current_lon = d_lat, d_lon

        # --- Check total point count ---
        if len(api_points) > 15:  # GraphHopper typical limit
            print(f"  ⚠️ Too many points ({len(api_points)}), skipping this permutation")
            continue

        print(f"    Points: {len(api_points)} (including {total_waypoints_added} safety waypoints)")

        # --- Call API ---
        params = {
            'point': api_points,
            'vehicle': vehicle,
            'locale': 'vi',
            'instructions': 'true',
            'calc_points': 'true',
            'points_encoded': 'false',
            'key': API_KEY
        }

        try:
            response = requests.get(GRAPHHOPPER_API, params=params, timeout=20)

            if response.status_code == 200:
                data = response.json()

                if 'paths' in data:
                    path = data['paths'][0]
                    coords = path['points']['coordinates']
                    check = check_route_in_vietnam(coords)

                    # Score: Prioritize SAFETY, then DISTANCE
                    # Heavy penalty for routes outside Vietnam
                    penalty_distance = path['distance'] + (check['percentage_outside'] * 1000000)

                    if penalty_distance < min_distance:
                        min_distance = penalty_distance
                        best_route = {
                            'coordinates': coords,
                            'distance': path['distance'],
                            'time': path['time'],
                            'instructions': path.get('instructions', []),
                            'vietnam_check': check,
                            'order': [0] + [i + 1 for i in perm],
                            'ordered_destinations': [destinations[i] for i in perm],
                            'waypoints_used': total_waypoints_added
                        }
                        print(f"    ✓ New best route found! Distance: {path['distance'] / 1000:.1f}km")
            else:
                print(f"    ❌ API error: {response.status_code}")

        except requests.exceptions.Timeout:
            print(f"    ❌ Timeout (permutation skipped)")
        except Exception as e:
            print(f"    ❌ Error: {e}")
            continue

    if best_route:
        print(f"✓ Optimization complete. Best route uses {best_route.get('waypoints_used', 0)} waypoints")
    else:
        print("❌ No valid route found")

    return best_route
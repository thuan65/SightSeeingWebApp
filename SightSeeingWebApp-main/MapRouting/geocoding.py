import requests
from urllib.parse import quote

NOMINATIM_API = "https://nominatim.openstreetmap.org/search"


def geocode_address(address):
    """
    Convert address to coordinates

    Args:
        address: Address to convert

    Returns:
        dict: {lat, lon, display_name} or None if not found
    """

    # Add "Vietnam" to address for better accuracy
    if "việt nam" not in address.lower() and "vietnam" not in address.lower():
        address = address + ", Vietnam"

    params = {
        'q': address,
        'format': 'json',
        'limit': 1,
        'countrycodes': 'vn',  # Limit to Vietnam
        'addressdetails': 1
    }

    headers = {
        'User-Agent': 'SonnaGuide/1.0'
    }

    try:
        response = requests.get(NOMINATIM_API, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()

        if data and len(data) > 0:
            result = data[0]
            return {
                'lat': float(result['lat']),
                'lon': float(result['lon']),
                'display_name': result['display_name'],
                'address': result.get('address', {})
            }
        else:
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error calling Geocoding API: {e}")
        return None


def reverse_geocode(lat, lon):
    """
    Convert coordinates to address

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        dict: Address information or None
    """

    url = "https://nominatim.openstreetmap.org/reverse"

    params = {
        'lat': lat,
        'lon': lon,
        'format': 'json',
        'addressdetails': 1
    }

    headers = {
        'User-Agent': 'SonnaGuide/1.0'
    }

    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()

        data = response.json()

        if data:
            return {
                'display_name': data['display_name'],
                'address': data.get('address', {})
            }
        else:
            return None

    except requests.exceptions.RequestException as e:
        print(f"Error calling Reverse Geocoding API: {e}")
        return None


if __name__ == "__main__":
    # Test geocoding
    test_addresses = [
        "Ben Thanh, District 1, HCMC",
        "Notre Dame Cathedral, Saigon",
        "Hoan Kiem Lake, Hanoi",
        "My Khe Beach, Da Nang"
    ]

    for address in test_addresses:
        print(f"\nAddress: {address}")
        result = geocode_address(address)
        if result:
            print(f"  Coordinates: {result['lat']}, {result['lon']}")
            print(f"  Full name: {result['display_name']}")
        else:
            print("  Not found!")

    # Test reverse geocoding
    print("\n\n=== Reverse Geocoding ===")
    result = reverse_geocode(10.7769, 106.7009)
    if result:
        print(f"Address: {result['display_name']}")
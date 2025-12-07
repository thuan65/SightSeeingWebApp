# geocoding.py
import requests
import time
import os

# Tốt nhất nên lấy từ biến môi trường, hoặc config.py
# MAPS_CO_API_KEY = os.environ.get("MAPS_CO_API_KEY", "YOUR_DEFAULT_KEY")
MAPS_CO_API_KEY = "6934fa9ead70c273351403whx21d101"


def geocode_address(address):
    if not address: return None

    url = "https://geocode.maps.co/search"

    # Xử lý từ khóa tìm kiếm
    search_query = address if "vietnam" in address.lower() else f"{address}, Vietnam"

    params = {'q': search_query, 'api_key': MAPS_CO_API_KEY}

    try:
        time.sleep(1)  # Rate limiting
        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data:
                result = data[0]
                return {
                    'lat': float(result['lat']),
                    'lon': float(result['lon']),
                    'display_name': result['display_name']
                }
    except Exception as e:
        print(f"❌ Geocoding Error: {e}")

    return None


def reverse_geocode(lat, lon):
    url = "https://geocode.maps.co/reverse"
    params = {'lat': lat, 'lon': lon, 'api_key': MAPS_CO_API_KEY}

    try:
        time.sleep(1)
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return {
                'name': data.get('display_name', ''),
                'address': data.get('address', {})
            }
    except Exception as e:
        print(f"❌ Reverse Geocoding Error: {e}")


    return None

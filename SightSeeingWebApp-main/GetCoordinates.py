import requests

# Get Place Coordinates
def get_address_coordinates(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {'q': address, 'format': 'json'}
    headers = {'User-Agent': 'PythonApp/1.0 (your_email@example.com)'}
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    if data:
        lat = float(data[0]['lat'])
        lon = float(data[0]['lon'])
        return lat, lon
    else:
        return None, None


# Get User Coordinates
TIMEOUT = 6
UA = {"User-Agent": "RouteBackend/1.0 (vdmhung@fitus.clc.edu.com)"}

def coords_by_address(address: str) -> tuple[float, float] | tuple[None, None]:
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": address, "format": "json", "limit": 1}
        r = requests.get(url, params=params, headers=UA, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if not data:
            return None, None
        return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        return None, None

def get_user_coordinates() -> tuple[float, float] | tuple[None, None]:
    try:
        ip = requests.get("https://api.ipify.org", timeout=TIMEOUT).text.strip()
        d = requests.get(f"https://ipwho.is/{ip}", timeout=TIMEOUT).json()
        if not d.get("success"):
            return None, None
        return float(d["latitude"]), float(d["longitude"])
    except Exception:
        return None, None

#Test
if __name__ == "__main__":
    # Place Coordinates
    address = "Hà Nội, Việt Nam"
    lat, lon = get_address_coordinates(address)
    print(f"Coordinates Of {address}: ({lat}, {lon})")

    # User Coordinates
    mylat, mylon = get_user_coordinates()
    print(f"Coordiantes Of User: ({mylat}, {mylon})")

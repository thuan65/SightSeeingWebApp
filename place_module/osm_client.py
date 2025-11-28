import requests

UA = {"User-Agent": "SmartSightseeing/1.0"}

def geocode_city(city: str):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": city, "format": "json", "limit": 1}

    r = requests.get(url, params=params, headers=UA)
    r.raise_for_status()
    data = r.json()

    if not data:
        return None, None

    return float(data[0]["lat"]), float(data[0]["lon"])


def fetch_osm_places(city: str, radius_km=5):
    lat, lon = geocode_city(city)
    if not lat or not lon:
        return []

    # bounding box (simple square)
    delta = radius_km / 111  # approx deg per km
    south = lat - delta
    north = lat + delta
    west  = lon - delta
    east  = lon + delta

    bbox = f"{south},{west},{north},{east}"

    overpass_url = "https://overpass-api.de/api/interpreter"

    query = f"""
    [out:json][timeout:25];
    (
      node["tourism"]({bbox});
      node["historic"]({bbox});
      node["natural"]({bbox});
      node["amenity"="restaurant"]({bbox});
      node["amenity"="museum"]({bbox});
    );
    out center;
    """

    r = requests.get(overpass_url, params={"data": query}, headers=UA)
    r.raise_for_status()
    raw = r.json().get("elements", [])

    results = []
    for p in raw:
        name = p.get("tags", {}).get("name")
        if not name:
            continue

        tags = p.get("tags", {})
        results.append({
            "name": name,
            "city": city,
            "lat": p.get("lat") or p.get("center", {}).get("lat"),
            "lon": p.get("lon") or p.get("center", {}).get("lon"),
            "tags": ", ".join(tags.keys()),
            "description": ", ".join(tags.values()),
            "rating": 0.0  
        })

    return results

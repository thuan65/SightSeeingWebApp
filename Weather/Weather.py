import requests
import json

def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,#Vĩ độ
        "longitude": lon,#Kinh độ
         "current_weather": True,
        "timezone": "Asia/Bangkok",
    }

    response = requests.get(url, params=params)
    return response.json()

data = get_weather(21.03, 105.85)  # Hà Nội

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
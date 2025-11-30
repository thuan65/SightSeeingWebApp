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

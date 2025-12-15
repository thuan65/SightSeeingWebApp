from flask import Flask, Blueprint, render_template, request, jsonify
import time
import urllib.parse
import requests, json

from models import Image
from extensions import db

weatherForecast_bp = Blueprint( "weather",__name__, template_folder= "weatheringWithYou")

@weatherForecast_bp.route("/weather/<int:place_id>")
def get_current_weather(place_id):
    lon = Image.query.with_entities(Image.longitude).filter_by(id=place_id).scalar()
    lat = Image.query.with_entities(Image.latitude).filter_by(id=place_id).scalar()
    print(f"Fetching weather for place_id={place_id}")

    if lat is None or lon is None:
        return jsonify({"error": "Failed to geocode address"}), 500
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,#Vĩ độ
        "longitude": lon,#Kinh độ
         "current_weather": True,
        "timezone": "Asia/Bangkok",
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch weather"}), 500

    data = response.json()
    print(data)
    return jsonify({
        "current_weather": data.get("current_weather", {}),
        "lat": lat,
        "lon": lon
    })

@weatherForecast_bp.route("/forecast/<int:place_id>")
def get_weather_forecast(place_id):
    place = Image.query.get(place_id)
    print(f"Fetching weather for place_id={place_id}")

    if not place:
        return jsonify({"error" : "Place not found"}), 404
    
    address = place.address

    geo = geocode_address(address)
    if not geo:
        return jsonify({"error": "Không tìm thấy tọa độ"}), 404

    lat, lon = geo['lat'], geo['lng']

    if lat is None or lon is None:
        return jsonify({"error" : "Failed to geocode the address"}), 500

   
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "timezone": "Asia/Bangkok",
    }
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch weather"}), 500

    print(response)
    data = response.json()
    return jsonify(data)



# # Get Place Coordinates
# def get_address_coordinates(address):
#     url = "https://nominatim.openstreetmap.org/search"
#     params = {'q': address, 'format': 'json'}
#     headers = {'User-Agent': 'PythonApp/1.0 (your_email@example.com)'}

#     response = requests.get(url, params=params, headers=headers)

#     if response.status_code != 200:
#         print("Error: Nominatim returned", response.status_code)
#         return None, None
    
#     if not response.text.strip():
#         print("Error: Empty response from Nominatim")
#         return None, None
    
#     try:
#         data = response.json()
#     except ValueError as e:
#         print("Error parsing JSON:", e)
#         print("Response text:", response.text)
#         return None, None

#     if data:
#         lat = float(data[0]['lat'])
#         lon = float(data[0]['lon'])
#         return lat, lon
#     else:
#         print("No data found for address:", address)
#         return None, None

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
            if data and 'lat' in data[0] and 'lon' in data[0]:
                result = data[0]
                return {
                    'lat': float(result['lat']),
                    'lng': float(result['lon']),
                    'display_name': result['display_name']
                }
        else:
            print(f" Geocoding failed, status: {response.status_code}, text: {response.text}")
    
    except Exception as e:
        print(f" Geocoding Error: {e}")

    return None


if __name__ == "__main__":
    pass
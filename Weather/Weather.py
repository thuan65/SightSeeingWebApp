from flask import Flask, render_template, request, jsonify
import requests, json

app = Flask(__name__, template_folder= "weatheringWithYou")


def get_current_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,#Vĩ độ
        "longitude": lon,#Kinh độ
         "current_weather": True,
        "timezone": "Asia/Bangkok",
    }

    response = requests.get(url, params=params)
    return response.json()

def get_weather_forecast(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "timezone": "Asia/Bangkok",
    }
    response = requests.get(url, params=params)
    return response.json()



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
    

@app.route("/")
def index():
    return render_template("weather.html")


@app.route("/weather")
def weather():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))
    data = get_current_weather(lat, lon)
    return jsonify(data)


@app.route("/forecast")
def forecast():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))
    data = get_weather_forecast(lat, lon)
    return jsonify(data)


if __name__ == "__main__":
    app.run(debug=False)
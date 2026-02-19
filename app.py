from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

API_KEY = os.environ.get("OPENWEATHER_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/weather")
def get_weather():
    city = request.args.get("city")
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    if city:
        params = {"q": city, "appid": API_KEY, "units": "metric"}
    elif lat and lon:
        params = {"lat": lat, "lon": lon, "appid": API_KEY, "units": "metric"}
    else:
        return jsonify({"error": "No location provided"}), 400

    response = requests.get(BASE_URL, params=params)
    if response.status_code != 200:
        return jsonify({"error": "City not found"}), 404

    data = response.json()
    return jsonify({
        "city": data["name"],
        "country": data["sys"]["country"],
        "temp": round(data["main"]["temp"]),
        "feels_like": round(data["main"]["feels_like"]),
        "humidity": data["main"]["humidity"],
        "description": data["weather"][0]["description"].title(),
        "icon": data["weather"][0]["icon"],
        "wind": round(data["wind"]["speed"] * 3.6),
    })

if __name__ == "__main__":
    app.run()

from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

API_KEY = os.environ.get("OPENWEATHER_API_KEY", "YOUR_API_KEY_HERE")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
GEO_URL = "http://api.openweathermap.org/geo/1.0/direct"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/cities")
def get_cities():
    q = request.args.get("q", "").strip()
    if not q or len(q) < 2:
        return jsonify([])

    params = {"q": q, "limit": 5, "appid": API_KEY}
    try:
        response = requests.get(GEO_URL, params=params, timeout=5)
    except requests.RequestException:
        return jsonify([])

    if response.status_code != 200:
        return jsonify([])

    cities = []
    seen = set()
    for item in response.json():
        key = (round(item["lat"], 3), round(item["lon"], 3))
        if key in seen:
            continue
        seen.add(key)
        cities.append({
            "name": item["name"],
            "country": item.get("country", ""),
            "state": item.get("state", ""),
            "lat": item["lat"],
            "lon": item["lon"],
        })
    return jsonify(cities)


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

    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
    except requests.RequestException:
        return jsonify({"error": "Failed to reach weather service"}), 502

    if response.status_code != 200:
        return jsonify({"error": "City not found"}), 404

    data = response.json()
    visibility_m = data.get("visibility")
    visibility_km = round(visibility_m / 1000, 1) if visibility_m is not None else None

    return jsonify({
        "city": data["name"],
        "country": data["sys"]["country"],
        "temp": round(data["main"]["temp"]),
        "feels_like": round(data["main"]["feels_like"]),
        "temp_min": round(data["main"]["temp_min"]),
        "temp_max": round(data["main"]["temp_max"]),
        "humidity": data["main"]["humidity"],
        "pressure": data["main"]["pressure"],
        "description": data["weather"][0]["description"].title(),
        "icon": data["weather"][0]["icon"],
        "wind": round(data["wind"]["speed"] * 3.6),
        "visibility": visibility_km,
    })


if __name__ == "__main__":
    app.run()

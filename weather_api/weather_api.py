from flask import Flask, jsonify, request
from functools import wraps
from datetime import datetime
import pytz
import random
import os
import json
import logging
from pathlib import Path
from api_keys import key_manager

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Single API Key from environment variable
API_KEY = os.getenv('API_KEY')
CAPITALS_JSON_PATH = os.getenv("CAPITALS_JSON_PATH")
# Sample city data

def load_cities():
    if not CAPITALS_JSON_PATH:
        raise RuntimeError("CAPITALS_JSON_PATH environment variable is not set")

    path = Path(CAPITALS_JSON_PATH)

    if not path.exists():
        raise RuntimeError(f"Cities file not found at {path}")

    with path.open(encoding="utf-8") as f:
        return json.load(f)


# Load once when app starts
CITIES = load_cities()


# Weather conditions
WEATHER_CONDITIONS = [
    {"code": 113, "description": "Sunny"},
    {"code": 116, "description": "Partly cloudy"},
    {"code": 119, "description": "Cloudy"},
    {"code": 122, "description": "Overcast"},
    {"code": 176, "description": "Patchy rain possible"},
    {"code": 296, "description": "Light rain"},
]

WIND_DIRECTIONS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", 
                   "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Only accept API key in header (secure)
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            logger.warning("Request without API key", extra={
                "ip": request.remote_addr,
                "path": request.path
            })
            return jsonify({
                "success": False,
                "error": {
                    "code": 401,
                    "type": "unauthorized",
                    "info": "Invalid or missing API key. Please provide a valid API key in the X-API-Key header."
                }
            }), 401
        
        # Validate against whitelist
        if not key_manager.is_valid(api_key):
            key_info = key_manager.get_key_info(api_key)
            logger.warning("Invalid API key attempt", extra={
                "ip": request.remote_addr,
                "key_name": key_info.get('name', 'unknown')
            })
            return jsonify({
                "success": False,
                "error": {
                    "code": 403,
                    "type": "forbidden",
                    "info": "API key not authorized"
                }
            }), 403
        
        # Log successful auth
        key_info = key_manager.get_key_info(api_key)
        logger.info("API request authorized", extra={
            "key_name": key_info.get('name'),
            "path": request.path
        })
        
        return f(*args, **kwargs)
    return decorated_function


def generate_weather_data(city_name, country=None, unit="m"):
    city_key = next(
        (k for k in CITIES.keys() if k.lower() == city_name.lower()),
        None
    )

    if city_key:
        city_data = CITIES[city_key]
        query = f"{city_key}, {city_data['country']}"
    else:
        # Default data for unknown cities
        city_data = {
            "country": country or "Unknown",
            "region": city_name,
            "lat": f"{random.uniform(-90, 90):.3f}",
            "lon": f"{random.uniform(-180, 180):.3f}",
            "timezone_id": "UTC"
        }
        if country:
            query = f"{city_name}, {country}"
    
    # Get timezone and current time
    tz = pytz.timezone(city_data['timezone_id'])
    now = datetime.now(tz)
    
    # Calculate UTC offset
    utc_offset = now.strftime('%z')
    utc_offset_hours = f"{int(utc_offset[:3])}.0"
    
    # Random weather condition
    weather = random.choice(WEATHER_CONDITIONS)
    
    # Generate data
    data = {
        "request": {
            "type": "City",
            "query": query,
            "language": "en",
            "unit": unit
        },
        "location": {
            "name": city_name,
            "country": city_data["country"],
            "region": city_data["region"],
            "lat": city_data["lat"],
            "lon": city_data["lon"],
            "timezone_id": city_data["timezone_id"],
            "localtime": now.strftime("%Y-%m-%d %H:%M"),
            "localtime_epoch": int(now.timestamp()),
            "utc_offset": utc_offset_hours
        },
        "current": {
            "observation_time": now.strftime("%I:%M %p"),
            "temperature": random.randint(-10, 35),
            "weather_code": weather["code"],
            "weather_descriptions": [
                weather["description"]
            ],
            "air_quality": {
                "co": f"{random.uniform(200, 600):.2f}",
                "no2": f"{random.uniform(10, 50):.3f}",
                "o3": f"{random.randint(30, 80)}",
                "so2": f"{random.uniform(1, 15):.1f}",
                "pm2_5": f"{random.uniform(1, 25):.2f}",
                "pm10": f"{random.uniform(1, 25):.2f}",
                "us-epa-index": str(random.randint(1, 6)),
                "gb-defra-index": str(random.randint(1, 10))
            },
            "wind_speed": random.randint(0, 50),
            "wind_degree": random.randint(0, 359),
            "wind_dir": random.choice(WIND_DIRECTIONS),
            "pressure": random.randint(980, 1040),
            "precip": random.randint(0, 20),
            "humidity": random.randint(30, 100),
            "cloudcover": random.randint(0, 100),
            "feelslike": random.randint(-10, 35),
            "uv_index": random.randint(1, 11),
            "visibility": random.randint(1, 20)
        }
    }
    
    return data

@app.route('/weather', methods=['GET'])
@require_api_key
def get_weather():
    """
    Get weather data for a city
    Query parameters:
    - city: City name (required)
    - country: Country name (optional)
    - unit: Unit system - 'm' for metric, 'f' for imperial (default: 'm')
    
    Example: /weather?city=New York&country=United States of America&unit=m
    """
    city = request.args.get('city')
    country = request.args.get('country')
    unit = request.args.get('unit', 'm')
    
    if not city:
        return jsonify({"error": "City parameter is required"}), 400
    
    weather_data = generate_weather_data(city, country, unit)
    return jsonify(weather_data)

@app.route('/weather/<city_name>', methods=['GET'])
@require_api_key
def get_weather_by_path(city_name):
    """
    Get weather data for a city using path parameter
    Query parameters:
    - country: Country name (optional)
    - unit: Unit system (default: 'm')
    
    Example: /weather/London?unit=m
    """
    country = request.args.get('country')
    unit = request.args.get('unit', 'm')
    
    weather_data = generate_weather_data(city_name, country, unit)
    return jsonify(weather_data)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint (no authentication required)"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/', methods=['GET'])
def home():
    """API documentation"""
    return jsonify({
        "message": "Weather Data API",
        "authentication": "API key required - use X-API-Key header or api_key query parameter",
        "endpoints": {
            "GET /weather": {
                "description": "Get weather data by query parameters",
                "authentication": "Required",
                "parameters": {
                    "city": "City name (required)",
                    "country": "Country name (optional)",
                    "unit": "Unit system: 'm' or 'f' (default: 'm')"
                },
                "example": "/weather?city=New York&country=United States of America"
            },
            "GET /weather/<city_name>": {
                "description": "Get weather data by path parameter",
                "authentication": "Required",
                "parameters": {
                    "country": "Country name (optional)",
                    "unit": "Unit system: 'm' or 'f' (default: 'm')"
                },
                "example": "/weather/London?unit=m"
            },
            "GET /health": {
                "description": "Health check endpoint",
                "authentication": "Not required"
            }
        },
        "available_cities": list(CITIES.keys())
    })

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
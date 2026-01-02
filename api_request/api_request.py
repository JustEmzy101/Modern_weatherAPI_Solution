import requests
import os
from dotenv import load_dotenv
import logging
load_dotenv()
logger = logging.getLogger(__name__)
def fetch_data():
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        raise ValueError("WEATHER_API_KEY not set in environment")
    
    api_url = "http://weather-api:5000/weather?city=London"
    headers = {"X-API-Key": api_key}
    
    try:
        response = requests.get(
            api_url,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}", exc_info=True)
        raise

def mock_fetch_data():
    
    return {'request': {'type': 'City', 'query': 'New York, United States of America', 'language': 'en', 'unit': 'm'}, 'location': {'name': 'New York', 'country': 'United States of America', 'region': 'New York', 'lat': '40.714', 'lon': '-74.006', 'timezone_id': 'America/New_York', 'localtime': '2025-12-03 02:24', 'localtime_epoch': 1764728640, 'utc_offset': '-5.0'}, 'current': {'observation_time': '07:24 AM', 'temperature': 2, 'weather_code': 116, 'weather_icons': ['https://cdn.worldweatheronline.com/images/wsymbols01_png_64/wsymbol_0004_black_low_cloud.png'], 'weather_descriptions': ['Partly cloudy'], 'astro': {'sunrise': '07:03 AM', 'sunset': '04:29 PM', 'moonrise': '03:05 PM', 'moonset': '05:30 AM', 'moon_phase': 'Waxing Gibbous', 'moon_illumination': 94}, 'air_quality': {'co': '227.85', 'no2': '24.95', 'o3': '41', 'so2': '5.45', 'pm2_5': '4.85', 'pm10': '4.85', 'us-epa-index': '1', 'gb-defra-index': '1'}, 'wind_speed': 23, 'wind_degree': 320, 'wind_dir': 'NW', 'pressure': 1010, 'precip': 0, 'humidity': 69, 'cloudcover': 50, 'feelslike': -3, 'uv_index': 0, 'visibility': 16, 'is_day': 'no'}}

fetch_data()
# mock_fetch_data()
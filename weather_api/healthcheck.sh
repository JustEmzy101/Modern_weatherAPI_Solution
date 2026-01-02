#!/bin/bash
python -c "
import urllib.request
import json
import os
try:
    api_key = os.getenv('WEATHER_API_KEY', '')
    req = urllib.request.Request('http://127.0.0.1:5000/weather?city=London', headers={'X-API-Key': api_key})
    urllib.request.urlopen(req)
    exit(0)
except:
    exit(1)
"

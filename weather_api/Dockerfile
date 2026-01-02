FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements_api.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements_api.txt

# Copy application code and configuration
COPY weather_api.py .
COPY api_keys.py .
COPY api_keys_config.json .
COPY full_world_capitals_plus_egypt.json .
COPY healthcheck.sh .
RUN chmod +x healthcheck.sh

# Expose port
EXPOSE 5000

# Set environment variables (non-secret)
ENV FLASK_APP=weather_api.py
ENV PYTHONUNBUFFERED=1
ENV API_KEYS_CONFIG=/app/api_keys_config.json
# Secrets (API_KEY, CAPITALS_JSON_PATH) provided by docker-compose

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --retries=5 --start-period=30s \
  CMD /app/healthcheck.sh


# Run the application
CMD ["python", "weather_api.py"]
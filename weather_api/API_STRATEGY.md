# Weather API - API Key Management Strategy

## Overview

The Weather API implements a secure, whitelisted API key strategy that allows:
- ✅ Multiple API keys per environment
- ✅ Instant key revocation (no rebuild needed)
- ✅ Key expiration scheduling
- ✅ Rate limiting configuration
- ✅ Key metadata and audit logging

## Architecture

```
┌─────────────────────────────────┐
│   docker-compose.yaml           │
│  (Provides API_KEY, CONFIG)     │
└──────────────┬──────────────────┘
               │
       ┌───────▼────────┐
       │ Weather API    │
       │ Container      │
       └────────────────┘
               │
       ┌───────▼──────────────────┐
       │ weather_api.py           │
       │ - Imports api_keys.py    │
       │ - Uses APIKeyManager     │
       └────────────┬─────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
    ┌────▼──────────┐  ┌──────▼─────────┐
    │ api_keys.py   │  │ api_keys_config│
    │ (Manager)     │  │     .json      │
    └───────────────┘  └────────────────┘
```

## Files

### 1. `api_keys.py`
The API key manager that validates keys against a whitelist.

**Features:**
- Load keys from JSON config
- Check if key is active
- Verify key hasn't expired
- Get key metadata (name, rate limit, etc.)

**Usage:**
```python
from api_keys import key_manager

# Check if key is valid
if key_manager.is_valid(api_key):
    # Allow request
    pass

# Get key info
key_info = key_manager.get_key_info(api_key)
print(key_info['name'])  # 'production-key'
```

### 2. `api_keys_config.json`
Configuration file with whitelisted API keys.

**Structure:**
```json
{
  "actual-key-string": {
    "name": "production-key",
    "active": true,
    "created_at": "2025-12-01T00:00:00",
    "expires_at": "2026-12-01T00:00:00",
    "rate_limit": 1000,
    "description": "Main production API key"
  }
}
```

**Key Fields:**
- `name` - Human-readable key name
- `active` - Enable/disable instantly
- `expires_at` - ISO format datetime (auto-revokes)
- `rate_limit` - Requests per minute (for future use)
- `description` - Documentation

## Workflow

### Adding a New API Key

1. **Generate new key:**
   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Add to `api_keys_config.json`:**
   ```json
   {
     "new-key-abc123def456": {
       "name": "staging-key",
       "active": true,
       "created_at": "2025-12-21T00:00:00",
       "expires_at": "2026-06-21T00:00:00",
       "rate_limit": 500,
       "description": "Staging environment key"
     }
   }
   ```

3. **No Docker rebuild needed!** Config is mounted as a volume:
   ```yaml
   volumes:
     - ./weather_api/api_keys_config.json:/app/api_keys_config.json
   ```

4. **Container reloads config on restart:**
   ```bash
   docker-compose restart weather-api
   ```

### Revoking an API Key

Two methods:

**Method 1: Instant (set active=false)**
```json
{
  "compromised-key-xyz": {
    "active": false,  // ← Set to false
    "name": "compromised"
  }
}
```

**Method 2: Scheduled (set expires_at to past)**
```json
{
  "deprecated-key": {
    "expires_at": "2025-12-20T00:00:00"  // ← Already expired
  }
}
```

Then restart:
```bash
docker-compose restart weather-api
```

### Authentication Flow

1. **Client sends request:**
   ```bash
   curl -H "X-API-Key: your-api-key" http://weather-api:5000/weather?city=London
   ```

2. **Server validates:**
   - Extract key from `X-API-Key` header
   - Check if key exists in whitelist
   - Check if key is active
   - Check if key hasn't expired
   - Log the attempt

3. **Response:**
   ```json
   // Success (200)
   {
     "location": {...},
     "current": {...}
   }
   
   // Unauthorized (401)
   {
     "error": {
       "code": 401,
       "type": "unauthorized",
       "info": "Invalid or missing API key"
     }
   }
   
   // Forbidden (403)
   {
     "error": {
       "code": 403,
       "type": "forbidden",
       "info": "API key not authorized"
     }
   }
   ```

## Docker Configuration

### Dockerfile
```dockerfile
# Copy config files
COPY api_keys.py .
COPY api_keys_config.json .

# Set path to config (from docker-compose)
ENV API_KEYS_CONFIG=/app/api_keys_config.json
```

### docker-compose.yaml
```yaml
weather-api:
  environment:
    API_KEY: ${WEATHER_API_KEY}  # For fallback (if needed)
    CAPITALS_JSON_PATH: ${CAPITALS_JSON_PATH:-/app/full_world_capitals_plus_egypt.json}
    API_KEYS_CONFIG: ${API_KEYS_CONFIG:-/app/api_keys_config.json}
    PYTHONUNBUFFERED: 1
  volumes:
    - ./weather_api/api_keys_config.json:/app/api_keys_config.json
```

### .env Configuration
```dotenv
WEATHER_API_KEY=5b7eae5a12f272dbba969b1e40916bbe
API_KEYS_CONFIG=/app/api_keys_config.json
```

## Environment-Specific Setup

### Development
```json
{
  "dev-key-12345": {
    "name": "dev-key",
    "active": true,
    "expires_at": "2025-12-31T00:00:00",
    "rate_limit": 10
  },
  "testing-key-67890": {
    "name": "testing-key",
    "active": true,
    "expires_at": "2025-12-31T00:00:00",
    "rate_limit": 100
  }
}
```

### Production
```json
{
  "prod-key-main": {
    "name": "production-primary",
    "active": true,
    "expires_at": "2026-12-21T00:00:00",
    "rate_limit": 10000
  },
  "prod-key-backup": {
    "name": "production-backup",
    "active": true,
    "expires_at": "2026-12-21T00:00:00",
    "rate_limit": 10000
  }
}
```

## Logging

All authentication attempts are logged with details:

```python
logger.info("API request authorized", extra={
    "key_name": "production-key",
    "path": "/weather",
    "ip": "192.168.1.100"
})

logger.warning("Invalid API key attempt", extra={
    "ip": "192.168.1.100",
    "key_name": "unknown"
})
```

## Security Best Practices

1. ✅ **Never put real API keys in code** - Use environment variables
2. ✅ **Keep config file out of git** - Add to `.gitignore`
3. ✅ **Rotate keys regularly** - Set expiration dates
4. ✅ **Use HTTPS in production** - Prevents key interception
5. ✅ **Only accept headers** - No API keys in URLs
6. ✅ **Log all attempts** - Audit trail for security
7. ✅ **Use strong random keys** - `secrets.token_urlsafe(32)`

## Troubleshooting

### Key not working
1. Check if key exists in `api_keys_config.json`
2. Check if `active: true`
3. Check if expiration date hasn't passed
4. Verify Docker config mounted the file correctly

### Config changes not taking effect
1. Restart the container: `docker-compose restart weather-api`
2. Check if volume mount is correct
3. Verify config JSON syntax is valid

### Health check failing
- Ensure API_KEY is set in .env
- Check container logs: `docker-compose logs weather-api`
- Verify Flask app is listening on 0.0.0.0:5000


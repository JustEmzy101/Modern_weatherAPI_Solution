# Quick Start Guide

Get the Weather Data Project running in 5 minutes.

## Prerequisites

```bash
# Verify installations
docker --version  # 20.10+
docker-compose --version  # 2.0+
```

## One-Time Setup

```bash
# 1. Clone
git clone <repo-url>
cd Weather_data_project

# 2. Run setup script
./setup.sh

# 3. Edit configuration (CRITICAL!)
nano .env
# Set: HOST_PROJECT_ROOT=/full/path/to/Weather_data_project
# Set: Strong passwords for DB_PASSWORD, AIRFLOW_DB_PASSWORD

nano docker/.env
# Set: Strong passwords for DATABASE_PASSWORD, POSTGRES_PASSWORD
```

## Start

```bash
docker-compose --env-file .env up -d
sleep 60  # Wait for services to initialize

# Verify
docker-compose ps  # All services should be "Up"
```

## Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **Airflow** | http://localhost:8080 | admin:admin |
| **Superset** | http://localhost:8088 | Check docker/.env |
| **Weather API** | http://localhost:5000 | API key required |
| **PostgreSQL** | localhost:5430 | Check .env |

## Test API

```bash
curl -H "X-API-Key: 5b7eae5a12f272dbba969b1e40916bbe" \
     http://localhost:5000/weather?city=London | jq
```

## View Data

```bash
# Connect to database
docker-compose exec -T db psql -U weather_user -d weather_db

# Check tables
SELECT COUNT(*) FROM raw_weather_data;
SELECT COUNT(*) FROM dev.stg_weather;
```

## View Pipeline

1. Open Airflow: http://localhost:8080
2. Find DAG: `weatherAPI_dbt_orchestrator`
3. Check task execution every 15 minutes

## Stop Services

```bash
docker-compose down
```

## Common Issues

### Issue: "HOST_PROJECT_ROOT not set"
```bash
# Check .env
cat .env | grep HOST_PROJECT_ROOT

# Must not be empty! Set it:
nano .env
# HOST_PROJECT_ROOT=/home/user/repos/Weather_data_project
```

### Issue: "Cannot connect to database"
```bash
# Wait longer for startup
sleep 60
docker-compose ps

# Check DB logs
docker-compose logs db | tail -20
```

### Issue: "Port 5000 already in use"
```bash
# Find what's using it
lsof -i :5000

# Or use different port in docker-compose.yaml
```

## Full Documentation

- **README.md** - Complete guide
- **DEPENDENCIES.md** - Architecture & dependencies
- **SETUP.md** - Detailed setup instructions

---

**Tip:** Run `docker-compose logs -f` in another terminal to watch real-time logs while testing!

# Setup Guide - Environment Configuration

## Quick Start

### 1. Initial Setup
```bash
# Navigate to project directory
cd /home/marwan/repos/Weather_data_project

# Copy the environment template
cp .env.example .env

# Edit .env with your actual values
nano .env
```

### 2. Required Environment Variables

**Database Credentials:**
```dotenv
DB_USER=weather_user                           # PostgreSQL user
DB_PASSWORD=your-secure-password-here          # PostgreSQL password (must set!)
DB_NAME=weather_db                             # Database name
```

**Airflow Database:**
```dotenv
AIRFLOW_DB_USER=airflow                        # Airflow's database user
AIRFLOW_DB_PASSWORD=your-secure-airflow-pass   # Airflow DB password (must set!)
AIRFLOW_DB_NAME=airflow_db                     # Airflow database name
```

**Weather API:**
```dotenv
WEATHER_API_KEY=5b7eae5a12f272dbba969b1e40916bbe    # Your API key
CAPITALS_JSON_PATH=/app/full_world_capitals_plus_egypt.json
```

**Project Path:**
```dotenv
PROJECT_ROOT=/opt/airflow/project    # Path inside Airflow container (usually /opt/airflow/project)
```

### 3. Generate Secure Passwords

Use Python to generate random passwords:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Or use OpenSSL:
```bash
openssl rand -base64 32
```

### 4. Start Services

```bash
# Using docker-compose with .env file
docker-compose --env-file .env up -d

# Or if docker-compose reads .env automatically
docker-compose up -d
```

### 5. Verify Setup

```bash
# Check services are running
docker-compose ps

# Check logs
docker-compose logs -f af  # Airflow logs
docker-compose logs -f db  # Database logs
docker-compose logs -f weather-api  # Weather API logs
```

---

## Environment Variables by Component

### Airflow Container
Receives these variables:
- `PROJECT_ROOT` - Path to project
- `DB_USER`, `DB_PASSWORD`, `DB_NAME` - Weather DB credentials
- `AIRFLOW_DB_USER`, `AIRFLOW_DB_PASSWORD`, `AIRFLOW_DB_NAME` - Airflow DB credentials

### Database Container
Receives these variables:
- `POSTGRES_USER` - Default user
- `POSTGRES_PASSWORD` - Default user password
- `POSTGRES_DB` - Default database name

### Weather API Container
Receives these variables:
- `API_KEY` - Authentication key
- `CAPITALS_JSON_PATH` - Path to cities data file
- `PYTHONUNBUFFERED` - Python output buffering

---

## Development vs Production

### Development (.env)
```dotenv
PROJECT_ROOT=/opt/airflow/project
DB_PASSWORD=dev-password-123
WEATHER_API_KEY=dev-key-xyz
LOG_LEVEL=DEBUG
```

### Production (.env.prod)
```dotenv
PROJECT_ROOT=/opt/airflow/project
DB_PASSWORD=<random-secure-password>
WEATHER_API_KEY=<secure-production-key>
LOG_LEVEL=INFO
AIRFLOW_DB_PASSWORD=<random-secure-password>
```

---

## Troubleshooting

### Error: "PROJECT_ROOT environment variable not set"
- Make sure `.env` file exists
- Verify `PROJECT_ROOT` is defined in `.env`
- Ensure docker-compose uses `.env` file

### Error: "Connection refused" (Airflow to DB)
- Check database is running: `docker-compose ps`
- Verify `DB_PASSWORD` matches in `.env`
- Check database logs: `docker-compose logs db`

### Error: "Invalid API key"
- Ensure `WEATHER_API_KEY` is set in `.env`
- Verify it matches in docker-compose output
- Check weather API logs: `docker-compose logs weather-api`

### Paths not found in Airflow DAG
- Verify `PROJECT_ROOT` points to correct path
- Ensure dbt folder exists in that path
- Check Airflow logs: `docker-compose logs af`

---

## Security Checklist

- [ ] `.env` file created (not committed)
- [ ] All `DB_PASSWORD` values are unique and strong
- [ ] `WEATHER_API_KEY` is kept secret
- [ ] `.env` file has restricted permissions: `chmod 600 .env`
- [ ] Never share `.env` file in version control
- [ ] Use `.env.example` for documentation instead

---

## Command Examples

```bash
# Start all services
docker-compose --env-file .env up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f  # All logs
docker-compose logs -f af  # Airflow only
docker-compose logs -f db  # Database only

# Rebuild images
docker-compose --env-file .env build

# Remove everything (WARNING: deletes data!)
docker-compose down -v
```

---

## Next Steps

After successful startup:

1. Access Airflow UI: http://localhost:8080
2. Access Superset UI: http://localhost:8088
3. Verify weather API: `curl -H "X-API-Key: <your-key>" http://localhost:5000/weather?city=London`
4. Check database connection: `psql -h localhost -U weather_user -d weather_db`


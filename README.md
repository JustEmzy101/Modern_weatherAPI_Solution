# Weather Data Project

A production-grade data pipeline that fetches real-time weather data, transforms it using dbt, validates data quality with Soda, and visualizes insights in Apache Superset. All orchestrated by Apache Airflow.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA PIPELINE FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Weather API    →    PostgreSQL    →    dbt Transform    →     │
│  (Mock Service)     (Raw Data)     (Staging + Mart)           │
│                                                                 │
│         ↓ (Every 15 minutes via Airflow DAG)                   │
│                                                                 │
│  Soda Data Quality Checks  →  Apache Superset (BI)             │
│  (Validate + Monitor)         (Dashboards)                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Components

| Component | Purpose | Port | Technology |
|-----------|---------|------|-----------|
| **weather-api** | Mock weather data provider | 5000 | Flask + Python |
| **PostgreSQL** | Data warehouse | 5430 | PostgreSQL 17 |
| **Airflow** | Workflow orchestration | 8080 | Apache Airflow 3.1.3 |
| **dbt** | Data transformation | - | dbt 1.7.0 |
| **Soda** | Data quality validation | - | Soda Core |
| **Superset** | BI & visualization | 8088 | Apache Superset 3.0.0 |
| **Redis** | Caching layer | 6379 | Redis 7 |

## 📋 Prerequisites

- **Docker:** Version 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose:** Version 2.0+ ([Install Docker Compose](https://docs.docker.com/compose/install/))
- **Git:** For cloning the repository
- **Available Ports:** 5000, 5430, 8080, 8088, 6379 (check with `netstat` or `lsof`)
- **Disk Space:** At least 5GB for Docker images and data

### Verify Installation

```bash
docker --version
docker-compose --version
```

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Weather_data_project
```

### 2. Run Setup Script

```bash
./setup.sh
```

This will:
- Create `.env` from template
- Create `docker/.env` from template
- Guide you through configuration

### 3. Configure Environment Variables

Edit `.env` with your values:

```bash
nano .env
```

**Critical settings to update:**

```dotenv
# Set this to your project directory path (REQUIRED!)
HOST_PROJECT_ROOT=/path/to/Weather_data_project

# Use strong passwords in production
DB_PASSWORD=your-secure-password
AIRFLOW_DB_PASSWORD=your-secure-airflow-password
```

Also edit `docker/.env`:

```bash
nano docker/.env
```

Update database passwords:

```dotenv
DATABASE_PASSWORD=your-secure-password
POSTGRES_PASSWORD=your-secure-password
```

### 4. Start Services

```bash
docker-compose --env-file .env up -d
```

Monitor startup:

```bash
docker-compose logs -f
```

Wait for all services to be healthy (~60 seconds):

```bash
docker-compose ps
```

All services should show `Up` status.

### 5. Access Services

Once all services are healthy:

- **Airflow UI:** http://localhost:8080
  - Default login: `admin:admin` (set by Airflow)
  - Navigate to DAGs → `weatherAPI_dbt_orchestrator`

- **Superset:** http://localhost:8088
  - Default login: Check `docker/.env` for credentials
  - Add PostgreSQL data source: `postgresql://weather_user:PASSWORD@db:5432/weather_db`

- **Weather API:** http://localhost:5000/weather?city=London
  - Requires `X-API-Key` header (see API section below)

- **PostgreSQL:** 
  ```bash
  psql -h localhost -p 5430 -U weather_user -d weather_db
  ```

## 📚 Configuration Guide

### Environment Variables

#### Root `.env` File

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HOST_PROJECT_ROOT` | ✅ Yes | - | Absolute path to project on host machine |
| `DB_USER` | ❌ No | `weather_user` | Database username |
| `DB_PASSWORD` | ✅ Yes | - | Database password (strong!) |
| `DB_NAME` | ❌ No | `weather_db` | Database name |
| `AIRFLOW_DB_PASSWORD` | ✅ Yes | - | Airflow database password |
| `WEATHER_API_KEY` | ❌ No | - | API key for authentication |
| `DBT_DB_PASSWORD` | ✅ Yes | - | dbt connection password |

#### Docker `.env` File

| Variable | Purpose |
|----------|---------|
| `DATABASE_PASSWORD` | Superset database password |
| `POSTGRES_PASSWORD` | PostgreSQL root password |
| `SUPERSET_SECRET_KEY` | Superset session secret (use strong random value) |

### Platform-Specific Setup

<details>
<summary><b>🐧 Linux</b></summary>

```bash
# Set HOST_PROJECT_ROOT
HOST_PROJECT_ROOT=$(pwd)

# Edit .env and set it
sed -i "s|^HOST_PROJECT_ROOT=.*|HOST_PROJECT_ROOT=$HOST_PROJECT_ROOT|" .env

# Start
docker-compose --env-file .env up -d
```

</details>

<details>
<summary><b>🍎 macOS</b></summary>

```bash
# Set HOST_PROJECT_ROOT
HOST_PROJECT_ROOT=$(pwd)

# Edit .env using nano or vim
nano .env
# Change: HOST_PROJECT_ROOT=/path/to/Weather_data_project

# Start
docker-compose --env-file .env up -d
```

</details>

<details>
<summary><b>🪟 Windows (PowerShell)</b></summary>

```powershell
# Get full path
$projectPath = (Get-Location).Path
Write-Host "Set HOST_PROJECT_ROOT to: $projectPath"

# Edit .env with notepad
notepad .env
# Change: HOST_PROJECT_ROOT=C:\path\to\Weather_data_project

# Start
docker-compose --env-file .env up -d
```

</details>

## 🔌 API Documentation

### Weather API

Base URL: `http://localhost:5000`

#### Get Weather Data

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
     "http://localhost:5000/weather?city=London"
```

**Response:**
```json
{
  "current": {
    "temperature": 15,
    "weather_descriptions": ["Partly cloudy"],
    "humidity": 65,
    "wind_speed": 12,
    ...
  },
  "location": {
    "name": "London",
    "country": "United Kingdom",
    "lat": "51.509",
    "lon": "-0.128"
  }
}
```

**Parameters:**
- `city` (required): City name
- `X-API-Key` header (required): Valid API key

**Authentication:**
- Uses header-based API key (secure, won't appear in logs/URLs)
- API keys configured in `weather_api/api_keys_config.json`
- Each key has expiration date and active status

## 🔄 Data Pipeline

### Airflow DAG: `weatherAPI_dbt_orchestrator`

Runs every 15 minutes with three tasks:

```
Task 1: pull_push_to_db (PythonOperator)
  ↓
  └─→ Fetches weather data from API
  └─→ Inserts into PostgreSQL raw table
  └─→ Implements retry logic & connection pooling

Task 2: dbt_run (DockerOperator)
  ↓
  └─→ Transforms raw data to staging
  └─→ Creates dimensional models (SCD2 tracking)
  └─→ Generates mart tables for BI

Task 3: soda_scan (DockerOperator)
  ↓
  └─→ Validates data quality
  └─→ Checks for nulls, freshness, duplicates
  └─→ Monitors data integrity
```

### Database Schema

```
Raw Layer (Ingestion):
  - raw_weather_data (auto-created by Airflow task)

Staging Layer (dbt):
  - stg_weather (cleaned and deduplicated)
  - stg_weather_SCD2 (SCD2 history tracking)

Mart Layer (BI):
  - dim_weather_scd2 (dimension table)
  - weather_report (fact table for dashboards)
```

### dbt Models

Located in `dbt/my_project/models/`:

- **staging/stg_weather.sql** - Cleans raw data
- **mart/dim_weather_scd2.sql** - SCD2 dimension (history tracking)
- **mart/weather_report.sql** - Fact table for Superset

Run dbt locally:

```bash
dbt run --profiles-dir dbt
dbt test --profiles-dir dbt
dbt docs generate --profiles-dir dbt
```

## 🧪 Testing & Validation

### Check Data Pipeline

```bash
# View Airflow DAG runs
docker-compose logs airflow | grep "weatherAPI_dbt_orchestrator"

# Check database data
docker-compose exec -T db psql -U weather_user -d weather_db \
  -c "SELECT COUNT(*) FROM dev.stg_weather;"

# Verify dbt models
docker-compose logs dbt | grep "model"

# Check Soda validation
docker-compose logs soda-core | grep "failed\|passed"
```

### Manual API Test

```bash
# Test weather API
curl -H "X-API-Key: 5b7eae5a12f272dbba969b1e40916bbe" \
     "http://localhost:5000/weather?city=Paris" | jq

# Test with different city
curl -H "X-API-Key: 5b7eae5a12f272dbba969b1e40916bbe" \
     "http://localhost:5000/weather?city=Tokyo" | jq
```

### Database Verification

```bash
# Connect to database
docker-compose exec -T db psql -U weather_user -d weather_db

# Check raw data
SELECT COUNT(*) FROM raw_weather_data;
SELECT DISTINCT city FROM raw_weather_data;

# Check staged data
SELECT COUNT(*) FROM dev.stg_weather;

# Check dimensions
SELECT COUNT(*) FROM dev.dim_weather_scd2;

# View latest weather
SELECT city, temperature, weather_descriptions, inserted_at 
FROM dev.stg_weather 
ORDER BY inserted_at DESC LIMIT 10;
```

## 📊 Dashboards

### Creating a Superset Dashboard

1. **Add Database Connection:**
   - Superset UI → Settings → Database Connections
   - Click "+ DATABASE"
   - Engine: `PostgreSQL`
   - Connection string: `postgresql://weather_user:PASSWORD@db:5432/weather_db`

2. **Add Datasets:**
   - Click "+ DATASET"
   - Select tables: `stg_weather`, `dim_weather_scd2`, `weather_report`

3. **Create Dashboard:**
   - Click "+ DASHBOARD"
   - Add charts showing:
     - Temperature trends by city
     - Weather conditions distribution
     - Humidity vs pressure
     - Data freshness (latest updates)

## 🛠️ Troubleshooting

### Issue: DAG fails with "HOST_PROJECT_ROOT not set"

**Cause:** Environment variable not properly set
**Solution:**
```bash
# Verify in .env
grep HOST_PROJECT_ROOT .env

# Restart with env file
docker-compose down
docker-compose --env-file .env up -d
```

### Issue: Cannot connect to database

**Cause:** Database not fully initialized
**Solution:**
```bash
# Wait longer for database startup
sleep 60
docker-compose ps

# Check database logs
docker-compose logs db | tail -50
```

### Issue: dbt models failed to run

**Cause:** Usually profiles.yml not properly configured
**Solution:**
```bash
# Verify dbt profiles
cat dbt/profiles.yml

# Check dbt logs
docker-compose logs dbt

# Restart dbt service
docker-compose restart dbt
```

### Issue: Superset can't reach database

**Cause:** Database credentials incorrect
**Solution:**
```bash
# Test connection from Superset container
docker-compose exec superset psql -h db -U weather_user -d weather_db

# Check docker/.env has correct password
grep DATABASE_PASSWORD docker/.env
```

### Issue: "port already in use" error

**Cause:** Another service is using the port
**Solution:**
```bash
# Find what's using the port
lsof -i :5000   # weather-api
lsof -i :8080   # Airflow
lsof -i :8088   # Superset
lsof -i :5430   # PostgreSQL

# Kill the process or use different port
docker-compose down  # Clean shutdown
```

### Issue: Out of disk space

**Cause:** Docker images and data taking too much space
**Solution:**
```bash
# Clean up old Docker data
docker system prune -a

# Remove volumes (WARNING: deletes data!)
docker-compose down -v
```

### View Detailed Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f airflow
docker-compose logs -f weather-api
docker-compose logs -f db

# Last N lines
docker-compose logs --tail=100 airflow
```

## 📦 Maintenance

### Stopping Services

```bash
# Graceful shutdown
docker-compose down

# With volume cleanup (WARNING: deletes data!)
docker-compose down -v
```

### Restarting Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart airflow
docker-compose restart db
```

### Upgrading Versions

Update versions in `docker-compose.yaml`:

```yaml
# Edit service image versions
image: apache/airflow:3.1.3  # Change version
image: postgres:17           # Change version
```

Then rebuild:

```bash
docker-compose build --no-cache
docker-compose up -d
```

### Backing Up Data

```bash
# Backup PostgreSQL database
docker-compose exec -T db pg_dump -U weather_user weather_db > backup.sql

# Restore from backup
docker-compose exec -T db psql -U weather_user weather_db < backup.sql
```

## 🔒 Security Considerations

### For Development

This setup is configured for **development**. For production:

1. **Change all default passwords** in `.env` and `docker/.env`
2. **Use strong secrets:**
   ```bash
   openssl rand -base64 32  # Generate strong password
   ```
3. **Enable HTTPS** with reverse proxy (nginx/Traefik)
4. **Use secrets management** (AWS Secrets Manager, HashiCorp Vault)
5. **Set `SUPERSET_ENV=production`** in docker/.env
6. **Disable DEV_MODE** in docker/.env
7. **Implement authentication** (LDAP, OAuth2, SAML)
8. **Network isolation** - Don't expose database ports publicly
9. **Regular backups** of PostgreSQL data
10. **Monitor logs** for security issues

## 📚 Additional Resources

- **Airflow Docs:** https://airflow.apache.org/
- **dbt Documentation:** https://docs.getdbt.com/
- **Superset Docs:** https://superset.apache.org/
- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **Soda Docs:** https://docs.soda.io/

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 Project Structure

```
Weather_data_project/
├── airflow/                    # Airflow DAGs and plugins
│   └── dags/
│       └── dbt_orchestrator.py # Main orchestration DAG
├── api_request/                # Python ETL task
│   ├── api_request.py         # API client
│   └── insert_records.py       # Database insert logic
├── dbt/                        # dbt transformation project
│   ├── profiles.yml           # dbt database config
│   └── my_project/
│       ├── models/            # SQL transformation models
│       ├── tests/             # dbt tests
│       └── seeds/             # seed data
├── weather_api/               # Flask weather API service
│   ├── weather_api.py        # API application
│   ├── api_keys.py           # API key management
│   ├── api_keys_config.json  # API key whitelist
│   └── Dockerfile            # Container definition
├── postgres/                  # PostgreSQL initialization
│   ├── airflow_init.sql      # Create Airflow schema
│   └── superset_init.sql     # Create Superset schema
├── soda/                      # Data quality checks
│   ├── configuration.yml     # Soda config
│   └── checks/
│       └── weather_checks.yaml # Quality rules
├── docker/                    # Superset configuration
│   ├── docker-bootstrap.sh   # Superset startup
│   ├── docker-init.sh        # Superset initialization
│   └── superset_config.py    # Superset settings
├── docker-compose.yaml        # Service orchestration
├── .env.example              # Environment template
├── setup.sh                  # Setup script
└── README.md                 # This file
```

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 🐛 Support

For issues or questions:
1. Check [Troubleshooting](#-troubleshooting) section
2. Review logs: `docker-compose logs -f`
3. Check `.env` configuration
4. Verify prerequisites are installed

---

**Last Updated:** December 25, 2025  
**Status:** Production-Ready ✅

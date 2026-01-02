# Project Dependencies & Architecture

## Overview

This document explains the dependencies, requirements, and architecture of the Weather Data Project.

## System Requirements

### Docker & Containerization

| Component | Version | Purpose |
|-----------|---------|---------|
| **Docker** | 20.10+ | Container runtime |
| **Docker Compose** | 2.0+ | Multi-container orchestration |
| **Docker Buildkit** | Enabled | Faster image builds (auto-enabled in Compose) |

### Hardware Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4GB | 8GB+ |
| **Disk** | 5GB | 20GB |
| **Network** | Any | High-speed internet |

## Service Dependencies

### Service Startup Order

The `docker-compose.yaml` defines proper dependencies to ensure services start in correct order:

```
1. Network Creation
   ↓
2. PostgreSQL Database (db)
   ↓
3. Redis Cache (superset_cache)
   ↓
4. Weather API (weather-api)  [Independent, but waits for db]
   ↓
5. Superset Init (superset-init) [Waits for db + redis]
   ↓
6. Superset App (superset)  [Waits for superset-init]
   ↓
7. Airflow (af)  [Waits for db]
   ↓
8. dbt (dbt)  [Waits for db]
   ↓
9. Soda Core (soda-core)  [Independent]
```

### Service Interdependencies

#### PostgreSQL Database (`db`)

```
Provides:
  ├── airflow_db (Airflow metadata)
  ├── superset_db (Superset metadata)
  └── weather_db (Business data)

Dependencies:
  └── None (root service)

Used By:
  ├── Airflow (airflow metadata + business data)
  ├── Superset (superset metadata + query data)
  ├── dbt (transformations)
  ├── Soda (quality checks)
  └── Weather API ingest task
```

#### Weather API (`weather-api`)

```
Provides:
  └── HTTP API (port 5000)
     └── Real-time weather data

Dependencies:
  └── None (independent service)

Used By:
  └── Airflow DAG → insert_records.py
     └── Fetches data every 15 minutes
```

#### Airflow (`af`)

```
Provides:
  ├── DAG Orchestration (port 8080)
  ├── Scheduling (every 15 minutes)
  └── Docker Operator for dbt/soda

Dependencies:
  └── PostgreSQL (airflow_db)
  └── HOST_PROJECT_ROOT environment variable

Used By:
  ├── Runs dbt transformations
  ├── Runs Soda quality checks
  └── Executes Python ETL tasks
```

#### dbt (`dbt`)

```
Provides:
  └── Data transformations
     ├── Staging models
     └── Mart models

Dependencies:
  └── PostgreSQL (weather_db)
  └── dbt/profiles.yml configuration

Used By:
  └── Airflow DockerOperator
     └── Executed as part of DAG
```

#### Superset (`superset`)

```
Provides:
  └── BI & Visualization (port 8088)
     └── Dashboards, charts, queries

Dependencies:
  ├── PostgreSQL (superset_db)
  ├── Redis (caching)
  └── superset-init (initialization)

Used By:
  └── End users (browsers)
```

#### Soda (`soda-core`)

```
Provides:
  └── Data Quality Validation
     └── Checks for nulls, freshness, duplicates

Dependencies:
  └── PostgreSQL (weather_db)

Used By:
  └── Airflow DockerOperator
     └── Executed as part of DAG
```

## Python Dependencies

### Root Requirements (`requirements.txt`)

Used by: **Airflow** and **Python tasks**

```
Main Categories:
├── Pipeline & ETL
│   ├── apache-airflow (DAG orchestration)
│   ├── apache-airflow-providers-docker (Docker support)
│   ├── sqlalchemy (ORM & connections)
│   └── psycopg2-binary (PostgreSQL driver)
│
├── Reliability
│   ├── tenacity (retry logic)
│   └── requests (HTTP client)
│
├── Data Processing
│   ├── pandas (data manipulation)
│   └── pyarrow (data serialization)
│
├── Quality & Testing
│   ├── pytest (testing framework)
│   └── pylint (code linting)
│
└── Logging & Monitoring
    └── python-json-logger (structured logging)
```

**Note:** These are installed when Airflow image starts.

### Weather API Requirements (`weather_api/requirements_api.txt`)

Used by: **Flask Weather API container**

```
├── Flask (web framework)
├── Werkzeug (WSGI utilities)
├── requests (HTTP client)
└── python-dotenv (environment loading)
```

## Docker Image Dependencies

### Images Used

| Service | Image | Purpose | Pinned? |
|---------|-------|---------|---------|
| weather-api | `weather-api:1.0.0` | Custom Python Flask app | ✅ Yes |
| PostgreSQL | `postgres:17` | Relational database | ✅ Yes |
| Airflow | `apache/airflow:3.1.3` | Workflow orchestration | ✅ Yes |
| dbt | `ghcr.io/dbt-labs/dbt-postgres:1.9.latest` | Data transformation | ⚠️ Latest tag |
| Superset | `apache/superset:3.0.0-py310` | BI platform | ✅ Yes |
| Redis | `redis:7` | Cache layer | ✅ Yes |
| Soda | `justemzy101/soda-core:v2` | Quality checks | ✅ Yes |

### Custom Image Build

**weather-api** is built from local Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements_api.txt .
RUN pip install -r requirements_api.txt

COPY weather_api.py api_keys.py api_keys_config.json .
COPY full_world_capitals_plus_egypt.json .

EXPOSE 5000
CMD ["python", "weather_api.py"]
```

Built locally with: `docker-compose build weather-api`

## Database Schema Dependencies

### PostgreSQL Initialization

On first startup, initialization scripts run:

1. **airflow_init.sql** (`/postgres/airflow_init.sql`)
   ```sql
   CREATE SCHEMA airflow_db;
   -- Creates Airflow metadata schema
   ```

2. **superset_init.sql** (`/postgres/superset_init.sql`)
   ```sql
   CREATE SCHEMA superset_db;
   -- Creates Superset metadata schema
   ```

3. **Auto-created by Airflow task:**
   ```sql
   CREATE TABLE raw_weather_data (...)
   CREATE SCHEMA dev
   ```

### Airflow → PostgreSQL Flow

```
Airflow Task 1 (Python)
  ↓
  INSERT INTO raw_weather_data (from weather-api)
  ↓
dbt Models (Task 2)
  ↓
  Transform → CREATE VIEW stg_weather
  ↓
  Transform → CREATE TABLE dim_weather_scd2
  ↓
  Transform → CREATE TABLE weather_report
  ↓
Soda Checks (Task 3)
  ↓
  VALIDATE raw_weather_data
  VALIDATE dev.stg_weather
  VALIDATE dev.dim_weather_scd2
```

## Environment Variable Dependencies

### Required Variables

These MUST be set in `.env` for the project to work:

```dotenv
# Critical - Blocks DAG execution if missing
HOST_PROJECT_ROOT=/path/to/Weather_data_project

# Critical - Database won't accept connections
DB_PASSWORD=secure-password
AIRFLOW_DB_PASSWORD=secure-password
DBT_DB_PASSWORD=secure-password
```

### Optional Variables (Have Defaults)

```dotenv
DB_USER=weather_user          # Default if not set
DB_NAME=weather_db            # Default if not set
AIRFLOW_DB_USER=airflow       # Default if not set
DBT_DB_USER=weather_user      # Default if not set
DBT_DB_HOST=db                # Default if not set
DBT_SCHEMA=dev                # Default if not set
```

### Where Variables Are Used

```
.env File Variables
├── docker-compose.yaml
│   ├── PostgreSQL service
│   ├── Airflow service
│   ├── dbt service
│   ├── Soda service
│   └── Superset service
│
├── dbt/profiles.yml (at runtime)
│   └── Database connection
│
└── airflow/dags/dbt_orchestrator.py (at runtime)
    └── HOST_PROJECT_ROOT validation
```

## Volume & Mount Dependencies

### Docker Volumes

```
Volumes Used:

1. redis:/data
   Purpose: Redis persistence
   Used By: Superset cache

2. postgres/data:/var/lib/postgresql/data
   Purpose: Database persistence
   Used By: PostgreSQL
   Note: Managed by docker-compose, survives restarts
```

### Bind Mounts (Host ↔ Container)

```
Host Path                      Container Path           Service
──────────────────────────────────────────────────────────────────
./airflow/dags            →    /opt/airflow/dags       airflow
./api_request             →    /opt/airflow/include    airflow
./dbt                     →    /opt/airflow/project/dbt airflow
/var/run/docker.sock      →    /var/run/docker.sock    airflow
                                                        (Docker-in-Docker)

./dbt/my_project          →    /usr/app                dbt
./dbt                     →    /root/.dbt              dbt

./soda                    →    /app/soda               soda-core

./docker                  →    /app/docker             superset
./superset-core           →    /app/superset-core      superset

./postgres/data           →    /var/lib/postgresql/data postgres

./weather_api/api_keys_config.json → /app/api_keys_config.json weather-api
```

## Network Dependencies

### Docker Network

**Network Name:** `my-network` (bridge mode)

All services connected to single network for inter-service communication:

```
Service Discovery (DNS):
  weather-api:5000     (accessible as "weather-api" from other containers)
  db:5432              (accessible as "db" from other containers)
  airflow:8080         (accessible as "airflow" from other containers)
  redis:6379           (accessible as "redis" from other containers)
  superset:8088        (accessible as "superset" from other containers)
```

### Port Mapping

```
Host Port  →  Container Port  Service
──────────────────────────────────────
5000       →  5000            weather-api
5430       →  5432            PostgreSQL
8080       →  8080            Airflow
8088       →  8088            Superset
6379       →  6379            Redis (localhost only)
```

## Execution Flow Dependencies

### DAG Execution Sequence

Triggered every 15 minutes by Airflow:

```
Task 1: pull_push_to_db (PythonOperator)
  Environment Dependencies:
  ├── DB_PASSWORD → PostgreSQL connection
  ├── WEATHER_API_KEY → API authentication
  └── CONNECTION_POOLING → SQLAlchemy config

  ↓↓↓ (Task depends on parent completion)

Task 2: dbt_run (DockerOperator)
  Environment Dependencies:
  ├── HOST_PROJECT_ROOT → Mount dbt folder
  ├── DBT_DB_PASSWORD → dbt profiles.yml
  ├── DBT_DB_HOST → dbt profiles.yml
  └── Docker Volume Mounts → /usr/app (dbt project)

  ↓↓↓ (Task depends on parent completion)

Task 3: soda_scan (DockerOperator)
  Environment Dependencies:
  ├── HOST_PROJECT_ROOT → Mount soda folder
  ├── DB_PASSWORD → Soda configuration
  └── Docker Volume Mounts → /app/soda (checks)
```

## Dependency Version Compatibility

### Compatible Versions

These versions are tested together:

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.11 | Base for Airflow, API, dbt |
| PostgreSQL | 17 | Latest stable |
| Airflow | 3.1.3 | Latest as of Dec 2025 |
| dbt-postgres | 1.9.latest | dbt 1.7 compatible |
| Superset | 3.0.0 | Latest stable |
| Redis | 7 | Latest stable |

### Breaking Changes to Watch

```
If upgrading:
- Airflow 2.x → 3.x: API changes in operators
- dbt 1.7 → 2.0: Model configuration syntax changes
- Superset 2.x → 3.x: Database connection format changes
```

## Troubleshooting Dependencies

### Missing Service

If a service won't start, check:

1. **Does its dependency exist?**
   ```bash
   docker-compose ps | grep dependency-service
   ```

2. **Is dependency healthy?**
   ```bash
   docker-compose ps  # Check STATUS column
   ```

3. **Are environment variables set?**
   ```bash
   docker-compose config | grep SERVICE_NAME
   ```

### Connection Errors

If services can't communicate:

1. **Are they on same network?**
   ```bash
   docker network ls
   docker network inspect my-network
   ```

2. **Is service listening?**
   ```bash
   docker-compose logs service-name | grep "listening\|ERROR"
   ```

3. **Are credentials correct?**
   ```bash
   grep PASSWORD .env
   grep PASSWORD docker/.env
   ```

---

**Last Updated:** December 25, 2025

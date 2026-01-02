# Project Audit Report - Weather Data Project

**Date:** 2025-12-21  
**Status:** 🔴 Critical Issues Found  

---

## 🔴 CRITICAL ISSUES

### 1. **Weather API Image Tag Mismatch**
**Location:** `docker-compose.yaml` line 43
```yaml
weather-api:
  image: weather-api:latest  # ❌ This tag doesn't exist!
```

**Problem:** 
- Image reference is `weather-api:latest` but was never built
- Dockerfile exists but hasn't been built
- Container won't start

**Solution:**
```bash
# Build the image first
docker build -t weather-api:latest weather_api/

# Or let docker-compose build it
docker-compose build weather-api
```

---

### 2. **Redis Service Missing Dependency**
**Location:** `docker-compose.yaml` line 199
```yaml
superset-init:
  depends_on:
    redis:
      condition: service_started  # ❌ Redis not defined in 'depends_on' correctly
```

**Problem:**
- `superset-init` waits for redis, but it's defined AFTER superset-init
- Docker-compose reads services in order, redis comes later

**Solution:** Move redis service definition before superset-init, or fix depends_on.

---

### 3. **Soda Container Configuration Issues**
**Location:** `docker-compose.yaml` lines 210-223
```yaml
soda-core:
  environment:
    - DB_USER="weahter_user"      # ❌ TYPO: "weahter" should be "weather"
    - DB_PASSWORD="weather_pass"  # ❌ Hardcoded password (should be ${DB_PASSWORD})
```

**Problems:**
- Typo in DB_USER (`weahter_user` instead of `weather_user`)
- Hardcoded password instead of using environment variable
- Container runs `tail -F /dev/null` (does nothing - just sleeps)

---

### 4. **Airflow Database Connection Hardcoded**
**Location:** `docker-compose.yaml` line 73
```yaml
af:
  environment:
    AIRFLOW__DATABASE__SQL_ALCHEMY_CONN: postgresql+psycopg2://airflow:airflow@db:5432/airflow_db
    # ❌ Credentials hardcoded, should use ${AIRFLOW_DB_USER}:${AIRFLOW_DB_PASSWORD}
```

**Problem:**
- Hardcoded `airflow:airflow` doesn't match environment variables
- `.env` has `AIRFLOW_DB_USER` and `AIRFLOW_DB_PASSWORD` but not used

---

### 5. **Healthcheck Dependencies Problem**
**Location:** `docker-compose.yaml` lines 91-93
```yaml
depends_on:
  db:
    condition: service_healthy
  weather-api:
    condition: service_healthy
```

**Problem:**
- Airflow tries to connect to weather-api during DAG execution
- But weather-api container isn't built (issue #1)
- Healthcheck will timeout waiting for weather-api

---

### 6. **Missing volumes mount for API config**
**Location:** `docker-compose.yaml` lines 43-58
```yaml
weather-api:
  # ❌ Missing volume mount for api_keys_config.json
  # volumes are not defined, so config file isn't accessible
```

**Problem:**
- Dockerfile expects to find `api_keys_config.json` at `/app/`
- But it's not mounted from host, only COPIED during build
- After container starts, changes to config are not visible

---

### 7. **.env File Has Test Values**
**Location:** `.env`
```dotenv
DB_PASSWORD=weather_pass           # ❌ Test password, too simple
AIRFLOW_DB_PASSWORD=airflow        # ❌ Test password, matches username
WEATHER_API_KEY=5b7eae5a12f272... # ❌ Real key exposed
```

**Problem:**
- Test credentials are weak
- Real API key might be exposed
- Not secure for production

---

### 8. **DAG Import Paths Wrong**
**Location:** `airflow/dags/dbt_orchestrator.py` line 4
```python
from insert_records import main  # ❌ Wrong path!
```

**Problem:**
- File is at `api_request/insert_records.py`
- But DAG imports as just `insert_records`
- Works because `/opt/airflow/include` is in PYTHONPATH
- But confusing and fragile

---

## 🟠 MAJOR ISSUES

### 9. **DBT Service Runs Immediately**
**Location:** `docker-compose.yaml` lines 117-124
```yaml
dbt:
  command: run  # ❌ This runs immediately and exits
```

**Problem:**
- DBT task runs once when container starts, then exits
- Should only run when triggered by DAG
- This is a standalone container, not called by Airflow DockerOperator

---

### 10. **Superset Dependencies Wrong**
**Location:** `docker-compose.yaml` line 145
```yaml
depends_on:
  superset-init:
    condition: service_completed_successfully  # ❌ Might not wait properly
```

**Problem:**
- Order of dependencies is important
- Superset-init depends on redis which hasn't started yet

---

## 🔵 CONFIGURATION ISSUES

### 11. **Requirements Files Incomplete**
**Issue:** `weather_api/requirements_api.txt` doesn't include curl
```
# Missing for healthcheck to work:
# curl is used in healthcheck but not Python package
```

---

## 📊 Service Health Matrix

| Service | Status | Issue |
|---------|--------|-------|
| **db (PostgreSQL)** | ✅ Ready | No issues |
| **weather-api** | 🔴 Won't start | Image not built |
| **af (Airflow)** | 🟠 Won't start | Waits for weather-api |
| **dbt** | 🔴 Broken | Runs once, doesn't wait for calls |
| **superset** | 🟠 Broken | Dependency order wrong |
| **redis** | ✅ Ready | No issues |
| **soda-core** | 🔴 Broken | Typo in credentials |

---

## 🛠️ Fix Priority

### **P0 (Must Fix Now)**
1. Build weather-api image
2. Fix soda credentials typo
3. Fix Airflow DB connection hardcoding
4. Fix weather-api volume mount

### **P1 (Should Fix)**
5. Fix DAG import paths
6. Fix superset dependency order
7. Update test credentials in .env

### **P2 (Nice to Have)**
8. Remove dbt standalone service (use DockerOperator)
9. Add proper logging to containers
10. Document the architecture

---

## 📝 Current Project Structure Health

```
✅ Code Quality
  - Python code is clean
  - Docker configs mostly correct
  - dbt models exist

🟠 Configuration
  - Many hardcoded values
  - Typos in environment variables
  - Missing volume mounts
  - Image not built

🔴 Runability
  - Won't start with docker-compose up
  - Multiple dependency issues
  - Service health checks have circular dependencies

⚠️ Security
  - Test credentials in .env
  - API key might be exposed
  - No secret management
```

---

## 📋 Recommended Action Plan

### **Step 1: Fix Critical Build Issues (15 min)**
1. Build weather-api: `docker build -t weather-api:latest weather_api/`
2. Fix soda typo: `weahter_user` → `weather_user`
3. Fix Airflow connection to use env vars
4. Fix weather-api volume mount

### **Step 2: Fix Dependency Order (10 min)**
5. Reorder services in docker-compose
6. Fix redis/superset dependencies
7. Remove dbt standalone service

### **Step 3: Fix Configuration (10 min)**
8. Update import paths in DAG
9. Add proper logging
10. Document each service

### **Step 4: Secure (10 min)**
11. Generate strong test passwords
12. Document secret management
13. Update .gitignore

---

## 🚀 Next Steps

Would you like me to:
- [ ] Fix all P0 issues immediately
- [ ] Explain each issue in detail
- [ ] Create a working docker-compose.yaml from scratch
- [ ] Document the correct architecture

**Recommendation:** Fix P0 issues first (takes 15 min), then verify everything starts.


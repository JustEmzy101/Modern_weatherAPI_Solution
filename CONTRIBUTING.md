# Contributing to Weather Data Project

Thank you for your interest in contributing! This document outlines guidelines for developing and contributing to the Weather Data Project.

## Quick Links
- [Architecture Overview](README.md#architecture-overview)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Adding Features](#adding-features)
- [Running Tests](#running-tests)

## Development Setup

### Prerequisites
- Docker & Docker Compose (see [README.md](README.md) for installation)
- Git
- Text editor (VS Code recommended)

### Initial Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Weather_data_project
   ```

2. Run setup script:
   ```bash
   ./setup.sh
   ```
   Follow prompts to configure environment variables from `.env.example`

3. Start services:
   ```bash
   make up
   ```

4. Verify everything is working:
   ```bash
   make verify
   ```

## Working with the Codebase

### Project Structure Overview
```
Weather_data_project/
├── airflow/               # Orchestration DAGs
│   └── dags/             # DAG definitions
├── dbt/                  # Data transformation
│   └── my_project/      # dbt project models
├── api_request/          # Data ingestion from weather API
├── soda/                 # Data quality checks
├── weather_api/          # Mock weather API service
├── docker/               # Docker configurations
├── postgres/             # Database initialization
└── superset-core/        # Analytics visualization
```

### Environment Variables
All configuration is managed through environment files:
- `.env` - Main configuration (database, API keys, paths)
- `docker/.env` - Superset-specific configuration

**Never commit `.env` files!** Use `.example` templates instead.

### Python Code Standards

#### Code Style
- Use **PEP 8** for all Python code
- Line length: 100 characters maximum
- Use type hints where practical
- Use meaningful variable names (avoid single letters except in loops)

#### Example:
```python
def fetch_weather_data(api_key: str, location: str) -> dict:
    """
    Fetch weather data from API.
    
    Args:
        api_key: API authentication key
        location: City or location name
        
    Returns:
        Dictionary containing weather data
    """
    # Implementation here
```

#### Imports Organization
1. Standard library imports
2. Third-party imports
3. Local imports

```python
import os
import logging
from typing import Dict

import requests
from flask import Flask, jsonify

from config import API_KEY
from utils import format_response
```

#### Logging
Use Python's logging module for all output (not print statements):
```python
import logging

logger = logging.getLogger(__name__)

logger.info("Starting weather data fetch")
logger.error("Failed to fetch data: %s", str(error))
```

### dbt Development Standards

#### SQL Style Guide
- Use lowercase for SQL keywords (SELECT, FROM, WHERE)
- Use meaningful aliases: `SELECT created_at as event_date` (not `ca`)
- Include comments for complex logic:
  ```sql
  -- Calculate rolling 7-day average temperature
  WITH daily_temps AS (
    SELECT date, avg_temp FROM raw_weather
  )
  SELECT 
    date,
    AVG(avg_temp) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as temp_7day_avg
  FROM daily_temps
  ```

#### Model Organization
- **sources/** - Raw data definitions
- **staging/** - Light transformations, renaming, data cleaning
- **mart/** - Business-ready denormalized tables
- **tests/** - dbt data quality tests

#### Adding a New Model
1. Create SQL file in appropriate directory (`staging/`, `mart/`, etc.)
2. Add `.yml` configuration with description and tests
3. Run dbt parse to validate:
   ```bash
   make dbt-parse
   ```
4. Test the model:
   ```bash
   make dbt-test
   ```

### YAML Standards

#### Configuration Files
- Use 2-space indentation (NOT tabs)
- Use quotes for string values
- Include comments for non-obvious settings

```yaml
# docker-compose.yaml
services:
  postgres:
    image: postgres:17-alpine
    environment:
      POSTGRES_PASSWORD: "${DB_PASSWORD}"
    ports:
      - "5432:5432"
```

### Shell Script Standards

#### Script Best Practices
```bash
#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Use meaningful variable names
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${PROJECT_ROOT}/logs/setup.log"

# Add helpful comments
# Check if required tools are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Use consistent logging
echo "✅ Setup complete"
```

## Adding Features

### Workflow for New Features

#### 1. Create a Feature Branch
```bash
git checkout -b feature/weather-alerts
```

#### 2. Make Changes
- Keep commits logical and focused
- Write descriptive commit messages:
  ```
  Add weather alert functionality
  
  - Implement alert threshold checking
  - Add email notification service
  - Include tests for alert logic
  ```

#### 3. Test Changes Locally
```bash
# Build updated images
make build

# Restart services
make restart

# Run verification
make verify

# Check logs for errors
make logs-airflow
make logs-api
```

#### 4. Create Pull Request
- Describe what changed and why
- Reference any related issues
- Ensure all tests pass

### Example: Adding a New Data Source

1. **Create API request module** (`api_request/fetch_new_source.py`):
   ```python
   import requests
   import logging
   
   logger = logging.getLogger(__name__)
   
   def fetch_solar_data(api_key: str) -> dict:
       """Fetch solar radiation data from external API."""
       response = requests.get(
           "https://api.example.com/solar",
           params={"key": api_key}
       )
       response.raise_for_status()
       return response.json()
   ```

2. **Create dbt staging model** (`dbt/my_project/models/staging/stg_solar.sql`):
   ```sql
   SELECT
       created_at,
       location,
       solar_radiation::numeric as radiation_watts
   FROM {{ source('raw', 'solar_data') }}
   WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
   ```

3. **Add data quality tests** (`dbt/my_project/models/staging/stg_solar.yml`):
   ```yaml
   models:
     - name: stg_solar
       columns:
         - name: radiation_watts
           tests:
             - not_null
             - dbt_utils.accepted_range:
                 min_value: 0
                 max_value: 1500
   ```

4. **Update Airflow DAG** to call the new fetch function

## Running Tests

### Database Tests (dbt)
```bash
# Test all dbt models
make dbt-test

# Test specific model
docker-compose exec dbt dbt test --select stg_weather

# Generate dbt documentation
make dbt-docs
```

### Data Quality Tests (Soda)
```bash
# Run Soda checks
docker-compose exec soda soda scan -c configuration.yml

# Check specific dataset
docker-compose exec soda soda scan -c configuration.yml -d weather
```

### API Tests
```bash
# Test weather API endpoint
make test-api

# Or manually:
curl http://localhost:8000/weather?location=london
```

### Manual Service Health Checks
```bash
# Run comprehensive health check
make verify

# Or directly:
./verify.sh
```

## Troubleshooting Development Issues

### Services Won't Start
```bash
# Check service logs
make logs-airflow
make logs-api
make logs-postgres

# Verify environment is set up
cat .env | head -20

# Rebuild from scratch
make clean
make build
make up
```

### dbt Model Failures
```bash
# Check dbt parsing
docker-compose exec dbt dbt parse

# See full error
docker-compose exec dbt dbt test --debug

# Verify database connectivity
docker-compose exec dbt dbt debug
```

### Database Connection Issues
```bash
# Test PostgreSQL connection
docker-compose exec postgres psql -U airflow_user -d weather_db -c "SELECT version();"

# Check port availability
lsof -i :5432
```

## Git Workflow Best Practices

### Before Committing
```bash
# Check what you're about to commit
git status
git diff

# Verify tests pass
make verify

# Review log output
docker-compose logs --tail=50
```

### Commit Messages
Follow this format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat:` New feature
- `fix:` Bug fix
- `refactor:` Code refactoring
- `test:` Adding tests
- `docs:` Documentation
- `chore:` Build, dependency updates

Example:
```
feat(airflow): add data quality check DAG

- Implement Soda integration in orchestration
- Add dbt run dependencies
- Include retry logic for failed checks

Closes #42
```

### Branches to Avoid
Never commit directly to:
- `main` or `master` - Always use feature branches
- Create descriptive branch names: `feature/auth`, `bugfix/api-timeout`, `docs/setup-guide`

## Documentation

### When to Update Documentation
- **Feature added:** Update README.md and relevant docs
- **Config changed:** Update .env.example and DEPENDENCIES.md
- **Process changed:** Update CONTRIBUTING.md or QUICKSTART.md
- **Bug fixed:** Add to troubleshooting section if applicable

### Documentation Standards
- Use clear, concise language
- Include examples where helpful
- Keep documentation in sync with code
- Use Markdown with proper formatting

## Questions or Issues?

1. **Check existing documentation:**
   - [README.md](README.md) - Architecture and setup
   - [QUICKSTART.md](QUICKSTART.md) - 5-minute guide
   - [DEPENDENCIES.md](DEPENDENCIES.md) - Detailed dependencies

2. **Review code comments** in relevant files

3. **Check service logs:**
   ```bash
   make logs
   ```

4. **Create an issue** with detailed description of problem

## Code Review Checklist

When reviewing PRs, check:
- ✅ Code follows style guidelines
- ✅ Tests are included and passing
- ✅ Documentation is updated
- ✅ No hardcoded credentials or paths
- ✅ Environment variables used correctly
- ✅ Commit messages are clear
- ✅ Changes are logically grouped
- ✅ No unnecessary dependencies added

---

Thank you for contributing! Your improvements make this project better for everyone. 🚀

# Development Guide

Quick reference for common development tasks.

## Quick Commands

### Start Development
```bash
./setup.sh          # First time: configure environment
make up             # Start all services
make verify         # Confirm everything is running
```

### Monitor Services
```bash
make logs           # View all logs
make logs-airflow   # View specific service logs
make ps             # Show service status
```

### Make Changes & Rebuild
```bash
make build          # Rebuild images (after code changes)
make restart        # Restart services
```

### Cleanup
```bash
make down           # Stop all services
make clean          # Remove containers and volumes (⚠️ deletes data)
```

## Common Workflows

### Testing a Python Change in API
```bash
# Edit weather_api/weather_api.py
make build                    # Rebuild weather-api image
make restart                  # Restart the service
make test-api                 # Test the endpoint
make logs-weather-api         # Check logs if needed
```

### Testing a dbt Change
```bash
# Edit dbt/my_project/models/staging/stg_weather.sql
docker-compose exec dbt dbt parse          # Validate syntax
docker-compose exec dbt dbt test           # Run tests
docker-compose exec dbt dbt run            # Execute transformation
docker-compose logs dbt                    # Check logs
```

### Testing an Airflow DAG Change
```bash
# Edit airflow/dags/dbt_orchestrator.py
make logs-airflow                          # Check DAG was reloaded
# The DAG auto-reloads every 30 seconds

# Test DAG manually (optional)
docker-compose exec airflow airflow dags test dbt_orchestrator_dag
```

### Database Query Testing
```bash
# Connect to database shell
make shell-db

# Run SQL
SELECT * FROM public.raw_weather LIMIT 5;
SELECT COUNT(*) FROM public.weather_report;
```

## File Editing Tips

### Using VS Code

1. **Install Extensions** (optional but helpful):
   - Python (Microsoft)
   - Prettier (formatting)
   - SQL Tools (database queries)
   - YAML (validation)

2. **Workspace Settings** (.vscode/settings.json):
   ```json
   {
     "python.linting.enabled": true,
     "python.linting.pylintEnabled": true,
     "editor.formatOnSave": true,
     "[python]": {
       "editor.defaultFormatter": "ms-python.python",
       "editor.formatOnSave": true
     }
   }
   ```

3. **Opening Database Shell in Terminal**:
   ```bash
   # Tab 1: Monitor logs
   make logs -f
   
   # Tab 2: Query database
   make shell-db
   ```

## Debugging Techniques

### Check Service Health
```bash
# Comprehensive health check
./verify.sh

# Check specific service
docker-compose ps weather-api
```

### View Detailed Logs
```bash
# Last 100 lines
docker-compose logs --tail=100 airflow

# Follow logs in real-time
docker-compose logs -f soda

# Specific timestamp
docker-compose logs --since 2024-01-01 --until 2024-01-02 weather-api
```

### Inspect Running Container
```bash
# Get shell access to container
docker-compose exec airflow bash

# Run Python in container
docker-compose exec weather-api python -c "import requests; print(requests.__version__)"

# Check environment variables
docker-compose exec dbt env | grep DBT
```

### Database Debugging
```bash
# Check if database has data
docker-compose exec postgres psql -U airflow_user -d weather_db -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public';"

# Count rows in key tables
docker-compose exec postgres psql -U airflow_user -d weather_db -c "SELECT 'raw_weather' as table_name, COUNT(*) FROM raw_weather UNION ALL SELECT 'stg_weather', COUNT(*) FROM stg_weather;"

# Check latest data
docker-compose exec postgres psql -U airflow_user -d weather_db -c "SELECT * FROM raw_weather ORDER BY created_at DESC LIMIT 5;"
```

## Performance Optimization

### Speed Up Builds
```bash
# Docker uses .dockerignore to exclude files from build context
# Current exclusions: .git, docs, IDE files, Python cache
# Rebuilds are ~30% faster due to reduced context

# To add more exclusions, edit .dockerignore files:
# - .dockerignore (root)
# - weather_api/.dockerignore
```

### Reduce Log Clutter
```bash
# Filter logs to specific service
docker-compose logs airflow --tail=50

# Exclude specific service
docker-compose logs --tail=50 $(docker-compose config --services | grep -v soda)
```

### Database Query Performance
```bash
# Check query performance
docker-compose exec postgres psql -U airflow_user -d weather_db -c "EXPLAIN ANALYZE SELECT * FROM weather_report WHERE date = CURRENT_DATE;"

# View table sizes
docker-compose exec postgres psql -U airflow_user -d weather_db -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

## Environment Variable Troubleshooting

### Check Current Configuration
```bash
# View all environment variables
cat .env

# View specific variable
grep HOST_PROJECT_ROOT .env

# Check if variable is set in running container
docker-compose exec airflow env | grep AIRFLOW_HOME
```

### Reload Configuration
```bash
# Environment changes require restart
make restart

# Or restart specific service
docker-compose restart airflow
```

## Common Issues & Solutions

### "Cannot connect to database"
```bash
# 1. Check if postgres is running
docker-compose ps postgres

# 2. Check logs
docker-compose logs postgres

# 3. Test connection from container
docker-compose exec airflow psql -h postgres -U airflow_user -d weather_db -c "SELECT 1"

# 4. Verify .env variables
grep DB_ .env
```

### "DAG not updating in Airflow UI"
```bash
# Airflow auto-reloads DAGs every 30 seconds
# Force reload by restarting
docker-compose restart airflow

# Check for DAG parsing errors
docker-compose logs airflow | grep ERROR
```

### "dbt models failing"
```bash
# Check dbt debug output
docker-compose exec dbt dbt debug

# Validate dbt project
docker-compose exec dbt dbt parse

# Run single model with debugging
docker-compose exec dbt dbt run --select stg_weather --debug
```

### "Low disk space"
```bash
# Check Docker disk usage
docker system df

# Clean up unused images/containers
make clean

# Remove all dangling images
docker image prune -f
```

## Git Workflow

### Before Pushing Changes
```bash
# 1. Verify environment is clean
make verify

# 2. Check what's changed
git status
git diff

# 3. Run tests
docker-compose exec dbt dbt test

# 4. Review logs for any errors
docker-compose logs --tail=20

# 5. Commit with clear message
git add .
git commit -m "feat(dbt): add new weather dimension table"

# 6. Push
git push origin feature/branch-name
```

### Avoiding Common Mistakes
```bash
# ❌ DON'T commit .env files
git add .env          # DON'T!
git add .env.example  # DO THIS instead

# ✅ DO check before committing
git diff --cached | grep -i password   # Check for secrets

# ✅ DO exclude large files
echo "*.log" >> .gitignore
echo "*.pyc" >> .gitignore

# ✅ DO keep commits focused
# One feature or fix per commit
```

## Reference Documentation

- [README.md](README.md) - Architecture overview
- [QUICKSTART.md](QUICKSTART.md) - 5-minute setup
- [DEPENDENCIES.md](DEPENDENCIES.md) - Detailed system requirements
- [CONTRIBUTING.md](CONTRIBUTING.md) - Code standards
- [docs/](docs/) - Additional audit and strategy documents

---

Happy coding! 🚀

.PHONY: help setup build up down logs logs-% stop restart clean test-api verify ps shell

help:
	@echo "Weather Data Project - Convenient Commands"
	@echo ""
	@echo "Setup & Configuration:"
	@echo "  make setup          Setup project (create .env files)"
	@echo "  make build          Build all Docker images"
	@echo ""
	@echo "Running Services:"
	@echo "  make up             Start all services (docker-compose up -d)"
	@echo "  make down           Stop all services (docker-compose down)"
	@echo "  make stop           Stop services without removing"
	@echo "  make restart        Restart all services"
	@echo "  make ps             Show service status"
	@echo ""
	@echo "Monitoring & Debugging:"
	@echo "  make logs           Show logs from all services"
	@echo "  make logs-airflow   Show logs from specific service"
	@echo "  make logs-db        (replace 'airflow' with service name)"
	@echo "  make logs-weather-api"
	@echo "  make verify         Run health checks"
	@echo "  make shell-db       Connect to database shell"
	@echo ""
	@echo "Testing:"
	@echo "  make test-api       Test weather API endpoint"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean          Remove containers and volumes (WARNING: deletes data!)"
	@echo ""

setup:
	@echo "Running setup script..."
	@./setup.sh

build:
	@echo "Building Docker images..."
	docker-compose build

up:
	@echo "Starting services..."
	docker-compose --env-file .env up -d
	@echo ""
	@echo "Waiting for services to initialize (60 seconds)..."
	@sleep 60
	@echo ""
	@make ps
	@echo ""
	@echo "✅ Services started! Access:"
	@echo "  - Airflow: http://localhost:8080"
	@echo "  - Superset: http://localhost:8088"
	@echo "  - Weather API: http://localhost:5000/weather?city=London"

down:
	@echo "Stopping services..."
	docker-compose down
	@echo "✅ Services stopped"

stop:
	@echo "Stopping services (keeping volumes)..."
	docker-compose stop
	@echo "✅ Services stopped"

restart:
	@echo "Restarting services..."
	docker-compose restart
	@sleep 10
	@make ps

ps:
	@echo "Service Status:"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@docker-compose ps
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

logs:
	@docker-compose logs -f

logs-%:
	@docker-compose logs -f $*

verify:
	@echo "Verifying project health..."
	@echo ""
	@./verify.sh

test-api:
	@echo "Testing Weather API..."
	@echo ""
	@curl -s -H "X-API-Key: ${WEATHER_API_KEY}" \
		"http://localhost:5000/weather?city=London" | python3 -m json.tool 2>/dev/null || \
	echo "❌ API test failed. Is the service running? Run 'make up' first."
	@echo ""

shell-db:
	@echo "Connecting to PostgreSQL database..."
	@docker-compose exec -T db psql -U weather_user -d weather_db

shell-%:
	@docker-compose exec $* bash

clean:
	@echo "⚠️  WARNING: This will delete all containers and volumes (data loss!)"
	@read -p "Are you sure? Type 'yes' to confirm: " confirm && \
	[ "$$confirm" = "yes" ] && \
	docker-compose down -v && \
	echo "✅ Cleaned" || \
	echo "Cancelled"

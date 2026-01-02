#!/bin/bash
#
# Health Check & Verification Script
# Validates that all services are running and accessible
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Weather Data Project - Health Check               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Color-coded status function
check_service() {
    local service=$1
    local port=$2
    local name=$3
    
    if docker-compose ps "$service" 2>/dev/null | grep -q "Up"; then
        echo -e "${GREEN}✅${NC} $name (port $port) - Running"
        
        # Try to connect if port is provided
        if [ ! -z "$port" ]; then
            if timeout 5 bash -c "echo > /dev/tcp/127.0.0.1/$port" 2>/dev/null; then
                echo -e "   ${GREEN}✓${NC} Port $port is accessible"
            else
                echo -e "   ${YELLOW}⚠${NC} Port $port not responding yet (starting up?)"
            fi
        fi
    else
        echo -e "${RED}❌${NC} $name - NOT RUNNING"
        return 1
    fi
}

# Check Docker daemon
echo -e "${YELLOW}[1/3] Checking Docker...${NC}"
if docker ps > /dev/null 2>&1; then
    echo -e "${GREEN}✅${NC} Docker is running"
else
    echo -e "${RED}❌${NC} Docker is not running"
    exit 1
fi
echo ""

# Check services
echo -e "${YELLOW}[2/3] Checking Services...${NC}"
HEALTHY=0
TOTAL=0

check_service "weather-api" "5000" "Weather API" && HEALTHY=$((HEALTHY+1)) || true
TOTAL=$((TOTAL+1))

check_service "weather_data_project-db-1" "5430" "PostgreSQL Database" && HEALTHY=$((HEALTHY+1)) || true
TOTAL=$((TOTAL+1))

check_service "airflow" "8080" "Apache Airflow" && HEALTHY=$((HEALTHY+1)) || true
TOTAL=$((TOTAL+1))

check_service "superset_app" "8088" "Apache Superset" && HEALTHY=$((HEALTHY+1)) || true
TOTAL=$((TOTAL+1))

check_service "superset_cache" "6379" "Redis Cache" && HEALTHY=$((HEALTHY+1)) || true
TOTAL=$((TOTAL+1))

check_service "soda-core" "" "Soda Data Quality" && HEALTHY=$((HEALTHY+1)) || true
TOTAL=$((TOTAL+1))

echo ""

# Check environment
echo -e "${YELLOW}[3/3] Checking Configuration...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✅${NC} .env file exists"
    
    if grep -q "HOST_PROJECT_ROOT=" .env; then
        HOST_ROOT=$(grep "HOST_PROJECT_ROOT=" .env | cut -d= -f2)
        if [ ! -z "$HOST_ROOT" ] && [ "$HOST_ROOT" != "/path/to/Weather_data_project" ]; then
            echo -e "${GREEN}✅${NC} HOST_PROJECT_ROOT is set: $HOST_ROOT"
        else
            echo -e "${RED}❌${NC} HOST_PROJECT_ROOT not configured"
        fi
    fi
    
    if grep -q "DB_PASSWORD=" .env; then
        echo -e "${GREEN}✅${NC} DB_PASSWORD is set"
    fi
    
    if grep -q "AIRFLOW_DB_PASSWORD=" .env; then
        echo -e "${GREEN}✅${NC} AIRFLOW_DB_PASSWORD is set"
    fi
else
    echo -e "${RED}❌${NC} .env file not found - run 'make setup' first"
fi

if [ -f "docker/.env" ]; then
    echo -e "${GREEN}✅${NC} docker/.env file exists"
else
    echo -e "${RED}❌${NC} docker/.env file not found"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "Service Status: ${GREEN}$HEALTHY/$TOTAL${NC} running"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test API if weather-api is running
echo -e "${YELLOW}[API Test]${NC}"
if timeout 5 bash -c "echo > /dev/tcp/127.0.0.1/5000" 2>/dev/null; then
    echo "Testing weather API endpoint..."
    if RESPONSE=$(curl -s -H "X-API-Key: ${WEATHER_API_KEY}" \
        "http://localhost:5000/weather?city=London" 2>/dev/null); then
        if echo "$RESPONSE" | grep -q '"temperature"'; then
            echo -e "${GREEN}✅${NC} API responding correctly"
        else
            echo -e "${YELLOW}⚠${NC} API responded but data may be incomplete"
        fi
    else
        echo -e "${YELLOW}⚠${NC} API not responding"
    fi
else
    echo -e "${YELLOW}⚠${NC} API port not accessible"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $HEALTHY -eq $TOTAL ]; then
    echo -e "${GREEN}✅ All checks passed!${NC}"
    echo ""
    echo "Access services at:"
    echo "  • Airflow:    http://localhost:8080"
    echo "  • Superset:   http://localhost:8088"
    echo "  • Weather API: http://localhost:5000/weather?city=London"
    exit 0
else
    echo -e "${YELLOW}⚠ Some services are not running${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Check configuration: cat .env | grep -E 'HOST|PASSWORD'"
    echo "  2. View logs: docker-compose logs -f"
    echo "  3. Restart services: docker-compose restart"
    exit 1
fi

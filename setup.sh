#!/bin/bash
#
# Weather Data Project Setup Script
# This script initializes the environment for first-time setup
#

set -e

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║   Weather Data Project - Initial Setup                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check if .env already exists
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists. Skipping creation."
    read -p "Do you want to reconfigure? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 0
    fi
fi

# Check if docker/.env exists
if [ -f "docker/.env" ]; then
    echo "⚠️  docker/.env file already exists."
else
    echo "📋 Creating docker/.env from template..."
    cp docker/.env.example docker/.env
    echo "✅ Created docker/.env"
fi

# Create root .env
echo ""
echo "📋 Creating .env from template..."
cp .env.example .env
echo "✅ Created .env"

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "⚠️  IMPORTANT: Edit .env before running docker-compose"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Required changes:"
echo ""
echo "1. Set HOST_PROJECT_ROOT to your project path:"
echo "   Linux/Mac:   HOST_PROJECT_ROOT=$(pwd)"
echo "   Windows:     HOST_PROJECT_ROOT=C:\\path\\to\\Weather_data_project"
echo ""
echo "2. Set secure passwords for databases:"
echo "   - DB_PASSWORD (weather database)"
echo "   - AIRFLOW_DB_PASSWORD (Airflow database)"
echo "   - Superset password in docker/.env"
echo ""
echo "3. Set WEATHER_API_KEY if you have a real API key"
echo ""
echo "After editing, run:"
echo "  docker-compose --env-file .env up -d"
echo ""

# Offer to edit .env
read -p "Would you like to edit .env now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ${EDITOR:-nano} .env
fi

echo ""
echo "✅ Setup complete!"
echo ""

#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================="
echo "Soda Core Data Quality Scanner"
echo "Version: $(soda --version)"
echo "=================================================="

# Check if configuration file exists
if [ ! -f "/app/soda/configuration.yml" ]; then
    echo -e "${RED}ERROR: Configuration file not found at /app/soda/configuration.yml${NC}"
    echo "Please mount your configuration directory:"
    echo "  -v /path/to/soda:/app/soda"
    exit 1
fi

# If no arguments provided, show help
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Usage:${NC}"
    echo "  docker run --rm -v /path/to/soda:/app/soda your-image scan [options]"
    echo ""
    echo "Examples:"
    echo "  # Run a scan"
    echo "  docker run --rm -v ./soda:/app/soda your-image scan -d my_db -c /app/soda/configuration.yml /app/soda/checks/checks.yml"
    echo ""
    echo "  # Run with JSON output"
    echo "  docker run --rm -v ./soda:/app/soda your-image scan -d my_db -c /app/soda/configuration.yml /app/soda/checks/checks.yml -o json"
    echo ""
    soda --help
    exit 0
fi

# Execute soda command with all arguments
echo -e "${GREEN}Executing: soda $@${NC}"
echo ""

# Run soda and capture exit code
soda "$@"
EXIT_CODE=$?

echo ""
echo "=================================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Scan completed successfully${NC}"
else
    echo -e "${RED}✗ Scan failed with exit code: $EXIT_CODE${NC}"
fi
echo "=================================================="

exit $EXIT_CODE
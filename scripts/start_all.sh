#!/bin/bash

# BUPT EDU LLM Platform - Start All Services
# This script starts all subprojects and the platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  BUPT EDU LLM Platform Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Load environment variables
if [ -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${GREEN}Loading environment variables...${NC}"
    export $(cat "$PROJECT_ROOT/.env" | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}Warning: .env file not found. Using default values.${NC}"
    echo -e "${YELLOW}Please copy .env.example to .env and configure it.${NC}"
fi

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to start a service
start_service() {
    local service_name=$1
    local service_dir=$2
    local start_command=$3
    local port=$4

    echo -e "${BLUE}Starting ${service_name}...${NC}"

    if check_port $port; then
        echo -e "${YELLOW}  Port $port is already in use. Skipping ${service_name}.${NC}"
        return
    fi

    cd "$service_dir"

    # Start service in background
    nohup $start_command > "${PROJECT_ROOT}/logs/${service_name}.log" 2>&1 &
    local pid=$!

    echo $pid > "${PROJECT_ROOT}/logs/${service_name}.pid"

    # Wait a moment and check if service started
    sleep 2
    if ps -p $pid > /dev/null; then
        echo -e "${GREEN}  ${service_name} started successfully (PID: $pid)${NC}"
    else
        echo -e "${RED}  Failed to start ${service_name}${NC}"
        cat "${PROJECT_ROOT}/logs/${service_name}.log"
    fi
}

# Create logs directory if it doesn't exist
mkdir -p "$PROJECT_ROOT/logs"

# Start Solar News Crawler
if [ "${SOLAR_NEWS_ENABLED:-true}" = "true" ]; then
    SOLAR_NEWS_DIR="${SOLAR_NEWS_DIR:-$PROJECT_ROOT/solar_news_crawler/solar_news_crawler}"
    SOLAR_NEWS_PORT="${SOLAR_NEWS_PORT:-5000}"

    start_service "solar_news_crawler" "$SOLAR_NEWS_DIR" "python app.py" "$SOLAR_NEWS_PORT"
fi

# Start Sentiment Analysis (if enabled)
# if [ "${SENTIMENT_ENABLED:-false}" = "true" ]; then
#     SENTIMENT_DIR="${SENTIMENT_DIR:-$PROJECT_ROOT/sentiment_analysis}"
#     SENTIMENT_PORT="${SENTIMENT_PORT:-5001}"
#
#     start_service "sentiment_analysis" "$SENTIMENT_DIR" "python app.py" "$SENTIMENT_PORT"
# fi

# Start Nginx (if enabled and not already running)
if [ "${NGINX_ENABLED:-true}" = "true" ]; then
    echo -e "${BLUE}Checking Nginx...${NC}"

    if ! command -v nginx &> /dev/null; then
        echo -e "${YELLOW}  Nginx is not installed. Please install Nginx and configure it manually.${NC}"
    elif systemctl is-active --quiet nginx; then
        echo -e "${GREEN}  Nginx is already running${NC}"
    else
        echo -e "${BLUE}  Starting Nginx...${NC}"
        sudo systemctl start nginx
        echo -e "${GREEN}  Nginx started successfully${NC}"
    fi
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All services started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Access the platform at: ${BLUE}http://localhost${NC}"
echo ""
echo -e "Running services:"
echo -e "  - Landing Page: ${BLUE}http://localhost/${NC}"
echo -e "  - Solar News Crawler: ${BLUE}http://localhost/solar_news/${NC}"
echo ""
echo -e "To stop all services, run: ${YELLOW}./scripts/stop_all.sh${NC}"
echo ""

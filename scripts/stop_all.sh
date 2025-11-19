#!/bin/bash

# BUPT EDU LLM Platform - Stop All Services
# This script stops all running subprojects

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
echo -e "${BLUE}  BUPT EDU LLM Platform Shutdown${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="${PROJECT_ROOT}/logs/${service_name}.pid"

    echo -e "${BLUE}Stopping ${service_name}...${NC}"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")

        if ps -p $pid > /dev/null 2>&1; then
            kill $pid
            sleep 2

            # Force kill if still running
            if ps -p $pid > /dev/null 2>&1; then
                echo -e "${YELLOW}  Force killing ${service_name}...${NC}"
                kill -9 $pid
            fi

            echo -e "${GREEN}  ${service_name} stopped${NC}"
        else
            echo -e "${YELLOW}  ${service_name} is not running${NC}"
        fi

        rm "$pid_file"
    else
        echo -e "${YELLOW}  PID file not found for ${service_name}${NC}"
    fi
}

# Stop all services
stop_service "solar_news_crawler"
# stop_service "sentiment_analysis"

# Optionally stop Nginx
# echo -e "${BLUE}Stopping Nginx (if managed by systemd)...${NC}"
# if systemctl is-active --quiet nginx; then
#     sudo systemctl stop nginx
#     echo -e "${GREEN}  Nginx stopped${NC}"
# else
#     echo -e "${YELLOW}  Nginx is not running${NC}"
# fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  All services stopped successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

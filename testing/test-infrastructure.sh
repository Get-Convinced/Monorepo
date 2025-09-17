#!/bin/bash

# Test script for infrastructure components
# Tests PostgreSQL, Redis, Qdrant, and Ollama connectivity

echo "🏗️  Testing Infrastructure Components"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test endpoints
POSTGRES_HOST="localhost:5432"
REDIS_HOST="localhost:6380"
QDRANT_URL="http://localhost:6336"
OLLAMA_URL="http://localhost:11434"

echo -e "\n${YELLOW}1. Testing PostgreSQL connection...${NC}"
if command -v psql > /dev/null; then
    if PGPASSWORD=postgres psql -h localhost -p 5432 -U postgres -d akamvp -c "SELECT 1;" > /dev/null 2>&1; then
        echo -e "PostgreSQL: ${GREEN}✓ Connected${NC}"
    else
        echo -e "PostgreSQL: ${RED}✗ Connection failed${NC}"
    fi
else
    echo -e "PostgreSQL: ${YELLOW}⚠ psql not installed, skipping direct test${NC}"
    # Test via Docker
    if docker exec monorepo-postgres-1 psql -U postgres -d akamvp -c "SELECT 1;" > /dev/null 2>&1; then
        echo -e "PostgreSQL (via Docker): ${GREEN}✓ Connected${NC}"
    else
        echo -e "PostgreSQL (via Docker): ${RED}✗ Connection failed${NC}"
    fi
fi

echo -e "\n${YELLOW}2. Testing Redis connection...${NC}"
if command -v redis-cli > /dev/null; then
    if redis-cli -h localhost -p 6380 ping | grep -q "PONG"; then
        echo -e "Redis: ${GREEN}✓ Connected${NC}"
    else
        echo -e "Redis: ${RED}✗ Connection failed${NC}"
    fi
else
    echo -e "Redis: ${YELLOW}⚠ redis-cli not installed, testing via HTTP${NC}"
    # Test via Docker
    if docker exec monorepo-redis-1 redis-cli ping | grep -q "PONG"; then
        echo -e "Redis (via Docker): ${GREEN}✓ Connected${NC}"
    else
        echo -e "Redis (via Docker): ${RED}✗ Connection failed${NC}"
    fi
fi

echo -e "\n${YELLOW}3. Testing Qdrant connection...${NC}"
if curl -s "$QDRANT_URL/collections" > /dev/null; then
    echo -e "Qdrant: ${GREEN}✓ Connected${NC}"
    # Show collections
    COLLECTIONS=$(curl -s "$QDRANT_URL/collections" | jq -r '.result.collections[].name' 2>/dev/null || echo "[]")
    if [ "$COLLECTIONS" != "[]" ] && [ -n "$COLLECTIONS" ]; then
        echo -e "  Collections: ${COLLECTIONS}"
    else
        echo -e "  Collections: ${YELLOW}None${NC}"
    fi
else
    echo -e "Qdrant: ${RED}✗ Connection failed${NC}"
fi

echo -e "\n${YELLOW}4. Testing Ollama connection...${NC}"
if curl -s "$OLLAMA_URL/api/tags" > /dev/null; then
    echo -e "Ollama: ${GREEN}✓ Connected${NC}"
    # Check for mxbai-embed-large model
    if curl -s "$OLLAMA_URL/api/tags" | jq -r '.models[].name' | grep -q "mxbai-embed-large"; then
        echo -e "  mxbai-embed-large model: ${GREEN}✓ Available${NC}"
    else
        echo -e "  mxbai-embed-large model: ${RED}✗ Not found${NC}"
        echo -e "  ${YELLOW}Run: ollama pull mxbai-embed-large${NC}"
    fi
else
    echo -e "Ollama: ${RED}✗ Connection failed${NC}"
    echo -e "  ${YELLOW}Make sure Ollama is running: ollama serve${NC}"
fi

echo -e "\n${YELLOW}5. Testing Docker services...${NC}"
DOCKER_SERVICES=("monorepo-postgres-1" "monorepo-redis-1" "monorepo-qdrant-1")

for service in "${DOCKER_SERVICES[@]}"; do
    if docker ps --format "table {{.Names}}" | grep -q "$service"; then
        STATUS=$(docker inspect --format='{{.State.Status}}' "$service" 2>/dev/null)
        if [ "$STATUS" = "running" ]; then
            echo -e "  $service: ${GREEN}✓ Running${NC}"
        else
            echo -e "  $service: ${RED}✗ Not running (Status: $STATUS)${NC}"
        fi
    else
        echo -e "  $service: ${RED}✗ Not found${NC}"
    fi
done

echo -e "\n${GREEN}✓ Infrastructure test completed!${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. If any services failed, run: docker compose up -d"
echo "2. If Ollama failed, run: ollama serve"
echo "3. If mxbai-embed-large missing, run: ollama pull mxbai-embed-large"

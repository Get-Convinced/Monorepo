#!/bin/bash

# Test script for service health endpoints
# Tests Backend, Document Processor, and Firecrawl services

echo "🚀 Testing Service Health"
echo "========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Service endpoints
BACKEND_URL="http://localhost:8082"
DOCUMENT_PROCESSOR_URL="http://localhost:8081"
FIRECRAWL_URL="http://localhost:3002"

echo -e "\n${YELLOW}1. Testing Backend service...${NC}"
if curl -s "$BACKEND_URL/health" > /dev/null; then
    RESPONSE=$(curl -s "$BACKEND_URL/health")
    echo -e "Backend: ${GREEN}✓ Healthy${NC}"
    echo "  Response: $RESPONSE"
else
    echo -e "Backend: ${RED}✗ Not responding${NC}"
    echo -e "  ${YELLOW}Make sure backend is running on port 8082${NC}"
fi

echo -e "\n${YELLOW}2. Testing Document Processor service...${NC}"
if curl -s "$DOCUMENT_PROCESSOR_URL/health" > /dev/null; then
    RESPONSE=$(curl -s "$DOCUMENT_PROCESSOR_URL/health")
    echo -e "Document Processor: ${GREEN}✓ Healthy${NC}"
    echo "  Response: $RESPONSE"
    
    # Test embedding configuration
    echo -e "\n  ${YELLOW}Checking embedding configuration...${NC}"
    EMBED_CONFIG=$(curl -s "$DOCUMENT_PROCESSOR_URL/embedding-config" | jq '.' 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "  Embedding Config:"
        echo "$EMBED_CONFIG" | jq '.' | sed 's/^/    /'
    else
        echo -e "  ${YELLOW}⚠ Could not retrieve embedding config${NC}"
    fi
else
    echo -e "Document Processor: ${RED}✗ Not responding${NC}"
    echo -e "  ${YELLOW}Make sure document processor is running on port 8081${NC}"
    echo -e "  ${YELLOW}Run: cd apps/document-processor && source .venv/bin/activate && uvicorn src.main:app --host 0.0.0.0 --port 8081${NC}"
fi

echo -e "\n${YELLOW}3. Testing Firecrawl service...${NC}"
if curl -s "$FIRECRAWL_URL/test" > /dev/null 2>&1; then
    RESPONSE=$(curl -s "$FIRECRAWL_URL/test")
    echo -e "Firecrawl: ${GREEN}✓ Healthy${NC}"
    echo "  Response: $RESPONSE"
elif curl -s "$FIRECRAWL_URL/" > /dev/null 2>&1; then
    # Try root endpoint if /test doesn't exist
    echo -e "Firecrawl: ${GREEN}✓ Responding${NC}"
    echo -e "  ${YELLOW}Note: Using root endpoint (official Firecrawl)${NC}"
else
    echo -e "Firecrawl: ${RED}✗ Not responding${NC}"
    echo -e "  ${YELLOW}Check if Firecrawl container is running: docker compose ps${NC}"
    echo -e "  ${YELLOW}Check logs: docker compose logs firecrawl${NC}"
fi

echo -e "\n${YELLOW}4. Testing service connectivity...${NC}"

# Test document processor -> Firecrawl
if curl -s "$DOCUMENT_PROCESSOR_URL/health" > /dev/null && curl -s "$FIRECRAWL_URL/" > /dev/null 2>&1; then
    echo -e "Document Processor ↔ Firecrawl: ${GREEN}✓ Both services reachable${NC}"
    
    # Test Firecrawl integration endpoint
    FIRECRAWL_TEST=$(curl -s -X POST "$DOCUMENT_PROCESSOR_URL/test-firecrawl" 2>/dev/null)
    if echo "$FIRECRAWL_TEST" | jq -e '.status == "ok"' > /dev/null 2>&1; then
        echo -e "Firecrawl Integration: ${GREEN}✓ Working${NC}"
    else
        echo -e "Firecrawl Integration: ${YELLOW}⚠ May have issues${NC}"
        echo "  Response: $FIRECRAWL_TEST"
    fi
else
    echo -e "Document Processor ↔ Firecrawl: ${RED}✗ One or both services unavailable${NC}"
fi

echo -e "\n${YELLOW}5. Service status summary...${NC}"

# Check which services are running
SERVICES_STATUS=""

if curl -s "$BACKEND_URL/health" > /dev/null 2>&1; then
    SERVICES_STATUS="${SERVICES_STATUS}Backend(✓) "
else
    SERVICES_STATUS="${SERVICES_STATUS}Backend(✗) "
fi

if curl -s "$DOCUMENT_PROCESSOR_URL/health" > /dev/null 2>&1; then
    SERVICES_STATUS="${SERVICES_STATUS}DocProcessor(✓) "
else
    SERVICES_STATUS="${SERVICES_STATUS}DocProcessor(✗) "
fi

if curl -s "$FIRECRAWL_URL/" > /dev/null 2>&1; then
    SERVICES_STATUS="${SERVICES_STATUS}Firecrawl(✓)"
else
    SERVICES_STATUS="${SERVICES_STATUS}Firecrawl(✗)"
fi

echo "Services: $SERVICES_STATUS"

echo -e "\n${GREEN}✓ Service health test completed!${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. If Backend failed: Check if backend service is running"
echo "2. If Document Processor failed: Start with uvicorn command above"
echo "3. If Firecrawl failed: Check Docker container status"

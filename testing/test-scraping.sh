#!/bin/bash

# Test script for complete scraping pipeline
# Tests Firecrawl scraping -> Document processing -> Qdrant ingestion

echo "🔥 Testing Complete Scraping Pipeline"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test URLs
DOCUMENT_PROCESSOR_URL="http://localhost:8081"
FIRECRAWL_URL="http://localhost:3002"
QDRANT_URL="http://localhost:6336"

echo -e "\n${YELLOW}1. Testing service health...${NC}"

# Test document processor
echo -n "Document Processor: "
if curl -s "$DOCUMENT_PROCESSOR_URL/health" > /dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    exit 1
fi

# Test Firecrawl
echo -n "Firecrawl: "
if curl -s "$FIRECRAWL_URL/test" > /dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    exit 1
fi

# Test Qdrant
echo -n "Qdrant: "
if curl -s "$QDRANT_URL/collections" > /dev/null; then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${RED}✗ FAILED${NC}"
    exit 1
fi

echo -e "\n${YELLOW}2. Testing embedding configuration...${NC}"
curl -s "$DOCUMENT_PROCESSOR_URL/embedding-config" | jq '.'

echo -e "\n${YELLOW}3. Testing embedding generation...${NC}"
curl -X POST "$DOCUMENT_PROCESSOR_URL/test-embeddings" | jq '.'

echo -e "\n${YELLOW}4. Testing Firecrawl integration...${NC}"
curl -X POST "$DOCUMENT_PROCESSOR_URL/test-firecrawl" | jq '.'

echo -e "\n${YELLOW}5. Listing existing collections...${NC}"
curl -s "$DOCUMENT_PROCESSOR_URL/collections" | jq '.'

echo -e "\n${YELLOW}6. Testing website scraping (this will take a moment)...${NC}"
echo "Scraping https://example.com..."

SCRAPE_RESPONSE=$(curl -s -X POST "$DOCUMENT_PROCESSOR_URL/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "collection_name": "test_collection",
    "metadata": {"source": "test_script", "scraped_by": "integration_test"}
  }')

echo "Scrape job response:"
echo "$SCRAPE_RESPONSE" | jq '.'

JOB_ID=$(echo "$SCRAPE_RESPONSE" | jq -r '.job_id')
echo -e "\nJob ID: ${YELLOW}$JOB_ID${NC}"

echo -e "\n${YELLOW}7. Waiting for processing to complete...${NC}"
echo "Note: This runs in the background. Check logs with: docker compose logs -f"

# Wait a bit for processing
sleep 5

echo -e "\n${YELLOW}8. Checking collections after scraping...${NC}"
curl -s "$DOCUMENT_PROCESSOR_URL/collections" | jq '.'

echo -e "\n${YELLOW}9. Getting collection info...${NC}"
curl -s "$DOCUMENT_PROCESSOR_URL/collections/test_collection/info" | jq '.'

echo -e "\n${GREEN}✓ Integration test completed!${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Check the document processor logs: docker compose logs document-processor"
echo "2. Check Firecrawl logs: docker compose logs firecrawl"
echo "3. Query the collection directly via Qdrant API: curl -s http://localhost:6336/collections/test_collection"
echo -e "\n${YELLOW}Note:${NC} Using Ollama embeddings with mxbai-embed-large model. Make sure Ollama is running!"
echo "To switch to OpenAI embeddings, set EMBEDDING_PROVIDER=openai and OPENAI_API_KEY in .env.local"

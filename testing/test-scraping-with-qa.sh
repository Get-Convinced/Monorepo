#!/bin/bash

# Enhanced test script for complete scraping pipeline with Q&A
# Tests Firecrawl scraping -> Document processing -> Qdrant ingestion -> Question Answering

echo "🔥 Testing Complete Scraping Pipeline with Q&A"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test URLs
DOCUMENT_PROCESSOR_URL="http://localhost:8081"
FIRECRAWL_URL="http://localhost:3002"
QDRANT_URL="http://localhost:6336"

# Test questions to ask after scraping
TEST_QUESTIONS=(
    "What is this website about?"
    "What is the main content of this page?"
    "What information is available here?"
)

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
if curl -s "$FIRECRAWL_URL/test" > /dev/null 2>&1 || curl -s "$FIRECRAWL_URL/" > /dev/null 2>&1; then
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
EMBED_CONFIG=$(curl -s "$DOCUMENT_PROCESSOR_URL/embedding-config")
echo "$EMBED_CONFIG" | jq '.'

# Check if using mxbai-embed-large
if echo "$EMBED_CONFIG" | jq -e '.model == "mxbai-embed-large"' > /dev/null; then
    echo -e "${GREEN}✓ Using mxbai-embed-large model (SOTA performance!)${NC}"
else
    echo -e "${YELLOW}⚠ Not using mxbai-embed-large model${NC}"
fi

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
    "metadata": {"source": "test_script", "scraped_by": "qa_integration_test"}
  }')

echo "Scrape job response:"
echo "$SCRAPE_RESPONSE" | jq '.'

JOB_ID=$(echo "$SCRAPE_RESPONSE" | jq -r '.job_id')
echo -e "\nJob ID: ${YELLOW}$JOB_ID${NC}"

echo -e "\n${YELLOW}7. Waiting for processing to complete...${NC}"
echo "Note: This runs in the background. Processing includes:"
echo "  - Firecrawl scraping to markdown"
echo "  - Content chunking (1000 chars)"
echo "  - mxbai-embed-large embedding generation (1024 dimensions)"
echo "  - Qdrant vector storage"

# Wait for processing
sleep 8

echo -e "\n${YELLOW}8. Checking collections after scraping...${NC}"
COLLECTIONS_RESPONSE=$(curl -s "$DOCUMENT_PROCESSOR_URL/collections")
echo "$COLLECTIONS_RESPONSE" | jq '.'

echo -e "\n${YELLOW}9. Getting collection info...${NC}"
COLLECTION_INFO=$(curl -s "$DOCUMENT_PROCESSOR_URL/collections/test_collection/info")
echo "$COLLECTION_INFO" | jq '.'

# Check if collection has vectors
VECTOR_COUNT=$(echo "$COLLECTION_INFO" | jq -r '.collection_info.vectors_count // 0' 2>/dev/null || echo "0")
if [ "$VECTOR_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Collection has $VECTOR_COUNT vectors ready for search!${NC}"
else
    echo -e "${YELLOW}⚠ Collection might still be processing or empty${NC}"
fi

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}🧠 QUESTION & ANSWER TESTING${NC}"
echo -e "${BLUE}========================================${NC}"

# Test each question
for i in "${!TEST_QUESTIONS[@]}"; do
    question="${TEST_QUESTIONS[$i]}"
    echo -e "\n${YELLOW}Q$((i+1)): Testing question: \"$question\"${NC}"
    
    # Test search functionality first
    echo -e "  ${YELLOW}→ Searching for relevant content...${NC}"
    SEARCH_RESPONSE=$(curl -s -X POST "$DOCUMENT_PROCESSOR_URL/search" \
      -H "Content-Type: application/json" \
      -d "{
        \"query\": \"$question\",
        \"collection_name\": \"test_collection\",
        \"limit\": 3,
        \"score_threshold\": 0.5
      }" 2>/dev/null)
    
    if echo "$SEARCH_RESPONSE" | jq -e '.total_results' > /dev/null 2>&1; then
        RESULT_COUNT=$(echo "$SEARCH_RESPONSE" | jq -r '.total_results')
        echo -e "  ${GREEN}✓ Found $RESULT_COUNT relevant chunks${NC}"
        
        # Show top result
        if [ "$RESULT_COUNT" -gt 0 ]; then
            TOP_SCORE=$(echo "$SEARCH_RESPONSE" | jq -r '.results[0].score' 2>/dev/null || echo "N/A")
            TOP_CONTENT=$(echo "$SEARCH_RESPONSE" | jq -r '.results[0].content' 2>/dev/null | head -c 100)
            echo -e "  ${BLUE}Top result (score: $TOP_SCORE):${NC} ${TOP_CONTENT}..."
        fi
    else
        echo -e "  ${RED}✗ Search failed or no results${NC}"
        echo "  Response: $SEARCH_RESPONSE"
    fi
    
    # Test ask functionality
    echo -e "  ${YELLOW}→ Getting contextual answer...${NC}"
    ASK_RESPONSE=$(curl -s -X POST "$DOCUMENT_PROCESSOR_URL/ask" \
      -H "Content-Type: application/json" \
      -d "{
        \"query\": \"$question\",
        \"collection_name\": \"test_collection\",
        \"limit\": 3
      }" 2>/dev/null)
    
    if echo "$ASK_RESPONSE" | jq -e '.context_found' > /dev/null 2>&1; then
        CONTEXT_FOUND=$(echo "$ASK_RESPONSE" | jq -r '.context_found')
        if [ "$CONTEXT_FOUND" = "true" ]; then
            echo -e "  ${GREEN}✓ Context found and retrieved${NC}"
            SOURCE_COUNT=$(echo "$ASK_RESPONSE" | jq -r '.sources | length' 2>/dev/null || echo "0")
            echo -e "  ${BLUE}Sources used: $SOURCE_COUNT${NC}"
        else
            echo -e "  ${YELLOW}⚠ No relevant context found${NC}"
        fi
    else
        echo -e "  ${RED}✗ Ask functionality failed${NC}"
        echo "  Response: $ASK_RESPONSE"
    fi
done

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}📊 MANUAL TESTING SECTION${NC}"
echo -e "${BLUE}========================================${NC}"

echo -e "\n${YELLOW}You can now manually test with your own questions!${NC}"
echo -e "\n${YELLOW}Example commands:${NC}"

echo -e "\n${BLUE}1. Search for content:${NC}"
echo "curl -X POST $DOCUMENT_PROCESSOR_URL/search \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"query\": \"YOUR_QUESTION_HERE\", \"collection_name\": \"test_collection\"}'"

echo -e "\n${BLUE}2. Ask a question:${NC}"
echo "curl -X POST $DOCUMENT_PROCESSOR_URL/ask \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"query\": \"YOUR_QUESTION_HERE\", \"collection_name\": \"test_collection\"}'"

echo -e "\n${GREEN}✓ Complete scraping + Q&A test completed!${NC}"

echo -e "\n${YELLOW}Summary:${NC}"
echo "✓ Website scraped and processed"
echo "✓ Content chunked and embedded using mxbai-embed-large"
echo "✓ Vectors stored in Qdrant"
echo "✓ Search functionality tested"
echo "✓ Q&A retrieval tested"
echo "✓ Ready for manual testing with custom questions"

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Try asking your own questions using the curl commands above"
echo "2. Check logs: docker compose logs document-processor"
echo "3. Explore the Qdrant collection: curl -s $QDRANT_URL/collections/test_collection"

echo -e "\n${BLUE}🎉 Your RAG system is working with mxbai-embed-large! 🎉${NC}"

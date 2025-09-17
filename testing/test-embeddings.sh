#!/bin/bash

# Test script for embedding functionality
# Tests Ollama and OpenAI embedding generation

echo "🧠 Testing Embedding Generation"
echo "==============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Service endpoints
DOCUMENT_PROCESSOR_URL="http://localhost:8081"
OLLAMA_URL="http://localhost:11434"

echo -e "\n${YELLOW}1. Testing Ollama embedding generation...${NC}"

# Test direct Ollama API
TEST_TEXT="This is a test sentence for embedding generation."
OLLAMA_RESPONSE=$(curl -s "$OLLAMA_URL/api/embeddings" -d "{\"model\": \"mxbai-embed-large\", \"prompt\": \"Represent this sentence for searching relevant passages: $TEST_TEXT\"}" 2>/dev/null)

if echo "$OLLAMA_RESPONSE" | jq -e '.embedding' > /dev/null 2>&1; then
    EMBEDDING_DIM=$(echo "$OLLAMA_RESPONSE" | jq '.embedding | length')
    echo -e "Ollama Direct API: ${GREEN}✓ Working${NC}"
    echo "  Model: mxbai-embed-large"
    echo "  Embedding dimension: $EMBEDDING_DIM"
    echo "  Expected dimension: 1024"
    
    if [ "$EMBEDDING_DIM" = "1024" ]; then
        echo -e "  Dimension check: ${GREEN}✓ Correct${NC}"
    else
        echo -e "  Dimension check: ${YELLOW}⚠ Unexpected dimension${NC}"
    fi
else
    echo -e "Ollama Direct API: ${RED}✗ Failed${NC}"
    echo "  Error: $OLLAMA_RESPONSE"
    echo -e "  ${YELLOW}Make sure mxbai-embed-large model is available: ollama pull mxbai-embed-large${NC}"
fi

echo -e "\n${YELLOW}2. Testing Document Processor embedding endpoint...${NC}"

# Test document processor embedding endpoint
if curl -s "$DOCUMENT_PROCESSOR_URL/health" > /dev/null; then
    EMBED_TEST_RESPONSE=$(curl -s -X POST "$DOCUMENT_PROCESSOR_URL/test-embeddings" 2>/dev/null)
    
    if echo "$EMBED_TEST_RESPONSE" | jq -e '.test_successful == true' > /dev/null 2>&1; then
        echo -e "Document Processor Embeddings: ${GREEN}✓ Working${NC}"
        
        # Extract details
        PROVIDER=$(echo "$EMBED_TEST_RESPONSE" | jq -r '.provider')
        MODEL=$(echo "$EMBED_TEST_RESPONSE" | jq -r '.model')
        ACTUAL_DIM=$(echo "$EMBED_TEST_RESPONSE" | jq -r '.dimension')
        EXPECTED_DIM=$(echo "$EMBED_TEST_RESPONSE" | jq -r '.expected_dimension')
        
        echo "  Provider: $PROVIDER"
        echo "  Model: $MODEL"
        echo "  Actual dimension: $ACTUAL_DIM"
        echo "  Expected dimension: $EXPECTED_DIM"
        
        if [ "$ACTUAL_DIM" = "$EXPECTED_DIM" ]; then
            echo -e "  Dimension match: ${GREEN}✓ Correct${NC}"
        else
            echo -e "  Dimension match: ${YELLOW}⚠ Mismatch${NC}"
        fi
    else
        echo -e "Document Processor Embeddings: ${RED}✗ Failed${NC}"
        ERROR_MSG=$(echo "$EMBED_TEST_RESPONSE" | jq -r '.error // "Unknown error"')
        echo "  Error: $ERROR_MSG"
        echo "  Full response: $EMBED_TEST_RESPONSE"
    fi
else
    echo -e "Document Processor Embeddings: ${RED}✗ Service not available${NC}"
fi

echo -e "\n${YELLOW}3. Testing embedding configuration...${NC}"

if curl -s "$DOCUMENT_PROCESSOR_URL/health" > /dev/null; then
    CONFIG_RESPONSE=$(curl -s "$DOCUMENT_PROCESSOR_URL/embedding-config" 2>/dev/null)
    
    if echo "$CONFIG_RESPONSE" | jq -e '.' > /dev/null 2>&1; then
        echo -e "Embedding Configuration: ${GREEN}✓ Retrieved${NC}"
        echo "$CONFIG_RESPONSE" | jq '.' | sed 's/^/  /'
        
        # Check if using Ollama
        PROVIDER=$(echo "$CONFIG_RESPONSE" | jq -r '.provider')
        if [ "$PROVIDER" = "ollama" ]; then
            OLLAMA_URL_CONFIG=$(echo "$CONFIG_RESPONSE" | jq -r '.ollama_url')
            echo -e "\n  ${YELLOW}Ollama Configuration:${NC}"
            echo "    URL: $OLLAMA_URL_CONFIG"
            
            # Test connectivity to configured Ollama URL
            if curl -s "$OLLAMA_URL_CONFIG/api/tags" > /dev/null 2>&1; then
                echo -e "    Connectivity: ${GREEN}✓ Reachable${NC}"
            else
                echo -e "    Connectivity: ${RED}✗ Not reachable${NC}"
            fi
        fi
    else
        echo -e "Embedding Configuration: ${RED}✗ Failed to retrieve${NC}"
        echo "  Response: $CONFIG_RESPONSE"
    fi
fi

echo -e "\n${YELLOW}4. Performance test...${NC}"

# Test embedding generation speed
if curl -s "$DOCUMENT_PROCESSOR_URL/health" > /dev/null; then
    echo "Testing embedding generation speed..."
    
    START_TIME=$(date +%s.%N)
    PERF_RESPONSE=$(curl -s -X POST "$DOCUMENT_PROCESSOR_URL/test-embeddings" 2>/dev/null)
    END_TIME=$(date +%s.%N)
    
    if echo "$PERF_RESPONSE" | jq -e '.test_successful == true' > /dev/null 2>&1; then
        DURATION=$(echo "$END_TIME - $START_TIME" | bc 2>/dev/null || echo "N/A")
        echo -e "  Generation time: ${GREEN}${DURATION}s${NC}"
        
        # Rough performance assessment
        if command -v bc > /dev/null && [ "$DURATION" != "N/A" ]; then
            if (( $(echo "$DURATION < 2.0" | bc -l) )); then
                echo -e "  Performance: ${GREEN}✓ Fast${NC}"
            elif (( $(echo "$DURATION < 5.0" | bc -l) )); then
                echo -e "  Performance: ${YELLOW}⚠ Moderate${NC}"
            else
                echo -e "  Performance: ${RED}⚠ Slow${NC}"
            fi
        fi
    else
        echo -e "  Performance test: ${RED}✗ Failed${NC}"
    fi
fi

echo -e "\n${GREEN}✓ Embedding test completed!${NC}"
echo -e "\n${YELLOW}Summary:${NC}"
echo "- Ollama direct API test"
echo "- Document processor embedding integration test"
echo "- Configuration validation"
echo "- Performance assessment"

echo -e "\n${YELLOW}Troubleshooting:${NC}"
echo "1. If Ollama tests fail: Ensure 'ollama serve' is running"
echo "2. If model missing: Run 'ollama pull mxbai-embed-large'"
echo "3. If dimension mismatch: Check EMBEDDING_DIMENSION in .env.local"
echo "4. If slow performance: Consider using a smaller model or GPU acceleration"

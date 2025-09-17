#!/bin/bash

# Complete integration test suite
# Runs all tests in sequence to validate the entire system

echo "🧪 AI Knowledge Agent - Complete Integration Test"
echo "================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results tracking
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

# Function to run a test and track results
run_test() {
    local test_name="$1"
    local test_script="$2"
    
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}Running: $test_name${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    if [ -f "$test_script" ] && [ -x "$test_script" ]; then
        if ./"$test_script"; then
            echo -e "\n${GREEN}✓ $test_name PASSED${NC}"
            ((TESTS_PASSED++))
        else
            echo -e "\n${RED}✗ $test_name FAILED${NC}"
            ((TESTS_FAILED++))
            FAILED_TESTS+=("$test_name")
        fi
    else
        echo -e "\n${RED}✗ $test_name - Script not found or not executable${NC}"
        ((TESTS_FAILED++))
        FAILED_TESTS+=("$test_name")
    fi
}

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}Starting comprehensive integration test...${NC}"
echo -e "${YELLOW}Test directory: $SCRIPT_DIR${NC}"
echo -e "${YELLOW}Timestamp: $(date)${NC}"

# Pre-flight checks
echo -e "\n${YELLOW}Pre-flight checks...${NC}"

# Check if we're in the right directory
if [ ! -f "test-infrastructure.sh" ]; then
    echo -e "${RED}✗ Test scripts not found. Make sure you're in the testing directory.${NC}"
    exit 1
fi

# Make sure all test scripts are executable
chmod +x *.sh

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if required services are up
echo "Checking Docker services..."
REQUIRED_SERVICES=("postgres" "redis" "qdrant")
for service in "${REQUIRED_SERVICES[@]}"; do
    if docker compose ps | grep -q "$service.*Up"; then
        echo -e "  $service: ${GREEN}✓ Running${NC}"
    else
        echo -e "  $service: ${RED}✗ Not running${NC}"
        echo -e "${YELLOW}Starting Docker services...${NC}"
        cd .. && docker compose up -d && cd testing
        sleep 5
        break
    fi
done

echo -e "\n${YELLOW}Running test suite...${NC}"

# Run tests in sequence
run_test "Infrastructure Test" "test-infrastructure.sh"
run_test "Services Test" "test-services.sh"
run_test "Embeddings Test" "test-embeddings.sh"
run_test "Scraping Pipeline Test" "test-scraping.sh"

# Final results
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}INTEGRATION TEST RESULTS${NC}"
echo -e "${BLUE}========================================${NC}"

TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
echo -e "Total tests run: $TOTAL_TESTS"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}🎉 ALL TESTS PASSED! 🎉${NC}"
    echo -e "${GREEN}The AI Knowledge Agent system is working correctly.${NC}"
    
    echo -e "\n${YELLOW}System is ready for:${NC}"
    echo "✓ Website scraping via Firecrawl"
    echo "✓ Content processing and chunking"
    echo "✓ Local embedding generation with Ollama"
    echo "✓ Vector storage in Qdrant"
    echo "✓ End-to-end knowledge ingestion pipeline"
    
    exit 0
else
    echo -e "\n${RED}❌ SOME TESTS FAILED ❌${NC}"
    echo -e "${RED}Failed tests:${NC}"
    for test in "${FAILED_TESTS[@]}"; do
        echo -e "  - $test"
    done
    
    echo -e "\n${YELLOW}Troubleshooting steps:${NC}"
    echo "1. Check service logs: docker compose logs [service_name]"
    echo "2. Ensure all services are running: docker compose ps"
    echo "3. Check Ollama is running: ollama serve"
    echo "4. Verify model is available: ollama list"
    echo "5. Check document processor: curl http://localhost:8081/health"
    
    exit 1
fi

#!/bin/bash

# Extract Ragie API debug information from CloudWatch logs
# Usage: ./extract-ragie-debug.sh

echo "=== Extracting Ragie API debug information ==="
echo ""

# Get logs from the last 5 minutes
LOGS=$(aws logs tail /ecs/get-convinced-prod --region ap-south-1 --since 5m --format short 2>&1)

# Extract curl command
echo "📋 **CURL COMMAND:**"
echo "---"
echo "$LOGS" | grep -A 20 "Equivalent curl command" | grep "curl_command" | sed 's/.*curl_command": "//g' | sed 's/".*//g' | sed 's/\\n/\n/g'
echo ""
echo "---"
echo ""

# Extract form data
echo "📦 **FORM DATA SENT:**"
echo "---"
echo "$LOGS" | grep "form_data_keys\|form_data_values" | tail -2
echo ""
echo "---"
echo ""

# Extract file info
echo "📄 **FILE INFO:**"
echo "---"
echo "$LOGS" | grep "file_info" | tail -1
echo ""
echo "---"
echo ""

# Extract error response
echo "❌ **ERROR RESPONSE (if any):**"
echo "---"
echo "$LOGS" | grep -A 5 "response_body" | grep -v "null" | tail -10
echo ""
echo "---"
echo ""

# Extract status code
echo "📊 **STATUS CODE:**"
echo "---"
echo "$LOGS" | grep "HTTP/1.1" | grep "api.ragie.ai" | tail -1
echo ""
echo "---"

echo ""
echo "✅ **To test locally:**"
echo "1. Copy the curl command above"
echo "2. Replace YOUR_RAGIE_API_KEY with: $(aws secretsmanager get-secret-value --secret-id get-convinced-prod-app-secrets --region ap-south-1 --query 'SecretString' --output text | jq -r '.RAGIE_API_KEY' | head -c 20)..."
echo "3. Replace the file path with a local test file"
echo "4. Run the curl command"
echo ""
echo "📧 **To share with Ragie team:**"
echo "Share the curl command (with your real API key) and the error response body"

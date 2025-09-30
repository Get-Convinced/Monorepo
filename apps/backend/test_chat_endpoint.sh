#!/bin/bash
# Test script for chat endpoint with real Frontegg token

echo "🧪 Testing Chat Endpoint"
echo "========================"
echo ""

# Real Frontegg token and org ID
AUTH_TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ijg0M2JiZTkzIn0.eyJzdWIiOiJjM2UxMzQ0OC03ZDA5LTQ3N2QtODc5Ny1lOWUwMGRjMGNjYzgiLCJuYW1lIjoiR2F1dGFtIFNhYmhhaGl0IiwiZW1haWwiOiJnYXV0YW1nc2FiaGFoaXRAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsIm1ldGFkYXRhIjp7fSwicm9sZXMiOlsiQWRtaW4iXSwicGVybWlzc2lvbnMiOlsiZmUuYWNjb3VudC1zZXR0aW5ncy5yZWFkLmFwcCIsImZlLmNvbm5lY3Rpdml0eS4qIiwiZmUuc2VjdXJlLioiXSwidGVuYW50SWQiOiIyZGI4OTU3ZC05Yzk3LTRiNmEtYjc5ZC1jZmUwZTZiOTQwZmUiLCJ0ZW5hbnRJZHMiOlsiMmRiODk1N2QtOWM5Ny00YjZhLWI3OWQtY2ZlMGU2Yjk0MGZlIl0sInByb2ZpbGVQaWN0dXJlVXJsIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jSVVHUHNUSWlwczJrc0xxSlZscjZYN29VTV9ZTzdvQVNJQ1FkV19FTEdCVllvcGpHblJjZz1zOTYtYyIsInNpZCI6ImQyMTFlOTEyLThjYjEtNDEyOC1hYWUxLTdlMTgzYWY3YzFlNiIsInR5cGUiOiJ1c2VyVG9rZW4iLCJhcHBsaWNhdGlvbklkIjoiZmNkYmNiMDYtN2M5ZC00NjNkLTliMDQtYzEyZTJmMWI4ODlhIiwibm9uY2UiOiJ6bGJsVDExc01qcDVzemFIIiwiYXVkIjoiODQzYmJlOTMtZWI4ZC00OWNmLWI1M2ItOTBiZDYwMjY1YzgyIiwiaXNzIjoiaHR0cHM6Ly9hcHAtZ3Jpa2x4bm5zeGFnLmZyb250ZWdnLmNvbSIsImlhdCI6MTc1OTE2NTcxNCwiZXhwIjoxNzU5MjUyMTE0fQ.MUlulN1KGmxx4dqg2EhYfdbSgDDtALAPCgn3-15c-v0U4Y9zsZ2-CbRJcSqDZAL8rPwNfoSJJnxYiIw909FzzH8v__C3zsGqHDQGeTO0qgKFXUXpAXGKhBpAb22lgQu1TgIxUBqlGA83fBtRwk7aqZbGypNn_ln8zb2ZtJavtsfvRRRQUEGACSovvO2dHtwZnFRhc5OBZHFbHaXvkT8iCH8QAKOlzGvsKR1eM0XE8OkZw_aGgH5AtUfnsHw3z2X1e-CB3V6ItKsAFh7sfOa2vs2D2-_jxMpBLmpH7H82PRUOFSGRcgAePffcVKY2DfwjwGPiuZbqtD-U8t-fSrBilA"
ORG_ID="2db8957d-9c97-4b6a-b79d-cfe0e6b940fe"
BASE_URL="http://localhost:8001"

echo "📍 Endpoint: GET $BASE_URL/api/v1/chat/session"
echo "🔑 Organization: $ORG_ID"
echo ""

# Make the request
response=$(curl -s -w "\n%{http_code}" -X GET "$BASE_URL/api/v1/chat/session" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "X-Organization-ID: $ORG_ID" \
  -H "Content-Type: application/json")

# Extract status code and body
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

echo "📊 Response Status: $http_code"
echo "📦 Response Body:"
echo "$body" | python3 -m json.tool 2>/dev/null || echo "$body"
echo ""

# Check for success
if [ "$http_code" = "200" ]; then
    echo "✅ SUCCESS - Chat endpoint is working!"
else
    echo "❌ FAILED - Status code: $http_code"
    
    # Check backend logs for errors
    echo ""
    echo "🔍 Checking backend logs for errors..."
    if [ -f "/tmp/backend_new.log" ]; then
        tail -30 /tmp/backend_new.log | grep -i "error\|ConnectionDoesNotExist\|connection.*closed" | tail -5
    fi
fi

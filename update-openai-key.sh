#!/bin/bash

# Script to update OpenAI API key in AWS Secrets Manager
# Usage: ./update-openai-key.sh YOUR_NEW_OPENAI_API_KEY

if [ -z "$1" ]; then
    echo "❌ Error: OpenAI API key is required"
    echo ""
    echo "Usage: ./update-openai-key.sh YOUR_NEW_OPENAI_API_KEY"
    echo ""
    echo "Example:"
    echo "  ./update-openai-key.sh sk-proj-abc123..."
    exit 1
fi

NEW_KEY="$1"

echo "=== Validating new OpenAI API key ==="
VALIDATION=$(curl -s https://api.openai.com/v1/models -H "Authorization: Bearer $NEW_KEY" | jq -r '.error.code // "valid"')

if [ "$VALIDATION" != "valid" ]; then
    echo "❌ Error: The provided API key is invalid"
    echo "OpenAI returned: $VALIDATION"
    exit 1
fi

echo "✅ API key is valid!"
echo ""

echo "=== Fetching current secrets ==="
CURRENT_SECRETS=$(aws secretsmanager get-secret-value \
    --secret-id get-convinced-prod-app-secrets \
    --region ap-south-1 \
    --query 'SecretString' \
    --output text)

echo "✅ Current secrets fetched"
echo ""

echo "=== Updating OpenAI API key ==="
UPDATED_SECRETS=$(echo "$CURRENT_SECRETS" | jq --arg key "$NEW_KEY" '.OPENAI_API_KEY = $key')

aws secretsmanager update-secret \
    --secret-id get-convinced-prod-app-secrets \
    --region ap-south-1 \
    --secret-string "$UPDATED_SECRETS" \
    --output text > /dev/null

echo "✅ OpenAI API key updated in Secrets Manager"
echo ""

echo "=== Forcing ECS deployment to pick up new secret ==="
aws ecs update-service \
    --cluster get-convinced-prod-cluster \
    --service backend \
    --region ap-south-1 \
    --force-new-deployment \
    --query 'service.status' \
    --output text > /dev/null

echo "✅ ECS deployment triggered"
echo ""
echo "🎉 **Done!**"
echo ""
echo "The backend will restart in ~2 minutes with the new OpenAI API key."
echo "You can monitor the deployment with:"
echo "  aws ecs describe-services --cluster get-convinced-prod-cluster --services backend --region ap-south-1"

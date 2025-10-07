#!/bin/bash
set -e

# Backend Deployment Script - Fix for S3 Timeout Issue
# This script deploys the backend with the S3 service initialization fix

echo "=================================="
echo "Backend Deployment - S3 Fix"
echo "=================================="
echo ""

# Check AWS credentials
echo "Checking AWS credentials..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "✓ Deploying to AWS account: $ACCOUNT_ID"

if [ "$ACCOUNT_ID" != "362479991031" ]; then
    echo "❌ ERROR: Wrong AWS account! Expected 362479991031, got $ACCOUNT_ID"
    echo "Please set AWS_PROFILE=get-convinced or configure correct credentials"
    exit 1
fi

echo ""
echo "Step 1: Building Docker image..."
docker build --platform linux/amd64 \
    -t 362479991031.dkr.ecr.ap-south-1.amazonaws.com/get-convinced-prod-backend:latest \
    -f apps/backend/Dockerfile .

echo ""
echo "Step 2: Logging into ECR..."
aws ecr get-login-password --region ap-south-1 | \
    docker login --username AWS --password-stdin \
    362479991031.dkr.ecr.ap-south-1.amazonaws.com

echo ""
echo "Step 3: Pushing image to ECR..."
docker push 362479991031.dkr.ecr.ap-south-1.amazonaws.com/get-convinced-prod-backend:latest

echo ""
echo "Step 4: Forcing new ECS deployment..."
aws ecs update-service \
    --cluster get-convinced-prod-cluster \
    --service backend \
    --force-new-deployment \
    --region ap-south-1 \
    --output json | jq '.service.deployments[0] | {status: .status, desiredCount: .desiredCount, runningCount: .runningCount}'

echo ""
echo "✓ Deployment initiated!"
echo ""
echo "Monitoring deployment progress..."
echo "Press Ctrl+C to stop monitoring (deployment will continue)"
echo ""

# Monitor deployment for 2 minutes
for i in {1..24}; do
    sleep 5
    STATUS=$(aws ecs describe-services \
        --cluster get-convinced-prod-cluster \
        --services backend \
        --region ap-south-1 \
        --query 'services[0].deployments[0].{status:status,running:runningCount,desired:desiredCount}' \
        --output json | jq -r '.status + " - Running: " + (.running|tostring) + "/" + (.desired|tostring)')
    echo "[$i/24] $STATUS"
    
    # Check if deployment is complete
    RUNNING=$(aws ecs describe-services \
        --cluster get-convinced-prod-cluster \
        --services backend \
        --region ap-south-1 \
        --query 'services[0].runningCount' \
        --output text)
    DESIRED=$(aws ecs describe-services \
        --cluster get-convinced-prod-cluster \
        --services backend \
        --region ap-south-1 \
        --query 'services[0].desiredCount' \
        --output text)
    
    if [ "$RUNNING" = "$DESIRED" ] && [ "$RUNNING" != "0" ]; then
        echo ""
        echo "✓ Deployment complete!"
        break
    fi
done

echo ""
echo "Testing backend health..."
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://api.getconvinced.ai/health --max-time 5)

if [ "$HEALTH_STATUS" = "200" ]; then
    echo "✓ Backend is healthy!"
else
    echo "⚠ Backend health check returned: $HEALTH_STATUS"
fi

echo ""
echo "=================================="
echo "Deployment Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Test the /documents endpoint in your browser"
echo "2. Check CloudWatch logs if issues persist:"
echo "   aws logs tail /ecs/get-convinced-prod --follow --region ap-south-1"
echo ""

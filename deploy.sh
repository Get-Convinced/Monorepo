#!/bin/bash

# Deploy AI Knowledge Agent to AWS ECS
# Builds Docker image, pushes to ECR, and updates ECS service

set -e

echo "🚀 AI Knowledge Agent Deployment"
echo "=================================="
echo ""

# Configuration
AWS_PROFILE="${AWS_PROFILE:-get-convinced}"
AWS_REGION="ap-south-1"
ECR_REPOSITORY="362479991031.dkr.ecr.ap-south-1.amazonaws.com/get-convinced-prod-backend"
ECS_CLUSTER="get-convinced-prod-cluster"
ECS_SERVICE="backend"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD)}"

echo "📋 Configuration:"
echo "  AWS Profile: $AWS_PROFILE"
echo "  AWS Region: $AWS_REGION"
echo "  ECR Repository: $ECR_REPOSITORY"
echo "  Image Tag: $IMAGE_TAG"
echo "  ECS Cluster: $ECS_CLUSTER"
echo "  ECS Service: $ECS_SERVICE"
echo ""

# Step 1: Authenticate with ECR
echo "🔐 Step 1: Authenticating with ECR..."
aws ecr get-login-password \
    --profile "$AWS_PROFILE" \
    --region "$AWS_REGION" | \
    docker login \
    --username AWS \
    --password-stdin "$ECR_REPOSITORY"
echo "✅ ECR authentication successful"
echo ""

# Step 2: Build Docker image
echo "🏗️  Step 2: Building Docker image..."
docker build \
    -f apps/backend/Dockerfile \
    -t "$ECR_REPOSITORY:$IMAGE_TAG" \
    -t "$ECR_REPOSITORY:latest" \
    --platform linux/amd64 \
    .
echo "✅ Docker image built successfully"
echo ""

# Step 3: Push to ECR
echo "📤 Step 3: Pushing image to ECR..."
docker push "$ECR_REPOSITORY:$IMAGE_TAG"
docker push "$ECR_REPOSITORY:latest"
echo "✅ Image pushed to ECR"
echo ""

# Step 4: Update ECS service
echo "🔄 Step 4: Updating ECS service..."
aws ecs update-service \
    --profile "$AWS_PROFILE" \
    --region "$AWS_REGION" \
    --cluster "$ECS_CLUSTER" \
    --service "$ECS_SERVICE" \
    --force-new-deployment \
    --no-cli-pager
echo "✅ ECS service update initiated"
echo ""

# Step 5: Wait for deployment
echo "⏳ Step 5: Waiting for deployment to complete..."
echo "   This may take 3-5 minutes..."
aws ecs wait services-stable \
    --profile "$AWS_PROFILE" \
    --region "$AWS_REGION" \
    --cluster "$ECS_CLUSTER" \
    --services "$ECS_SERVICE"
echo "✅ Deployment completed successfully!"
echo ""

# Step 6: Verify deployment
echo "🔍 Step 6: Verifying deployment..."
BACKEND_URL="http://get-convinced-prod-alb-638605407.ap-south-1.elb.amazonaws.com"
echo "   Testing health endpoint: $BACKEND_URL/health"
echo ""

sleep 10  # Give ALB a moment to route to new tasks

HEALTH_RESPONSE=$(curl -s "$BACKEND_URL/health" || echo "failed")
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ Health check passed!"
    echo ""
    echo "$HEALTH_RESPONSE" | jq '.' 2>/dev/null || echo "$HEALTH_RESPONSE"
else
    echo "⚠️  Health check failed or service not ready yet"
    echo "   Response: $HEALTH_RESPONSE"
    echo "   Check ECS logs: https://console.aws.amazon.com/ecs/"
fi
echo ""

echo "🎉 Deployment Summary"
echo "===================="
echo "✅ Image: $ECR_REPOSITORY:$IMAGE_TAG"
echo "✅ Cluster: $ECS_CLUSTER"
echo "✅ Service: $ECS_SERVICE"
echo "✅ Backend URL: $BACKEND_URL"
echo ""
echo "📊 View logs:"
echo "   aws ecs describe-services --profile $AWS_PROFILE --cluster $ECS_CLUSTER --services $ECS_SERVICE"
echo ""
echo "🔧 Rollback (if needed):"
echo "   aws ecs update-service --profile $AWS_PROFILE --cluster $ECS_CLUSTER --service $ECS_SERVICE --task-definition <previous-task-def>"
echo ""
echo "✨ Deployment complete!"

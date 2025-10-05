# Staging Environment

This directory contains the Terraform configuration for the staging environment.

## Configuration

- **Environment**: Staging
- **AWS Region**: ap-south-1
- **Database**: db.t3.micro (free tier eligible)
- **ECS**: 0.5 vCPU, 1GB RAM
- **Scaling**: 1-2 instances
- **Deletion Protection**: Disabled

## Deployment

### Prerequisites

1. AWS CLI configured with appropriate permissions
2. Terraform installed (>= 1.0)
3. AWS profile configured for staging

### Deploy Infrastructure

```bash
# Navigate to staging directory
cd infra/envs/staging

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply changes
terraform apply
```

### Deploy Application

```bash
# Build and push backend image
cd ../../../
docker build -t get-convinced-backend ./apps/backend
docker tag get-convinced-backend:latest $(terraform -chdir=infra/envs/staging output -raw ecr_repository_url):latest
docker push $(terraform -chdir=infra/envs/staging output -raw ecr_repository_url):latest

# Update ECS service
aws ecs update-service \
  --cluster $(terraform -chdir=infra/envs/staging output -raw ecs_cluster_name) \
  --service $(terraform -chdir=infra/envs/staging output -raw ecs_service_name) \
  --force-new-deployment
```

## Environment Variables

### Backend Environment Variables

See `backend.env` for the complete list of environment variables.

### Frontend Environment Variables (Vercel)

Set these in the Vercel dashboard:

- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_FRONTEGG_CLIENT_ID`: Frontegg client ID

## Monitoring

- **Health Check**: `http://<alb-dns-name>/health`
- **Logs**: CloudWatch Logs group `/ecs/get-convinced-staging`
- **Metrics**: CloudWatch Metrics for ECS service

## Cleanup

To destroy the staging environment:

```bash
terraform destroy
```

**Warning**: This will permanently delete all resources including the database.

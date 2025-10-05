# Infrastructure as Code

This directory contains Terraform configurations for deploying the AI Knowledge Agent monorepo to AWS.

## Architecture

- **Frontend**: Next.js on Vercel (configured separately)
- **Backend**: Fastify on ECS Fargate with Redis sidecar
- **Database**: RDS Postgres
- **Infrastructure**: Terraform-managed AWS resources

## Structure

```
infra/
├── modules/
│   ├── network/     # VPC, subnets, security groups
│   ├── database/    # RDS Postgres
│   ├── service/     # ECS Fargate, ALB
│   └── iam/         # IAM roles for CI/CD
├── envs/
│   ├── staging/     # Staging environment
│   └── prod/        # Production environment
└── .github/workflows/ # CI/CD pipelines
```

## Prerequisites

1. **AWS CLI configured** with appropriate permissions
2. **Terraform** installed (>= 1.0)
3. **AWS Profile** configured for deployment

## Quick Start

### 1. Configure AWS Profile
```bash
aws configure --profile get-convinced
export AWS_PROFILE=get-convinced
```

### 2. Deploy Infrastructure
```bash
# Navigate to environment
cd envs/staging

# Initialize Terraform
terraform init

# Plan deployment
terraform plan

# Apply changes
terraform apply
```

### 3. Deploy Application
```bash
# Build and push backend image
cd ../../../
docker build -t get-convinced-backend ./apps/backend
docker tag get-convinced-backend:latest <ECR_REPO_URI>:latest
docker push <ECR_REPO_URI>:latest

# Update ECS service
aws ecs update-service --cluster <CLUSTER_NAME> --service <SERVICE_NAME> --force-new-deployment

# Frontend deployment is handled automatically by Vercel
# No manual deployment needed - Vercel deploys from main branch
```

## Environment Variables

### Required for Backend
- `DATABASE_URL` - Postgres connection string
- `REDIS_URL` - Redis connection (localhost for sidecar)
- `NODE_ENV` - Environment (staging/production)

### Required for Frontend (Vercel)
Set these in the Vercel dashboard:
- `NEXT_PUBLIC_API_URL` - Backend API endpoint
- `NEXT_PUBLIC_FRONTEGG_CLIENT_ID` - Frontegg client ID

**Note**: Vercel automatically deploys from the main branch. No GitHub Actions needed for deployment.

## Security

- All resources deployed in private subnets
- Database accessible only from backend security group
- ALB provides public endpoint for backend API
- Secrets stored in AWS Secrets Manager

## Monitoring

- CloudWatch Logs for application logs
- CloudWatch Metrics for performance monitoring
- Health checks on `/health` endpoint
- ECS service auto-scaling based on CPU/memory

## Cost Optimization

- RDS instance: `db.t3.micro` (free tier eligible)
- ECS Fargate: 0.25 vCPU, 512 MB RAM (minimal)
- Redis sidecar: No additional cost
- ALB: Pay per request

## Troubleshooting

### Common Issues
1. **ECS task fails to start**: Check CloudWatch logs
2. **Database connection fails**: Verify security groups
3. **ALB health checks fail**: Check backend `/health` endpoint
4. **Terraform state issues**: Use `terraform refresh`

### Useful Commands
```bash
# View ECS logs
aws logs tail /ecs/get-convinced-backend --follow

# Check ECS service status
aws ecs describe-services --cluster <CLUSTER> --services <SERVICE>

# View ALB target health
aws elbv2 describe-target-health --target-group-arn <TARGET_GROUP_ARN>
```

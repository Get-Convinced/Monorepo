# Production Environment

This directory contains the Terraform configuration for the production environment.

## Configuration

- **Environment**: Production
- **AWS Region**: ap-south-1
- **Database**: db.t3.small with 100GB storage
- **ECS**: 1 vCPU, 2GB RAM
- **Scaling**: 2-10 instances
- **Deletion Protection**: Enabled
- **Backup Retention**: 30 days
- **Monitoring**: Enhanced monitoring enabled

## Deployment

### Prerequisites

1. AWS CLI configured with appropriate permissions
2. Terraform installed (>= 1.0)
3. AWS profile configured for production
4. Domain name and SSL certificate configured (optional)

### Deploy Infrastructure

```bash
# Navigate to production directory
cd infra/envs/prod

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
docker tag get-convinced-backend:latest $(terraform -chdir=infra/envs/prod output -raw ecr_repository_url):latest
docker push $(terraform -chdir=infra/envs/prod output -raw ecr_repository_url):latest

# Update ECS service
aws ecs update-service \
  --cluster $(terraform -chdir=infra/envs/prod output -raw ecs_cluster_name) \
  --service $(terraform -chdir=infra/envs/prod output -raw ecs_service_name) \
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

- **Health Check**: `https://<domain-name>/health` or `http://<alb-dns-name>/health`
- **Logs**: CloudWatch Logs group `/ecs/get-convinced-prod`
- **Metrics**: CloudWatch Metrics for ECS service
- **Alerts**: CloudWatch Alarms for critical metrics

## Security

- **Database**: Encrypted at rest, accessible only from private subnets
- **Load Balancer**: HTTPS only (if certificate configured)
- **Secrets**: Stored in AWS Secrets Manager
- **IAM**: Least privilege access

## Backup and Recovery

- **Database**: Automated daily backups with 30-day retention
- **Final Snapshot**: Created before deletion (if enabled)
- **Cross-Region**: Consider setting up cross-region backup for critical data

## Scaling

- **Auto Scaling**: Based on CPU (70%) and Memory (80%) utilization
- **Scale Out**: 2-10 instances
- **Scale In**: Minimum 2 instances maintained

## Maintenance

- **Database Maintenance**: Sunday 4:00-5:00 AM UTC
- **Backup Window**: 3:00-4:00 AM UTC
- **Updates**: Deploy during low-traffic periods

## Cleanup

**⚠️ WARNING**: Production environment cleanup should be done with extreme caution.

```bash
# First, disable deletion protection
terraform apply -var="enable_deletion_protection=false"

# Then destroy (this will create a final snapshot)
terraform destroy
```

**Note**: This will permanently delete all resources including the database. A final snapshot will be created if deletion protection was enabled.

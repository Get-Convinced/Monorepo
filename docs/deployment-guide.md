# Deployment Guide - AI Knowledge Agent

## 🎯 **Overview**
This guide covers the complete deployment process for the AI Knowledge Agent infrastructure and applications using Terraform and AWS.

**Related Documentation:**
- [Production Debugging Guide](../apps/backend/docs/DEBUGGING_PRODUCTION.md) - Troubleshooting and monitoring production issues
- [GitHub Secrets Setup](./github-secrets-setup.md) - Configuring CI/CD secrets

## 🏗️ **Infrastructure Architecture**

### **AWS Services Used**
- **ECS Fargate**: Container orchestration for backend service
- **Application Load Balancer (ALB)**: Public endpoint with SSL termination
- **RDS PostgreSQL**: Managed database with public access
- **ECR**: Container registry for Docker images
- **Secrets Manager**: Secure storage for database credentials and app secrets
- **VPC**: Network isolation with public/private subnets
- **CloudWatch**: Logging and monitoring

### **Terraform Structure**
```
infra/
├── main.tf                    # Main Terraform configuration
├── terraform.tf              # Provider and backend configuration
├── modules/
│   ├── network/              # VPC, subnets, security groups
│   ├── database/             # RDS PostgreSQL and secrets
│   ├── service/              # ECS, ALB, ECR
│   └── iam/                  # IAM roles and policies
└── envs/
    └── prod/
        ├── terraform.tfvars  # Environment-specific variables
        └── backend.env       # Application environment variables
```

## 🔐 **Secrets Management Strategy**

### **AWS Secrets Manager**
All sensitive configuration is stored in AWS Secrets Manager:

1. **Database Credentials** (`get-convinced-prod-db-credentials`)
   - `username`: Database username
   - `password`: Database password
   - `host`: RDS endpoint
   - `port`: Database port
   - `dbname`: Database name

2. **Application Secrets** (`get-convinced-prod-app-secrets`)
   - `DATABASE_URL`: Direct PostgreSQL connection string
   - `FRONTEGG_API_KEY`: Frontegg authentication key
   - `OPENAI_API_KEY`: OpenAI API key
   - `RAGIE_API_KEY`: Ragie API key

### **Environment Variables**
Non-sensitive configuration is stored in `infra/envs/prod/backend.env`:
```bash
# Application Configuration
APP_NAME=AI Knowledge Agent Backend
APP_VERSION=1.0.0
ENVIRONMENT=production
LOG_LEVEL=INFO

# Database Configuration (non-sensitive)
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# API Configuration
BACKEND_PORT=8001
CORS_ORIGINS=https://your-frontend-domain.com
```

## 🚀 **Deployment Process**

### **Prerequisites**
1. **AWS CLI** configured with appropriate credentials
2. **Terraform** v1.5+ installed
3. **Docker** installed for building images
4. **AWS Profile** configured (recommended: `get-convinced`)

### **Step 1: Initial Setup**
```bash
# Clone repository
git clone <your-repo-url>
cd Monorepo

# Configure AWS profile
export AWS_PROFILE=get-convinced
aws sts get-caller-identity  # Verify correct account

# Navigate to infrastructure directory
cd infra
```

### **Step 2: Create Secrets in AWS Secrets Manager**
```bash
# Database credentials
aws secretsmanager create-secret \
  --name "get-convinced-prod-db-credentials" \
  --description "Database credentials for production" \
  --secret-string '{
    "username": "postgres",
    "password": "your-secure-password",
    "host": "get-convinced-prod-db.cf8smywe03wb.ap-south-1.rds.amazonaws.com",
    "port": "5432",
    "dbname": "ai_knowledge_agent"
  }' \
  --region ap-south-1

# Application secrets
aws secretsmanager create-secret \
  --name "get-convinced-prod-app-secrets" \
  --description "Application secrets for production" \
  --secret-string '{
    "DATABASE_URL": "postgresql://postgres:your-secure-password@get-convinced-prod-db.cf8smywe03wb.ap-south-1.rds.amazonaws.com:5432/ai_knowledge_agent",
    "FRONTEGG_API_KEY": "your-frontegg-api-key",
    "OPENAI_API_KEY": "your-openai-api-key",
    "RAGIE_API_KEY": "your-ragie-api-key"
  }' \
  --region ap-south-1
```

### **Step 3: Initialize Terraform**
```bash
# Initialize Terraform
terraform init

# Review planned changes
terraform plan -var-file="envs/prod/terraform.tfvars"

# Apply infrastructure
terraform apply -var-file="envs/prod/terraform.tfvars"
```

### **Step 4: Build and Deploy Backend**
```bash
# Build Docker image
docker build -f apps/backend/Dockerfile -t get-convinced-prod-backend --platform linux/amd64 .

# Login to ECR
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 362479991031.dkr.ecr.ap-south-1.amazonaws.com

# Tag and push image
docker tag get-convinced-prod-backend:latest 362479991031.dkr.ecr.ap-south-1.amazonaws.com/get-convinced-prod-backend:latest
docker push 362479991031.dkr.ecr.ap-south-1.amazonaws.com/get-convinced-prod-backend:latest

# Force new ECS deployment
aws ecs update-service \
  --cluster get-convinced-prod-cluster \
  --service backend \
  --force-new-deployment \
  --region ap-south-1
```

### **Step 5: Verify Deployment**
```bash
# Check health endpoint
curl http://get-convinced-prod-alb-638605407.ap-south-1.elb.amazonaws.com/health

# Check ECS service status
aws ecs describe-services \
  --cluster get-convinced-prod-cluster \
  --services backend \
  --region ap-south-1

# Check logs
aws logs tail /ecs/get-convinced-prod --follow --region ap-south-1
```

## 🔒 **GitHub Secrets Protection**

### **What NOT to Commit**
❌ **Never commit these files:**
- `infra/envs/prod/backend.env` (contains sensitive data)
- `*.tfvars` files with secrets
- AWS credentials
- API keys
- Database passwords

### **GitHub Actions Secrets**
For CI/CD, store secrets in GitHub repository settings:

1. **Go to Repository Settings** → **Secrets and variables** → **Actions**
2. **Add the following secrets:**

```
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=ap-south-1
FRONTEGG_API_KEY=your-frontegg-key
OPENAI_API_KEY=your-openai-key
RAGIE_API_KEY=your-ragie-key
```

### **GitHub Actions Workflow**
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v4
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
        aws-region: ${{ secrets.AWS_REGION }}
    
    - name: Build and push Docker image
      run: |
        docker build -f apps/backend/Dockerfile -t get-convinced-prod-backend --platform linux/amd64 .
        aws ecr get-login-password --region ${{ secrets.AWS_REGION }} | docker login --username AWS --password-stdin 362479991031.dkr.ecr.${{ secrets.AWS_REGION }}.amazonaws.com
        docker tag get-convinced-prod-backend:latest 362479991031.dkr.ecr.${{ secrets.AWS_REGION }}.amazonaws.com/get-convinced-prod-backend:latest
        docker push 362479991031.dkr.ecr.${{ secrets.AWS_REGION }}.amazonaws.com/get-convinced-prod-backend:latest
    
    - name: Deploy to ECS
      run: |
        aws ecs update-service \
          --cluster get-convinced-prod-cluster \
          --service backend \
          --force-new-deployment \
          --region ${{ secrets.AWS_REGION }}
```

## 🛡️ **Security Best Practices**

### **Infrastructure Security**
1. **VPC Isolation**: Services run in private subnets with controlled access
2. **Security Groups**: Restrictive inbound/outbound rules
3. **IAM Roles**: Least privilege access for ECS tasks
4. **Secrets Manager**: Encrypted storage with automatic rotation
5. **ALB**: SSL termination and security headers

### **Application Security**
1. **Environment Variables**: Sensitive data via Secrets Manager
2. **Database**: Public access for development, private in production
3. **Authentication**: Frontegg JWT token validation
4. **CORS**: Restricted origins
5. **Logging**: No sensitive data in logs

### **Deployment Security**
1. **GitHub Secrets**: Encrypted storage in repository
2. **AWS IAM**: Separate deployment user with minimal permissions
3. **Terraform State**: Stored in S3 with encryption
4. **Docker Images**: Scanned for vulnerabilities
5. **Network**: Private subnets for application containers

## 🔧 **Troubleshooting**

### **Common Issues**

1. **ECS Tasks Failing**
   ```bash
   # Check task logs
   aws logs tail /ecs/get-convinced-prod --follow --region ap-south-1
   
   # Check task status
   aws ecs describe-tasks --cluster get-convinced-prod-cluster --tasks <task-arn> --region ap-south-1
   ```

2. **Database Connection Issues**
   ```bash
   # Check RDS status
   aws rds describe-db-instances --db-instance-identifier get-convinced-prod-db --region ap-south-1
   
   # Test connection
   psql -h get-convinced-prod-db.cf8smywe03wb.ap-south-1.rds.amazonaws.com -U postgres -d ai_knowledge_agent
   ```

3. **ALB Health Check Failures**
   ```bash
   # Check target group health
   aws elbv2 describe-target-health --target-group-arn arn:aws:elasticloadbalancing:ap-south-1:362479991031:targetgroup/get-convinced-prod-tg/f2317c8e282cfce7 --region ap-south-1
   ```

### **Rollback Procedure**
```bash
# Rollback to previous ECS service deployment
aws ecs update-service \
  --cluster get-convinced-prod-cluster \
  --service backend \
  --task-definition get-convinced-prod-backend:2 \
  --region ap-south-1

# Rollback infrastructure changes
terraform apply -var-file="envs/prod/terraform.tfvars" -target=module.service
```

## 📊 **Monitoring and Alerts**

### **CloudWatch Metrics**
- ECS service CPU and memory utilization
- ALB request count and latency
- RDS connection count and CPU utilization
- Application error rates

### **Log Aggregation**
- ECS task logs in CloudWatch
- Application logs with structured formatting
- Error tracking and alerting

### **Health Checks**
- ALB health checks on `/health` endpoint
- ECS service health monitoring
- Database connection monitoring

## 🎯 **Next Steps**

1. **Set up monitoring dashboards** in CloudWatch
2. **Configure alerting** for critical metrics
3. **Implement log aggregation** and analysis
4. **Set up backup and disaster recovery**
5. **Implement blue-green deployments**
6. **Add performance testing** to CI/CD pipeline

---

**Remember**: Always test deployments in a staging environment before production, and keep your secrets secure!

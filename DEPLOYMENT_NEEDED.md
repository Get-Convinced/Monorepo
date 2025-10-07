# 🚨 Deployment Needed - Backend Fix

## Problem
The `/api/v1/ragie/documents` endpoint is timing out because the backend is trying to initialize the S3 service on every request, which hangs for 30+ seconds.

## Solution
The code has been fixed to skip S3 service initialization (using direct upload mode instead). However, the fix needs to be deployed.

## What Was Changed
**File:** `apps/backend/src/api/ragie.py`
**Change:** Disabled S3 service initialization in `get_ragie_service()` function to prevent timeout.

```python
# OLD CODE (causes timeout):
try:
    ragie_s3_service = get_s3_service()  # This hangs!
    _ragie_service_instance = RagieService(ragie_client=ragie_client, ragie_s3_service=ragie_s3_service)
except Exception as e:
    _ragie_service_instance = RagieService(ragie_client=ragie_client)

# NEW CODE (fixed):
# For now, skip S3 service initialization to avoid timeouts
logger.info("Initializing Ragie service without S3 (direct upload mode)")
_ragie_service_instance = RagieService(ragie_client=ragie_client)
```

## How to Deploy

### Option 1: Run the deployment script (Requires ECR permissions)
```bash
cd /Users/gauthamgsabahit/workspace/convinced/Monorepo
export AWS_PROFILE=get-convinced
./deploy-backend-fix.sh
```

### Option 2: Manual deployment (Requires ECR permissions)
```bash
cd /Users/gauthamgsabahit/workspace/convinced/Monorepo
export AWS_PROFILE=get-convinced

# Build image
docker build --platform linux/amd64 \
    -t 362479991031.dkr.ecr.ap-south-1.amazonaws.com/get-convinced-prod-backend:latest \
    -f apps/backend/Dockerfile .

# Login to ECR
aws ecr get-login-password --region ap-south-1 | \
    docker login --username AWS --password-stdin \
    362479991031.dkr.ecr.ap-south-1.amazonaws.com

# Push image
docker push 362479991031.dkr.ecr.ap-south-1.amazonaws.com/get-convinced-prod-backend:latest

# Force new deployment
aws ecs update-service \
    --cluster get-convinced-prod-cluster \
    --service backend \
    --force-new-deployment \
    --region ap-south-1
```

## Current Status
- ✅ Code fix implemented
- ✅ AWS profile set to correct account (get-convinced - 362479991031)
- ✅ Infrastructure is healthy
- ❌ **Deployment blocked** - User `convinced-poc` lacks ECR permissions

## Required IAM Permissions
The user needs the following IAM policy attached:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "ecr:PutImage",
                "ecr:InitiateLayerUpload",
                "ecr:UploadLayerPart",
                "ecr:CompleteLayerUpload"
            ],
            "Resource": "*"
        }
    ]
}
```

Or simply attach the AWS managed policy: `AmazonEC2ContainerRegistryPowerUser`

## Verification After Deployment
```bash
# Test health endpoint (should be fast)
curl https://api.getconvinced.ai/health

# Test documents endpoint (should no longer timeout)
curl "https://api.getconvinced.ai/api/v1/ragie/documents" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Organization-ID: YOUR_ORG_ID"

# Check logs
aws logs tail /ecs/get-convinced-prod --follow --region ap-south-1
```

## Related Documentation
- [Production Debugging Guide](apps/backend/docs/DEBUGGING_PRODUCTION.md)
- [Deployment Guide](docs/deployment-guide.md)

---

**Created:** January 2025
**Status:** Awaiting deployment

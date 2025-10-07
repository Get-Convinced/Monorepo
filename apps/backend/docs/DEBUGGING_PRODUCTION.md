# Production Debugging Guide

## 🔍 **Quick Diagnostics Commands**

### **1. Check ECS Service Status**

```bash
# List all services in the cluster
aws ecs list-services \
  --cluster get-convinced-prod-cluster \
  --region ap-south-1

# Get detailed service information
aws ecs describe-services \
  --cluster get-convinced-prod-cluster \
  --services backend \
  --region ap-south-1 \
  --output json | jq '.services[0] | {
    serviceName: .serviceName,
    status: .status,
    runningCount: .runningCount,
    desiredCount: .desiredCount,
    deployments: .deployments
  }'
```

### **2. List Running Tasks**

```bash
# Get all task ARNs
aws ecs list-tasks \
  --cluster get-convinced-prod-cluster \
  --service-name backend \
  --region ap-south-1

# Get detailed task information
aws ecs describe-tasks \
  --cluster get-convinced-prod-cluster \
  --tasks $(aws ecs list-tasks --cluster get-convinced-prod-cluster --service-name backend --region ap-south-1 --query 'taskArns[0]' --output text) \
  --region ap-south-1 \
  --output json | jq '.tasks[0] | {
    taskArn: .taskArn,
    lastStatus: .lastStatus,
    healthStatus: .healthStatus,
    cpu: .cpu,
    memory: .memory,
    containers: .containers[] | {
      name: .name,
      lastStatus: .lastStatus,
      healthStatus: .healthStatus,
      exitCode: .exitCode
    }
  }'
```

### **3. View CloudWatch Logs**

#### **Tail logs in real-time**
```bash
# Follow logs (Ctrl+C to stop)
aws logs tail /ecs/get-convinced-prod \
  --follow \
  --region ap-south-1

# Tail logs from last 5 minutes
aws logs tail /ecs/get-convinced-prod \
  --follow \
  --since 5m \
  --region ap-south-1

# Filter logs (exclude health checks)
aws logs tail /ecs/get-convinced-prod \
  --follow \
  --filter-pattern '- "GET /health"' \
  --region ap-south-1
```

#### **Search logs**
```bash
# Get logs from last 30 minutes
aws logs filter-log-events \
  --log-group-name /ecs/get-convinced-prod \
  --start-time $(($(date +%s) - 1800))000 \
  --region ap-south-1 \
  --limit 50 \
  --query 'events[*].message' \
  --output text

# Search for errors
aws logs filter-log-events \
  --log-group-name /ecs/get-convinced-prod \
  --filter-pattern "ERROR" \
  --start-time $(($(date +%s) - 1800))000 \
  --region ap-south-1 \
  --limit 50 \
  --query 'events[*].message' \
  --output text

# Search for specific endpoint
aws logs filter-log-events \
  --log-group-name /ecs/get-convinced-prod \
  --filter-pattern "documents" \
  --start-time $(($(date +%s) - 1800))000 \
  --region ap-south-1 \
  --limit 50 \
  --query 'events[*].message' \
  --output text
```

#### **Get logs from specific container**
```bash
# First, get the task ID
TASK_ID=$(aws ecs list-tasks \
  --cluster get-convinced-prod-cluster \
  --service-name backend \
  --region ap-south-1 \
  --query 'taskArns[0]' \
  --output text | awk -F/ '{print $NF}')

# Get logs from backend container
aws logs get-log-events \
  --log-group-name /ecs/get-convinced-prod \
  --log-stream-name "backend/backend/${TASK_ID}" \
  --region ap-south-1 \
  --limit 50 \
  --start-from-head=false \
  --query 'events[*].message' \
  --output text

# Get logs from migration container
aws logs get-log-events \
  --log-group-name /ecs/get-convinced-prod \
  --log-stream-name "migration/backend/${TASK_ID}" \
  --region ap-south-1 \
  --limit 50 \
  --query 'events[*].message' \
  --output text
```

### **4. Check ALB Health**

```bash
# Get target group ARN
TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups \
  --region ap-south-1 \
  --query 'TargetGroups[?TargetGroupName==`get-convinced-prod-tg`].TargetGroupArn' \
  --output text)

# Check target health
aws elbv2 describe-target-health \
  --target-group-arn $TARGET_GROUP_ARN \
  --region ap-south-1 \
  --output table

# Get detailed health status
aws elbv2 describe-target-health \
  --target-group-arn $TARGET_GROUP_ARN \
  --region ap-south-1 \
  --output json | jq '.TargetHealthDescriptions[] | {
    target: .Target.Id,
    port: .Target.Port,
    state: .TargetHealth.State,
    reason: .TargetHealth.Reason,
    description: .TargetHealth.Description
  }'
```

### **5. Test Endpoints**

```bash
# Test health endpoint (should be fast)
time curl -s -o /dev/null -w "HTTP %{http_code} - %{time_total}s\n" \
  https://api.getconvinced.ai/health

# Test authenticated endpoint
time curl -s -w "HTTP %{http_code} - %{time_total}s\n" \
  --max-time 10 \
  "https://api.getconvinced.ai/api/v1/ragie/documents" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Organization-ID: YOUR_ORG_ID"

# Verbose test to see connection details
curl -v --max-time 10 \
  "https://api.getconvinced.ai/api/v1/ragie/documents" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Organization-ID: YOUR_ORG_ID" \
  2>&1 | tail -50
```

### **6. Check Resource Usage**

```bash
# Get CPU and memory metrics (last 5 minutes)
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=backend Name=ClusterName,Value=get-convinced-prod-cluster \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average Maximum \
  --region ap-south-1

aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ServiceName,Value=backend Name=ClusterName,Value=get-convinced-prod-cluster \
  --start-time $(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average Maximum \
  --region ap-south-1
```

### **7. Check Database Connection**

```bash
# Get RDS instance status
aws rds describe-db-instances \
  --db-instance-identifier get-convinced-prod-db \
  --region ap-south-1 \
  --output json | jq '.DBInstances[0] | {
    status: .DBInstanceStatus,
    endpoint: .Endpoint.Address,
    port: .Endpoint.Port,
    engine: .Engine,
    engineVersion: .EngineVersion,
    allocatedStorage: .AllocatedStorage,
    storageType: .StorageType
  }'

# Check database connections (requires psql)
PGPASSWORD=$(aws secretsmanager get-secret-value \
  --secret-id get-convinced-prod-db-credentials \
  --region ap-south-1 \
  --query SecretString \
  --output text | jq -r '.password') \
DB_HOST=$(aws secretsmanager get-secret-value \
  --secret-id get-convinced-prod-db-credentials \
  --region ap-south-1 \
  --query SecretString \
  --output text | jq -r '.host') \
psql -h $DB_HOST -U postgres -d ai_knowledge_agent -c "SELECT count(*) FROM pg_stat_activity;"
```

### **8. Check Secrets**

```bash
# List all secrets (without values)
aws secretsmanager list-secrets \
  --region ap-south-1 \
  --query 'SecretList[?starts_with(Name, `get-convinced-prod`)].Name' \
  --output table

# Get secret keys (not values)
aws secretsmanager get-secret-value \
  --secret-id get-convinced-prod-app-secrets \
  --region ap-south-1 \
  --query SecretString \
  --output text | jq -r 'keys[]'

# Verify DATABASE_URL exists
aws secretsmanager get-secret-value \
  --secret-id get-convinced-prod-app-secrets \
  --region ap-south-1 \
  --query SecretString \
  --output text | jq -r 'has("DATABASE_URL")'
```

---

## 🚨 **Common Issues & Solutions**

### **Issue 1: Endpoint Timing Out**

**Symptoms:**
- Request hangs for 30+ seconds
- No logs appear in CloudWatch
- Frontend shows "pending" forever

**Debug:**
```bash
# Check if request reaches ALB
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups --region ap-south-1 --query 'TargetGroups[?TargetGroupName==`get-convinced-prod-tg`].TargetGroupArn' --output text) \
  --region ap-south-1

# Check recent logs for the endpoint
aws logs tail /ecs/get-convinced-prod --follow --since 1m --region ap-south-1
```

**Common Causes:**
- Backend trying to connect to external service (S3, Ragie) that's timing out
- Database connection pool exhausted
- Blocking synchronous operation in async code

**Solution:**
- Check CloudWatch logs for where it's stuck
- Look for "Initializing..." or connection messages
- May need to disable problematic service initialization

### **Issue 2: 500 Internal Server Error**

**Symptoms:**
- Endpoint returns 500 immediately
- Error logged in CloudWatch

**Debug:**
```bash
# Search for errors in last 10 minutes
aws logs filter-log-events \
  --log-group-name /ecs/get-convinced-prod \
  --filter-pattern "ERROR" \
  --start-time $(($(date +%s) - 600))000 \
  --region ap-south-1 \
  --limit 20 \
  --query 'events[*].message' \
  --output text
```

**Common Causes:**
- Missing environment variable
- Database connection failed
- Invalid configuration

### **Issue 3: Task Keeps Restarting**

**Symptoms:**
- Task starts, then stops repeatedly
- Health checks failing

**Debug:**
```bash
# Get task failure reason
aws ecs describe-tasks \
  --cluster get-convinced-prod-cluster \
  --tasks $(aws ecs list-tasks --cluster get-convinced-prod-cluster --service-name backend --region ap-south-1 --query 'taskArns[0]' --output text) \
  --region ap-south-1 \
  --query 'tasks[0].stoppedReason' \
  --output text

# Check container exit codes
aws ecs describe-tasks \
  --cluster get-convinced-prod-cluster \
  --tasks $(aws ecs list-tasks --cluster get-convinced-prod-cluster --service-name backend --region ap-south-1 --query 'taskArns[0]' --output text) \
  --region ap-south-1 \
  --query 'tasks[0].containers[*].{name:name,exitCode:exitCode,reason:reason}' \
  --output table
```

**Common Causes:**
- Migration container failing
- Missing secrets/environment variables
- Database connection failed during startup

### **Issue 4: High Memory/CPU Usage**

**Symptoms:**
- Slow response times
- Tasks being killed by ECS

**Debug:**
```bash
# Check current resource usage
aws ecs describe-tasks \
  --cluster get-convinced-prod-cluster \
  --tasks $(aws ecs list-tasks --cluster get-convinced-prod-cluster --service-name backend --region ap-south-1 --query 'taskArns[]' --output text) \
  --region ap-south-1 \
  --query 'tasks[*].{taskArn:taskArn,cpu:cpu,memory:memory,containers:containers[*].{name:name,cpu:cpu,memory:memory}}' \
  --output json | jq
```

**Solution:**
- May need to increase task CPU/memory in Terraform
- Check for memory leaks in application code
- Review CloudWatch metrics for patterns

---

## 🔄 **Deployment Commands**

### **Force New Deployment**
```bash
# Force ECS to pull latest image and restart
aws ecs update-service \
  --cluster get-convinced-prod-cluster \
  --service backend \
  --force-new-deployment \
  --region ap-south-1

# Monitor deployment progress
watch -n 5 'aws ecs describe-services \
  --cluster get-convinced-prod-cluster \
  --services backend \
  --region ap-south-1 \
  --query "services[0].deployments[*].{status:status,desired:desiredCount,running:runningCount,pending:pendingCount}" \
  --output table'
```

### **Stop Unhealthy Task**
```bash
# Stop a specific task (forces restart)
TASK_ARN=$(aws ecs list-tasks \
  --cluster get-convinced-prod-cluster \
  --service-name backend \
  --region ap-south-1 \
  --query 'taskArns[0]' \
  --output text)

aws ecs stop-task \
  --cluster get-convinced-prod-cluster \
  --task $TASK_ARN \
  --reason "Manual restart for debugging" \
  --region ap-south-1
```

### **Scale Service**
```bash
# Scale down to 0 (stops all tasks)
aws ecs update-service \
  --cluster get-convinced-prod-cluster \
  --service backend \
  --desired-count 0 \
  --region ap-south-1

# Scale back up to 1
aws ecs update-service \
  --cluster get-convinced-prod-cluster \
  --service backend \
  --desired-count 1 \
  --region ap-south-1
```

---

## 📊 **Monitoring Dashboard**

### **Quick Status Check Script**

Save this as `check-backend-status.sh`:

```bash
#!/bin/bash

echo "=== Backend Status Check ==="
echo ""

echo "1. Service Status:"
aws ecs describe-services \
  --cluster get-convinced-prod-cluster \
  --services backend \
  --region ap-south-1 \
  --query 'services[0].{status:status,running:runningCount,desired:desiredCount}' \
  --output table

echo ""
echo "2. Target Health:"
TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups \
  --region ap-south-1 \
  --query 'TargetGroups[?TargetGroupName==`get-convinced-prod-tg`].TargetGroupArn' \
  --output text)
aws elbv2 describe-target-health \
  --target-group-arn $TARGET_GROUP_ARN \
  --region ap-south-1 \
  --output table

echo ""
echo "3. Recent Errors (last 5 minutes):"
aws logs filter-log-events \
  --log-group-name /ecs/get-convinced-prod \
  --filter-pattern "ERROR" \
  --start-time $(($(date +%s) - 300))000 \
  --region ap-south-1 \
  --limit 5 \
  --query 'events[*].message' \
  --output text

echo ""
echo "4. Health Endpoint Test:"
curl -s -o /dev/null -w "Status: %{http_code}, Time: %{time_total}s\n" \
  https://api.getconvinced.ai/health
```

Make it executable:
```bash
chmod +x check-backend-status.sh
./check-backend-status.sh
```

---

## 🔐 **Security Notes**

- Never log or expose secrets in CloudWatch logs
- Use `jq` to filter sensitive data when debugging
- Rotate credentials if accidentally exposed
- Use AWS Secrets Manager for all sensitive configuration

---

## 📝 **Useful Aliases**

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
# Backend debugging aliases
alias backend-logs='aws logs tail /ecs/get-convinced-prod --follow --region ap-south-1'
alias backend-status='aws ecs describe-services --cluster get-convinced-prod-cluster --services backend --region ap-south-1 --query "services[0].{status:status,running:runningCount,desired:desiredCount}" --output table'
alias backend-tasks='aws ecs list-tasks --cluster get-convinced-prod-cluster --service-name backend --region ap-south-1'
alias backend-health='curl -s -o /dev/null -w "Status: %{http_code}, Time: %{time_total}s\n" https://api.getconvinced.ai/health'
alias backend-restart='aws ecs update-service --cluster get-convinced-prod-cluster --service backend --force-new-deployment --region ap-south-1'
```

---

**Last Updated:** January 2025

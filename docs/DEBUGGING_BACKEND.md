# Backend Debugging Guide

## 🔍 **Quick Diagnostics**

### **1. Check if backend is running**
```bash
curl https://api.getconvinced.ai/health
# Should return: {"status":"ok","service":"backend"}
```

### **2. Tail live logs (follow mode)**
```bash
# Follow all logs in real-time
aws logs tail /ecs/get-convinced-prod --region ap-south-1 --since 5m --follow

# Filter for specific patterns while following
aws logs tail /ecs/get-convinced-prod --region ap-south-1 --since 5m --follow | grep -i "error\|upload\|POST"
```

### **3. Check recent errors**
```bash
# Last 10 minutes of errors
aws logs tail /ecs/get-convinced-prod --region ap-south-1 --since 10m --format short | grep -i "error\|exception\|failed"

# Last 30 minutes
aws logs tail /ecs/get-convinced-prod --region ap-south-1 --since 30m --format short | grep -i "error"
```

### **4. Check upload activity**
```bash
# Check for upload/document operations
aws logs tail /ecs/get-convinced-prod --region ap-south-1 --since 10m --format short | grep -iE "(upload|POST.*document|ragie.*upload)"
```

### **5. Check specific endpoint**
```bash
# Check /api/v1/ragie/documents activity
aws logs tail /ecs/get-convinced-prod --region ap-south-1 --since 10m --format short | grep "/api/v1/ragie/documents"
```

---

## 🏥 **Health Checks**

### **Check ECS Service Status**
```bash
aws ecs describe-services \
  --cluster get-convinced-prod-cluster \
  --services backend \
  --region ap-south-1 \
  --query 'services[0].{Running:runningCount,Desired:desiredCount,Status:status,Health:deployments[0].rolloutState}' \
  --output json | jq
```

### **Check Task Health**
```bash
# Get running task ID
TASK_ID=$(aws ecs list-tasks \
  --cluster get-convinced-prod-cluster \
  --service-name backend \
  --region ap-south-1 \
  --desired-status RUNNING \
  --query 'taskArns[0]' \
  --output text | awk -F/ '{print $NF}')

echo "Task ID: $TASK_ID"

# Check task health
aws ecs describe-tasks \
  --cluster get-convinced-prod-cluster \
  --tasks $TASK_ID \
  --region ap-south-1 \
  --query 'tasks[0].{Status:lastStatus,Health:healthStatus,CPU:cpu,Memory:memory}' \
  --output json | jq
```

### **Check ALB Target Health**
```bash
# Get target group ARN
TG_ARN=$(aws elbv2 describe-target-groups \
  --region ap-south-1 \
  --names get-convinced-prod-tg \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

# Check target health
aws elbv2 describe-target-health \
  --region ap-south-1 \
  --target-group-arn $TG_ARN \
  --query 'TargetHealthDescriptions[*].{Target:Target.Id,Port:Target.Port,Health:TargetHealth.State,Reason:TargetHealth.Reason}' \
  --output table
```

---

## 🐛 **Common Issues & Solutions**

### **Issue: Upload stuck/timing out**

**Diagnosis:**
```bash
# 1. Check if request is reaching backend
aws logs tail /ecs/get-convinced-prod --region ap-south-1 --since 5m --follow | grep "POST"

# 2. Check for timeout errors
aws logs tail /ecs/get-convinced-prod --region ap-south-1 --since 5m | grep -i "timeout"

# 3. Check CORS errors
aws logs tail /ecs/get-convinced-prod --region ap-south-1 --since 5m | grep -i "cors\|origin"
```

**Common causes:**
- Frontend not sending request (check browser console)
- CORS blocking request (check OPTIONS preflight)
- Request timing out before reaching backend
- Backend processing too slow

**Solutions:**
```bash
# Test upload directly with curl
curl -X POST https://api.getconvinced.ai/api/v1/ragie/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "X-Organization-ID: YOUR_ORG_ID" \
  -F "file=@test.pdf" \
  -v

# Check if backend is responding
curl -v https://api.getconvinced.ai/health
```

### **Issue: CORS errors**

**Diagnosis:**
```bash
# Test OPTIONS request
curl -X OPTIONS https://api.getconvinced.ai/api/v1/ragie/documents \
  -H "Origin: https://get-convinced-kb.vercel.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: authorization,content-type" \
  -v
```

**Solution:**
Check `apps/backend/src/main.py` CORS configuration includes your frontend URL.

### **Issue: 500 Internal Server Error**

**Diagnosis:**
```bash
# Get detailed error from logs
aws logs tail /ecs/get-convinced-prod --region ap-south-1 --since 10m --format short | grep -A 10 "500\|Internal Server Error"
```

**Common causes:**
- Database connection issues
- Missing environment variables
- Unhandled exceptions in code

---

## 📊 **Performance Monitoring**

### **Check Memory Usage**
```bash
aws cloudwatch get-metric-statistics \
  --region ap-south-1 \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ServiceName,Value=backend Name=ClusterName,Value=get-convinced-prod-cluster \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average \
  --output table
```

### **Check CPU Usage**
```bash
aws cloudwatch get-metric-statistics \
  --region ap-south-1 \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=backend Name=ClusterName,Value=get-convinced-prod-cluster \
  --start-time $(date -u -v-1H +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average \
  --output table
```

---

## 🚀 **Deployment Commands**

### **Force New Deployment**
```bash
aws ecs update-service \
  --cluster get-convinced-prod-cluster \
  --service backend \
  --region ap-south-1 \
  --force-new-deployment
```

### **Check Deployment Status**
```bash
aws ecs describe-services \
  --cluster get-convinced-prod-cluster \
  --services backend \
  --region ap-south-1 \
  --query 'services[0].deployments' \
  --output json | jq
```

### **Stop Unhealthy Task**
```bash
# Get task ID
TASK_ID=$(aws ecs list-tasks \
  --cluster get-convinced-prod-cluster \
  --service-name backend \
  --region ap-south-1 \
  --query 'taskArns[0]' \
  --output text | awk -F/ '{print $NF}')

# Stop task (ECS will start a new one)
aws ecs stop-task \
  --cluster get-convinced-prod-cluster \
  --task $TASK_ID \
  --region ap-south-1 \
  --reason "Manual restart for debugging"
```

---

## 🔧 **Useful Aliases**

Add these to your `~/.zshrc` or `~/.bashrc`:

```bash
# Backend logs
alias backend-logs='aws logs tail /ecs/get-convinced-prod --region ap-south-1 --since 10m --format short'
alias backend-logs-live='aws logs tail /ecs/get-convinced-prod --region ap-south-1 --follow'
alias backend-errors='aws logs tail /ecs/get-convinced-prod --region ap-south-1 --since 30m --format short | grep -i "error\|exception"'

# Backend health
alias backend-health='curl -s https://api.getconvinced.ai/health | jq'
alias backend-status='aws ecs describe-services --cluster get-convinced-prod-cluster --services backend --region ap-south-1 --query "services[0].{Running:runningCount,Desired:desiredCount,Status:status}" --output json | jq'

# Quick deploy
alias backend-deploy='cd /Users/gauthamgsabahit/workspace/convinced/Monorepo && ./deploy-backend-fix.sh'
```

---

## 📞 **Emergency Procedures**

### **Backend is completely down**
```bash
# 1. Check if task is running
aws ecs list-tasks --cluster get-convinced-prod-cluster --service-name backend --region ap-south-1

# 2. Check why tasks are failing
aws ecs describe-tasks --cluster get-convinced-prod-cluster --tasks $(aws ecs list-tasks --cluster get-convinced-prod-cluster --service-name backend --region ap-south-1 --query 'taskArns[0]' --output text) --region ap-south-1 --query 'tasks[0].stoppedReason'

# 3. Force new deployment
aws ecs update-service --cluster get-convinced-prod-cluster --service backend --region ap-south-1 --force-new-deployment
```

### **Database connection issues**
```bash
# Check if database is accessible
aws rds describe-db-instances --region ap-south-1 --db-instance-identifier get-convinced-prod-db --query 'DBInstances[0].{Status:DBInstanceStatus,Endpoint:Endpoint.Address}'

# Check security group rules
aws ec2 describe-security-groups --region ap-south-1 --group-ids sg-036129cc309ff33ac --query 'SecurityGroups[0].IpPermissions'
```

---

## 📝 **Log Patterns to Watch**

### **Success Patterns**
```
✅ "Application startup complete"
✅ "200 OK"
✅ "Initialized Ragie client"
✅ "Document uploaded successfully"
```

### **Warning Patterns**
```
⚠️  "Retrying"
⚠️  "Timeout"
⚠️  "Slow query"
⚠️  "High memory usage"
```

### **Error Patterns**
```
❌ "500 Internal Server Error"
❌ "Connection refused"
❌ "Authentication failed"
❌ "ResourceInitializationError"
❌ "exec format error"
```

---

**Last Updated:** October 6, 2025

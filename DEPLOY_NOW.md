# 🚀 Deploy Smart Source Tracking - Quick Guide

## ✅ **What's Already Done**

- ✅ Code committed and pushed to GitHub
- ✅ Backend changes: +230 LOC
- ✅ Frontend changes: +140 LOC  
- ✅ Database migration script ready
- ✅ Documentation complete

## 🎯 **What Happens Next (Automatic)**

### **1. Backend Auto-Deploy (via Render)**
Your backend will automatically redeploy from the main branch push:
- **URL**: https://dashboard.render.com/
- **Service**: ai-knowledge-backend
- **Status**: Check logs for "Deployment started"
- **Time**: ~3-5 minutes

### **2. Frontend Auto-Deploy (if using Vercel/Render)**
- Frontend should auto-deploy from main branch
- **Time**: ~2-3 minutes

## 📋 **What YOU Need to Do**

### **Step 1: Run Database Migration** ⚠️ REQUIRED

```bash
# Navigate to database package
cd packages/database

# Make script executable (first time only)
chmod +x migrate_production.sh

# Run the migration script - IT WILL AUTO-FETCH DATABASE_URL! 🎉
./migrate_production.sh

# The script will automatically:
# 1. 🔐 Fetch credentials from AWS Secrets Manager (via Terraform)
# 2. 🔗 Construct DATABASE_URL
# 3. ✅ Check connection
# 4. ⚠️  Ask for backup confirmation
# 5. 📋 Show preview of changes
# 6. 🚀 Run migration
# 7. ✅ Verify success
```

**Requirements:**
- AWS CLI configured with `get-convinced` profile
  - Run: `aws sts get-caller-identity --profile get-convinced`
  - Should show Account: 362479991031
- Access to AWS Secrets Manager
- **Network Access**: Your IP must be allowed in RDS security group
  - If connection fails, add your IP to the security group in AWS Console

**Using a different AWS profile?**
```bash
AWS_PROFILE=your-profile-name ./migrate_production.sh
```

**Manual Override (if auto-fetch fails):**
```bash
# Fetch secret manually
cd ../../infra
export AWS_PROFILE=get-convinced
SECRET_ARN=$(terraform output -raw database_secret_arn)
aws secretsmanager get-secret-value --profile get-convinced --secret-id $SECRET_ARN

# Set DATABASE_URL manually
export DATABASE_URL="postgresql://user:pass@host:port/ai_knowledge_agent"
cd ../packages/database
./migrate_production.sh
```

### **Step 2: Verify Backend Deployment**

```bash
# Check health endpoint
curl https://api.getconvinced.ai/health

# Should return:
# {
#   "status": "healthy",
#   "timestamp": "2025-...",
#   "checks": {...}
# }
```

### **Step 3: Test the Feature**

1. **Open your app**: https://your-frontend-url.com
2. **Go to chat**
3. **Ask a question**: "What were our Q4 results?"
4. **Verify**:
   - ✅ Response appears
   - ✅ Inline citations show: `[1] Document.pdf [3] Report.xlsx`
   - ✅ Click "Show Sources"
   - ✅ See "3 Used / 15 Total" badge
   - ✅ Green "Used" badges on sources
   - ✅ Usage reasons displayed

### **Step 4: Monitor (First Hour)**

```bash
# Watch backend logs
# Via Render Dashboard: https://dashboard.render.com/
# Look for:
✅ "LLM response generated with sources"
✅ "Sources saved with usage tracking"
❌ No "OpenAI API error"
```

## 🔍 **Expected Behavior**

### **New Messages (with function calling)**
```
┌─────────────────────────────────────────┐
│ Based on Q4 report, revenue was $5.2M  │
│ ─────────────────────────────────────── │
│ Sources used:                           │
│  [1] Q4_Report.pdf   [3] Budget.xlsx   │
│                                         │
│ 3:45 PM   📚 3 used / 15 total          │
└─────────────────────────────────────────┘
```

### **Old Messages (legacy)**
```
┌─────────────────────────────────────────┐
│ Response from before the update...      │
│                                         │
│ 3:45 PM   📚 15 sources                 │
│ ⓘ Legacy message: all sources shown    │
└─────────────────────────────────────────┘
```

## ⚠️ **If Something Goes Wrong**

### **Rollback Migration**
```bash
cd packages/database
alembic downgrade -1
```

### **Check Logs**
```bash
# Render Dashboard > Your Service > Logs
# Or via CLI:
render logs --service ai-knowledge-backend --tail
```

### **Contact Info**
- GitHub Issues: https://github.com/Get-Convinced/Monorepo/issues
- OpenAI API Status: https://status.openai.com/

## 📊 **Cost Impact**

- **OpenAI API**: ~5% increase per message
  - Function calling adds ~50-100 tokens
  - Better accuracy = fewer retries
  - **Net impact**: Roughly neutral

- **Infrastructure**: No change
  - Same compute requirements
  - Same database size
  - Same network costs

## 🎉 **Success Indicators**

Within 1 hour, you should see:
- ✅ New messages show 3-5 used sources (not 15-20)
- ✅ "Used" badges on source cards
- ✅ Usage reason explanations
- ✅ Inline citations work
- ✅ "Show All" toggle works
- ✅ Old messages still display correctly
- ✅ No errors in logs
- ✅ No user complaints

## 🚨 **Troubleshooting**

### **Issue: Migration fails**
```bash
# Check database connection
psql "$DATABASE_URL" -c "SELECT version();"

# Check if columns already exist
psql "$DATABASE_URL" -c "\d chat_sources"
```

### **Issue: Backend won't deploy**
```bash
# Check Render logs
# Common issues:
# - Missing env var: OPENAI_API_KEY
# - Database connection error
# - Docker build failure
```

### **Issue: Frontend not updated**
```bash
# Force redeploy on Vercel
vercel --prod --force

# Or via dashboard:
# Vercel Dashboard > Deployments > Redeploy
```

### **Issue: No "Used" badges showing**
```bash
# Check OpenAI API key is set
curl https://api.getconvinced.ai/health | jq .

# Check logs for:
"LLM response generated with sources"
"sources_used_count": 3

# If "sources_used_count": 0, function calling failed
# This is OK - automatic fallback should work
```

## 📞 **Need Help?**

1. **Check logs first**: Render Dashboard > Logs
2. **Check OpenAI usage**: https://platform.openai.com/usage  
3. **Check database**: Verify migration ran successfully
4. **Create GitHub issue** with logs and error messages

---

## 📝 **Quick Commands Reference**

```bash
# Get DATABASE_URL from Terraform
cd infra && terraform output database_url

# Run migration
cd packages/database && ./migrate_production.sh

# Check backend health
curl https://api.getconvinced.ai/health

# View logs (Render)
render logs --service ai-knowledge-backend --tail

# Force frontend redeploy (Vercel)
vercel --prod --force
```

---

**Current Status**: 
- ✅ Code deployed to GitHub
- ⏳ Backend auto-deploying (check Render)
- ⏳ Frontend auto-deploying (check Vercel)
- ⚠️  **YOU NEED TO**: Run database migration

**Time to Complete**: 10-15 minutes

**Let's ship it! 🚢**

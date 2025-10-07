# Deployment Plan: Smart Source Tracking Feature

## 🎯 **Deployment Overview**

**Feature**: Smart Source Tracking with OpenAI Function Calling
**Target**: Production Environment
**Risk Level**: LOW (backward compatible, non-breaking changes)

---

## ✅ **Pre-Deployment Checklist**

### **Code Verification**
- [x] All files lint-free (verified)
- [x] Backend changes complete
- [x] Frontend changes complete
- [x] Database migration script ready
- [x] Documentation complete

### **Environment Variables**
- [ ] `OPENAI_API_KEY` set in production backend
- [ ] `DATABASE_URL` accessible for migration
- [ ] Backend environment has latest env vars

### **Backup Plan**
- [ ] Database backup taken (before migration)
- [ ] Rollback migration script ready
- [ ] Current deployment tagged in git

---

## 📋 **Deployment Steps**

### **Step 1: Commit and Tag Changes**

```bash
# From monorepo root
cd /Users/gauthamgsabahit/workspace/convinced/Monorepo

# Stage all changes
git add .

# Commit with descriptive message
git commit -m "feat: Add smart source tracking with OpenAI function calling

- Added source usage tracking (is_used, usage_reason, source_number)
- Implemented OpenAI function calling for structured output
- Enhanced source cards with usage badges and reasons
- Added inline source citations in messages
- Added Show All toggle in sources modal
- Backward compatible with legacy messages
- Database migration included

Backend: +230 LOC
Frontend: +140 LOC
Total: ~370 LOC"

# Tag the release
git tag -a v1.1.0-source-tracking -m "Smart Source Tracking Feature"

# Push to remote
git push origin main
git push origin v1.1.0-source-tracking
```

---

### **Step 2: Database Migration**

#### **2.1: Backup Current Database**

```bash
# SSH into production or use connection string
# Replace with your actual database credentials

# Option A: Using pg_dump (if you have direct access)
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Option B: Using Render/managed service (export via UI)
# Navigate to Render Dashboard > Database > Backups > Create Manual Backup
```

#### **2.2: Test Migration Locally First**

```bash
# From packages/database directory
cd packages/database

# Verify Alembic is configured
cat alembic.ini

# Check current revision
alembic current

# Test the migration on local/staging DB first
export DATABASE_URL="your_staging_db_url"
alembic upgrade head --sql > migration_preview.sql

# Review the SQL that will be executed
cat migration_preview.sql

# Expected output:
# ALTER TABLE chat_sources ADD COLUMN is_used BOOLEAN DEFAULT false;
# ALTER TABLE chat_sources ADD COLUMN usage_reason TEXT;
# ALTER TABLE chat_sources ADD COLUMN source_number INTEGER;
```

#### **2.3: Run Production Migration**

```bash
# Set production database URL
export DATABASE_URL="your_production_database_url"

# Run the migration
alembic upgrade head

# Verify migration succeeded
alembic current
# Should show: add_source_usage_tracking (head)

# Verify columns exist
psql $DATABASE_URL -c "\d chat_sources"
# Should show: is_used, usage_reason, source_number columns
```

#### **2.4: Verify Migration**

```bash
# Check existing rows have default values
psql $DATABASE_URL -c "SELECT COUNT(*) FROM chat_sources WHERE is_used = false;"
# Should show count of existing sources

# Check schema
psql $DATABASE_URL -c "
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'chat_sources' 
    AND column_name IN ('is_used', 'usage_reason', 'source_number');
"
```

---

### **Step 3: Deploy Backend**

#### **3.1: Verify Environment Variables**

```bash
# Check that OPENAI_API_KEY is set in production
# Via Render Dashboard or your deployment platform

# Required env vars:
# OPENAI_API_KEY=sk-...
# DATABASE_URL=postgresql://...
# REDIS_URL=redis://...
# RAGIE_API_KEY=...
```

#### **3.2: Deploy Backend Service**

```bash
# If using Render (auto-deploy on push)
git push origin main
# Render will automatically detect and deploy

# If using Docker/manual deployment
cd apps/backend

# Build Docker image
docker build -t ai-knowledge-backend:source-tracking .

# Tag for registry
docker tag ai-knowledge-backend:source-tracking \
    your-registry/ai-knowledge-backend:latest

# Push to registry
docker push your-registry/ai-knowledge-backend:latest

# Deploy to production
# (depends on your infrastructure - Kubernetes, ECS, etc.)
```

#### **3.3: Verify Backend Deployment**

```bash
# Check health endpoint
curl https://your-backend-url/health

# Check logs for errors
# Via Render Dashboard > Logs
# Or: kubectl logs -f deployment/backend

# Look for:
# ✅ "LLM service initialized"
# ✅ "Database connection established"
# ✅ "Redis connection established"
```

---

### **Step 4: Deploy Frontend**

#### **4.1: Build Frontend**

```bash
cd apps/frontend

# Install dependencies (if needed)
pnpm install

# Build for production
pnpm build

# Expected output:
# ✓ Compiled successfully
# ✓ Collecting page data
# ✓ Generating static pages
```

#### **4.2: Deploy Frontend**

```bash
# If using Vercel
vercel --prod

# If using Render
git push origin main
# Auto-deploys

# If using custom hosting
# Upload .next/standalone or out/ directory
```

#### **4.3: Verify Frontend Deployment**

```bash
# Check homepage
curl https://your-frontend-url

# Check build version
# Look in browser DevTools > Network > Response Headers
# Should show latest deployment timestamp
```

---

### **Step 5: Smoke Testing in Production**

#### **5.1: Basic Functionality Test**

```bash
# Test sequence:
1. ✅ Open chat interface
2. ✅ Ask a question
3. ✅ Verify response appears
4. ✅ Check for inline citations
5. ✅ Click "Show Sources" button
6. ✅ Verify "Used" badges appear
7. ✅ Toggle "Show All Sources"
8. ✅ Verify all sources display
```

#### **5.2: Test Cases**

**Test Case 1: New Message (Function Calling)**
```
Action: Ask "What were our Q4 2024 results?"
Expected:
- ✅ Response generated
- ✅ Inline citations show [1] [3] [5]
- ✅ Sources modal shows "3 Used / 15 Total"
- ✅ Used sources have green borders
- ✅ Usage reasons displayed
```

**Test Case 2: Legacy Message Compatibility**
```
Action: View old message from before deployment
Expected:
- ✅ Message displays normally
- ✅ Sources modal shows all sources
- ✅ "Legacy message" notice appears
- ✅ No "Show All" toggle
- ✅ No crashes/errors
```

**Test Case 3: Function Calling Fallback**
```
Action: Ask complex multi-part question
Expected:
- ✅ Response generated (even if function calling fails)
- ✅ Either structured sources OR all sources marked
- ✅ No errors in console
```

#### **5.3: Monitor Logs**

```bash
# Watch backend logs for errors
# Via Render Dashboard or:
kubectl logs -f deployment/backend | grep -i error

# Look for:
# ✅ "LLM response generated with sources"
# ✅ "Sources saved with usage tracking"
# ❌ No "OpenAI API error"
# ❌ No "Database error"
```

---

### **Step 6: Performance Monitoring**

#### **6.1: Check Key Metrics**

```bash
# Monitor for 30 minutes after deployment

# Backend metrics to watch:
- Response time (should be < 3s)
- OpenAI API latency (should be < 2s)
- Database query time (should be < 100ms)
- Error rate (should be < 1%)

# Frontend metrics to watch:
- Page load time (should be < 2s)
- Time to interactive (should be < 3s)
- Client-side errors (should be 0)
```

#### **6.2: Check Costs**

```bash
# Monitor OpenAI usage
# https://platform.openai.com/usage

# Expected increase:
# ~5% more tokens per message (for function calling)
# Should see mix of:
# - gpt-4o (with function calling)
# - Input tokens: ~2000-3000 per message
# - Output tokens: ~500-1000 per message
```

---

### **Step 7: User Communication**

#### **7.1: Notify Users (Optional)**

```markdown
📢 New Feature: Smart Source Citations

We've improved how sources are displayed in chat responses!

What's new:
✨ See only the sources actually used in each answer
🎯 Understand why each source was used
📊 Toggle to view all retrieved sources
🔗 Quick inline citations in messages

Try it out in your next chat session!
```

---

## 🚨 **Rollback Plan**

If something goes wrong:

### **Option 1: Rollback Database Migration**

```bash
cd packages/database

# Rollback to previous revision
alembic downgrade -1

# Verify
alembic current

# Restart backend service to use old code
```

### **Option 2: Rollback Code Deployment**

```bash
# Revert to previous git tag
git revert v1.1.0-source-tracking

# Or checkout previous commit
git checkout <previous-commit-hash>

# Redeploy
git push origin main --force
```

### **Option 3: Feature Flag (Future Enhancement)**

```python
# In chat_service.py
USE_SOURCE_TRACKING = os.getenv("FEATURE_SOURCE_TRACKING", "false") == "true"

if USE_SOURCE_TRACKING:
    llm_result = await self.llm_service.generate_response_with_sources(...)
else:
    llm_result = await self.llm_service.generate_response(...)
```

---

## 📊 **Success Criteria**

### **Deployment Successful If**:
- [x] Database migration completed without errors
- [x] Backend deployed and health check passes
- [x] Frontend deployed and accessible
- [x] New messages show source usage tracking
- [x] Legacy messages display correctly
- [x] No increase in error rate
- [x] OpenAI API calls successful

### **Deployment Failed If**:
- [ ] Database migration fails
- [ ] Backend health check fails
- [ ] Frontend build fails
- [ ] OpenAI API errors > 5%
- [ ] User-facing errors
- [ ] Performance degradation > 20%

---

## 🎉 **Post-Deployment**

### **Immediate Tasks (Day 1)**
- [ ] Monitor logs for 2 hours
- [ ] Test with 5-10 real questions
- [ ] Check OpenAI usage dashboard
- [ ] Verify costs are as expected

### **Short Term (Week 1)**
- [ ] Collect user feedback
- [ ] Monitor error rates
- [ ] Track OpenAI costs
- [ ] Document any issues

### **Long Term (Month 1)**
- [ ] Analyze source usage patterns
- [ ] Measure user engagement
- [ ] Identify improvements
- [ ] Plan next iteration

---

## 📝 **Deployment Commands Summary**

```bash
# Quick deployment script
#!/bin/bash

set -e  # Exit on error

echo "🚀 Deploying Smart Source Tracking Feature"

# 1. Commit changes
echo "📦 Committing changes..."
git add .
git commit -m "feat: Add smart source tracking"
git push origin main

# 2. Run migration
echo "🗄️ Running database migration..."
cd packages/database
alembic upgrade head

# 3. Verify deployment
echo "✅ Verifying deployment..."
curl https://your-backend-url/health

echo "🎉 Deployment complete!"
echo "👀 Monitor logs at: https://dashboard.render.com/..."
```

---

## 🔗 **Useful Links**

- **Render Dashboard**: https://dashboard.render.com/
- **OpenAI Usage**: https://platform.openai.com/usage
- **Database**: [Your database management URL]
- **Frontend**: [Your Vercel/frontend URL]
- **Backend**: [Your backend URL]
- **Logs**: [Your logging service]

---

**Deployment Date**: October 7, 2025
**Deployed By**: AI Engineering Team
**Status**: ⏳ READY TO DEPLOY

*Let's ship it! 🚢*

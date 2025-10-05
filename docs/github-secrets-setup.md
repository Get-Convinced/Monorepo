# GitHub Secrets Setup Guide

## 🔐 **Protecting Your Secrets**

### **Step 1: Add Secrets to GitHub Repository**

1. **Go to your GitHub repository**
2. **Click on Settings** → **Secrets and variables** → **Actions**
3. **Click "New repository secret"**
4. **Add these secrets:**

```
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=ap-south-1
AWS_ACCOUNT_ID=362479991031
FRONTEGG_API_KEY=your-frontegg-key
OPENAI_API_KEY=your-openai-key
RAGIE_API_KEY=your-ragie-key
```

### **Step 2: Create AWS IAM User for CI/CD**

```bash
# Create IAM user for GitHub Actions
aws iam create-user --user-name github-actions-deploy

# Attach policies
aws iam attach-user-policy \
  --user-name github-actions-deploy \
  --policy-arn arn:aws:iam::aws:policy/AmazonECS_FullAccess

aws iam attach-user-policy \
  --user-name github-actions-deploy \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess

# Create access keys
aws iam create-access-key --user-name github-actions-deploy
```

### **Step 3: What's Protected**

✅ **Safe to commit:**
- `infra/envs/prod/backend.env.example` (template)
- `.github/workflows/deploy.yml` (uses secrets)
- `docs/deployment-guide.md` (documentation)

❌ **Never commit:**
- `infra/envs/prod/backend.env` (actual secrets)
- AWS credentials
- API keys
- Database passwords

### **Step 4: Verify Protection**

```bash
# Check what's ignored
git status --ignored

# Verify no secrets in repo
git grep -r "sk-" .  # OpenAI keys
git grep -r "AKIA" .  # AWS keys
```

Your secrets are now protected! 🛡️

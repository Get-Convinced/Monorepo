#!/bin/bash

# Production Database Migration Script
# For Smart Source Tracking Feature

set -e  # Exit on error

# AWS Profile Configuration
AWS_PROFILE="${AWS_PROFILE:-get-convinced}"

echo "🗄️  Production Database Migration"
echo "=================================="
echo ""
echo "⚠️  WARNING: This will modify the production database!"
echo ""
echo "This migration will:"
echo "  - Add 'is_used' column (BOOLEAN, default false)"
echo "  - Add 'usage_reason' column (TEXT, nullable)"  
echo "  - Add 'source_number' column (INTEGER, nullable)"
echo ""
echo "To chat_sources table"
echo ""
echo "🔐 Using AWS Profile: $AWS_PROFILE"
echo ""

# Function to get database URL from AWS Secrets Manager
get_db_url_from_secrets() {
    echo "🔐 Fetching database credentials from AWS Secrets Manager..."
    
    # Get secret ARN from Terraform
    cd ../../infra
    export AWS_PROFILE="$AWS_PROFILE"
    SECRET_ARN=$(terraform output -raw database_secret_arn 2>/dev/null)
    
    if [ -z "$SECRET_ARN" ]; then
        echo "⚠️  Could not get secret ARN from Terraform"
        return 1
    fi
    
    echo "   Secret ARN: $SECRET_ARN"
    
    # Fetch secret from AWS
    SECRET_JSON=$(aws secretsmanager get-secret-value \
        --profile "$AWS_PROFILE" \
        --secret-id "$SECRET_ARN" \
        --query SecretString \
        --output text 2>/dev/null)
    
    if [ -z "$SECRET_JSON" ]; then
        echo "⚠️  Could not fetch secret from AWS"
        return 1
    fi
    
    # Parse JSON to get credentials
    DB_USERNAME=$(echo "$SECRET_JSON" | jq -r .username)
    DB_PASSWORD=$(echo "$SECRET_JSON" | jq -r .password)
    DB_ENDPOINT=$(terraform output -raw database_endpoint 2>/dev/null)
    DB_NAME=$(terraform output -raw database_name 2>/dev/null)
    
    cd - > /dev/null
    
    # Construct DATABASE_URL (endpoint already includes :5432)
    export DATABASE_URL="postgresql://${DB_USERNAME}:${DB_PASSWORD}@${DB_ENDPOINT}/${DB_NAME}"
    
    echo "✅ Database URL fetched successfully"
    return 0
}

# Try to get DATABASE_URL automatically
if [ -z "$DATABASE_URL" ]; then
    echo "📋 DATABASE_URL not set, attempting to fetch automatically..."
    echo ""
    
    # Try AWS Secrets Manager first
    if get_db_url_from_secrets; then
        echo ""
    else
        echo ""
        echo "❌ Could not automatically fetch database credentials"
        echo ""
        echo "Please set DATABASE_URL manually:"
        echo "  export DATABASE_URL='postgresql://user:pass@host:port/dbname'"
        echo ""
        echo "You can get it from:"
        echo "  1. AWS Secrets Manager:"
        echo "     aws secretsmanager get-secret-value --secret-id <arn>"
        echo ""
        echo "  2. Or use this command:"
        echo "     cd infra && terraform output -raw database_endpoint"
        echo ""
        exit 1
    fi
else
    echo "✅ Using provided DATABASE_URL"
    echo ""
fi

echo "✅ DATABASE_URL is set"
echo ""

# Confirm before proceeding
read -p "Do you want to proceed with the migration? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Migration cancelled"
    exit 0
fi

echo ""
echo "📋 Step 1: Check current database schema"
echo "========================================"
psql "$DATABASE_URL" -c "\d chat_sources" || {
    echo "❌ Could not connect to database or table doesn't exist"
    exit 1
}

echo ""
echo "✅ Connection successful"
echo ""

# Create backup notice
echo "📦 Step 2: Backup recommendation"
echo "========================================"
echo ""
echo "⚠️  IMPORTANT: Create a database backup before proceeding!"
echo ""
echo "To create backup:"
echo "  1. Via AWS RDS Console: Go to RDS > Snapshots > Create Snapshot"
echo "  2. Or run: pg_dump \"\$DATABASE_URL\" > backup_\$(date +%Y%m%d_%H%M%S).sql"
echo ""
read -p "Have you created a backup? (yes/no): " BACKUP_CONFIRM

if [ "$BACKUP_CONFIRM" != "yes" ]; then
    echo "❌ Please create a backup first, then run this script again"
    exit 0
fi

echo ""
echo "🔍 Step 3: Preview migration SQL"
echo "========================================"
echo ""

# Show the migration SQL
echo "The following SQL will be executed:"
echo ""
echo "ALTER TABLE chat_sources ADD COLUMN is_used BOOLEAN DEFAULT false NOT NULL;"
echo "ALTER TABLE chat_sources ADD COLUMN usage_reason TEXT;"
echo "ALTER TABLE chat_sources ADD COLUMN source_number INTEGER;"
echo "ALTER TABLE chat_sources ALTER COLUMN is_used DROP DEFAULT;"
echo ""

read -p "Ready to execute? (yes/no): " EXECUTE_CONFIRM

if [ "$EXECUTE_CONFIRM" != "yes" ]; then
    echo "❌ Migration cancelled"
    exit 0
fi

echo ""
echo "🚀 Step 4: Running Alembic migration"
echo "========================================"
echo ""

# Check current revision
echo "Current database revision:"
alembic current

echo ""
echo "Running migration..."
alembic upgrade head

echo ""
echo "New database revision:"
alembic current

echo ""
echo "✅ Step 5: Verify migration"
echo "========================================"
echo ""

# Verify columns exist
echo "Checking new columns..."
psql "$DATABASE_URL" -c "
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'chat_sources' 
    AND column_name IN ('is_used', 'usage_reason', 'source_number')
ORDER BY column_name;
"

echo ""

# Check existing rows have default values
echo "Checking existing rows..."
psql "$DATABASE_URL" -c "
SELECT 
    COUNT(*) as total_sources,
    SUM(CASE WHEN is_used = false THEN 1 ELSE 0 END) as sources_with_default_false,
    SUM(CASE WHEN usage_reason IS NULL THEN 1 ELSE 0 END) as sources_without_reason,
    SUM(CASE WHEN source_number IS NULL THEN 1 ELSE 0 END) as sources_without_number
FROM chat_sources;
"

echo ""
echo "✅ Migration completed successfully!"
echo ""
echo "📊 Next steps:"
echo "  1. Verify backend deployment: curl https://api.getconvinced.ai/health"
echo "  2. Test with a new question in the chat"
echo "  3. Check that 'Used' badges appear on sources"
echo "  4. Monitor logs for any errors"
echo ""
echo "🎉 Smart Source Tracking is now live!"

#!/bin/bash

# Production Database Migration Script
# For Smart Source Tracking Feature

set -e  # Exit on error

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

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL environment variable is not set"
    echo ""
    echo "Please set it first:"
    echo "  export DATABASE_URL='postgresql://user:pass@host:port/dbname'"
    echo ""
    echo "You can find the DATABASE_URL from:"
    echo "  - AWS RDS Console"
    echo "  - Terraform outputs: terraform output database_url"
    echo "  - AWS Secrets Manager"
    exit 1
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

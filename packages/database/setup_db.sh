#!/bin/bash
# Database setup script for AI Knowledge Agent

set -e

echo "🚀 Setting up AI Knowledge Agent Database..."

# Load environment variables
if [ -f "database.env" ]; then
    echo "📋 Loading environment variables..."
    export $(cat database.env | xargs)
fi

# Check if PostgreSQL is running
echo "🔍 Checking PostgreSQL status..."
if ! brew services list | grep -q "postgresql.*started"; then
    echo "⚠️  PostgreSQL not running. Starting it..."
    brew services start postgresql@15
    sleep 3
fi

# Check if database exists
echo "🔍 Checking if database exists..."
if ! psql -d ai_knowledge_agent -c "SELECT 1;" >/dev/null 2>&1; then
    echo "📊 Creating database..."
    createdb ai_knowledge_agent
fi

# Run migrations
echo "🔄 Running database migrations..."
alembic upgrade head

# Test connection
echo "🧪 Testing database connection..."
python3 simple_test.py

echo "✅ Database setup completed successfully!"
echo ""
echo "📊 Database Information:"
echo "   Host: ${DB_HOST:-localhost}"
echo "   Port: ${DB_PORT:-5432}"
echo "   Database: ${DB_NAME:-ai_knowledge_agent}"
echo "   User: ${DB_USER:-gauthamgsabahit}"
echo ""
echo "🔧 Available commands:"
echo "   • View tables: psql -d ai_knowledge_agent -c '\\dt'"
echo "   • Run migrations: alembic upgrade head"
echo "   • Create new migration: alembic revision --autogenerate -m 'Description'"
echo "   • Test connection: python3 simple_test.py"



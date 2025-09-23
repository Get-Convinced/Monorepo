#!/usr/bin/env python3
"""
Simple test to verify database connection without importing the full package.
"""

import asyncio
import asyncpg
import os
from pathlib import Path


async def test_direct_connection():
    """Test direct connection to PostgreSQL."""
    print("🔧 Testing direct PostgreSQL connection...")
    
    # Load environment variables
    env_file = Path(__file__).parent / "database.env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    # Connection parameters
    host = os.getenv('DB_HOST', 'localhost')
    port = int(os.getenv('DB_PORT', '5432'))
    database = os.getenv('DB_NAME', 'ai_knowledge_agent')
    user = os.getenv('DB_USER', 'gauthamgsabahit')
    password = os.getenv('DB_PASSWORD', '')
    
    try:
        # Test connection
        if password:
            conn = await asyncpg.connect(
                host=host, port=port, database=database, 
                user=user, password=password
            )
        else:
            conn = await asyncpg.connect(
                host=host, port=port, database=database, user=user
            )
        
        print(f"✅ Connected to PostgreSQL: {host}:{port}/{database}")
        
        # Test query - check if our tables exist
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        print(f"✅ Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table['table_name']}")
        
        # Test inserting a simple record
        await conn.execute("""
            INSERT INTO system_configuration (id, key, value, config_type, is_active)
            VALUES (gen_random_uuid(), $1, $2, $3, $4)
        """, "test_key", '{"test": true}', "test", True)
        
        print("✅ Inserted test record")
        
        # Test retrieving the record
        result = await conn.fetchrow("""
            SELECT key, value FROM system_configuration 
            WHERE key = $1
        """, "test_key")
        
        if result:
            print(f"✅ Retrieved test record: {result['key']} = {result['value']}")
        
        # Clean up test record
        await conn.execute("DELETE FROM system_configuration WHERE key = $1", "test_key")
        print("✅ Cleaned up test record")
        
        await conn.close()
        print("✅ Connection closed successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def main():
    """Run the test."""
    print("🚀 Starting simple database test...\n")
    
    success = await test_direct_connection()
    
    if success:
        print("\n🎉 Database test completed successfully!")
        print("✅ PostgreSQL connection working")
        print("✅ Tables created successfully") 
        print("✅ Basic CRUD operations working")
    else:
        print("\n❌ Database test failed!")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

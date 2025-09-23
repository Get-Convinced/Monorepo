#!/usr/bin/env python3
"""
Basic test to verify database package is available.
"""

import sys
from pathlib import Path

# Add the database package to the path
DB_PACKAGE_PATH = Path(__file__).parent.parent.parent / "packages" / "database" / "src"
if str(DB_PACKAGE_PATH) not in sys.path:
    sys.path.insert(0, str(DB_PACKAGE_PATH))

print("🔧 Testing basic database package availability...")

try:
    # Try to import the database components directly
    from models import ProcessingStatus, ProcessorType
    print(f"✅ ProcessingStatus: {ProcessingStatus.PENDING.value}")
    print(f"✅ ProcessorType: {ProcessorType.GPT_4O.value}")
    
    from config import DatabaseConfig
    config = DatabaseConfig()
    print(f"✅ Database config: {config.host}:{config.port}/{config.database}")
    
    from database import DatabaseClient
    client = DatabaseClient()
    print("✅ Database client created")
    
    print("\n🎉 Basic database package test passed!")
    print("✅ Models imported successfully")
    print("✅ Configuration working")
    print("✅ Database client created")
    
except Exception as e:
    print(f"❌ Basic database test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n📋 Database Integration Summary:")
print("✅ Database package is accessible")
print("✅ Models and enums working")
print("✅ Configuration system working")
print("✅ Database client can be created")
print("\n🚀 Ready to integrate with document processor!")



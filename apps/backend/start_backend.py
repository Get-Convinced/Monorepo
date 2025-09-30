#!/usr/bin/env python3
"""
Simple script to start the backend server.
"""
import uvicorn
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv('.env.local')
    
    port = int(os.getenv("PORT", 8082))
    host = os.getenv("HOST", "0.0.0.0")
    
    print("🚀 Starting AI Knowledge Agent Backend...")
    print("📊 Request logging enabled")
    print(f"🌐 Server will be available at: http://localhost:{port}")
    print(f"📋 API docs available at: http://localhost:{port}/docs")
    print("-" * 60)
    
    uvicorn.run(
        "src.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info",
        access_log=True
    )

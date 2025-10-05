#!/usr/bin/env python3
"""
Simple script to start the backend server.
"""
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables FIRST, before any imports that might use them
from dotenv import load_dotenv
load_dotenv('.env.local', override=True)

import uvicorn
import signal

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down server...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    port = int(os.getenv("PORT", 8001))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print("Starting AI Knowledge Agent Backend...")
    print("Request logging enabled")
    print(f"Server will be available at: http://localhost:{port}")
    print(f"API docs available at: http://localhost:{port}/docs")
    if reload:
        print("Hot reload: ENABLED (Ctrl+C to stop)")
    print("-" * 60)
    
    try:
        uvicorn.run(
            "src.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
            access_log=True,
            reload_delay=0.5,  # Reduce reload sensitivity
            use_colors=True
        )
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        sys.exit(0)

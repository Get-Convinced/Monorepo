"""
Simple FastAPI backend for testing authentication without database dependencies.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(
    title="AI Knowledge Agent Backend",
    description="Backend API for AI Knowledge Agent with Frontegg authentication",
    version="0.1.0"
)

# CORS for frontend
frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
allowed_origins = {frontend_origin, "http://127.0.0.1:3000"}
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allowed_origins),
    allow_origin_regex=r"^http://[a-zA-Z0-9\-\.]+:3000$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "backend"}

@app.get("/")
async def root():
    return {
        "service": "backend",
        "env": os.getenv("APP_ENV", "local"),
        "version": "0.1.0",
        "description": "AI Knowledge Agent Backend API"
    }

@app.get("/api/status")
async def api_status():
    """API status endpoint with service information."""
    return {
        "service": "backend",
        "status": "healthy",
        "version": "0.1.0",
        "features": [
            "Frontegg authentication",
            "CORS enabled",
            "Health monitoring"
        ],
        "endpoints": {
            "health": "/health",
            "status": "/api/status"
        }
    }

# Simple user endpoint for testing authentication
@app.get("/users/me")
async def get_current_user():
    """Mock endpoint for testing authentication."""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "name": "Test User",
        "message": "Authentication working! This is a mock response."
    }

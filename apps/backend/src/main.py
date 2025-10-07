from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from .api import organization_router, file_router
from .api.ragie import router as ragie_router
from .api.ragie_extensions import router as ragie_extensions_router
from .api.chat import router as chat_router

app = FastAPI(
    title="AI Knowledge Agent Backend",
    description="Backend API for AI Knowledge Agent with organization and file management",
    version="0.1.0"
)

# Simple request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"[REQUEST] {request.method} {request.url}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"[RESPONSE] {response.status_code} - {process_time:.4f}s")
    
    return response

# CORS for frontend - Allow localhost for development and Vercel for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Development origins
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        # Production origins - Vercel deployments
        "https://get-convinced.vercel.app",
        "https://get-convinced-git-main-get-convinced.vercel.app",
        "https://monorepo-frontend.vercel.app",
        "https://get-convinced-kb.vercel.app"
    ],
    allow_origin_regex=r"^(http://(localhost|127\.0\.0\.1):300[0-9]|https://.*\.vercel\.app)$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(organization_router)
app.include_router(file_router)
app.include_router(ragie_router)
app.include_router(ragie_extensions_router)
app.include_router(chat_router)


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
            "Organization management (dummy)",
            "File upload/download with S3",
            "Document processing integration"
        ],
        "endpoints": {
            "organizations": "/organizations",
            "files": "/files"
        }
    }

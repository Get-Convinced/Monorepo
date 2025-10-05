"""
Additional Ragie API endpoints for enhanced functionality.

This module provides additional endpoints that extend the core Ragie functionality
with analytics and other enhanced features.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException

from ..services.ragie_service import RagieService
from ..adapters.ragie_client import RagieClient
from ..auth import require_auth, get_organization_id
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ragie", tags=["ragie-extensions"])


# Import the singleton service from main ragie module
from .ragie import get_ragie_service


@router.get(
    "/documents/analytics",
    response_model=Dict[str, Any],
    summary="Document Analytics",
    description="Get basic document usage analytics and insights"
)
async def get_document_analytics(
    user_id: str = Depends(require_auth),
    organization_id: str = Depends(get_organization_id),
    ragie_service: RagieService = Depends(get_ragie_service)
) -> Dict[str, Any]:
    """
    Get basic document analytics and usage insights.
    
    Returns statistics about document counts, file types, and processing status.
    """
    try:
        # Get all documents to calculate analytics
        result = await ragie_service.list_documents(
            organization_id=organization_id,
            limit=1000  # Get a large batch for analytics
        )
        
        if not result.success:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": "ANALYTICS_ERROR",
                        "message": result.error
                    }
                }
            )
        
        documents = result.data.documents
        
        # Calculate analytics
        total_documents = len(documents)
        
        # File type breakdown
        by_file_type = {}
        for doc in documents:
            # Extract file extension
            ext = doc.name.split('.')[-1].lower() if '.' in doc.name else 'unknown'
            if ext not in by_file_type:
                by_file_type[ext] = {"count": 0, "size_bytes": 0}
            by_file_type[ext]["count"] += 1
        
        # Status breakdown
        by_status = {}
        for doc in documents:
            status = doc.status
            by_status[status] = by_status.get(status, 0) + 1
        
        # Upload trends (simplified)
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        last_7_days = len([doc for doc in documents if doc.created_at >= week_ago])
        last_30_days = len([doc for doc in documents if doc.created_at >= month_ago])
        
        analytics_data = {
            "total_documents": total_documents,
            "total_size_bytes": 0,  # Not available from Ragie
            "by_file_type": by_file_type,
            "by_status": by_status,
            "upload_trends": {
                "last_7_days": last_7_days,
                "last_30_days": last_30_days
            }
        }
        
        logger.info("Document analytics generated", extra={
            "total_documents": total_documents,
            "organization_id": organization_id,
            "user_id": user_id
        })
        
        return {
            "success": True,
            "data": analytics_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error in analytics", extra={
            "organization_id": organization_id,
            "user_id": user_id,
            "error": str(e)
        })
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred"
                }
            }
        )

"""
Authentication dependencies with auto-provisioning.

These dependencies extend the base Frontegg auth to automatically provision
users and organizations in our database on first request.
"""

import logging
from typing import Dict, Any, Tuple
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from shared_database.database import get_async_session
from shared_database.models import User, Organization
from .frontegg_sdk_auth import get_current_user_sdk, get_organization_id_sdk
from ..services.user_provisioning_service import UserProvisioningService

logger = logging.getLogger(__name__)


async def get_current_user_with_provisioning(
    frontegg_user: Dict[str, Any] = Depends(get_current_user_sdk),
    session: AsyncSession = Depends(get_async_session)
) -> Tuple[Dict[str, Any], User, Organization]:
    """
    Get current user with automatic provisioning.
    
    This dependency:
    1. Verifies the Frontegg JWT token
    2. Auto-provisions user and organization if they don't exist
    3. Returns the Frontegg user info, DB user, and DB organization
    
    Returns:
        Tuple of (frontegg_user_dict, db_user, db_organization)
    """
    try:
        # Initialize provisioning service
        provisioning_service = UserProvisioningService(session)
        
        # Get or create user and organization
        db_user, db_organization = await provisioning_service.get_or_create_user_and_org(
            frontegg_user
        )
        
        return frontegg_user, db_user, db_organization
        
    except Exception as e:
        logger.error(f"Failed to provision user/org: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"User provisioning failed: {str(e)}"
        )


# Simplified dependencies that just return the parts you need

async def get_provisioned_user(
    data: Tuple[Dict[str, Any], User, Organization] = Depends(get_current_user_with_provisioning)
) -> User:
    """Get the provisioned database user."""
    return data[1]


async def get_provisioned_organization(
    data: Tuple[Dict[str, Any], User, Organization] = Depends(get_current_user_with_provisioning)
) -> Organization:
    """Get the provisioned database organization."""
    return data[2]


# Convenience dependency that returns user_id and organization_id as strings
async def get_user_and_org_ids(
    data: Tuple[Dict[str, Any], User, Organization] = Depends(get_current_user_with_provisioning)
) -> Tuple[str, str]:
    """
    Get user_id and organization_id as strings.
    
    Returns:
        Tuple of (user_id_str, organization_id_str)
    """
    _, db_user, db_organization = data
    return str(db_user.id), str(db_organization.id)


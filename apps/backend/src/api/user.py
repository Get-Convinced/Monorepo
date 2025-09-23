"""
User API endpoints.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared_database import DatabaseClient
from shared_database.database import get_async_session
from ..auth.frontegg_auth import get_current_user, get_current_user_optional
from ..models.user import (
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
    UserListResponse,
    UserOrganizationsResponse
)

router = APIRouter(prefix="/users", tags=["users"])


def get_db_client() -> DatabaseClient:
    """Dependency to get database client."""
    return DatabaseClient()


@router.post("/", response_model=UserResponse)
async def create_user(
    request: UserCreateRequest,
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """Create a new user."""
    try:
        # Check if email already exists
        existing_user = await db_client.get_user_by_email(session, request.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail=f"User with email '{request.email}' already exists"
            )
        
        # Create user
        user = await db_client.create_user(
            session=session,
            email=request.email,
            name=request.name,
            profile_data=request.profile_data,
            avatar_url=request.avatar_url
        )
        
        await session.commit()
        return UserResponse.model_validate(user)
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.get("/", response_model=UserListResponse)
async def list_users(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user)  # Require authentication
):
    """List users with pagination."""
    try:
        from shared_database.services import UserService
        service = UserService(session)
        users = await service.list_users(limit=limit, offset=offset)
        
        # Get total count (simplified - in production you'd want a proper count query)
        total = len(users)  # This is not accurate for pagination
        
        return UserListResponse(
            users=[UserResponse.model_validate(user) for user in users],
            total=total,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """Get user by ID."""
    try:
        user = await db_client.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse.model_validate(user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.get("/email/{email}", response_model=UserResponse)
async def get_user_by_email(
    email: str,
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """Get user by email."""
    try:
        user = await db_client.get_user_by_email(session, email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return UserResponse.model_validate(user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user: {str(e)}")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    request: UserUpdateRequest,
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """Update user."""
    try:
        from shared_database.services import UserService
        service = UserService(session)
        
        user = await service.update_user(
            user_id=user_id,
            name=request.name,
            profile_data=request.profile_data,
            avatar_url=request.avatar_url
        )
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        await session.commit()
        return UserResponse.model_validate(user)
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session)
):
    """Get current user's profile from Frontegg token."""
    try:
        # Get user email from Frontegg token
        user_email = current_user.get("email")
        if not user_email:
            raise HTTPException(status_code=400, detail="No email found in token")
        
        # Try to find user in our database
        user = await db_client.get_user_by_email(session, user_email)
        
        if not user:
            # Create user if doesn't exist (first time login)
            user = await db_client.create_user(
                session=session,
                email=user_email,
                name=current_user.get("name", ""),
                profile_data=current_user,
                avatar_url=current_user.get("profilePictureUrl")
            )
            await session.commit()
        
        return UserResponse.model_validate(user)
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")


@router.get("/{user_id}/organizations", response_model=UserOrganizationsResponse)
async def get_user_organizations(
    user_id: UUID,
    db_client: DatabaseClient = Depends(get_db_client),
    session: AsyncSession = Depends(get_async_session),
    current_user: dict = Depends(get_current_user)  # Require authentication
):
    """Get user's organizations."""
    try:
        # Verify user exists
        user = await db_client.get_user_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        memberships = await db_client.get_user_organizations(session, user_id)
        
        organizations = []
        for membership in memberships:
            organizations.append({
                "organization_id": membership.organization.id,
                "organization_name": membership.organization.name,
                "organization_slug": membership.organization.slug,
                "role": membership.role,
                "permissions": membership.permissions,
                "joined_at": membership.joined_at,
                "is_active": membership.is_active
            })
        
        return UserOrganizationsResponse(
            organizations=organizations,
            total=len(organizations)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user organizations: {str(e)}")
